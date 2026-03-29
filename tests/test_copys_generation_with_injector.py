# -*- coding: utf-8 -*-
"""Integration tests for prompt injection in copys generation"""

from src.utils.prompt_injector import inject_channel_config


def test_aicdmx_channel_config():
    """Test: Verificar que AICDMX config se inyecta correctamente"""
    config = {
        "mandatory_hashtags": ["#AICDMX"],
        "optional_hashtags_count": 1,
        "hashtag_example": "#AICDMX #DevLife"
    }

    test_prompt = """
    Hashtags: {mandatory_hashtags}
    Ejemplo: {hashtag_example}
    Adicionales: {optional_hashtag_count}
    """

    result = inject_channel_config(test_prompt, config)

    assert "#AICDMX" in result
    assert "#DevLife" in result
    assert "1" in result
    print("✅ AICDMX config injected correctly")


def test_photography_channel_config():
    """Test: Verificar que nuevo canal funciona"""
    config = {
        "mandatory_hashtags": ["#Photography", "#Composition"],
        "optional_hashtags_count": 2,
        "hashtag_example": "#Photography #Composition #PhotographyTips"
    }

    test_prompt = "Hashtags: {mandatory_hashtags} - Ejemplo: {hashtag_example}"
    result = inject_channel_config(test_prompt, config)

    # Verificar que se inyectó correctamente
    assert "#Photography" in result
    assert "#Composition" in result
    assert "#AICDMX" not in result  # ← Clave: no debe tener AICDMX
    print("✅ Photography config injected correctly")


def test_generic_template():
    """Test: Template genérico funciona con cualquier config"""
    configs = [
        {
            "name": "tech-channel",
            "mandatory_hashtags": ["#Tech", "#Dev"],
            "optional_hashtags_count": 1,
            "hashtag_example": "#Tech #Dev #Programming"
        },
        {
            "name": "music-channel",
            "mandatory_hashtags": ["#Music", "#OriginalMusic"],
            "optional_hashtags_count": 2,
            "hashtag_example": "#Music #OriginalMusic #SoundDesign"
        }
    ]

    template = "Channel hashtags: {mandatory_hashtags}. Add {optional_hashtag_count} more. Example: {hashtag_example}"

    for config in configs:
        result = inject_channel_config(template, config)
        for hashtag in config["mandatory_hashtags"]:
            assert hashtag in result, f"Missing {hashtag} in {config['name']}"
        print(f"✅ {config['name']} config works correctly")


def test_backward_compatibility_aicdmx():
    """Test: Asegurar que AICDMX sigue funcionando exactamente igual"""
    # Config AICDMX (la que se usa actualmente)
    config = {
        "mandatory_hashtags": ["#AICDMX"],
        "optional_hashtags_count": 1,
        "hashtag_example": "#AICDMX #DevLife"
    }

    # Simular prompt antes (con hardcoding)
    old_prompt = "SIEMPRE incluye #AICDMX obligatorio"

    # Simular prompt después (con placeholder)
    new_prompt = "SIEMPRE incluye {mandatory_hashtags} obligatorio"

    # Inyectar
    result = inject_channel_config(new_prompt, config)

    # Resultado debe ser igual al prompt anterior
    assert result == old_prompt
    print("✅ AICDMX backward compatibility verified")


if __name__ == "__main__":
    test_aicdmx_channel_config()
    test_photography_channel_config()
    test_generic_template()
    test_backward_compatibility_aicdmx()
    print("\n✅✅✅ All integration tests passed!")
