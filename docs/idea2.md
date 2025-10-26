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

## 🎯 Por Implementar

### Fase 1: Core functionality
- [ ] Crear módulo `copys_generator.py`
- [ ] Integración con Gemini API (2.5 Flash/Pro)
- [ ] Prompt engineering para batch processing
- [ ] Parseo de respuesta JSON
- [ ] Guardado en `copys/clips_copys.json`

### Fase 2: CLI Integration
- [ ] Nuevo menú "Generate AI copies"
- [ ] Selector de modelo (Flash/Pro)
- [ ] Selector de estilo (Viral/Educational/Storytelling)
- [ ] Progress bar para generación
- [ ] Mensaje de éxito con top clips

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
