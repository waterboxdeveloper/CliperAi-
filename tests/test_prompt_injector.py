# -*- coding: utf-8 -*-
"""Test para prompt_injector.py"""

from src.utils.prompt_injector import inject_channel_config


def test_inject_mandatory_hashtags():
    """Test: Inyecta hashtags obligatorios"""
    config = {
        "mandatory_hashtags": ["#AICDMX"],
        "optional_hashtags_count": 1,
        "hashtag_example": "#AICDMX #DevLife"
    }
    prompt = "Incluye {mandatory_hashtags} siempre"
    result = inject_channel_config(prompt, config)
    assert result == "Incluye #AICDMX siempre"
    print("✅ test_inject_mandatory_hashtags passed")


def test_inject_multiple_hashtags():
    """Test: Múltiples hashtags obligatorios"""
    config = {
        "mandatory_hashtags": ["#photography", "#composition"],
        "optional_hashtags_count": 2,
        "hashtag_example": "#photography #composition"
    }
    prompt = "Usa {mandatory_hashtags} en todos los copys"
    result = inject_channel_config(prompt, config)
    assert result == "Usa #photography #composition en todos los copys"
    print("✅ test_inject_multiple_hashtags passed")


def test_inject_optional_count():
    """Test: Inyecta número de hashtags opcionales"""
    config = {
        "mandatory_hashtags": ["#AICDMX"],
        "optional_hashtags_count": 2,
        "hashtag_example": "#AICDMX #DevLife"
    }
    prompt = "Incluye {optional_hashtag_count} hashtags adicionales"
    result = inject_channel_config(prompt, config)
    assert result == "Incluye 2 hashtags adicionales"
    print("✅ test_inject_optional_count passed")


def test_inject_example():
    """Test: Inyecta ejemplo"""
    config = {
        "mandatory_hashtags": ["#AICDMX"],
        "optional_hashtags_count": 1,
        "hashtag_example": "#AICDMX #DevLife"
    }
    prompt = "Ejemplo: {hashtag_example}"
    result = inject_channel_config(prompt, config)
    assert result == "Ejemplo: #AICDMX #DevLife"
    print("✅ test_inject_example passed")


def test_inject_multiple_placeholders():
    """Test: Múltiples placeholders en un prompt"""
    config = {
        "mandatory_hashtags": ["#AICDMX"],
        "optional_hashtags_count": 1,
        "hashtag_example": "#AICDMX #DevLife"
    }
    prompt = "Usa {mandatory_hashtags}, luego {optional_hashtag_count} hashtag más. Ejemplo: {hashtag_example}"
    result = inject_channel_config(prompt, config)
    expected = "Usa #AICDMX, luego 1 hashtag más. Ejemplo: #AICDMX #DevLife"
    assert result == expected
    print("✅ test_inject_multiple_placeholders passed")


def test_inject_empty_config():
    """Test: Config vacía usa defaults"""
    config = {}
    prompt = "Hashtags: {mandatory_hashtags}, Ejemplo: {hashtag_example}"
    result = inject_channel_config(prompt, config)
    # Espera strings vacíos
    assert "{mandatory_hashtags}" not in result  # No quedan placeholders
    print("✅ test_inject_empty_config passed")


if __name__ == "__main__":
    test_inject_mandatory_hashtags()
    test_inject_multiple_hashtags()
    test_inject_optional_count()
    test_inject_example()
    test_inject_multiple_placeholders()
    test_inject_empty_config()
    print("\n✅✅✅ All tests passed!")
