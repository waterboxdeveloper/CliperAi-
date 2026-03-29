# -*- coding: utf-8 -*-
"""
End-to-end test: Verificar que prompts inyectados funcionan en copys_generator
"""

from src.utils.prompt_injector import inject_channel_config
from src.prompts import get_prompt_for_style


def test_prompts_have_no_hardcoded_aicdmx():
    """Test: Verificar que prompts NO tienen #AICDMX hardcodeado"""
    styles = ["viral", "educational", "storytelling"]

    for style in styles:
        prompt = get_prompt_for_style(style, language="es")

        # Contar menciones de #AICDMX que sean en ejemplos ejecutables
        # (Ignorar comentarios tipo "MAL (sin #AICDMX)")
        lines = prompt.split('\n')
        hardcoded_count = 0
        for line in lines:
            # Si la línea tiene #AICDMX pero no es un comentario de "MAL" o "BIEN"
            if '#AICDMX"' in line and not ('MAL' in line or 'BIEN' in line):
                hardcoded_count += 1

        assert hardcoded_count == 0, f"Found {hardcoded_count} hardcoded #AICDMX in {style} prompt"
        print(f"✅ {style} prompt: No hardcoded #AICDMX")


def test_prompts_have_placeholders():
    """Test: Verificar que prompts tienen placeholders para inyectar"""
    styles = ["viral", "educational", "storytelling"]

    for style in styles:
        prompt = get_prompt_for_style(style, language="es")

        # Debe tener al menos estos placeholders
        assert "{mandatory_hashtags}" in prompt, f"{style} missing {mandatory_hashtags}"
        print(f"✅ {style} prompt: Has {{mandatory_hashtags}} placeholder")


def test_injection_in_base_prompt():
    """Test: Inyectar en base prompt funciona"""
    from src.prompts.base_prompts import SYSTEM_PROMPT

    config = {
        "mandatory_hashtags": ["#AICDMX"],
        "optional_hashtags_count": 1,
        "hashtag_example": "#AICDMX #DevLife"
    }

    result = inject_channel_config(SYSTEM_PROMPT, config)

    # Verificar inyección
    assert "#AICDMX" in result, "AICDMX not injected"
    assert "{mandatory_hashtags}" not in result, "Placeholder not replaced"
    assert "DevLife" in result, "Example not injected"
    print("✅ Base prompt injection works correctly")


def test_injection_in_style_prompts():
    """Test: Inyectar en style prompts funciona"""
    styles_modules = [
        ("viral", "src.prompts.viral_prompt_es", "VIRAL_STYLE_PROMPT_ES"),
        ("educational", "src.prompts.educational_prompt_es", "EDUCATIONAL_STYLE_PROMPT_ES"),
        ("storytelling", "src.prompts.storytelling_prompt_es", "STORYTELLING_STYLE_PROMPT_ES"),
    ]

    config = {
        "mandatory_hashtags": ["#AICDMX"],
        "optional_hashtags_count": 1,
        "hashtag_example": "#AICDMX #DevLife"
    }

    for style_name, module_path, var_name in styles_modules:
        # Importar dinámicamente
        module = __import__(module_path, fromlist=[var_name])
        prompt = getattr(module, var_name)

        result = inject_channel_config(prompt, config)

        # Verificar inyección
        assert "{mandatory_hashtags}" not in result, f"{style_name} placeholder not replaced"
        print(f"✅ {style_name} prompt injection works")


def test_injection_with_different_channels():
    """Test: Inyección funciona con diferentes canales"""
    channels = {
        "AICDMX": {
            "mandatory_hashtags": ["#AICDMX"],
            "optional_hashtags_count": 1,
            "hashtag_example": "#AICDMX #DevLife"
        },
        "Photography": {
            "mandatory_hashtags": ["#Photography", "#Composition"],
            "optional_hashtags_count": 2,
            "hashtag_example": "#Photography #Composition"
        },
        "Music": {
            "mandatory_hashtags": ["#OriginalMusic"],
            "optional_hashtags_count": 2,
            "hashtag_example": "#OriginalMusic #Indie"
        }
    }

    from src.prompts.base_prompts import SYSTEM_PROMPT

    for channel_name, config in channels.items():
        result = inject_channel_config(SYSTEM_PROMPT, config)

        # Verificar que hashtags del canal están presentes
        for hashtag in config["mandatory_hashtags"]:
            assert hashtag in result, f"{channel_name}: {hashtag} not in result"

        # Verificar que NO hay hashtags de otros canales
        if channel_name != "AICDMX":
            assert "#AICDMX" not in result, f"{channel_name}: Should not have #AICDMX"

        print(f"✅ {channel_name} channel injection works correctly")


def test_copys_generator_imports_injector():
    """Test: copys_generator.py importa y usa el injector"""
    import inspect
    from src.copys_generator import CopysGenerator

    # Verificar que el archivo importa inject_channel_config
    source = inspect.getsource(CopysGenerator._generate_copies_for_style)

    # Verificar que usa inject_channel_config
    assert "inject_channel_config" in source, "copys_generator doesn't use inject_channel_config"
    assert "channel_config" in source, "copys_generator doesn't have channel_config"
    print("✅ copys_generator.py imports and uses inject_channel_config")


def test_config_files_exist():
    """Test: Verificar que archivos de config existen"""
    from pathlib import Path

    configs = [
        "config/channels/aicdmx.yaml",
        "config/channels/generic.yaml",
        "config/channels/example-photography.yaml"
    ]

    for config_path in configs:
        path = Path(config_path)
        assert path.exists(), f"Config file missing: {config_path}"
        print(f"✅ {config_path} exists")


def test_full_flow_simulation():
    """Test: Simular flujo completo sin LLM"""
    from src.prompts import get_prompt_for_style

    # Paso 1: Cargar prompt
    prompt = get_prompt_for_style("viral", language="es")
    print("  1. ✅ Loaded viral prompt")

    # Paso 2: Inyectar config
    config = {
        "mandatory_hashtags": ["#TestChannel"],
        "optional_hashtags_count": 1,
        "hashtag_example": "#TestChannel #Test"
    }
    injected_prompt = inject_channel_config(prompt, config)
    print("  2. ✅ Injected channel config")

    # Paso 3: Verificar que se inyectó
    assert "#TestChannel" in injected_prompt
    assert "{mandatory_hashtags}" not in injected_prompt
    print("  3. ✅ Verification passed")

    # Paso 4: Simular que LLM recibiría este prompt
    sample_clip = {
        "clip_id": 1,
        "transcript": "This is a test transcript",
        "duration": 30,
        "opening_words": "This is a test"
    }

    # El prompt estaría listo para Gemini/Claude
    assert len(injected_prompt) > 0
    assert "#TestChannel" in injected_prompt
    print("  4. ✅ Prompt ready for LLM (Gemini/Claude)")

    print("✅ Full flow simulation completed successfully")


if __name__ == "__main__":
    print("\n=== INTEGRATION TESTS ===\n")

    test_prompts_have_no_hardcoded_aicdmx()
    print()

    test_prompts_have_placeholders()
    print()

    test_injection_in_base_prompt()
    print()

    test_injection_in_style_prompts()
    print()

    test_injection_with_different_channels()
    print()

    test_copys_generator_imports_injector()
    print()

    test_config_files_exist()
    print()

    print("\n=== FULL FLOW TEST ===\n")
    test_full_flow_simulation()

    print("\n" + "="*50)
    print("✅✅✅ ALL INTEGRATION TESTS PASSED!")
    print("="*50)
