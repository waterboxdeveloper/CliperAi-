# FEATURE: Prompts Generalization (Remove AICDMX Hardcoding)

**Objetivo**: Hacer prompts genéricos permitiendo que cada canal defina sus hashtags

**Tiempo estimado**: 2.5 horas
**Complejidad**: Media
**Impacto**: Alto (desbloquea multicanal)

---

## 📋 Pasos del Plan

### ✅ Paso 1: Crear sistema de inyección (30 min)
- [ ] `01-create-injector.md` - Crear `prompt_injector.py`
- [ ] Función `inject_channel_config()`
- [ ] Tests básicos

### ✅ Paso 2: Actualizar base_prompts.py (20 min)
- [ ] `02-update-base-prompts.md` - Reemplazar hardcodes
- [ ] Cambiar instrucciones generales
- [ ] Cambiar ejemplos

### ✅ Paso 3: Actualizar prompts por estilo (30 min)
- [ ] `03-update-style-prompts.md` - Actualizar viral/educational/storytelling
- [ ] Versiones EN y ES
- [ ] Verificar consistencia

### ✅ Paso 4: Integrar en LangGraph (20 min)
- [ ] `04-integrate-copys-generator.md` - Inyectar en flujo
- [ ] Cargar config de canal
- [ ] Pasar a prompts

### ✅ Paso 5: Crear configs por canal (15 min)
- [ ] `05-channel-configs.md` - Crear YAML files
- [ ] AICDMX config (default)
- [ ] Generic template
- [ ] Example: photography

### ✅ Paso 6: Testing y validación (30 min)
- [ ] `06-testing.md` - Tests por canal
- [ ] Verificar AICDMX (backward compat)
- [ ] Verificar nuevo canal

---

## 🎯 Checkpoint: Qué lograremos

**Antes** (AICDMX hardcoded en 30+ lugares):
```python
# base_prompts.py
"- DEBE incluir SIEMPRE el hashtag #AICDMX"

# viral_prompt_es.py
"Mezcla: #AICDMX + nicho + trending"
```

**Después** (Inyectado desde config):
```python
# base_prompts.py (genérico)
"- DEBE incluir SIEMPRE estos hashtags: {mandatory_hashtags}"

# config/aicdmx.yaml
mandatory_hashtags: ["#AICDMX"]

# config/fotografia.yaml
mandatory_hashtags: ["#photography", "#composition"]
```

---

## ✨ Beneficios

- ✅ AICDMX sigue funcionando (backward compatible)
- ✅ Nuevo canal = copiar config, no clonar prompts
- ✅ Cambiar hashtags sin editar código
- ✅ Prompts genéricos reutilizables

---

**Comenzar con Paso 1?** Sí/No
