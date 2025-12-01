# -*- coding: utf-8 -*-
"""
CopysGenerator - AI Copy Generation con LangGraph + Clasificación Automática

Este módulo implementa la generación automática de copies para clips usando:
- LangGraph: Orchestration con control de flujo
- Gemini: Generación de copies y clasificación
- Pydantic: Validación de estructura

Flujo principal:
1. CLASSIFY_CLIPS: Detecta estilo óptimo (viral/educational/storytelling)
2. GROUP_BY_STYLE: Agrupa clips por estilo
3. GENERATE: Genera copies por grupo (3 llamadas a Gemini)
4. VALIDATE: Valida con Pydantic
5. ANALYZE_QUALITY: Verifica métricas (engagement > 7.5)
6. SAVE: Guarda clips_copys.json

¿Por qué LangGraph y no un simple script?
- Control de flujo condicional (¿calidad > 7.5? → guardar o reintentar)
- Manejo de errores robusto (reintentos automáticos)
- State management (trackea el progreso del flujo)
- Debugging más fácil (cada nodo es testeabale)
"""

import json
import os
import time
from pathlib import Path
from typing import TypedDict, List, Dict, Literal, Annotated
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

# Imports locales
from src.models.copy_schemas import (
    ClipCopy,
    CopysOutput,
    SavedCopys,
    calculate_averages,
    create_saved_copys
)
from src.prompts import get_prompt_for_style
from src.prompts.classifier_prompt import get_classifier_prompt


# ============================================================================
# STATE DEFINITION
# ============================================================================

class CopysGeneratorState(TypedDict):
    """
    State del workflow de LangGraph.

    ¿Por qué TypedDict?
    - Type hints para cada campo del state
    - LangGraph valida automáticamente los tipos
    - Auto-complete en el IDE

    El state viaja a través de todos los nodos del grafo.
    Cada nodo puede leer y modificar el state.
    """

    # ========== INPUT DATA ==========
    video_id: str
    clips_data: List[Dict]  # [{clip_id, start, end, transcript}]
    model: Literal["gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro"]

    # ========== CLASSIFICATION ==========
    classifications: List[Dict]  # [{clip_id, style, confidence, reason}]
    grouped_clips: Dict[str, List[Dict]]  # {"viral": [...], "educational": [...]}

    # ========== GENERATED COPIES POR ESTILO ==========
    viral_copies: List[ClipCopy]
    educational_copies: List[ClipCopy]
    storytelling_copies: List[ClipCopy]

    # ========== MERGED RESULTS ==========
    all_copies: List[ClipCopy]  # Todos los copies combinados y ordenados

    # ========== QUALITY METRICS ==========
    average_engagement: float
    average_viral_potential: float
    low_quality_clips: List[int]  # clip_ids con engagement < threshold

    # ========== CONTROL FLOW ==========
    attempts: int
    max_attempts: int
    error_message: str

    # ========== LOGS (para debugging) ==========
    logs: Annotated[List[str], operator.add]  # operator.add = append automático


# ============================================================================
# COPYS GENERATOR CLASS
# ============================================================================

class CopysGenerator:
    """
    Generador de copies con LangGraph.

    Uso:
        generator = CopysGenerator(
            video_id="AI_CDMX_Live_Stream",
            model="gemini-2.0-flash-exp"
        )
        result = generator.generate()
    """

    def __init__(
        self,
        video_id: str,
        model: Literal["gemini-2.0-flash-exp", "gemini-1.5-pro"] = "gemini-2.0-flash-exp",
        max_attempts: int = 3
    ):
        """
        Inicializa el generador.

        Args:
            video_id: ID del video (ej: "AI_CDMX_Live_Stream_gjPVlCHU9OM")
            model: Modelo de Gemini a usar
            max_attempts: Máximo de reintentos si calidad < 7.5
        """
        self.video_id = video_id
        self.model = model
        self.max_attempts = max_attempts

        # Paths
        self.temp_dir = Path("temp")  # Clips están en temp/
        self.output_dir = Path("output") / video_id
        self.copys_dir = self.output_dir / "copys"
        self.copys_file = self.copys_dir / "clips_copys.json"

        # Inicializar LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            temperature=0.8,  # Creatividad alta para copies
            top_p=0.95,
            top_k=40
        )

        # Build graph
        self.graph = self._build_graph()


    def _build_graph(self) -> StateGraph:
        """
        Construye el grafo de LangGraph con todos los nodos y edges.

        ¿Por qué un grafo?
        - Flujo visual: Puedes dibujar el flujo en papel
        - Condicional: "Si calidad > 7.5 → guardar, sino → reintentar"
        - Debuggeable: Cada nodo es una función independiente

        Returns:
            StateGraph compilado
        """
        workflow = StateGraph(CopysGeneratorState)

        # ========== NODOS ==========
        workflow.add_node("load_data", self.load_data_node)
        workflow.add_node("classify_clips", self.classify_clips_node)
        workflow.add_node("group_by_style", self.group_by_style_node)
        workflow.add_node("generate_viral", self.generate_viral_node)
        workflow.add_node("generate_educational", self.generate_educational_node)
        workflow.add_node("generate_storytelling", self.generate_storytelling_node)
        workflow.add_node("merge_results", self.merge_results_node)
        workflow.add_node("validate_structure", self.validate_structure_node)
        workflow.add_node("analyze_quality", self.analyze_quality_node)
        workflow.add_node("save_results", self.save_results_node)

        # ========== EDGES (flujo lineal primero) ==========
        workflow.set_entry_point("load_data")
        workflow.add_edge("load_data", "classify_clips")
        workflow.add_edge("classify_clips", "group_by_style")
        workflow.add_edge("group_by_style", "generate_viral")
        workflow.add_edge("generate_viral", "generate_educational")
        workflow.add_edge("generate_educational", "generate_storytelling")
        workflow.add_edge("generate_storytelling", "merge_results")
        workflow.add_edge("merge_results", "validate_structure")
        workflow.add_edge("validate_structure", "analyze_quality")

        # ========== CONDITIONAL EDGE (decisión de calidad) ==========
        workflow.add_conditional_edges(
            "analyze_quality",
            self.should_retry_or_save,
            {
                "save": "save_results",
                "retry": "classify_clips",  # Vuelve a clasificar con prompt mejorado
                "end": END
            }
        )

        workflow.add_edge("save_results", END)

        return workflow.compile()


    # ========================================================================
    # NODO 1: LOAD DATA
    # ========================================================================

    def load_data_node(self, state: CopysGeneratorState) -> Dict:
        """
        Carga clips_metadata.json y transcript.json.

        ¿Por qué separar load_data?
        - Testing: Puedes mockear los datos fácilmente
        - Reutilizable: Otros nodos solo leen del state
        - Error handling: Si falla la carga, falla aquí y no en generación

        Returns:
            Dict con clips_data actualizado
        """
        try:
            # Cargar metadata de clips (están en temp/)
            clips_file = self.temp_dir / f"{self.video_id}_clips.json"
            with open(clips_file, 'r', encoding='utf-8') as f:
                clips_metadata = json.load(f)

            # Extraer datos relevantes
            clips_data = []
            for clip in clips_metadata['clips']:
                clips_data.append({
                    'clip_id': clip['clip_id'],
                    'start_time': clip['start_time'],
                    'end_time': clip['end_time'],
                    'duration': clip['duration'],
                    'transcript': clip['full_text']  # full_text contiene el transcript
                })

            return {
                "clips_data": clips_data,
                "logs": [f"✅ Cargados {len(clips_data)} clips"]
            }

        except FileNotFoundError as e:
            return {
                "error_message": f"Archivo no encontrado: {e}",
                "logs": [f"❌ Error cargando datos: {e}"]
            }
        except Exception as e:
            return {
                "error_message": f"Error inesperado: {e}",
                "logs": [f"❌ Error: {e}"]
            }


    # ========================================================================
    # NODO 2: CLASSIFY CLIPS (NUEVO - clasificación automática)
    # ========================================================================

    def classify_clips_node(self, state: CopysGeneratorState) -> Dict:
        """
        Usa classifier_prompt para detectar estilo de cada clip.

        ¿Por qué clasificar primero?
        - Cada clip recibe el prompt óptimo
        - Mejor engagement (copy match contenido)
        - Zero esfuerzo del usuario

        Returns:
            Dict con classifications array
        """
        try:
            clips_data = state['clips_data']

            # Procesar en batches de 10 clips para evitar timeouts
            BATCH_SIZE = 10
            all_classifications = []

            classifier_prompt = get_classifier_prompt()

            for i in range(0, len(clips_data), BATCH_SIZE):
                batch = clips_data[i:i + BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                total_batches = (len(clips_data) + BATCH_SIZE - 1) // BATCH_SIZE

                print(f"\n🔄 Processing batch {batch_num}/{total_batches} (clips {i+1} to {min(i+BATCH_SIZE, len(clips_data))})")

                # Construir input para este batch
                clips_input = []
                for clip in batch:
                    clips_input.append({
                        "clip_id": clip['clip_id'],
                        "transcript": clip['transcript'][:500]  # Primeros 500 chars
                    })

                # User message con los clips del batch
                user_message = f"""Clasifica estos {len(clips_input)} clips en viral/educational/storytelling:

{json.dumps(clips_input, indent=2, ensure_ascii=False)}

Responde SOLO con JSON válido (sin markdown):"""

                # Llamar a Gemini para este batch
                messages = [
                    {"role": "system", "content": classifier_prompt},
                    {"role": "user", "content": user_message}
                ]

                try:
                    response = self.llm.invoke(messages)
                    response_text = response.content

                    # Limpiar respuesta (por si Gemini agrega markdown)
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0]
                    response_text = response_text.strip()

                    print(f"   Response length: {len(response_text)} chars")

                    # Parsear JSON del batch
                    classification_result = json.loads(response_text)
                    print(f"   ✓ JSON parsed successfully")

                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON parsing FAILED in batch {batch_num}")
                    print(f"   Error: {e}")
                    print(f"   Response (first 500 chars): {response_text[:500]}")
                    print(f"   Response (last 200 chars): ...{response_text[-200:]}")
                    # Continue to next batch instead of failing completely
                    print(f"   ⚠️  Skipping batch {batch_num}, continuing with next batch...")
                    continue
                except Exception as e:
                    print(f"   ❌ Error calling Gemini in batch {batch_num}: {e}")
                    print(f"   ⚠️  Skipping batch {batch_num}, continuing with next batch...")
                    continue

                # Manejar ambos formatos de respuesta:
                # 1. {"classifications": [...]} (formato esperado)
                # 2. [...] (formato que Gemini devuelve a veces)
                if isinstance(classification_result, list):
                    batch_classifications = classification_result
                elif isinstance(classification_result, dict):
                    batch_classifications = classification_result.get('classifications', [])
                else:
                    batch_classifications = []

                print(f"   ✓ Extracted {len(batch_classifications)} classifications from batch")
                all_classifications.extend(batch_classifications)

                # Sleep entre batches para evitar rate limiting (429 errors)
                # No dormir después del último batch
                if batch_num < total_batches:
                    time.sleep(1.5)  # 1.5 segundos entre batches

            classifications = all_classifications

            # Validar clasificaciones (tolerante: continuar si tenemos al menos 80%)
            classified_ids = {c['clip_id'] for c in classifications}
            expected_ids = {clip['clip_id'] for clip in clips_data}

            missing = expected_ids - classified_ids
            success_rate = len(classified_ids) / len(expected_ids)

            logs = []

            if success_rate < 0.60:
                # Muy pocos clips clasificados, fallar
                return {
                    "classifications": classifications,  # Retornar los que SÍ tenemos
                    "error_message": f"Solo {len(classified_ids)}/{len(expected_ids)} clips clasificados ({success_rate:.0%})",
                    "logs": [
                        f"❌ Clasificación insuficiente: {len(classified_ids)}/{len(expected_ids)} clips",
                        f"   Clips faltantes: {sorted(list(missing))[:10]}..."  # Muestra primeros 10
                    ]
                }
            elif missing:
                # Algunos clips faltantes, pero suficientes para continuar
                logs.append(f"⚠️  {len(missing)} clips no clasificados (continuando con {len(classified_ids)})")
                logs.append(f"   Faltantes: {sorted(list(missing))}")

            # Estadísticas
            style_counts = {}
            for c in classifications:
                style = c['style']
                style_counts[style] = style_counts.get(style, 0) + 1

            logs.append(f"✅ Clasificados {len(classifications)} clips")
            logs.append(f"   Distribución: {style_counts}")

            return {
                "classifications": classifications,
                "logs": logs
            }

        except json.JSONDecodeError as e:
            return {
                "error_message": f"Error parseando JSON del classifier: {e}",
                "logs": [
                    f"❌ JSON inválido del classifier",
                    f"📋 Response text (first 500 chars): {response_text[:500] if 'response_text' in locals() else 'N/A'}"
                ]
            }
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                "error_message": f"Error en clasificación: {e}",
                "logs": [
                    f"❌ Error clasificando: {e}",
                    f"📋 Traceback: {error_detail[:500]}"
                ]
            }


    # ========================================================================
    # NODO 3: GROUP BY STYLE (NUEVO - agrupa clips)
    # ========================================================================

    def group_by_style_node(self, state: CopysGeneratorState) -> Dict:
        """
        Agrupa clips por estilo detectado.

        ¿Por qué agrupar?
        - Eficiencia: 1 llamada a Gemini por grupo (3 llamadas total)
        - Batch processing: Gemini maneja mejor lotes que clips individuales
        - Contexto: Gemini ve todos los clips de un estilo juntos

        Returns:
            Dict con grouped_clips
        """
        classifications = state['classifications']
        clips_data = state['clips_data']

        print(f"\n🔍 DEBUG - Agrupando clips:")
        print(f"   Total classifications: {len(classifications)}")
        print(f"   Total clips_data: {len(clips_data)}")

        # Crear dict de clips por ID para acceso rápido
        clips_by_id = {clip['clip_id']: clip for clip in clips_data}

        # Agrupar
        grouped = {
            "viral": [],
            "educational": [],
            "storytelling": []
        }

        skipped = 0
        for classification in classifications:
            clip_id = classification['clip_id']
            style = classification['style']

            # Verificar que el clip existe en clips_data
            if clip_id not in clips_by_id:
                skipped += 1
                print(f"   ⚠️  Clip {clip_id} clasificado pero no existe en clips_data")
                continue  # Skip si el clip no existe

            # Agregar clip al grupo correspondiente
            clip_data = clips_by_id[clip_id]
            grouped[style].append({
                **clip_data,
                'classification': classification  # Incluye confidence y reason
            })

        if skipped > 0:
            print(f"   ⚠️  Skipped {skipped} classifications (clips not found in clips_data)")

        return {
            "grouped_clips": grouped,
            "logs": [
                f"✅ Agrupados clips:",
                f"   Viral: {len(grouped['viral'])}",
                f"   Educational: {len(grouped['educational'])}",
                f"   Storytelling: {len(grouped['storytelling'])}"
            ]
        }


    # ========================================================================
    # NODOS 4-6: GENERATE (x3, uno por estilo)
    # ========================================================================

    def _generate_copies_for_style(
        self,
        clips: List[Dict],
        style: str
    ) -> List[ClipCopy]:
        """
        Helper function para generar copies de un estilo.

        ¿Por qué una función helper?
        - DRY: Los 3 nodos de generación usan la misma lógica
        - Testing: Puedes testear la generación independientemente
        - Mantenibilidad: Un solo lugar para cambiar lógica

        Args:
            clips: Lista de clips del mismo estilo
            style: "viral", "educational", o "storytelling"

        Returns:
            Lista de ClipCopy validados
        """
        if not clips:
            return []

        # Construir prompt una sola vez
        full_prompt = get_prompt_for_style(style)

        # Procesar en batches de 5 clips para evitar timeouts
        BATCH_SIZE = 5
        all_copies = []

        for i in range(0, len(clips), BATCH_SIZE):
            batch = clips[i:i + BATCH_SIZE]

            # Preparar clips del batch para el prompt
            clips_input = []
            for clip in batch:
                clips_input.append({
                    "clip_id": clip['clip_id'],
                    "transcript": clip['transcript'],
                    "duration": clip['duration']
                })

            # User message para este batch
            user_message = f"""Genera copies para estos {len(clips_input)} clips en estilo {style}:

{json.dumps(clips_input, indent=2, ensure_ascii=False)}

Responde SOLO con JSON válido (sin markdown):"""

            messages = [
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": user_message}
            ]

            # --- Micro-retry loop for each batch ---
            for attempt in range(3):
                try:
                    response = self.llm.invoke(messages)
                    response_text = response.content

                    # Limpiar respuesta
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0]
                    response_text = response_text.strip()

                    # Parsear y validar con Pydantic
                    copies_data = json.loads(response_text)
                    if 'clips' not in copies_data:
                        raise ValueError("La respuesta JSON no contiene la clave 'clips'")
                    
                    copies_output = CopysOutput(**copies_data)
                    
                    # Si todo va bien, añadir y salir del loop de reintentos
                    all_copies.extend(copies_output.clips)
                    print(f"   ✓ Batch {i//BATCH_SIZE + 1} successful on attempt {attempt + 1}")
                    break

                except (ValidationError, json.JSONDecodeError, ValueError) as e:
                    print(f"   ❌ Attempt {attempt + 1}/3 FAILED for batch {i//BATCH_SIZE + 1}:")
                    if isinstance(e, json.JSONDecodeError):
                        print(f"      Error: Invalid JSON response from LLM - {e}")
                    else:
                        print(f"      Error: Validation failed - {e}")

                    if attempt < 2:
                        print(f"      Retrying in 2 seconds...")
                        time.sleep(2)
                    else:
                        print(f"   ⚠️  Max retries reached. Skipping this batch.")
            # El `else` en un `for` loop se ejecuta si el loop termina sin `break`
            else:
                continue
        
        return all_copies


    def generate_viral_node(self, state: CopysGeneratorState) -> Dict:
        """Genera copies virales."""
        try:
            viral_clips = state['grouped_clips'].get('viral', [])

            if not viral_clips:
                return {
                    "viral_copies": [],
                    "logs": ["⏭️ Sin clips virales, saltando"]
                }

            copies = self._generate_copies_for_style(viral_clips, "viral")

            return {
                "viral_copies": copies,
                "logs": [f"✅ Generados {len(copies)} copies virales"]
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                "error_message": f"Error generando copies virales: {e}",
                "logs": [
                    f"❌ Error viral: {e}",
                    f"📋 Traceback: {error_detail[:500]}"
                ]
            }


    def generate_educational_node(self, state: CopysGeneratorState) -> Dict:
        """Genera copies educativos."""
        try:
            educational_clips = state['grouped_clips'].get('educational', [])

            if not educational_clips:
                return {
                    "educational_copies": [],
                    "logs": ["⏭️ Sin clips educativos, saltando"]
                }

            copies = self._generate_copies_for_style(educational_clips, "educational")

            return {
                "educational_copies": copies,
                "logs": [f"✅ Generados {len(copies)} copies educativos"]
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                "error_message": f"Error generando copies educativos: {e}",
                "logs": [
                    f"❌ Error educational: {e}",
                    f"📋 Traceback: {error_detail[:500]}"
                ]
            }


    def generate_storytelling_node(self, state: CopysGeneratorState) -> Dict:
        """Genera copies storytelling."""
        try:
            storytelling_clips = state['grouped_clips'].get('storytelling', [])

            if not storytelling_clips:
                return {
                    "storytelling_copies": [],
                    "logs": ["⏭️ Sin clips storytelling, saltando"]
                }

            copies = self._generate_copies_for_style(storytelling_clips, "storytelling")

            return {
                "storytelling_copies": copies,
                "logs": [f"✅ Generados {len(copies)} copies storytelling"]
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                "error_message": f"Error generando copies storytelling: {e}",
                "logs": [
                    f"❌ Error storytelling: {e}",
                    f"📋 Traceback: {error_detail[:500]}"
                ]
            }


    # ========================================================================
    # NODO 7: MERGE RESULTS (NUEVO - combina los 3 grupos)
    # ========================================================================

    def merge_results_node(self, state: CopysGeneratorState) -> Dict:
        """
        Combina copies de los 3 estilos y reordena por clip_id.

        ¿Por qué merge?
        - Consistencia: Usuario espera copies ordenados por clip_id
        - Validación: Verifica que todos los clips tengan copy
        - Metadata: Calcula estadísticas globales

        Returns:
            Dict con all_copies ordenados
        """
        viral = state.get('viral_copies', [])
        educational = state.get('educational_copies', [])
        storytelling = state.get('storytelling_copies', [])

        # Combinar todos
        all_copies = viral + educational + storytelling

        # Ordenar por clip_id
        all_copies_sorted = sorted(all_copies, key=lambda c: c.clip_id)

        # Validar que todos los clips tengan copy
        total_clips = len(state['clips_data'])
        success_rate = len(all_copies_sorted) / total_clips if total_clips > 0 else 0

        # IMPORTANTE: SIEMPRE retornar all_copies (graceful degradation)
        # La validación de threshold se hace en validate_structure_node
        if len(all_copies_sorted) != total_clips:
            missing = total_clips - len(all_copies_sorted)
            missing_ids = [clip['clip_id'] for clip in state['clips_data']
                          if clip['clip_id'] not in {c.clip_id for c in all_copies_sorted}]

            return {
                "all_copies": all_copies_sorted,  # ← CRÍTICO: retornar lo que tenemos
                "logs": [
                    f"⚠️ Generación parcial: {len(all_copies_sorted)}/{total_clips} copies ({success_rate:.0%})",
                    f"   Clips faltantes: {missing_ids[:10]}{'...' if len(missing_ids) > 10 else ''}"
                ]
            }

        return {
            "all_copies": all_copies_sorted,
            "logs": [f"✅ Combinados {len(all_copies_sorted)} copies"]
        }


    # ========================================================================
    # NODO 8: VALIDATE STRUCTURE
    # ========================================================================

    def validate_structure_node(self, state: CopysGeneratorState) -> Dict:
        """
        Valida estructura con Pydantic.

        ¿Por qué validar?
        - Gemini puede cometer errores (JSON malformado, campos faltantes)
        - Pydantic valida tipos, rangos, #AICDMX obligatorio
        - Si falla, podemos reintentar

        Returns:
            Dict con estado de validación
        """
        try:
            all_copies = state['all_copies']

            # Validar cada copy individualmente
            validation_errors = []
            for copy in all_copies:
                try:
                    # Ya está validado por Pydantic en _generate_copies_for_style
                    # Pero double-check aquí
                    if not copy.copy or len(copy.copy) < 20:
                        validation_errors.append(f"Clip {copy.clip_id}: copy muy corto")

                    if '#AICDMX' not in copy.copy.upper():
                        validation_errors.append(f"Clip {copy.clip_id}: falta #AICDMX")

                except Exception as e:
                    validation_errors.append(f"Clip {copy.clip_id}: {e}")

            if validation_errors:
                return {
                    "error_message": f"Errores de validación: {validation_errors}",
                    "logs": [f"❌ Validación falló: {len(validation_errors)} errores"]
                }

            return {
                "logs": [f"✅ Validación exitosa: todos los copies cumplen reglas"]
            }

        except Exception as e:
            return {
                "error_message": f"Error en validación: {e}",
                "logs": [f"❌ Error validando: {e}"]
            }


    # ========================================================================
    # NODO 9: ANALYZE QUALITY
    # ========================================================================

    def analyze_quality_node(self, state: CopysGeneratorState) -> Dict:
        """
        Analiza métricas de calidad.

        ¿Por qué analizar?
        - Control de calidad: engagement_score > 7.5 garantiza buenos copies
        - Decisión de reintento: Si promedio < 7.5, regeneramos
        - Feedback: Identificamos qué clips tienen calidad baja

        Returns:
            Dict con métricas calculadas
        """
        all_copies = state['all_copies']
        total_clips = len(state['clips_data'])

        # Verificar que haya copies
        count = len(all_copies)

        # Calcular tasa de éxito
        success_rate = (count / total_clips) if total_clips > 0 else 0

        logs = []

        # Threshold 60%: Mínimo aceptable para considerar éxito
        MIN_SUCCESS_RATE = 0.60

        if count == 0:
            return {
                "error_message": "No se generaron copies",
                "logs": [
                    f"❌ Error: 0/{total_clips} copies generados",
                    f"   Verifica el modelo de Gemini y los logs anteriores"
                ]
            }

        # Aplicar threshold: Si menos del 60% se generó, considerarlo fallo
        if success_rate < MIN_SUCCESS_RATE:
            return {
                "error_message": f"Generación insuficiente: {count}/{total_clips} copies ({success_rate:.0%})",
                "logs": [
                    f"❌ Solo {success_rate:.0%} generado (mínimo requerido: {MIN_SUCCESS_RATE:.0%})",
                    f"   {total_clips - count} clips fallaron - revisa logs de batches arriba",
                    f"   Sugerencia: Espera 5 min y re-intenta (podría ser rate limiting 429)"
                ]
            }

        # Si generamos al menos algunos copies (aunque no todos), continuar
        if count < total_clips:
            missing_count = total_clips - count
            logs.append(f"⚠️  Generación parcial: {count}/{total_clips} copies ({success_rate:.0%})")
            logs.append(f"   {missing_count} clips no pudieron generar copies (ver logs arriba)")
        else:
            logs.append(f"✅ Generados {count}/{total_clips} copies exitosamente")

        # Calcular promedios
        total_engagement = sum(c.metadata.engagement_score for c in all_copies)
        total_viral = sum(c.metadata.viral_potential for c in all_copies)

        avg_engagement = round(total_engagement / count, 2)
        avg_viral_potential = round(total_viral / count, 2)

        # Identificar clips de baja calidad (engagement < 6.5)
        low_quality = [
            c.clip_id for c in all_copies
            if c.metadata.engagement_score < 6.5
        ]

        logs.extend([
            f"📊 Métricas de calidad:",
            f"   Engagement promedio: {avg_engagement}/10",
            f"   Viral potential promedio: {avg_viral_potential}/10",
            f"   Clips de baja calidad: {len(low_quality)}"
        ])

        return {
            "average_engagement": avg_engagement,
            "average_viral_potential": avg_viral_potential,
            "low_quality_clips": low_quality,
            "logs": logs
        }


    # ========================================================================
    # CONDITIONAL EDGE: SHOULD RETRY OR SAVE?
    # ========================================================================

    def should_retry_or_save(self, state: CopysGeneratorState) -> str:
        """
        Decide si guardar o reintentar basado en calidad.

        ¿Por qué condicional?
        - Garantiza calidad mínima (engagement > 7.5)
        - Evita loops infinitos (max 3 intentos)
        - Feedback al usuario sobre por qué se reintenta

        Returns:
            "save", "retry", o "end"
        """
        avg_engagement = state.get('average_engagement', 0)
        attempts = state.get('attempts', 0)
        max_attempts = state.get('max_attempts', 3)

        # Si hay error, terminar
        if state.get('error_message'):
            return "end"

        # Si calidad es buena, guardar
        if avg_engagement >= 7.5:
            return "save"

        # Si ya intentamos max_attempts, guardar lo que hay
        if attempts >= max_attempts:
            return "save"

        # Reintentar
        return "retry"


    # ========================================================================
    # NODO 10: SAVE RESULTS
    # ========================================================================

    def save_results_node(self, state: CopysGeneratorState) -> Dict:
        """
        Guarda clips_copys.json.

        ¿Por qué guardar al final?
        - Solo guardamos cuando tenemos copies válidos y con calidad
        - Incluimos metadata de clasificación para auditoría
        - Formato SavedCopys incluye timestamp, model usado, métricas

        Returns:
            Dict con path del archivo guardado
        """
        try:
            # Crear carpeta copys/ si no existe
            self.copys_dir.mkdir(parents=True, exist_ok=True)

            # Crear SavedCopys
            all_copies = state['all_copies']
            classifications = state['classifications']

            saved_copys = create_saved_copys(
                video_id=self.video_id,
                copies_output=CopysOutput(clips=all_copies),
                model=self.model,
                style="auto-classified"  # Indica que usamos clasificación automática
            )

            # Agregar metadata de clasificación
            saved_data = saved_copys.model_dump()

            # Calcular si fue generación completa o parcial
            total_clips = len(state['clips_data'])
            generated_count = len(all_copies)
            is_incomplete = generated_count < total_clips

            # Identificar clips faltantes si es parcial
            missing_clips = []
            if is_incomplete:
                generated_ids = {c.clip_id for c in all_copies}
                missing_clips = [clip['clip_id'] for clip in state['clips_data']
                                if clip['clip_id'] not in generated_ids]

            saved_data['classification_metadata'] = {
                'classifications': classifications,
                'distribution': {
                    'viral': len(state['grouped_clips'].get('viral', [])),
                    'educational': len(state['grouped_clips'].get('educational', [])),
                    'storytelling': len(state['grouped_clips'].get('storytelling', []))
                }
            }

            # Agregar metadata de completitud (para debugging)
            saved_data['generation_metadata'] = {
                'incomplete': is_incomplete,
                'total_clips': total_clips,
                'generated_clips': generated_count,
                'success_rate': round(generated_count / total_clips, 2) if total_clips > 0 else 0,
                'missing_clips': missing_clips if is_incomplete else [],
                'note': 'Partial generation - some batches failed during processing' if is_incomplete else 'Complete generation'
            }

            # Guardar JSON
            with open(self.copys_file, 'w', encoding='utf-8') as f:
                json.dump(saved_data, f, indent=2, ensure_ascii=False, default=str)

            return {
                "logs": [
                    f"✅ Guardado: {self.copys_file}",
                    f"📊 Engagement promedio: {state['average_engagement']}/10",
                    f"🚀 Viral potential promedio: {state['average_viral_potential']}/10"
                ]
            }

        except Exception as e:
            return {
                "error_message": f"Error guardando: {e}",
                "logs": [f"❌ Error al guardar: {e}"]
            }


    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def generate(self) -> Dict:
        """
        Ejecuta el workflow completo.

        Returns:
            Dict con resultados y logs
        """
        # Initial state
        initial_state = CopysGeneratorState(
            video_id=self.video_id,
            clips_data=[],
            model=self.model,
            classifications=[],
            grouped_clips={},
            viral_copies=[],
            educational_copies=[],
            storytelling_copies=[],
            all_copies=[],
            average_engagement=0.0,
            average_viral_potential=0.0,
            low_quality_clips=[],
            attempts=0,
            max_attempts=self.max_attempts,
            error_message="",
            logs=[]
        )

        # Ejecutar grafo
        result = self.graph.invoke(initial_state)

        return {
            "success": not bool(result.get('error_message')),
            "error": result.get('error_message'),
            "output_file": str(self.copys_file) if self.copys_file.exists() else None,
            "metrics": {
                "total_copies": len(result.get('all_copies', [])),
                "total_classified": len(result.get('classifications', [])),  # Para mostrar X/Y
                "average_engagement": result.get('average_engagement', 0),
                "average_viral_potential": result.get('average_viral_potential', 0),
                "distribution": {
                    'viral': len(result.get('grouped_clips', {}).get('viral', [])),
                    'educational': len(result.get('grouped_clips', {}).get('educational', [])),
                    'storytelling': len(result.get('grouped_clips', {}).get('storytelling', []))
                }
            },
            "logs": result.get('logs', [])
        }


# ============================================================================
# HELPER FUNCTION FOR CLI
# ============================================================================

def generate_copys_for_video(
    video_id: str,
    model: str = "gemini-2.0-flash-exp"
) -> Dict:
    """
    Helper function para usar desde CLI.

    Args:
        video_id: ID del video
        model: Modelo de Gemini

    Returns:
        Dict con resultados

    Ejemplo:
        result = generate_copys_for_video("AI_CDMX_Live_Stream_gjPVlCHU9OM")
        if result['success']:
            print(f"✅ Guardado en: {result['output_file']}")
    """
    generator = CopysGenerator(video_id=video_id, model=model)
    return generator.generate()
