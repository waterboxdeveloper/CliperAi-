# Paso 1: Crear Sistema de Inyección de Hashtags

**Tiempo**: 30 minutos
**Archivo**: `src/utils/prompt_injector.py` (NUEVO)

---

## 🎯 Objetivo

Crear función que reemplace placeholders `{mandatory_hashtags}`, `{optional_hashtag_count}`, etc. con valores del canal.

---

## 📝 Código a implementar

Crear `src/utils/prompt_injector.py`:

```python
# -*- coding: utf-8 -*-
"""
Prompt Injector - Inyecta configuración de canal en prompts

¿Por qué existe esto?
- Prompts tienen placeholders: {mandatory_hashtags}, {optional_hashtag_count}
- Config de canal define valores reales: ["#AICDMX"], 1
- Este módulo reemplaza placeholders con valores del canal
- Resultado: prompts genéricos + configurables por canal
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

    Ejemplo:
    >>> config = {"mandatory_hashtags": ["#AICDMX"], "optional_hashtags_count": 1}
    >>> prompt = "Incluye {mandatory_hashtags} en el copy"
    >>> inject_channel_config(prompt, config)
    "Incluye #AICDMX en el copy"
    """
    # Preparar valores
    mandatory_hashtags_str = " ".join(channel_config.get("mandatory_hashtags", []))
    optional_hashtag_count = str(channel_config.get("optional_hashtags_count", 1))
    hashtag_example = channel_config.get("hashtag_example", "")

    # Reemplazar placeholders
    result = prompt.format(
        mandatory_hashtags=mandatory_hashtags_str,
        optional_hashtag_count=optional_hashtag_count,
        hashtag_example=hashtag_example
    )

    return result
```

---

## ✅ Paso 1.1: Crear archivo

**Archivo**: `/Users/ee/Documents/opino.tech/Cliper/src/utils/prompt_injector.py`

Copiar el código anterior al archivo.

---

## ✅ Paso 1.2: Test básico

Crear test en `tests/test_prompt_injector.py`:

```python
# -*- coding: utf-8 -*-
"""Test para prompt_injector.py"""

import pytest
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


if __name__ == "__main__":
    test_inject_mandatory_hashtags()
    test_inject_multiple_hashtags()
    test_inject_optional_count()
    test_inject_example()
    print("\n✅ All tests passed!")
```

---

## ✅ Paso 1.3: Ejecutar tests

```bash
cd /Users/ee/Documents/opino.tech/Cliper
python tests/test_prompt_injector.py
```

Expected output:
```
✅ test_inject_mandatory_hashtags passed
✅ test_inject_multiple_hashtags passed
✅ test_inject_optional_count passed
✅ test_inject_example passed

✅ All tests passed!
```

---

## ✅ Verificación

- [ ] Archivo `src/utils/prompt_injector.py` creado
- [ ] Función `inject_channel_config()` implementada
- [ ] Tests ejecutados exitosamente
- [ ] Código sin errores

---

## 🚀 Próximo: Paso 2

Una vez completado este paso, proceder a actualizar `base_prompts.py` con placeholders.

**Paso 2**: `02-update-base-prompts.md`
