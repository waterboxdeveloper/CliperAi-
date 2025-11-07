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
from .viral_prompt import get_viral_prompt
from .educational_prompt import get_educational_prompt
from .storytelling_prompt import get_storytelling_prompt


def get_prompt_for_style(style: str = "viral") -> str:
    """
    Retorna el prompt completo para el estilo especificado.

    ¿Por qué esta función?
    - Combina system prompt base + style prompt específico
    - Valida que el estilo sea correcto
    - Facilita el uso desde copys_generator.py

    Args:
        style: Estilo de copy ("viral", "educational", "storytelling")

    Returns:
        String con el prompt completo (system + style + format)

    Raises:
        ValueError: Si el estilo no es válido

    Ejemplo:
        >>> prompt = get_prompt_for_style("viral")
        >>> # Este prompt se envía a Gemini junto con los clips
    """
    # Mapeo de estilos a funciones
    style_prompts = {
        "viral": get_viral_prompt,
        "educational": get_educational_prompt,
        "storytelling": get_storytelling_prompt
    }

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
    "get_viral_prompt",
    "get_educational_prompt",
    "get_storytelling_prompt"
]
