# Plan: Generalización de Prompts (Remover AICDMX hardcodeado)

**Status**: 🎯 Propuesta
**Fecha**: 2026-03-22
**Objetivo**: Hacer prompts genéricos, permitir que cada canal defina sus hashtags

---

## 🔍 Diagnóstico: Dónde está AICDMX hardcodeado

**Archivos afectados**:
- `src/prompts/base_prompts.py` → Instrucciones generales
- `src/prompts/viral_prompt_es.py` → Ejemplos con #AICDMX
- `src/prompts/educational_prompt_es.py` → Ejemplos con #AICDMX
- `src/prompts/storytelling_prompt_es.py` → Probablemente igual
- `src/prompts/*_en.py` → Versiones en inglés (asumir mismo problema)

**Tipos de hardcoding**:

```python
# Tipo 1: Instrucción explícita (base_prompts.py:32)
"- DEBE incluir SIEMPRE el hashtag #AICDMX (obligatorio, branding)"

# Tipo 2: Ejemplos en prompts (viral_prompt_es.py:72)
"Mezcla: #AICDMX + nicho + trending"

# Tipo 3: Ejemplos de outputs (base_prompts.py:65-68)
"✅ 'Cuando tu code funciona en local pero no en prod 💀 #DevLife #AICDMX'"
```

**Total de menciones**: ~30+ referencias a #AICDMX en prompts

---

## 🎯 Solución: Sistema de Hashtags Inyectado

### Arquitectura propuesta

```
CONFIG (channel.yaml)
├── mandatory_hashtags: ["#AICDMX"]      ← Se inyecta aquí
├── optional_hashtags_count: 1-2
└── hashtag_strategy: "mix" | "trending" | "custom"

PROMPTS (*.py)
├── Sin #AICDMX hardcodeado
└── Template: "Mezcla: {mandatory_hashtags} + nicho + trending"

COPYS_GENERATOR
└── Inyecta hashtags en tiempo de ejecución
```

---

## 📝 Cambios necesarios

### Fase 1: Crear sistema de inyección (INMEDIATA)

**1. Extender `config/channels/aicdmx.yaml`**:
```yaml
name: "AICDMX"
mandatory_hashtags:
  - "#AICDMX"
optional_hashtags_strategy: "content_based"
optional_hashtags_count: 1
example: "#AICDMX #DevLife"
```

**2. Crear función de inyección** en `src/utils/prompt_injector.py` (NUEVO):
```python
def inject_channel_config(prompt: str, config: ChannelConfig) -> str:
    """
    Reemplaza placeholders de hashtags en prompts con valores del canal.

    Placeholders:
    - {mandatory_hashtags} → "#AICDMX"
    - {optional_hashtag_count} → "1"
    - {hashtag_example} → "#AICDMX #DevLife"
    """
    return prompt.format(
        mandatory_hashtags=" ".join(config.mandatory_hashtags),
        optional_hashtag_count=config.optional_hashtags_count,
        hashtag_example=config.example
    )
```

### Fase 2: Actualizar prompts (CORE CHANGE)

**Cambios en `base_prompts.py`**:

```diff
# ANTES (hardcodeado):
- DEBE incluir SIEMPRE el hashtag #AICDMX (obligatorio, branding)
- Además de #AICDMX, incluye 1-2 hashtags relevantes al contenido

# DESPUÉS (inyectado):
+ - DEBE incluir SIEMPRE estos hashtags: {mandatory_hashtags} (obligatorio, branding)
+ - Además de {mandatory_hashtags}, incluye {optional_hashtag_count} hashtags relevantes
```

**Cambios en `viral_prompt_es.py`** (línea 68-72):

```diff
# ANTES:
- Hashtags virales:
  - SIEMPRE incluye #AICDMX (obligatorio)
  - Mezcla: #AICDMX + nicho (específico) + trending (general)
  - Ejemplos: #AICDMX #TechTwitter, #AICDMX #DevLife, #AICDMX #AIRevolution

# DESPUÉS:
+ - Hashtags:
+   - SIEMPRE incluye: {mandatory_hashtags} (obligatorio)
+   - Mezcla: {mandatory_hashtags} + nicho (específico) + trending (general)
+   - Ejemplo: {hashtag_example}
```

**Cambios en ejemplos** (línea 75-77):

```diff
# ANTES:
✅ "La IA es revolucionaria. 3 formas en que cambió mi negocio en 3 meses 🚀 #AI #AICDMX"

# DESPUÉS:
✅ "La IA es revolucionaria. 3 formas en que cambió mi negocio en 3 meses 🚀 #AI {mandatory_hashtags}"
```

### Fase 3: Integrar inyección en LangGraph

**En `copys_generator.py`** (donde se cargan prompts):

```python
# ANTES:
prompt = get_prompt_for_style("viral", language="es")

# DESPUÉS:
prompt = get_prompt_for_style("viral", language="es")
prompt = inject_channel_config(prompt, channel_config)  # ← NUEVO
```

---

## ✅ Validación: Cómo asegurar que funciona

### Test casos por canal:

**AICDMX (actual)**:
```python
config = load_channel_config("aicdmx")
prompt = get_prompt_for_style("viral", "es")
prompt = inject_channel_config(prompt, config)
assert "#AICDMX" in prompt
assert "DevLife" in prompt  # ejemplo
```

**Nuevo canal (fotografía)**:
```python
config = load_channel_config("fotografia")
# config.mandatory_hashtags = ["#photography", "#composition"]
prompt = get_prompt_for_style("viral", "es")
prompt = inject_channel_config(prompt, config)
assert "#photography" in prompt
assert "#AICDMX" not in prompt  # ← Diferente canal
```

---

## 🎁 Beneficios

| Aspecto | Antes | Después |
|--------|-------|---------|
| **Hardcodeado para** | Solo AICDMX | Cualquier canal |
| **Cambiar hashtags** | Editar 5 archivos | Editar config YAML |
| **Nuevo canal** | Clonar y reescribir prompts | Copiar config + listo |
| **Mantenibilidad** | 🔴 Baja | 🟢 Alta |

---

## 📋 Plan de Implementación

### Paso 1: Sistema de inyección (30 min)
- [ ] Crear `src/utils/prompt_injector.py`
- [ ] Función `inject_channel_config()`
- [ ] Test básico

### Paso 2: Actualizar prompts (1 hora)
- [ ] Reemplazar hardcodes en `base_prompts.py`
- [ ] Reemplazar hardcodes en `viral_prompt_es.py`
- [ ] Reemplazar en `educational_prompt_es.py`
- [ ] Reemplazar en `storytelling_prompt_es.py`
- [ ] (Opcional) Reemplazar versiones EN

### Paso 3: Integrar en LangGraph (30 min)
- [ ] Importar `inject_channel_config` en `copys_generator.py`
- [ ] Llamar función cuando se cargan prompts
- [ ] Pasar `channel_config` a `get_prompt_for_style()`

### Paso 4: Extensión de config (15 min)
- [ ] Actualizar `config/channels/aicdmx.yaml`
- [ ] Crear template `config/channels/generic.yaml`
- [ ] Crear ejemplo `config/channels/example-photography.yaml`

### Paso 5: Testing (30 min)
- [ ] Test AICDMX (debe funcionar como antes)
- [ ] Test con nuevo canal
- [ ] Validar que copys tienen hashtags correctos

**TOTAL: ~2.5 horas**

---

## 🔄 Backward Compatibility

✅ **AICDMX seguirá funcionando igual**:
- Config tendrá `mandatory_hashtags: ["#AICDMX"]`
- Prompts con `{mandatory_hashtags}` se renderizarán con `#AICDMX`
- No hay breaking changes para usuario actual

---

## 🚀 Próximos Pasos

**¿Proceder con implementación?**

- [ ] Sí, comenzar Paso 1 (inyección)
- [ ] Sí, pero esperar a migración Claude primero
- [ ] No, mantener AICDMX hardcodeado por ahora

**Recomendación**: Hacer esto ANTES de Claude migration, así los prompts ya son genéricos para cualquier modelo.
