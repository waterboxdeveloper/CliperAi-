# -*- coding: utf-8 -*-
"""
Pydantic Schemas para AI Copy Generation

Este módulo define los "contratos" de datos que Gemini DEBE cumplir.
Pydantic valida automáticamente:
- Tipos (int, str, float)
- Rangos (1-10, 0-1)
- Longitudes (max 150 chars)
- Valores permitidos (Literal["viral", "educational", ...])

Si Gemini se equivoca, Pydantic rechaza y LangGraph reintenta.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from datetime import datetime


# ============================================================================
# METADATA DE UN CLIP
# ============================================================================

class CopyMetadata(BaseModel):
    """
    Metadata predictivo generado por IA para un clip.

    ¿Por qué existe esto?
    - Gemini no solo genera el copy, también ANALIZA el contenido
    - Predice engagement, viral potential, sentiment
    - Estos datos te ayudan a decidir qué clips publicar primero

    Validaciones automáticas:
    - sentiment solo puede ser uno de los 7 valores definidos
    - scores están en rangos válidos (0-1, 1-10)
    - primary_topics tiene entre 3-5 items
    """

    sentiment: Literal[
        "educational",          # Explica algo, enseña
        "humorous",            # Gracioso, ligero
        "inspirational",       # Motivacional
        "controversial",       # Opinionado, debate
        "curious_educational", # Preguntas que educan
        "relatable",          # "Esto me pasa a mí"
        "storytelling"        # Narrativa, anécdota
    ] = Field(
        description="Tono emocional del contenido"
    )

    @field_validator('sentiment', mode='before')
    @classmethod
    def normalize_sentiment(cls, v):
        """
        Normaliza sentiments híbridos que Gemini inventa.

        Gemini a veces combina categorías:
        - "educational_storytelling" → "storytelling"
        - "humorous_relatable" → "humorous"
        - "inspirational_educational" → "educational"

        Estrategia: Tomar el primer sentiment válido que encontremos.
        """
        if not isinstance(v, str):
            return v

        # Sentiments válidos (en orden de prioridad)
        valid_sentiments = [
            "curious_educational",  # Primero el compuesto
            "educational",
            "humorous",
            "inspirational",
            "controversial",
            "relatable",
            "storytelling"
        ]

        # Si es válido, retornar directo
        if v in valid_sentiments:
            return v

        # Si es híbrido (contiene _), buscar el primer sentiment válido
        for valid in valid_sentiments:
            if valid in v:
                return valid

        # Si no matchea nada, intentar con la primera palabra
        first_word = v.split('_')[0]
        if first_word in valid_sentiments:
            return first_word

        # Último recurso: retornar "relatable" como default
        return "relatable"

    sentiment_score: float = Field(
        ge=0.0,  # ge = greater or equal (>=)
        le=1.0,  # le = less or equal (<=)
        description="Intensidad emocional (0=neutro, 1=muy fuerte)"
    )

    engagement_score: float = Field(
        ge=1.0,
        le=10.0,
        description="Predicción de likes/comments/shares (1-10)"
    )

    suggested_thumbnail_timestamp: float = Field(
        ge=0.0,
        description="Segundo exacto del clip ideal para thumbnail"
    )

    primary_topics: List[str] = Field(
        min_length=2,  # Mínimo 2 topics (relajado para tolerar duplicados)
        max_length=10,  # Máximo 10 (se truncará a 5 en el validador)
        description="Temas principales del clip"
    )

    hook_strength: Literal["very_high", "high", "medium", "low"] = Field(
        description="Qué tan efectivo es el primer segundo"
    )

    viral_potential: float = Field(
        ge=1.0,
        le=10.0,
        description="Probabilidad de volverse viral (1-10)"
    )

    # Validador custom: primary_topics no debe tener duplicados y máximo 5
    @field_validator('primary_topics')
    @classmethod
    def topics_must_be_unique_and_limited(cls, v):
        """
        ¿Por qué este validador?
        1. Gemini a veces repite topics: ["AI", "AI", "tech"]
        2. Gemini a veces genera más de 5 topics

        Este validador:
        - Elimina duplicados (case-insensitive)
        - Trunca a máximo 5 topics
        - Mantiene el orden original
        """
        # Elimina duplicados manteniendo orden
        seen = set()
        unique = []
        for topic in v:
            if topic.lower() not in seen:
                seen.add(topic.lower())
                unique.append(topic)

        # Truncar a 5 topics máximo
        if len(unique) > 5:
            return unique[:5]

        return unique


# ============================================================================
# COPY COMPLETO DE UN CLIP
# ============================================================================

class ClipCopy(BaseModel):
    """
    Copy/caption completo para un clip.

    ¿Por qué existe esto?
    - Combina el texto (copy) con el análisis (metadata)
    - El copy es lo que se publica en TikTok/Reels
    - El metadata te ayuda a decidir CUÁNDO y DÓNDE publicarlo

    Validaciones:
    - clip_id debe ser >= 1
    - copy debe tener entre 20-150 caracteres (TikTok limit)
    """

    clip_id: int = Field(
        ge=1,
        description="ID del clip (1, 2, 3, ...) - corresponde al archivo {clip_id}.mp4"
    )

    copy: str = Field(
        min_length=20,   # Muy corto = poco contexto
        max_length=200,  # Permisivo (se ajustará en validador)
        description="Caption completo con hashtags integrados"
    )

    metadata: CopyMetadata = Field(
        description="Análisis predictivo del clip"
    )

    # Validador 1: Truncar inteligentemente si > 150 chars
    # Validador 2: copy debe tener al menos 1 hashtag
    # Validador 3: copy DEBE incluir #AICDMX (branding obligatorio)
    @field_validator('copy', mode='before')
    @classmethod
    def truncate_and_validate_copy(cls, v):
        """
        Valida y ajusta el copy para cumplir reglas:
        1. MAX 150 caracteres (límite TikTok)
        2. DEBE tener hashtags
        3. DEBE incluir #AICDMX (branding)

        Si Gemini genera > 150 chars, trunca INTELIGENTEMENTE:
        - Mantiene mensaje principal
        - SIEMPRE conserva #AICDMX
        - Elimina segundo hashtag si es necesario
        """
        import re

        if not isinstance(v, str):
            return v

        # Si cabe, validar y retornar
        if len(v) <= 150:
            # Validar hashtags
            if '#' not in v:
                raise ValueError('Copy must contain at least one hashtag')
            if '#AICDMX' not in v.upper():
                raise ValueError('Copy must include #AICDMX hashtag for branding')
            return v

        # Si es muy largo, truncar inteligentemente
        # Estrategia: Eliminar segundo hashtag (que NO sea AICDMX)

        # Encontrar todos los hashtags
        hashtags = re.findall(r'#\w+', v)

        # Identificar hashtags que NO son AICDMX
        other_hashtags = [h for h in hashtags if h.upper() != '#AICDMX']

        # Si hay más de un hashtag además de AICDMX, eliminar el último
        if len(other_hashtags) > 0:
            # Eliminar el último hashtag que NO sea AICDMX
            last_other = other_hashtags[-1]
            v_truncated = v.replace(last_other, '').strip()

            # Limpiar espacios dobles
            v_truncated = re.sub(r'\s+', ' ', v_truncated)

            # Si ahora cabe, retornar
            if len(v_truncated) <= 150:
                return v_truncated

        # Si aún no cabe, truncar a 147 chars y agregar "..."
        # Asegurarnos de que #AICDMX esté presente
        if '#AICDMX' in v.upper():
            # Buscar posición de #AICDMX
            aicdmx_pos = v.upper().find('#AICDMX')

            # Si #AICDMX está cerca del final, mantenerlo
            if aicdmx_pos > 130:
                # Truncar antes de AICDMX y agregar
                v = v[:aicdmx_pos].strip() + ' #AICDMX'
            else:
                # Truncar a 147 chars y verificar que AICDMX esté
                v = v[:147] + '...'
                if '#AICDMX' not in v.upper():
                    # Reemplazar último hashtag con AICDMX
                    v = re.sub(r'#\w+(?!.*#\w+)', '#AICDMX', v)

        return v[:150]  # Garantizar que nunca exceda 150


# ============================================================================
# OUTPUT COMPLETO DE GEMINI
# ============================================================================

class CopysOutput(BaseModel):
    """
    Response completo que Gemini debe devolver.

    ¿Por qué existe esto?
    - Define la estructura EXACTA que esperamos de Gemini
    - Si Gemini devuelve algo diferente, Pydantic lo rechaza
    - LangGraph usa este rechazo para reintentar con mejor prompt

    Ejemplo de lo que Gemini DEBE devolver:
    {
      "clips": [
        {
          "clip_id": 1,
          "copy": "Amazing content 🤯 #AI #Tech",
          "metadata": {...}
        },
        ...
      ]
    }
    """

    clips: List[ClipCopy] = Field(
        min_length=1,  # Al menos 1 clip
        description="Lista de todos los clips con sus copies"
    )

    class Config:
        """
        Config de Pydantic que ayuda a Gemini.

        ¿Por qué json_schema_extra?
        - Cuando LangGraph construye el prompt, incluye este ejemplo
        - Gemini ve EXACTAMENTE cómo debe formatear la respuesta
        - Es como darle la "plantilla del examen"
        """
        json_schema_extra = {
            "example": {
                "clips": [
                    {
                        "clip_id": 1,
                        "copy": "Ever wondered why Q&As get chaotic? 🤔 This changes everything #TechMeetups #AI",
                        "metadata": {
                            "sentiment": "curious_educational",
                            "sentiment_score": 0.75,
                            "engagement_score": 8.5,
                            "suggested_thumbnail_timestamp": 12.5,
                            "primary_topics": ["meetups", "Q&A", "community"],
                            "hook_strength": "high",
                            "viral_potential": 7.8
                        }
                    }
                ]
            }
        }


# ============================================================================
# WRAPPER FINAL PARA GUARDAR EN JSON
# ============================================================================

class SavedCopys(BaseModel):
    """
    Estructura del archivo clips_copys.json que se guarda en disco.

    ¿Por qué existe esto?
    - CopysOutput es lo que Gemini devuelve
    - SavedCopys es lo que guardamos (+ metadata extra)
    - Incluye info como: cuándo se generó, qué modelo se usó, métricas promedio

    Este es el archivo que verás en: output/VIDEO_NAME/copys/clips_copys.json
    """

    video_id: str = Field(
        description="ID del video (ej: AI_CDMX_Live_Stream_gjPVlCHU9OM)"
    )

    generated_at: datetime = Field(
        description="Timestamp de cuándo se generaron los copies"
    )

    model: str = Field(
        description="Modelo usado: gemini-2.5-flash o gemini-2.5-pro"
    )

    total_clips: int = Field(
        ge=1,
        description="Cantidad total de clips procesados"
    )

    style: str = Field(
        description="Estilo usado: viral, educational, storytelling"
    )

    average_engagement: float = Field(
        ge=0.0,
        le=10.0,
        description="Engagement score promedio de todos los clips"
    )

    average_viral_potential: float = Field(
        ge=0.0,
        le=10.0,
        description="Viral potential promedio de todos los clips"
    )

    clips: List[ClipCopy] = Field(
        description="Array completo de clips con copies y metadata"
    )

    class Config:
        """
        Configuración para serialización.

        ¿Por qué json_encoders?
        - datetime no es JSON-serializable por defecto
        - Este encoder convierte datetime a ISO string automáticamente
        - Resultado: "2025-10-26T11:30:00" en el JSON
        """
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_averages(copies_output: CopysOutput) -> tuple[float, float]:
    """
    Calcula promedios de engagement y viral potential.

    ¿Por qué esta función?
    - LangGraph necesita estos promedios para DECIDIR si regenerar
    - Si avg_engagement < 7.5 → regenera con mejor prompt
    - Si avg_viral < 6.0 → cambia de estilo

    Args:
        copies_output: Output de Gemini (validado por Pydantic)

    Returns:
        (avg_engagement, avg_viral_potential)
    """
    if not copies_output.clips:
        return 0.0, 0.0

    total_engagement = sum(c.metadata.engagement_score for c in copies_output.clips)
    total_viral = sum(c.metadata.viral_potential for c in copies_output.clips)

    count = len(copies_output.clips)

    return (
        round(total_engagement / count, 2),
        round(total_viral / count, 2)
    )


def create_saved_copys(
    video_id: str,
    model: str,
    style: str,
    copies_output: CopysOutput
) -> SavedCopys:
    """
    Convierte CopysOutput (de Gemini) a SavedCopys (para guardar).

    ¿Por qué esta función?
    - Gemini devuelve solo los clips
    - Necesitamos agregar metadata: timestamp, modelo usado, promedios
    - Esta función "envuelve" el output de Gemini con info adicional

    Args:
        video_id: ID del video procesado
        model: Modelo usado (gemini-2.5-flash/pro)
        style: Estilo usado (viral/educational/storytelling)
        copies_output: Output validado de Gemini

    Returns:
        SavedCopys listo para guardar como JSON
    """
    avg_engagement, avg_viral = calculate_averages(copies_output)

    return SavedCopys(
        video_id=video_id,
        generated_at=datetime.now(),
        model=model,
        total_clips=len(copies_output.clips),
        style=style,
        average_engagement=avg_engagement,
        average_viral_potential=avg_viral,
        clips=copies_output.clips
    )
