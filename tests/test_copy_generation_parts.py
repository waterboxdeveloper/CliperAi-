#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test individual de cada parte del copy generator.

Este script prueba paso por paso:
1. Load data (cargar clips desde temp/)
2. Classify clips (clasificar en viral/educational/storytelling)
3. Group by style (agrupar por estilo)
4. Generate copies for ONE style (generar copies para un estilo)

Uso:
    uv run python tests/test_copy_generation_parts.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_google_genai import ChatGoogleGenerativeAI
from src.prompts import get_prompt_for_style
from src.prompts.classifier_prompt import get_classifier_prompt


def test_1_load_clips():
    """Test 1: Cargar clips desde temp/"""
    print("=" * 60)
    print("TEST 1: Load Clips from temp/")
    print("=" * 60)

    try:
        # Buscar archivo de clips
        temp_dir = Path("temp")
        clips_files = list(temp_dir.glob("*_clips.json"))

        if not clips_files:
            print("❌ FAIL: No se encontraron archivos *_clips.json en temp/")
            return None

        clips_file = clips_files[0]
        print(f"✓ Encontrado: {clips_file}")

        # Cargar clips
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
                'transcript': clip['full_text']
            })

        print(f"✓ Cargados {len(clips_data)} clips")
        print(f"✓ Primer clip ID: {clips_data[0]['clip_id']}")
        print(f"✓ Transcript preview: {clips_data[0]['transcript'][:100]}...")

        return clips_data

    except Exception as e:
        print(f"❌ FAIL: Error cargando clips")
        print(f"   Error: {e}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return None


def test_2_classify_one_clip(clips_data):
    """Test 2: Clasificar UN solo clip"""
    print("\n" + "=" * 60)
    print("TEST 2: Classify ONE Clip")
    print("=" * 60)

    if not clips_data:
        print("❌ SKIP: No hay clips cargados")
        return None

    try:
        # Tomar solo el primer clip
        clip = clips_data[0]

        # Inicializar LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7
        )

        # Prompt del classifier
        classifier_prompt = get_classifier_prompt()

        # Preparar input de UN clip
        clip_input = {
            "clip_id": clip['clip_id'],
            "transcript": clip['transcript'][:500]  # Primeros 500 chars
        }

        user_message = f"""Clasifica este clip en viral/educational/storytelling:

{json.dumps([clip_input], indent=2, ensure_ascii=False)}

Responde SOLO con JSON válido (sin markdown):"""

        # Llamar a Gemini
        messages = [
            {"role": "system", "content": classifier_prompt},
            {"role": "user", "content": user_message}
        ]

        print(f"Clasificando clip {clip['clip_id']}...")
        response = llm.invoke(messages)
        response_text = response.content.strip()

        # Limpiar respuesta
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        response_text = response_text.strip()

        print(f"\nRaw response:\n{response_text}\n")

        # Parsear JSON
        classification_result = json.loads(response_text)
        classifications = classification_result.get('classifications', [])

        if not classifications:
            print("❌ FAIL: No se generaron clasificaciones")
            return None

        classification = classifications[0]
        print(f"✓ Clip {classification['clip_id']} clasificado como: {classification['style']}")
        print(f"✓ Confidence: {classification.get('confidence', 'N/A')}")
        print(f"✓ Reason: {classification.get('reason', 'N/A')}")

        return classifications

    except Exception as e:
        print(f"❌ FAIL: Error clasificando clip")
        print(f"   Error: {e}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return None


def test_3_generate_copy_for_one_clip(clips_data, style="viral"):
    """Test 3: Generar copy para UN solo clip con un estilo específico"""
    print("\n" + "=" * 60)
    print(f"TEST 3: Generate Copy for ONE Clip ({style} style)")
    print("=" * 60)

    if not clips_data:
        print("❌ SKIP: No hay clips cargados")
        return None

    try:
        # Tomar solo el primer clip
        clip = clips_data[0]

        # Inicializar LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.8
        )

        # Prompt del estilo
        full_prompt = get_prompt_for_style(style)

        # Preparar input de UN clip
        clip_input = {
            "clip_id": clip['clip_id'],
            "transcript": clip['transcript'],
            "duration": clip['duration']
        }

        user_message = f"""Genera copies para este 1 clip en estilo {style}:

{json.dumps([clip_input], indent=2, ensure_ascii=False)}

Responde SOLO con JSON válido (sin markdown):"""

        # Llamar a Gemini
        messages = [
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": user_message}
        ]

        print(f"Generando copy para clip {clip['clip_id']} en estilo {style}...")
        response = llm.invoke(messages)
        response_text = response.content.strip()

        # Limpiar respuesta
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        response_text = response_text.strip()

        print(f"\nRaw response:\n{response_text}\n")

        # Parsear JSON
        copies_data = json.loads(response_text)

        if 'clips' not in copies_data:
            print("❌ FAIL: Respuesta no tiene campo 'clips'")
            print(f"   Keys en respuesta: {copies_data.keys()}")
            return None

        clips_copies = copies_data['clips']

        if not clips_copies:
            print("❌ FAIL: Lista de clips vacía")
            return None

        copy = clips_copies[0]
        print(f"✓ Copy generado:")
        print(f"   Clip ID: {copy['clip_id']}")
        print(f"   Copy: {copy['copy']}")
        print(f"   Engagement: {copy['metadata']['engagement_score']}/10")
        print(f"   Viral potential: {copy['metadata']['viral_potential']}/10")

        # Validar que tenga #AICDMX
        if '#AICDMX' not in copy['copy'].upper():
            print("⚠️  WARNING: El copy no incluye #AICDMX")

        return clips_copies

    except Exception as e:
        print(f"❌ FAIL: Error generando copy")
        print(f"   Error: {e}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return None


def test_4_generate_copies_batch(clips_data, style="viral", batch_size=5):
    """Test 4: Generar copies para un BATCH de clips"""
    print("\n" + "=" * 60)
    print(f"TEST 4: Generate Copies for BATCH ({batch_size} clips, {style} style)")
    print("=" * 60)

    if not clips_data:
        print("❌ SKIP: No hay clips cargados")
        return None

    try:
        # Tomar los primeros N clips
        batch = clips_data[:batch_size]

        # Inicializar LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.8
        )

        # Prompt del estilo
        full_prompt = get_prompt_for_style(style)

        # Preparar input del batch
        clips_input = []
        for clip in batch:
            clips_input.append({
                "clip_id": clip['clip_id'],
                "transcript": clip['transcript'],
                "duration": clip['duration']
            })

        user_message = f"""Genera copies para estos {len(clips_input)} clips en estilo {style}:

{json.dumps(clips_input, indent=2, ensure_ascii=False)}

Responde SOLO con JSON válido (sin markdown):"""

        # Llamar a Gemini
        messages = [
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": user_message}
        ]

        print(f"Generando copies para {len(batch)} clips en estilo {style}...")
        response = llm.invoke(messages)
        response_text = response.content.strip()

        # Limpiar respuesta
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        response_text = response_text.strip()

        print(f"\nRaw response (first 500 chars):\n{response_text[:500]}...\n")

        # Parsear JSON
        copies_data = json.loads(response_text)

        if 'clips' not in copies_data:
            print("❌ FAIL: Respuesta no tiene campo 'clips'")
            print(f"   Keys en respuesta: {copies_data.keys()}")
            return None

        clips_copies = copies_data['clips']

        if not clips_copies:
            print("❌ FAIL: Lista de clips vacía")
            return None

        print(f"✓ Se generaron {len(clips_copies)} copies")

        # Mostrar primeros 3
        for copy in clips_copies[:3]:
            print(f"\n  Clip {copy['clip_id']}:")
            print(f"    Copy: {copy['copy'][:80]}...")
            print(f"    Engagement: {copy['metadata']['engagement_score']}/10")

        return clips_copies

    except Exception as e:
        print(f"❌ FAIL: Error generando copies en batch")
        print(f"   Error: {e}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return None


def main():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "COPY GENERATOR PARTS TEST SUITE" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Test 1: Load clips
    clips_data = test_1_load_clips()
    if not clips_data:
        print("\n❌ Cannot continue without clips data")
        return 1

    # Test 2: Classify one clip
    test_2_classify_one_clip(clips_data)

    # Test 3: Generate copy for one clip
    test_3_generate_copy_for_one_clip(clips_data, style="viral")

    # Test 4: Generate copies for batch
    test_4_generate_copies_batch(clips_data, style="educational", batch_size=5)

    print("\n" + "=" * 60)
    print("TESTS COMPLETADOS")
    print("=" * 60)
    print("\nSi todos los tests pasaron, el problema está en cómo LangGraph")
    print("combina los resultados. Si algún test falló, ese es el problema.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
