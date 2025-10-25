# -*- coding: utf-8 -*-
"""
Content Presets - Configuraciones optimizadas por tipo de contenido

Cada tipo de video tiene características únicas que requieren
diferentes configuraciones para transcripción y generación de clips.
"""

from typing import Dict, Any


# Definición de presets por tipo de contenido
CONTENT_PRESETS = {
    "podcast": {
        "name": "Podcast/Interview",
        "description": "Multiple speakers, natural topic changes",
        "icon": "🎙️",

        # Configuración de transcripción
        "transcription": {
            "model_size": "small",  # Mayor precisión para múltiples voces
            "enable_diarization": True,  # Importante: detectar speakers
            "language": None,  # Auto-detect
        },

        # Configuración de clips
        "clips": {
            "method": "clipsai",  # ClipsAI funciona bien aquí
            "min_duration": 60,   # 1 minuto mínimo
            "max_duration": 300,  # 5 minutos máximo
            "prefer_speaker_changes": True,  # Cortar en cambios de speaker
        },

        # Metadata
        "use_case": "Ideal for conversations, interviews, panel discussions"
    },

    "tutorial": {
        "name": "Tutorial/Educational",
        "description": "Single speaker, structured content",
        "icon": "📚",

        "transcription": {
            "model_size": "base",
            "enable_diarization": False,  # Un solo speaker
            "language": None,
        },

        "clips": {
            "method": "clipsai",  # Detecta secciones/conceptos
            "min_duration": 45,
            "max_duration": 180,  # 3 minutos máximo
            "prefer_speaker_changes": False,
        },

        "use_case": "Perfect for how-to videos, courses, tutorials"
    },

    "livestream": {
        "name": "Livestream/Conference",
        "description": "Long-form, continuous topic",
        "icon": "🎥",

        "transcription": {
            "model_size": "medium",  # Mayor precisión para contenido largo
            "enable_diarization": False,
            "language": None,
        },

        "clips": {
            "method": "hybrid",  # Intenta ClipsAI, fallback a fixed_time
            "min_duration": 60,
            "max_duration": 90,  # Clips cortos para redes sociales
            "prefer_speaker_changes": False,
            "fixed_time_fallback": True,  # Importante para livestreams
        },

        "use_case": "Best for conferences, webinars, long presentations"
    },

    "documentary": {
        "name": "Documentary/Narrative",
        "description": "Narrated content with clear sections",
        "icon": "🎬",

        "transcription": {
            "model_size": "small",
            "enable_diarization": False,
            "language": None,
        },

        "clips": {
            "method": "clipsai",
            "min_duration": 90,
            "max_duration": 240,  # 4 minutos máximo
            "prefer_speaker_changes": False,
        },

        "use_case": "Great for story-driven content, documentaries"
    },

    "short_form": {
        "name": "Short-form Content",
        "description": "Quick videos, single concept",
        "icon": "⚡",

        "transcription": {
            "model_size": "base",  # Rápido es suficiente
            "enable_diarization": False,
            "language": None,
        },

        "clips": {
            "method": "fixed_time",  # Cortes simples
            "min_duration": 15,
            "max_duration": 60,
            "prefer_speaker_changes": False,
        },

        "use_case": "Optimized for TikTok, Reels, Shorts"
    },
}


def get_preset(content_type: str) -> Dict[str, Any]:
    """
    Obtiene la configuración para un tipo de contenido

    Args:
        content_type: Tipo de contenido (podcast, tutorial, livestream, etc.)

    Returns:
        Dict con configuración completa
    """
    return CONTENT_PRESETS.get(content_type, CONTENT_PRESETS["tutorial"])


def list_presets() -> Dict[str, str]:
    """
    Lista todos los presets disponibles

    Returns:
        Dict con {key: "icon + name"}
    """
    return {
        key: f"{preset['icon']} {preset['name']}"
        for key, preset in CONTENT_PRESETS.items()
    }


def get_preset_description(content_type: str) -> str:
    """
    Obtiene la descripción de un preset
    """
    preset = CONTENT_PRESETS.get(content_type, {})
    return preset.get("description", "No description available")
