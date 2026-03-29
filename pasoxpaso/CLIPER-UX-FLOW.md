# CLIPER UX Flow Map

**Propósito:** Visualizar el flujo de navegación completo para identificar puntos de feedback

---

## 🚀 INICIO (main())

```
┌─────────────────────────────────────────┐
│  1. Mostrar BANNER                      │
│  2. Inicializar logging (logs/ file)    │
│  3. Escanear videos en downloads/       │
│  4. Sincronizar state                   │
└────────────────────┬────────────────────┘
                     │
              ¿Hay videos?
                  /    \
               SÍ       NO
               /          \
          ┌──────┐      ┌──────┐
          │ MENU │      │ MENU │
          │  A   │      │  B   │
          └──────┘      └──────┘
```

---

## 📋 MENÚ A: Con Videos (si downloads/ no está vacío)

**Localización:** `menu_principal()` línea 169

```
┌──────────────────────────────────────────┐
│       MAIN MENU (Videos Available)       │
├──────────────────────────────────────────┤
│ 1. Process a video                       │
│ 2. Download new video                    │
│ 3. Cleanup project data                  │
│ 4. Full Pipeline (auto) [Coming soon]    │
│ 5. Exit                                  │
└────┬────┬────┬────┬────────────────────┘
     │    │    │    │
    [1]  [2]  [3]  [4]  [5] → EXIT
     │    │    │    │
     ▼    ▼    ▼    ▼
```

---

## 📋 MENÚ B: Sin Videos (si downloads/ vacío)

**Localización:** `menu_principal()` línea 169 (rama else)

```
┌──────────────────────────────────────────┐
│        MAIN MENU (No Videos)             │
├──────────────────────────────────────────┤
│ 1. Download new video                    │
│ 2. Cleanup project data                  │
│ 3. Exit                                  │
└────┬────┬────┬────────────────────────┘
     │    │    │
    [1]  [2]  [3] → EXIT
     │    │    │
     ▼    ▼    ▼
```

---

## 🔄 OPCIÓN 1: Process a Video

**Función:** `opcion_procesar_video()` línea 320

```
┌────────────────────────────────┐
│ SELECT VIDEO                   │
│ ┌──────────────────────────┐   │
│ │ 1. Video A (80%)         │   │
│ │ 2. Video B (30%)         │   │
│ │ ...                      │   │
│ └──────────────────────────┘   │
└────────────────────────────────┘
         │
    [Video selected]
         │
         ▼
┌────────────────────────────────────────┐
│ PROCESS VIDEO SUBMENU                  │
│ Status: ✓ Transcribed | ✓ 5 clips     │
├────────────────────────────────────────┤
│ 1. Re-transcribe video                 │
│ 2. Generate/Regenerate clips           │
│ 3. Generate AI copies (clasificación)  │
│ 4. Export clips to video files         │
│ 5. Back to menu                        │
└───┬──┬──┬──┬──────────────────────────┘
    │  │  │  │
   [1][2][3][4][5]
    │  │  │  │
    ▼  ▼  ▼  ▼
```

### Subrama [1]: Re-transcribe
**Función:** `opcion_transcribir_video()` línea 438
- Ejecuta WhisperX
- Genera `temp/{video_id}_transcript.json`
- Actualiza state

### Subrama [2]: Generate/Regenerate Clips
**Función:** `opcion_generar_clips()` línea 588
- Ejecuta ClipsAI
- Genera `temp/{video_id}_clips_metadata.json`
- Actualiza state + lista clips en tabla

### Subrama [3]: Generate AI Copies
**Función:** `opcion_generar_copies()` línea 811

**Flujo de Configuración:**

```
┌─────────────────────────────────────┐
│ SELECT GEMINI MODEL:                │
│  [1] gemini-2.5-flash (default)    │
│  [2] gemini-1.5-pro                │
│  [3] Back to menu                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ SELECT LLM PROVIDER:                │ ← [NUEVO - Dual LLM Support]
│  [1] Gemini (requires GOOGLE_API)  │
│  [2] Claude (requires ANTHROPIC_API)│
│  [3] Back to menu                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Generating copies with LangGraph...  │
│ Using: [Gemini|Claude]              │
│                                      │
│ ✓ Classification                    │
│ ✓ Grouping by style                 │
│ ✓ Generation (viral/edu/story)      │
│ ✓ Validation                        │
│ ✓ Quality analysis                  │
└──────────────┬───────────────────────┘
               │
               ▼
       RESULTS SHOWN:
   • Total copies generated
   • Avg engagement score
   • Avg viral potential
   • Distribution by style
```

**Detalles:**
- **PASO2 Enhancement:** Extrae opening_words + speaker_hashtags
- **LLM Selection:** Elige entre Gemini (default) o Claude
- **Execution:** Ejecuta LangGraph + LLM elegido
- **Output:** Genera `output/{video_id}/copys/clips_copys.json`
- **Metrics:** Muestra engagement, viral potential, distribution

### Subrama [4]: Export Clips
**Función:** `opcion_exportar_clips()` línea 1160

**Flujo de Configuración:**

```
┌─────────────────────────────────────┐
│ 1. SELECT ASPECT RATIO              │
│   [1] Original (16:9)               │
│   [2] Vertical (9:16)               │
│   [3] Cuadrado (1:1)                │
│   [4] Volver al menú anterior       │
└──────────────┬──────────────────────┘
               │
               ▼ (solo si vertical)
┌─────────────────────────────────────┐
│ 2. FACE TRACKING (PASO3)            │
│   Enable intelligent reframing?     │
│   [y/n] (n)                         │
│   → Strategy: keep_in_frame/centered│
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. LOGO OVERLAY (PASO4)             │
│   Add logo? [y/n] (n)               │
│   → Position: top-right/left/etc    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. SUBTITLES                        │
│   Add subtitles? [y/n] (y)          │
│   → Style: default/bold/yellow/etc  │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│     📋 EXPORT CONFIGURATION REVIEW                   │
├──────────────────────────────────────────────────────┤
│ Aspect ratio:      Vertical (9:16)                   │
│ Face tracking:     ✓ keep_in_frame                   │
│ Logo:              ✓ top-right                       │
│ Subtitles:         ✓ small                           │
│ Clips to export:   3 de 5                            │
├──────────────────────────────────────────────────────┤
│ ¿Qué deseas hacer?                                   │
│                                                      │
│  [Y] Cambiar algo                                    │
│  [N] Proceder al export                              │
│  [C] Cancelar y volver al menú anterior              │
└──────────────┬───────────────────────────────────────┘
               │
        ┌──────┼──────┐
        │      │      │
       [Y]    [N]    [C]
        │      │      │
        ▼      ▼      ▼
     ┌─────┐┌─────┐┌─────┐
     │Edit │Export Done  │
     │Menu │     │Volver │
     └─────┘└─────┘└─────┘

EDIT MENU (si [Y]):
  [1] Aspect ratio
  [2] Face tracking (si vertical)
  [3] Logo
  [4] Subtitles
  [5] Clips a exportar
  [6] Volver a resumen

→ Edita opción → Vuelve a resumen → Puede cambiar múltiples opciones
```

**Arquitectura de Decision:**
- **Sin interrupciones:** Recolecta todas las configuraciones sin confirmación
- **Review final:** Una pantalla con resumen de todas las opciones
- **Edición granular:** Puede cambiar cualquier configuración sin afectar otras
- **Sin pérdida:** Si cancela [C], descarta todo y vuelve (sin guardar)
- **Loop de edición:** Puede hacer múltiples cambios antes de confirmar export

**Archivos generados:**
- `output/{video_id}/{style}/clip_{id}.mp4` - Clips exportados
- Subdirectories por estilo si clasificación existe (viral/educational/storytelling)

---

## 📥 OPCIÓN 2: Download New Video

**Función:** `opcion_descargar_video()` línea 217

```
┌────────────────────────────────┐
│ DOWNLOAD VIDEO                 │
├────────────────────────────────┤
│ Paste YouTube URL:             │
│ [_____________________________] │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ SELECT CONTENT TYPE            │
├────────────────────────────────┤
│ 1. Tech talk/Presentation      │
│ 2. Podcast/Interview           │
│ 3. Livestream [DEFAULT]        │
│ 4. Tutorial/Educational        │
│ 5. Other                       │
└────────────────────────────────┘
         │
    [Content type selected]
         │
         ▼
┌────────────────────────────────┐
│ Downloading...                 │
│ ✓ Downloaded successfully      │
├────────────────────────────────┤
│ Would you like to transcribe   │
│ this video now? [y/n]          │
└────────────────────────────────┘
        /    \
      YES    NO
       │      │
       ▼      ▼
   [Trans.] [Back]
```

---

## 🧹 OPCIÓN 3: Cleanup Project Data

**Función:** `opcion_cleanup_project()` línea 1336

```
┌────────────────────────────────────┐
│ CLEANUP PROJECT DATA               │
├────────────────────────────────────┤
│ 📊 Space Summary:                  │
│   💾 Downloaded: 2.5 GB            │
│   📝 Transcripts: 150 MB           │
│   📋 Clips meta: 45 MB             │
│   🎬 Exported: 8.2 GB              │
│   ─────────────────────            │
│   Total: 11 GB                     │
├────────────────────────────────────┤
│ Table: Cleanable Artifacts by      │
│        Video (tamaños granulares)  │
├────────────────────────────────────┤
│ CLEANUP OPTIONS:                   │
│ 1. Keep downloads & transcripts    │
│    (re-process mode)               │
│ 2. Fresh start (delete everything) │
│ 3. Back to main menu               │
└────┬────┬────────────────────────┘
     │    │
    [1]  [2]  [3]
     │    │    │
     ▼    ▼    ▼
```

### Subrama [1]: Re-process Mode
**Función:** `cleanup_keep_downloads_and_transcripts()` línea 1399

```
Confirmation:
✓ KEEP: Downloads + Transcripts
✗ DELETE: Clips metadata, outputs, logs, cache

Type YES to confirm
```

### Subrama [2]: Fresh Start
**Función:** `cleanup_entire_project()` línea 1558

```
WARNING: Will DELETE ALL project data
- All downloaded videos
- All transcripts
- All detected clips
- All exported clips
- Project state

Total space to free: 11 GB

Type 'DELETE ALL' to confirm
```

---

## 📊 Estado del Video (Persiste en project_state.json)

Cada video tiene estados que cambian según dónde estés:

```
Video: "AI_CDMX_Live_Stream_gjPVlCHU9OM"

State progression:
┌────────────────────────────────────┐
│ 1. DOWNLOADED ✓                    │
│    └─ Archivo: downloads/video.mp4 │
├────────────────────────────────────┤
│ 2. TRANSCRIBED ✓                   │
│    └─ Archivo: temp/video_trans.json
├────────────────────────────────────┤
│ 3. CLIPS_GENERATED ✓               │
│    └─ Archivo: temp/video_clips.json
│    └─ Count: 12 clips              │
├────────────────────────────────────┤
│ 4. COPYS_GENERATED ✓               │
│    └─ Archivo: output/copys/clips_copys.json
│    └─ Engagement avg: 8.2/10       │
├────────────────────────────────────┤
│ 5. CLIPS_EXPORTED ✓                │
│    └─ Count: 12 .mp4 files         │
│    └─ Total size: 2.1 GB           │
│    └─ Aspect ratio: 9:16           │
└────────────────────────────────────┘
```

---

## 🎯 Archivos Generados por Cada Paso

```
downloads/
└── AI_CDMX_Live_Stream_gjPVlCHU9OM.mp4  ← OPCIÓN 2

temp/
├── AI_CDMX_Live_Stream_gjPVlCHU9OM_transcript.json ← OPCIÓN 1[transcribe]
└── AI_CDMX_Live_Stream_gjPVlCHU9OM_clips_metadata.json ← OPCIÓN 1[clips]

output/
└── AI_CDMX_Live_Stream_gjPVlCHU9OM/
    ├── copys/
    │   └── clips_copys.json ← OPCIÓN 1[copies]
    ├── viral/
    │   ├── clip_1.mp4 ← OPCIÓN 1[export]
    │   ├── clip_1.srt
    │   ├── clip_2.mp4
    │   ├── clip_2.srt
    │   ...
    ├── educational/
    │   ...
    └── storytelling/
        ...

logs/
└── cliper_20260321_120530.log ← Logging automático en cada run
```

---

## 🔧 Puntos Clave de Interacción

| Pantalla | Dónde | Decisión | Impacto |
|----------|-------|----------|---------|
| Main Menu | `menu_principal()` | Opción 1-5 | Rama principal |
| Select Video | `opcion_procesar_video()` | Video a procesar | Determina qué se procesa |
| Process Submenu | Loop en opcion_procesar_video() | 1-4 | Qué paso ejecutar |
| Content Type | `opcion_descargar_video()` | Preset | Optimización para tipo |
| Cleanup Options | `opcion_cleanup_project()` | 1-2 | Qué mantener/borrar |
| Aspect Ratio | `opcion_exportar_clips()` | 16:9, 9:16, etc | Formato de salida |
| Gemini Model | `opcion_generar_copies()` | gemini-2.5-flash/pro | Modelo Gemini |
| LLM Provider | `opcion_generar_copies()` | Gemini/Claude | Qué LLM usar |

---

## 🔍 Lugares donde el Usuario da Input

```
1. Menu choices (numeric)
2. YouTube URLs (text)
3. Video selection (numeric)
4. Confirmations (Y/N)
5. Content type selection (numeric)
6. Gemini model selection (numeric)
7. LLM Provider selection (numeric) ← [NUEVO - Gemini vs Claude]
8. Aspect ratio selection (numeric)
9. Delete confirmations (text: "DELETE ALL")
```

---

## 📝 Sugerencias para Feedback

**¿Qué quieres cambiar?**

- **Orden de opciones** en algún menú?
- **Nombres de opciones** (más claros/cortos)?
- **Nuevas opciones** (ej: "Batch process multiple videos")?
- **Removedor opciones** (ej: "Full Pipeline - es confuso)?
- **Flujo de decisión** (ej: "Debería preguntar X antes de Y")?
- **Validaciones** (ej: "Debería validar URLs antes de descargar")?
- **Información mostrada** en cada pantalla?

---

## 📍 Referencias de Código

| Función | Línea | Pantalla |
|---------|-------|----------|
| `main()` | 1593 | Inicio + Loop |
| `menu_principal()` | 169 | Menú A/B |
| `opcion_procesar_video()` | 320 | Seleccionar + Procesar |
| `opcion_descargar_video()` | 217 | Descargar |
| `opcion_cleanup_project()` | 1336 | Cleanup |
| `opcion_transcribir_video()` | 438 | Transcribe |
| `opcion_generar_clips()` | 588 | Detect clips |
| `opcion_generar_copies()` | 811 | Generate copies (PASO2) |
| `opcion_exportar_clips()` | 971 | Export videos |
