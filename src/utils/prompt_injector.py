# -*- coding: utf-8 -*-
"""
Prompt Injector - Inyecta configuración de canal en prompts

¿Por qué existe esto?
- Prompts tienen placeholders: {mandatory_hashtags}, {optional_hashtag_count}
- Config de canal define valores reales: ["#AICDMX"], 1
- Este módulo reemplaza placeholders con valores del canal
- Resultado: prompts genéricos + configurables por canal

Ejemplo:
    config = {"mandatory_hashtags": ["#AICDMX"], "optional_hashtags_count": 1}
    prompt = "Incluye {mandatory_hashtags} siempre"
    result = inject_channel_config(prompt, config)
    # result = "Incluye #AICDMX siempre"
"""

from typing import Dict, Any


def inject_channel_config(prompt: str, channel_config: Dict[str, Any]) -> str:
    """
    Reemplaza placeholders de hashtags en prompts con valores del canal.

    Args:
        prompt: String del prompt con placeholders
        channel_config: Dict con configuración del canal

    Returns:
        Prompt con placeholders reemplazados

    Placeholders soportados:
    - {mandatory_hashtags} → "#AICDMX" o "#photography #composition"
    - {optional_hashtag_count} → "1" o "2"
    - {hashtag_example} → "#AICDMX #DevLife" (ejemplo del canal)

    Example:
        >>> config = {
        ...     "mandatory_hashtags": ["#AICDMX"],
        ...     "optional_hashtags_count": 1,
        ...     "hashtag_example": "#AICDMX #DevLife"
        ... }
        >>> prompt = "Incluye {mandatory_hashtags} en el copy"
        >>> inject_channel_config(prompt, config)
        'Incluye #AICDMX en el copy'
    """
    # Preparar valores
    mandatory_hashtags_str = " ".join(channel_config.get("mandatory_hashtags", []))
    optional_hashtag_count = str(channel_config.get("optional_hashtags_count", 1))
    hashtag_example = channel_config.get("hashtag_example", "")

    # Reemplazar placeholders de forma segura (reemplazos simples, sin format())
    # Esto evita problemas con otros placeholders como {opening_words}
    result = prompt.replace("{mandatory_hashtags}", mandatory_hashtags_str)
    result = result.replace("{optional_hashtag_count}", optional_hashtag_count)
    result = result.replace("{hashtag_example}", hashtag_example)

    return result
