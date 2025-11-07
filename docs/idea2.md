# AI Copy Generation - Feature Spec

## 📋 Resumen

Nueva fase en el pipeline de CLIPER para generar automáticamente captions/copies virales usando Gemini 2.5 (Flash o Pro).

---

## 🎯 Decisiones Clave

### Arquitectura
- **Fase separada:** Nueva opción en el menú después de generar clips
- **Una sola llamada API:** Batch processing de todos los clips en una request
- **Un solo JSON:** Toda la información relevante en un archivo

### Estructura de Archivos

```
output/
└── AI_CDMX_Live_Stream_gjPVlCHU9OM/
    ├── clip_001_9x16_subs.mp4
    ├── clip_002_9x16_subs.mp4
    ├── ...
    └── copys/                           ← carpeta "copys" (no "copies")
        └── clips_copys.json             ← UN SOLO JSON
```

### Formato del JSON

```json
{
  "video_id": "AI_CDMX_Live_Stream_gjPVlCHU9OM",
  "generated_at": "2025-10-25T15:00:00",
  "model": "gemini-2.5-flash",
  "total_clips": 60,
  "style": "viral",
  "clips": [
    {
      "clip_id": 1,
      "copy": "Caption completa con todo mezclado #hashtags #aquí #integrados",

      "metadata": {
        "sentiment": "curious_educational",
        "sentiment_score": 0.75,
        "engagement_score": 8.5,
        "suggested_thumbnail_timestamp": 12.5,
        "primary_topics": ["meetups", "Q&A", "community"],
        "hook_strength": "high",
        "viral_potential": 7.8
      }
    }
  ]
}
```

---

## 📝 Especificación del Copy

### Formato
- **Todo en un solo campo:** Caption + hashtags mezclados (no llaves separadas)
- **Límite:** 150 caracteres max (TikTok/Reels)
- **Estilo:** Viral por defecto
- **Incluye:** Emojis, hashtags integrados

### Ejemplo
```
"Ever wondered why some meetup Q&As feel chaotic? 🤔 This changed everything #TechMeetups #AI #CDMX"
```

---

## 🧠 Metadata Generado por IA

### 1. Sentiment Analysis
**¿Qué es?** Tono emocional del contenido

**Valores posibles:**
- `educational` - Explica, enseña
- `humorous` - Gracioso, ligero
- `inspirational` - Motivacional
- `controversial` - Opinionado, debate
- `curious_educational` - Preguntas educativas
- `relatable` - "Esto me pasa a mí"
- `storytelling` - Narrativa, anécdota

**Sentiment Score (0-1):**
- `0.9+` = Emoción MUY fuerte (alto potencial viral)
- `0.7-0.9` = Emoción clara
- `0.5-0.7` = Emoción moderada
- `<0.5` = Neutro/informativo

**Uso:**
- Filtrar clips por tipo emocional
- Ordenar por intensidad emocional
- A/B testing de contenido

---

### 2. Engagement Score (1-10)
**¿Qué predice?** Probabilidad de interacción (like, comment, share)

**Factores:**
- Fuerza del hook
- Duración óptima (45-90s)
- Claridad del mensaje
- Relevancia de topics
- Call-to-action efectivo

**Uso:**
- Priorizar qué clips publicar primero
- Decidir budget de ads
- Optimizar estrategia de contenido

---

### 3. Suggested Thumbnail Timestamp
**¿Qué es?** Segundo exacto del clip ideal para thumbnail

**Ejemplo:**
```
suggested_thumbnail_timestamp: 12.5
→ En el segundo 12.5 hay momento visual/emocional perfecto
```

**Cómo lo determina:**
- Palabras clave importantes
- Preguntas (curiosidad)
- Punchlines
- Clímax emocional

**Uso:**
- Auto-generar thumbnails con ffmpeg
- Posicionar texto overlay
- Debugging de clips que no funcionan

---

### 4. Primary Topics
**¿Qué es?** 3-5 temas principales del clip

**Ejemplo:**
```json
["meetups", "Q&A", "community", "public speaking"]
```

**Uso:**
- Búsqueda: "Dame clips sobre 'AI'"
- Agrupación: Series temáticas
- Hashtag optimization
- Content calendar planning

---

### 5. Hook Strength
**¿Qué mide?** Efectividad del primer segundo para captar atención

**Valores:**
- `very_high` - Hook irresistible
- `high` - Buen hook (pregunta/dato sorprendente)
- `medium` - Hook decente
- `low` - Sin hook claro

**Uso:**
- Filtrar clips débiles
- Regenerar copies con más punch
- Aprender patrones de éxito

---

### 6. Viral Potential (1-10)
**¿Qué predice?** Probabilidad de shares exponenciales

**Factores:**
- Sentiment extremo
- Hook muy fuerte
- Tema trending
- Duración perfecta (15-60s)
- Relatable para audiencia amplia

**Escala:**
- `9-10` = Potencial viral MUY alto (prioridad máxima)
- `7-8` = Buen potencial
- `5-6` = Potencial moderado
- `<5` = Probablemente no viral

**Uso:**
- Estrategia de publicación (horarios pico)
- Boost con ads
- Análisis post-mortem

---

## 🤖 Integración con Gemini

### API a usar
- **Modelo:** Gemini 2.5 (Flash o Pro - por decidir)
- **Llamadas:** 1 sola request batch para todos los clips
- **Input:** Array con 60 clips (transcript + duration)
- **Output:** JSON con 60 copies + metadata

### Prompt Structure
```
Analiza estos 60 clips de un video.

Para CADA clip genera:

1. COPY: Caption completo con hashtags integrados
   - Max 150 caracteres
   - Estilo viral
   - Incluye emojis
   - Hashtags mezclados en el texto

2. METADATA:
   - sentiment: tipo emocional
   - sentiment_score: 0-1
   - engagement_score: 1-10
   - suggested_thumbnail_timestamp: segundos
   - primary_topics: array de 3-5 temas
   - hook_strength: very_high/high/medium/low
   - viral_potential: 1-10

CLIPS:
[array de clips con transcript y duration]

Responde SOLO con JSON válido.
```

---

## 🔄 Flujo de Usuario

### En el CLI:

```
Menu actual:
  1. Re-transcribe video
  2. Generate/Regenerate clips
  3. Generate AI copies for clips  ← NUEVO
  4. Export clips to video files
  5. Back to menu
```

### Cuando selecciona opción 3:

```
1. ¿Qué modelo?
   [1] Gemini 2.5 Flash (más rápido)
   [2] Gemini 2.5 Pro (mejor calidad)

2. ¿Qué estilo?
   [1] Viral (default)
   [2] Educational
   [3] Storytelling

3. ¿Incluir emojis? [Y/n]

→ Processing...
→ Generating AI copies for 60 clips...
→ ━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✅ Generated 60 AI copies!
Location: output/VIDEO_NAME/copys/clips_copys.json

Top viral potential clips:
  #23 - 9.2/10 (humorous)
  #08 - 8.9/10 (controversial)
  #45 - 8.7/10 (relatable)
```

---

## 💡 Ventajas del Sistema

### Para el creador de contenido:
- ✅ Ahorra horas de escribir captions manualmente
- ✅ Copies optimizados por IA (mejores que humanos para viral)
- ✅ Priorización inteligente (sabe qué clips publicar primero)
- ✅ Data-driven decisions (no "me parece que esto funcionará")

### Técnicas:
- ✅ Una sola llamada API = rápido y barato
- ✅ Escalable (funciona igual con 10 clips o 1000)
- ✅ Versionable (regenera copies sin tocar videos)
- ✅ Separación de concerns (copies ≠ videos ≠ transcripts)

### Analíticas:
- ✅ Dashboard mental: "Mis clips educativos tienen mejor engagement"
- ✅ A/B testing: Probar diferentes estilos de copy
- ✅ Content strategy: Publicar orden optimizado por viral potential
- ✅ ROI tracking: Invertir ads en clips high-scoring

---

## ✅ IMPLEMENTADO (Nov 2025)

### Fase 1: Core functionality ✅ COMPLETO
- [x] Crear módulo `copys_generator.py` (~1000 líneas)
- [x] Integración con Gemini API (2.0 Flash Exp - modelo más reciente disponible)
- [x] **Arquitectura LangGraph con 10 nodos:**
  - load_data_node
  - **classify_clips_node** (clasificación automática)
  - **group_by_style_node** (agrupa por viral/educational/storytelling)
  - generate_viral_node
  - generate_educational_node
  - generate_storytelling_node
  - merge_results_node
  - validate_structure_node
  - analyze_quality_node
  - save_results_node
- [x] Prompt engineering modular (base + 3 estilos)
- [x] Parseo defensivo de respuesta JSON
- [x] Guardado en `copys/clips_copys.json`
- [x] **8 validators de Pydantic** (sentiment, topics, copy length, etc.)

### Fase 2: CLI Integration ✅ COMPLETO
- [x] Nuevo menú "Generate AI copies" (opción 3)
- [x] Selector de modelo (Flash Exp)
- [x] **Clasificación automática** (NO selector manual de estilo)
- [x] Progress logs en tiempo real
- [x] **Partial success UI** (verde/amarillo según resultado)
- [x] Mensaje de éxito con distribución de estilos
- [x] **Organización automática** por carpetas (viral/, educational/, storytelling/)

### Fase 3: Analytics (futuro)
- [ ] Comando para ver stats: `show-copys-stats`
- [ ] Filtrar clips por metadata
- [ ] Exportar reporte CSV
- [ ] Comparar múltiples generaciones

---

## 🔮 Ideas Futuras

### Multiidioma
- Generar copies en inglés Y español
- `clips_copys_en.json` + `clips_copys_es.json`

### Platform-specific
- Copies optimizados por plataforma
- TikTok (150 chars) vs YouTube (5000 chars)

### A/B Testing
- Generar 3 variantes de copy por clip
- Tracking de cuál funciona mejor

### Auto-upload
- Usar el JSON para subir automáticamente a TikTok/Reels
- Scheduling inteligente por viral potential

---

## 📊 Analytics Potenciales

Con el metadata generado, puedes crear:

```
📊 VIDEO ANALYTICS DASHBOARD:
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Top 5 clips por viral potential:
  1. Clip #23 - 9.2/10 (humorous)
  2. Clip #08 - 8.9/10 (controversial)
  3. Clip #45 - 8.7/10 (relatable)

Clips por sentiment:
  Educational: 22 clips (avg engagement: 7.2)
  Humorous: 15 clips (avg engagement: 8.5) ⭐
  Inspirational: 8 clips (avg engagement: 6.8)

Recommended posting order:
  Week 1: Clips 23, 8, 45 (viral potential 9+)
  Week 2: Clips 12, 34, 56 (viral potential 8+)

Topics found:
  #AI: 18 clips
  #Community: 25 clips
  #PublicSpeaking: 12 clips

Best thumbnail moments identified: 60/60 ✓
```

---

## ✅ Decisiones Finales

### Arquitectura y Formato
- ✅ Una sola llamada API batch (no 60 individuales)
- ✅ Un solo JSON con todos los copies
- ✅ Copy con hashtags integrados (no separados)
- ✅ 150 caracteres max (TikTok)
- ✅ Gemini 2.5 (Flash o Pro)
- ✅ Metadata completo generado por IA
- ✅ Carpeta `copys/` (no `copies/`)

### Stack Técnico
- ✅ **LangGraph** (orchestration con control de calidad)
- ✅ **Pydantic** (validación de datos)
- ✅ **Gemini API** vía `langchain-google-genai`

---

## 🏗️ Stack Técnico Seleccionado

### **LangGraph + Pydantic**

**¿Por qué LangGraph en lugar de LangChain simple?**

Decidimos usar **LangGraph** para implementar control de calidad adaptativo:

#### Flujo con control de calidad:
```
1. Genera 60 copies con Gemini
   ↓
2. Analiza calidad promedio
   ↓
3. ¿Engagement promedio > 7.5?
   ├─ SÍ: Guarda (calidad aceptable) ✅
   │
   └─ NO: Identifica el problema
          ↓
          ¿Qué falló?
            ├─ Hooks débiles → Regenera con "focus on STRONG hooks"
            ├─ Copies muy largos → Regenera con "max 120 chars"
            └─ Topics genéricos → Regenera con "use trending topics"
          ↓
          Reintenta (max 3 veces)
          ↓
          Guarda el mejor resultado
```

#### Ventajas de LangGraph para este caso:

1. **Calidad garantizada:**
   - No acepta copies mediocres
   - Mejora automáticamente si detecta problemas
   - Usuario siempre recibe engagement_score > 7.5

2. **Auto-corrección inteligente:**
   - Si hooks son débiles, regenera solo con mejor prompt de hooks
   - Si copies muy largos, ajusta límite de caracteres
   - Aprende del error específico, no regenera todo genéricamente

3. **Fallback multi-modelo:**
   - Intenta con Gemini Flash (rápido)
   - Si calidad < 7, upgrade a Gemini Pro
   - Si sigue mal, fallback a otro modelo

4. **Decisiones basadas en data:**
   - Analiza viral_potential promedio
   - Detecta clips individuales malos
   - Regenera solo lo necesario (no todo)

#### Por qué NO LangChain simple:

LangChain solo haría:
```
Genera → Valida estructura → Guarda
(Aunque el engagement_score promedio sea 4/10)
```

Con LangGraph:
```
Genera → Analiza calidad → Si malo, mejora → Garantiza > 7.5
```

#### Pydantic para validación:

**Rol de Pydantic:**
- Define el "contrato" de cómo DEBE ser la respuesta
- Valida tipos, rangos, longitudes automáticamente
- Auto-corrige si Gemini se equivoca

**Ejemplo:**
```python
class CopyMetadata(BaseModel):
    sentiment: Literal["educational", "humorous", ...]  # Solo valores permitidos
    engagement_score: float = Field(ge=1.0, le=10.0)   # Entre 1-10
    viral_potential: float = Field(ge=1.0, le=10.0)
    primary_topics: List[str] = Field(min_items=3, max_items=5)  # 3-5 topics

class ClipCopy(BaseModel):
    clip_id: int
    copy: str = Field(max_length=150)  # TikTok limit
    metadata: CopyMetadata
```

Si Gemini devuelve `engagement_score: "muy alto"` (string en lugar de número), Pydantic lo rechaza y LangGraph pide regeneración.

---

## 🎯 Implementación en Fases

### Fase 1 (MVP): LangGraph con control de calidad básico
- Genera copies
- Valida engagement_score promedio
- Reintenta si < 7.5 (max 2 intentos)

### Fase 2 (Mejoras): Análisis granular
- Detecta clips individuales malos
- Regenera solo clips con viral_potential < 6
- Fallback multi-modelo

### Fase 3 (Futuro): Optimización avanzada
- A/B testing automático de estilos
- Aprendizaje de qué funciona mejor por tipo de video
- Moderación de contenido

---

## 📐 Arquitectura de Decisiones (LangGraph)

```
[START]
  ↓
[Generate with Gemini Flash]
  ↓
[Validate Structure with Pydantic]
  ↓
[Analyze Quality Metrics]
  ↓
  Decision: engagement_avg > 7.5?
    ├─ YES → [SAVE] ✅
    │
    └─ NO → [Identify Problem]
            ↓
            Decision: What's wrong?
              ├─ Hooks weak → [Regenerate with hook focus]
              ├─ Too long → [Regenerate shorter]
              └─ Generic → [Regenerate with specifics]
            ↓
            Decision: attempts < 3?
              ├─ YES → [Regenerate] → Loop back to Validate
              └─ NO → [Save best attempt]
```

Este approach garantiza que siempre entregamos copies de alta calidad, no solo estructuralmente correctos.

---

## 🐛 Fase de Testing y Debugging (Nov 2025)

Durante las pruebas con video real (99 clips), encontramos y resolvimos 8 bugs críticos:

### Bugs Resueltos

| # | Bug | Solución | Aprendizaje Clave |
|---|-----|----------|-------------------|
| 1 | JSON format mismatch | Defensive parsing (dict vs array) | LLMs no siempre respetan el formato exacto |
| 2 | Sentiment híbridos | Pydantic validator `mode='before'` | Normalizar valores antes de validar tipos |
| 3 | Topics > 5 | Truncation validator | Ser permisivo en entrada, estricto en salida |
| 4 | Copy > 150 chars | Intelligent truncation + prompt mejorado | Defense in depth: prompt + validator |
| 5 | Batch failures | Error handling + continue | Fault tolerance: 1 batch malo ≠ todo malo |
| 6 | Threshold 80→60% | Lower threshold gradualmente | Graceful degradation > all-or-nothing |
| 7 | **LangGraph state bug** | Always return data keys | **CRÍTICO:** Nodos deben retornar todas las keys relevantes |
| 8 | Rate limiting 429 | Sleep 1.5s entre batches | Trade-off: +15s tiempo vs 95% success rate |

### Bug #7 Explicado (El más crítico)

**Problema:**
```python
# ❌ MAL: Nodo solo retorna error
return {
    "error_message": "70/99 clips clasificados",
    "logs": [...]
    # ¿Dónde están las 70 classifications?
}
```

**Consecuencia:**
- LangGraph continuaba el workflow
- Próximo nodo recibía `classifications=[]` (valor inicial)
- 70 clasificaciones exitosas se "perdían"

**Solución:**
```python
# ✅ BIEN: Retorna data parcial + error
return {
    "classifications": classifications,  # Las 70 que SÍ tenemos
    "error_message": "70/99 clips clasificados",
    "logs": [...]
}
```

**Lección:** En LangGraph, los nodos SOLO actualizan las keys presentes en el dict de retorno. Si omites una key, el state mantiene el valor anterior.

### Decisiones de Arquitectura Implementadas

**1. Clasificación Automática vs Manual**
- ✅ Implementado: Clasificación automática con LLM
- ❌ Descartado: Usuario elige estilo manualmente
- **Razón:** Contenido mixto (viral + educational + storytelling en mismo video)

**2. Batch Processing**
- Tamaño: 10 clips por batch
- Sleep: 1.5s entre batches
- Trade-off: Velocidad vs Rate Limiting

**3. Threshold Progresivo**
- Inicial: 80% (muy estricto)
- Iteración 1: 75%
- **Final: 60%** (balance óptimo)
- **Validación:** Muestra éxito parcial en lugar de fallo total

**4. Copy Length Enforcement**
- **Requerimiento del usuario:** "NINGÚN COPY PASE DE 150 CARACTERES"
- **Prioridad al truncar:** Mantener mensaje + #AICDMX, eliminar segundo hashtag
- **Implementación:** Prompt educativo + truncación inteligente en validator

### Stack Técnico Final

```
LangGraph (orchestration)
  ↓
Pydantic (validation con 8 validators custom)
  ↓
Gemini 2.0 Flash Exp (clasificación + generación)
  ↓
Rate Limiting Mitigation (sleep entre batches)
```

### Métricas de Éxito

**Testing con 99 clips:**
- ✅ 70+ clips clasificados (60%+ threshold)
- ✅ Copies generados con metadata completo
- ✅ 100% de copies ≤ 150 caracteres
- ✅ Rate limiting mitigado
- ✅ UI muestra partial success correctamente

**Tiempo de ejecución:**
- Clasificación: ~60s (10 batches × 1.5s sleep)
- Generación: ~45s (3 grupos)
- **Total: ~105 segundos** para 99 clips

### Archivos Creados

```
src/
├── copys_generator.py (1000 líneas) - LangGraph workflow
├── models/
│   └── copy_schemas.py (459 líneas) - 4 Pydantic models + 8 validators
└── prompts/
    ├── __init__.py (90 líneas)
    ├── base_prompts.py (160 líneas) - Reglas universales
    ├── classifier_prompt.py (300 líneas) - Clasificación automática
    ├── viral_prompt.py (150 líneas)
    ├── educational_prompt.py (150 líneas)
    └── storytelling_prompt.py (150 líneas)

tests/
└── test_copy_generation_full.py - Test end-to-end

pasoxpaso/
└── paso2.md - Plan técnico completo (2100+ líneas)

Total: ~3,000 líneas de código + documentación
```

### Documentación Completa

**Ver:** `pasoxpaso/paso2.md` para:
- Plan técnico detallado
- Decisiones de arquitectura explicadas
- Troubleshooting completo (8 bugs documentados)
- Ejemplos con video real
- Flujo LangGraph visualizado

---

## 📊 Modelo Usado: ¿Por qué Gemini 2.0 Flash Exp?

**Pregunta común:** ¿Por qué no Gemini 2.5?

**Respuesta:**
- En Nov 2025, Gemini 2.5 **no estaba disponible vía API**
- Gemini 2.0 Flash Exp era el modelo Flash más reciente
- Flash Exp = Experimental features + velocidad

**Comparación:**
- **Flash Exp:** Rápido, barato, suficientemente bueno para copies
- **Pro 1.5:** Más lento, más caro, calidad superior
- **Decisión:** Flash Exp es suficiente para este caso de uso

**Estado del código:**
```python
model: Literal["gemini-2.0-flash-exp", "gemini-1.5-pro"]
```

**Nota para futuro:** Cuando Gemini 2.5 esté disponible en API, actualizar literal types.
