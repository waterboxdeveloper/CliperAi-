# Plan: Generalización de CLIPER para uso global

**Status**: 🔄 Planificación
**Fecha**: 2026-03-22
**Objetivo**: Transformar CLIPER de herramienta específica para AICDMX a plataforma modular para cualquier canal/tipo de video

---

## 📊 Análisis del Estado Actual

### Problema: Sistema demasiado específico

CLIPER está hardcodeado para contenido de AICDMX:

```python
# AICDMX-specific hardcoding:
- #AICDMX obligatorio en todos los copies (copy_schemas.py:232)
- Estilos predefinidos: "viral", "educational", "storytelling"
- Hashtags speaker: Extraídos pero no configurables
- Tono/voz: Fijo por estilo, no personalizable
- Logo: Selección manual pero asumiendo AICDMX branding
```

**Impacto**:
- ❌ No funciona para otros canales
- ❌ Validación rechaza copies sin #AICDMX
- ❌ Prompts asumen contexto AICDMX
- ❌ Usuarios externos no pueden personalizarlo

### Casos de uso bloqueados

1. **Canal de fotografía**: Necesita hashtags sobre #photography, #composition
2. **Canal educativo**: Requiere contexto diferente (no clickbait)
3. **Canal de viajes**: Quiere emojis específicos de destinos
4. **Canal de tech**: Necesita hashtags técnicos (#docker, #kubernetes)

---

## 🎯 Visión de Generalización

### De específico → Modular

```
ANTES (AICDMX-only):
┌─────────────────────┐
│   CLIPER-AICDMX     │
│  - Hardcoded #AICDMX│
│  - 3 estilos fixed  │
│  - Logo: AICDMX     │
└─────────────────────┘

DESPUÉS (Platform):
┌───────────────────────────────┐
│   CLIPER Platform             │
├───────────────────────────────┤
│ Config Files (per channel)    │
│ ├── channel.yaml              │
│ ├── hashtags.yaml             │
│ ├── styles.yaml               │
│ └── branding.yaml             │
├───────────────────────────────┤
│ Core Pipeline (generic)       │
│ ├── Download → Transcribe     │
│ ├── Detect Clips → Generate   │
│ ├── Validate → Export         │
│ └── Publish                   │
└───────────────────────────────┘
```

---

## 📋 Cambios Arquitectónicos Necesarios

### Fase 1: Configuración (INMEDIATA)

**Objetivo**: Hacer el sistema configurable sin romper AICDMX actual

**Archivos nuevos**:
```
config/
├── channels/
│   ├── aicdmx.yaml          # Tu canal actual (default)
│   ├── generic.yaml         # Template para otros canales
│   └── example-photography.yaml
├── templates/
│   ├── prompts-aicdmx.yaml
│   ├── prompts-generic.yaml
│   └── hashtags.yaml
└── README.md
```

**Estructura de `channel.yaml`**:
```yaml
name: "AICDMX"
channel_type: "tech"
mandatory_hashtags:
  - "#AICDMX"
  - "#AI"
optional_hashtags_count: 1

preferred_tone: "viral"  # o "educational", "storytelling"

branding:
  logo: "assets/logo.png"
  color_theme: "cyan"
  watermark_text: "AICDMX"

content_rules:
  min_copy_length: 20
  max_copy_length: 150
  emoji_usage: "high"
  clickbait_level: "moderate"

styles:
  - name: "viral"
    description: "High-engagement, hook-driven"
  - name: "educational"
    description: "Teaches concepts"
  - name: "storytelling"
    description: "Narrative-driven"
```

**Cambios en código**:
1. `src/utils/config_loader.py` (NUEVO): Carga YAML del canal
2. `cliper.py`: Pregunta "¿Usar config AICDMX actual o nueva?"
3. `src/models/copy_schemas.py`: Validación basada en config (no hardcoded)

### Fase 2: Prompts Dinámicos

**Objetivo**: Prompts que se adapten al tipo de canal

**Cambio**:
```python
# ANTES:
prompt = get_prompt_for_style("viral", language="es")

# DESPUÉS:
prompt = get_prompt_for_style("viral", language="es", config=channel_config)
# Inyecta: mandatory_hashtags, tone, content_type, etc.
```

### Fase 3: Validación Flexible

**Objetivo**: Reglas de validación configurables por canal

**Cambios en `copy_schemas.py`**:
```python
class ClipCopy(BaseModel):
    # ... campos existentes ...

    @field_validator('copy', mode='before')
    @classmethod
    def validate_copy(cls, v, info):
        config = info.context.get('config')  # ← Nuevo: pasa config

        # Validación flexible basada en config
        if config.mandatory_hashtags:
            for hashtag in config.mandatory_hashtags:
                if hashtag not in v.upper():
                    raise ValueError(f"Missing {hashtag}")

        # ... resto de validaciones ...
```

### Fase 4: CLI Mejorado

**Objetivo**: Permitir seleccionar canal al iniciar

**Flujo nuevo**:
```
CLIPER - Video Clipper

1. ¿Qué canal?
   [1] AICDMX (default)
   [2] Mi nuevo canal
   [3] Crear nuevo canal

2. [Carga configuración del canal]

3. Procesa video con config personalizada
```

---

## 🛠️ Plan de Implementación

### Semana 1: Configuración Base

- [ ] Crear estructura `config/channels/`
- [ ] Crear `aicdmx.yaml` (migrar hardcodes)
- [ ] Crear `src/utils/config_loader.py`
- [ ] Integrar en `cliper.py` - pregunta de canal
- [ ] Actualizar `copy_schemas.py` para usar config

### Semana 2: Prompts Dinámicos

- [ ] Refactorizar prompts para inyectar config
- [ ] Crear templates para diferentes tipos de canal
- [ ] Testear con 2-3 estilos diferentes

### Semana 3: Validación Flexible

- [ ] Hacer validadores configurables
- [ ] Remover #AICDMX hardcoded
- [ ] Permitir reglas custom por canal

### Semana 4: Documentación + Ejemplos

- [ ] Guía "Crear nuevo canal"
- [ ] Ejemplos: fotografía, viajes, tech
- [ ] Templates reutilizables

---

## 📦 Impacto en Código Existente

### ✅ Lo que NO cambia
- Pipeline core (download → transcribe → detect → export)
- LangGraph structure
- Pydantic validation pattern
- FFmpeg integration

### ⚠️ Lo que SÍ cambia (backwards compatible)

| Archivo | Cambio | Impacto |
|---------|--------|--------|
| `cliper.py` | +Selector de canal | ✅ Pregunta al inicio |
| `copy_schemas.py` | Validación dinámica | ✅ Más flexible |
| `copys_generator.py` | Inyecta config en prompts | ✅ Internals, no API |
| Prompts `*.py` | Aceptan `config` param | ✅ Opcional |

### 🔄 Migración sin romper AICDMX

```python
# AICDMX sigue funcionando igual
cliper.py --channel aicdmx

# Nuevos usuarios pueden usar configuración custom
cliper.py --channel mi-fotografia
```

---

## 🎯 Beneficios Esperados

### Para ti (AICDMX)
- ✅ Mismo funcionamiento
- ✅ Pero configurable si cambias requerimientos
- ✅ Puedes iterar estilos sin editar código

### Para usuarios externos
- ✅ Plataforma vs tool específica
- ✅ Template "copy and customize"
- ✅ Comunidad puede compartir configs

### Para CLIPER como proyecto
- ✅ Separación: core pipeline vs configuración
- ✅ Testeable: múltiples configs
- ✅ Escalable: agregar canales sin changes

---

## 💡 Solución Inmediata (Hoy)

**Para desbloquear validación de #AICDMX ahora**:

1. Hacer #AICDMX opcional en `copy_schemas.py` ← YA HECHO ✅
2. Agregar flag `--strict-hashtag` para forzar validación
3. Guardar flag en config (defaultea a `false`)

```python
# En cliper.py:
strict_validation = Confirm.ask(
    "[cyan]Require channel hashtag in all copies?[/cyan]",
    default=False  # ← Flexible
)
```

---

## 🚀 Próximos Pasos

**¿Proceder con Generalización?**

1. ✅ **SÍ**: Crear estructura `todoCLIPER-GENERALIZATION/` con pasos detallados
2. ✅ **SÍ pero gradual**: Hacer Fase 1 (config) ahora, resto después
3. ❌ **NO**: Mantener AICDMX hardcoded, pero hacer validación más flexible

**Recomendación**: Opción 2 (gradual)
- Implementa Fase 1 ahora (~2 horas)
- Desbloquea otros canales en el futuro
- No requiere cambios drásticos a AICDMX

---

## 📚 Referencias

- Ejemplo config system: https://github.com/ansible/ansible-examples
- YAML structure: https://yaml.org/
- Dynamic validation: https://docs.pydantic.dev/latest/concepts/validators/
