# -*- coding: utf-8 -*-
"""
Prompts Module - AI Copy Generation Templates

Este módulo centraliza todos los prompts para diferentes estilos de copy.

¿Por qué este __init__.py?
- Facilita imports: `from src.prompts import get_prompt_for_style`
- Centraliza la lógica de selección de estilo
- Mantiene clean la interfaz para copys_generator.py

Estilos disponibles:
- viral: Máxima atención, hooks irresistibles
- educational: Valor educativo, claridad
- storytelling: Narrativa personal, conexión emocional
"""

from .base_prompts import build_base_system_prompt, SYSTEM_PROMPT, JSON_FORMAT_INSTRUCTIONS
# Spanish prompts (default - _es suffix)
from .viral_prompt_es import get_viral_prompt_es
from .educational_prompt_es import get_educational_prompt_es
from .storytelling_prompt_es import get_storytelling_prompt_es
# English prompts (_en suffix)
from .viral_prompt_en import get_viral_prompt_en
from .educational_prompt_en import get_educational_prompt_en
from .storytelling_prompt_en import get_storytelling_prompt_en


def get_prompt_for_style(style: str = "viral", language: str = "es") -> str:
    """
    Retorna el prompt completo para el estilo y idioma especificados.

    ¿Por qué esta función?
    - Combina system prompt base + style prompt específico
    - Soporta múltiples idiomas (Spanish + English)
    - Valida que el estilo e idioma sean correctos
    - Facilita el uso desde copys_generator.py

    Args:
        style: Estilo de copy ("viral", "educational", "storytelling")
        language: Idioma del prompt ("es" para español, "en" para inglés). Default: "es"

    Returns:
        String con el prompt completo (system + style + format)

    Raises:
        ValueError: Si el estilo o idioma no son válidos

    Ejemplo:
        >>> prompt = get_prompt_for_style("viral", language="es")
        >>> # Retorna prompt en español
        >>> prompt = get_prompt_for_style("viral", language="en")
        >>> # Retorna prompt en inglés
    """
    # Mapeo de idioma a funciones (Spanish)
    spanish_prompts = {
        "viral": get_viral_prompt_es,
        "educational": get_educational_prompt_es,
        "storytelling": get_storytelling_prompt_es
    }

    # Mapeo de idioma a funciones (English)
    english_prompts = {
        "viral": get_viral_prompt_en,
        "educational": get_educational_prompt_en,
        "storytelling": get_storytelling_prompt_en
    }

    # Selecciono el mapeo según el idioma
    language_lower = language.lower()
    if language_lower.startswith("es"):
        style_prompts = spanish_prompts
        lang_name = "español"
    elif language_lower.startswith("en"):
        style_prompts = english_prompts
        lang_name = "inglés"
    else:
        raise ValueError(
            f"Idioma '{language}' no válido. "
            f"Opciones: 'es' (español), 'en' (inglés)"
        )

    # Valido que el estilo sea correcto
    if style not in style_prompts:
        raise ValueError(
            f"Estilo '{style}' no válido. "
            f"Opciones: {', '.join(style_prompts.keys())}"
        )

    # Construyo el prompt completo
    base_prompt = build_base_system_prompt(include_format=True)
    style_prompt = style_prompts[style]()

    # Combino: base + style
    full_prompt = f"{base_prompt}\n\n{style_prompt}"

    return full_prompt


def get_available_styles() -> list[str]:
    """
    Retorna la lista de estilos disponibles.

    ¿Por qué esta función?
    - Para mostrar las opciones en el CLI
    - Para validar inputs del usuario
    - Mantiene una única fuente de verdad sobre estilos disponibles

    Returns:
        Lista de strings con los estilos disponibles

    Ejemplo:
        >>> styles = get_available_styles()
        >>> print(styles)
        ['viral', 'educational', 'storytelling']
    """
    return ["viral", "educational", "storytelling"]


# Exports principales
__all__ = [
    "get_prompt_for_style",
    "get_available_styles",
    "build_base_system_prompt",
    "SYSTEM_PROMPT",
    "JSON_FORMAT_INSTRUCTIONS",
    # Spanish prompts
    "get_viral_prompt_es",
    "get_educational_prompt_es",
    "get_storytelling_prompt_es",
    # English prompts
    "get_viral_prompt_en",
    "get_educational_prompt_en",
    "get_storytelling_prompt_en"
]
