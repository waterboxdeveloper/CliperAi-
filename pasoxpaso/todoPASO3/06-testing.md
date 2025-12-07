# Step 06: Testing & Validation

**Goal:** Thoroughly test face tracking with real videos and validate quality

---

## 📋 Testing Strategy

We need to test:
1. ✅ Different video types (single speaker, multiple people, no faces)
2. ✅ Both tracking strategies (keep_in_frame vs centered)
3. ✅ Different frame sample rates (1, 3, 5)
4. ✅ Quality comparison (face tracking vs static crop)
5. ✅ Error handling and edge cases

---

## ✅ Test Cases

### Test 6.1: Single Speaker Video (Ideal Case)

**Video:** Use your sample "Storycraft in the Age of AI" video

**Test Configurations:**

| Test | Strategy | Sample Rate | Expected Result |
|------|----------|-------------|-----------------|
| A1   | keep_in_frame | 3 | ✓ Smooth, minimal movement |
| A2   | centered | 3 | ✓ More movement, always centered |
| A3   | keep_in_frame | 1 | ✓ Smoothest, slower processing |
| A4   | keep_in_frame | 5 | ✓ Faster, slightly more jittery |

**Steps:**
1. Run CLIPER with test video
2. Select "Export clips"
3. Choose 9:16 aspect ratio
4. Enable face tracking with each configuration above
5. Export 2-3 clips

**Validation Checklist:**

- [ ] **A1 Test:** Face stays in frame, minimal camera movement
- [ ] **A1 Test:** No jerky movements when speaker shifts position
- [ ] **A1 Test:** Face doesn't hit edges of frame
- [ ] **A2 Test:** Face is always centered (more movement than A1)
- [ ] **A3 Test:** Noticeably smoother than A1 (but takes 3x longer)
- [ ] **A4 Test:** Faster processing, tracking still acceptable
- [ ] All exports complete without errors
- [ ] Output videos are valid MP4 files
- [ ] Subtitles (if enabled) appear correctly

---

### Test 6.2: Multiple People in Frame

**Scenario:** Video with 2+ people visible simultaneously

**Expected Behavior:** System should track the LARGEST face (assumed to be main speaker)

**Test:**
1. Find or create a test video with multiple people
2. Export with face tracking enabled
3. Verify largest face is tracked

**Validation:**
- [ ] System tracks the largest/most prominent face
- [ ] Doesn't jump between faces erratically
- [ ] If main speaker changes, tracking adapts smoothly

**Note:** If you don't have a multi-person video, document this as "Not tested - no suitable video available"

---

### Test 6.3: No Face Detected (Fallback Behavior)

**Scenario:** Video segments with no visible faces (e.g., showing slides, products, or B-roll)

**Expected Behavior:** Should fall back to static center crop

**Test:**
1. Use a video that includes segments without faces
2. Enable face tracking
3. Export a clip that contains a "no face" segment

**Validation:**
- [ ] No crash when face not detected
- [ ] Falls back to center crop gracefully
- [ ] Resumes face tracking when face reappears
- [ ] No warning/error spam in logs

---

### Test 6.4: Edge Cases

**Test these scenarios:**

#### Test 6.4a: Very Short Clip (< 3 seconds)
- [ ] Face tracking works on very short clips
- [ ] No performance issues

#### Test 6.4b: Face at Edge of Frame
- [ ] Handles speaker at extreme left/right of frame
- [ ] Crop doesn't go out of bounds
- [ ] No black bars or artifacts

#### Test 6.4c: Fast Movement
- [ ] Handles speaker moving quickly across frame
- [ ] Doesn't lose tracking
- [ ] Movement is smoothed appropriately

#### Test 6.4d: Poor Lighting
- [ ] MediaPipe still detects face in dim lighting
- [ ] Gracefully falls back if detection fails

---

### Test 6.5: Performance Benchmarking

**Measure processing time difference:**

**Setup:** Use same 60-second video clip

**Export with:**
1. Static crop (no face tracking)
2. Face tracking (sample rate 3)
3. Face tracking (sample rate 5)

**Record times:**

| Configuration | Processing Time | Speed Factor |
|---------------|-----------------|--------------|
| Static crop   | ___ seconds     | 1x (baseline) |
| Face track (3) | ___ seconds     | ___x slower   |
| Face track (5) | ___ seconds     | ___x slower   |

**Validation:**
- [ ] Face tracking is noticeably slower (expected)
- [ ] Higher sample rate = faster processing
- [ ] Processing time is acceptable for production use (<3x slower)

---

### Test 6.6: Quality Comparison

**Side-by-side visual comparison:**

**Export same clip with:**
1. Static center crop
2. Face tracking (keep_in_frame)

**Watch both and evaluate:**

| Aspect | Static Crop | Face Tracking | Winner |
|--------|-------------|---------------|--------|
| Subject always visible | | | |
| Professional look | | | |
| Minimal distracting movement | | | |
| Face appropriately framed | | | |
| Overall quality | | | |

**Validation:**
- [ ] Face tracking keeps speaker better framed
- [ ] Movement looks intentional, not robotic
- [ ] Quality improvement justifies processing time
- [ ] Would use this for production content

---

## 🎯 Overall Validation Checklist

Before moving to Step 07:

### Functionality
- [ ] Face tracking works on single-speaker videos
- [ ] Both strategies (keep_in_frame, centered) work
- [ ] Frame sampling rates (1, 3, 5) all work
- [ ] Fallback to center crop when no face detected
- [ ] Temporary files are cleaned up

### Quality
- [ ] Face stays in frame throughout clip
- [ ] Camera movement looks professional
- [ ] No jarring/jerky movements
- [ ] Better than static center crop

### Performance
- [ ] Processing time is acceptable
- [ ] No memory leaks or crashes
- [ ] Works with various video lengths

### Error Handling
- [ ] Graceful failures (doesn't crash)
- [ ] Helpful error messages
- [ ] Logs show useful debugging info

---

## 📊 Test Results Document

**Create:** `/pasoxpaso/todoPASO3/test-results.md`

**Template:**
```markdown
# Face Tracking Test Results

**Date:** [Date]
**Tester:** [Name]
**Environment:** [Local / Docker]

## Test 6.1: Single Speaker
- Configuration A1: [PASS/FAIL] - Notes: ___
- Configuration A2: [PASS/FAIL] - Notes: ___
- Configuration A3: [PASS/FAIL] - Notes: ___
- Configuration A4: [PASS/FAIL] - Notes: ___

## Test 6.2: Multiple People
- [PASS/FAIL/SKIPPED] - Notes: ___

## Test 6.3: No Face Fallback
- [PASS/FAIL] - Notes: ___

## Test 6.4: Edge Cases
- Very short clips: [PASS/FAIL]
- Face at edge: [PASS/FAIL]
- Fast movement: [PASS/FAIL]
- Poor lighting: [PASS/FAIL]

## Test 6.5: Performance
- Static crop time: ___ sec
- Face track (3): ___ sec (___x slower)
- Face track (5): ___ sec (___x slower)

## Test 6.6: Quality Comparison
Winner: [Static / Face Tracking]
Notes: ___

## Overall Assessment
- Ready for production: [YES/NO]
- Issues found: ___
- Recommended improvements: ___
```

- [ ] Created `test-results.md` with findings

---

## ❓ Common Issues & Solutions

**Problem:** Face tracking too slow
**Solution:** Increase sample rate to 5 or 10

**Problem:** Tracking is jittery
**Solution:** Need to implement smoothing (moving average) - mark for Step 07

**Problem:** Face goes out of frame sometimes
**Solution:** Reduce safe_zone_margin (e.g., 0.10 instead of 0.15)

**Problem:** Too much movement
**Solution:** Increase safe_zone_margin (e.g., 0.20 instead of 0.15)

---

---

## 🔬 Sesión de Testing 2025-11-29

**Estado:** VALIDACIÓN INICIAL COMPLETADA

### Implementación FFmpegVideoWriter Validada

**Test ejecutado:** `tests/test_ffmpeg_subprocess.py`

**Configuración:**
- Video: "Storycraft in the Age of AI" (LZlXASa8CZM)
- Clip: 10 segundos (30.0 - 40.0s)
- Resolución: 1080x1920 (9:16)
- Face tracking: ENABLED (keep_in_frame strategy)
- Sample rate: 3 frames

**Resultados:**

✅ **Face Tracking:**
- MediaPipe detectó rostro correctamente
- Crop dinámico aplicado (keep_in_frame)
- 300 frames procesados sin errores

✅ **FFmpegVideoWriter:**
- Subprocess FFmpeg funcional (arm64 nativo)
- Codec: libx264 (software encoding)
- Output: 3.40 MB para 10 segundos
- Video reproducible en VLC

⚠ **Limitaciones del Test Aislado:**
- Solo video frames (sin audio)
- Sin subtítulos
- Por diseño: test valida SOLO reframing

**Decisión arquitectónica:** Test aislado vs Pipeline completo

```
Test Aislado (tests/test_ffmpeg_subprocess.py):
└── FaceReframer.reframe_video()
    └── FFmpegVideoWriter: Solo video frames
    └── Propósito: Validar face tracking solamente

Pipeline Completo (VideoExporter):
├── FaceReframer: Genera temp video reframed
├── SubtitleGenerator: Crea SRT
└── FFmpeg merge: Video + Audio + Subtítulos
    └── Propósito: Producción con todas las features
```

### Cleanup Realizado

**Dependencias removidas:**
```bash
uv remove ffmpegcv  # Bug en macOS M4
```

**Archivos obsoletos eliminados:**
- tests/test_ffmpegcv_integration.py
- tests/test_ffmpegcv_minimal.py
- tests/test_ffmpegcv_debug.py

**Archivos organizados:**
- spike_face_reframing.py → tests/ (siguiendo .claude/claude.md)

### Bug Report Preparado

**Archivo:** `pasoxpaso/OPENCV-BUG-REPORT.md`

**Issue:** cv2.VideoWriter.write() falla en macOS Apple Silicon
- opencv-python 4.12.0 instala FFmpeg amd64 (no arm64)
- Afecta todos los package managers PyPI (pip, uv, poetry)
- Reporte listo para contribución open source

### Herramientas Instaladas

**VLC Media Player:**
```bash
brew install --cask vlc  # v3.0.21-arm64
```

**Razón:** QuickTime no abre algunos MP4 generados
**Solución:** VLC (universal codec support)

### Próximo Paso: Testing Pipeline Completo

**PENDIENTE:** Validar audio + subtítulos + face tracking integrados

**Blocker actual:** Archivos temp/ fueron limpiados
- `temp/*_transcript.json` (eliminado)
- `temp/*_clips.json` (eliminado)

**Solución propuesta:** Crear feature de cleanup en CLI (ver todoCLEANUP)

---

## 🔬 Sesión de Testing 2025-11-30: Bug Fixes

**Estado:** BUG FIXES VALIDADOS

### Bug Fix 1: Missing Audio (Face Tracking)

**Test creado:** `tests/test_audio_mapping.py`

**Propósito:** Validar comando FFmpeg con audio mapping cuando se usa face tracking

**Resultado:**
```bash
✓ COMANDO CORRECTO (con audio):
ffmpeg -i reframed.mp4 -i original.mp4 -map 0:v -map 1:a ...

✗ COMANDO INCORRECTO (sin audio):
ffmpeg -i reframed.mp4 -c:a aac ...  # No hay stream de audio
```

**Validación:**
- ✅ Comando genera 2 inputs correctamente
- ✅ `-map 0:v` mapea video del reframed
- ✅ `-map 1:a` mapea audio del original
- ✅ `-ss` y `-t` sincronizan audio

---

### Bug Fix 2: Duplicate Subtitles (Face Tracking)

**Test creado:** `tests/test_subtitle_filter_complex.py`

**Propósito:** Comparar sintaxis de `-filter_complex` vs `-vf` para subtítulos

**Resultado:**
```bash
❌ PROBLEMA (filter_complex):
-filter_complex "[0:v]subtitles='file.srt':force_style='...'[v]"
# Comillas causan duplicación

✓ SOLUCIÓN (map + vf):
-map 0:v -map 1:a -vf "subtitles='file.srt':force_style='...'"
# Sin duplicación
```

**Validación:**
- ✅ Sintaxis `-map` + `-vf` funciona correctamente
- ✅ Subtítulos se renderizan UNA sola vez
- ✅ Estilo `force_style` se aplica correctamente

---

### Diagnóstico de Archivos SRT

**Test creado:** `tests/diagnose_subtitles.py`

**Propósito:** Validar que archivos SRT no tengan contenido duplicado

**Uso:**
```bash
# Diagnosticar archivo SRT específico
uv run python tests/diagnose_subtitles.py output/video_id/1.srt

# Output:
# ✓ No hay timestamps duplicados
# ✓ No hay metadata ASS/SSA
# 📊 Total subtítulos: 28
```

**Validación:**
- ✅ SRT generados por `subtitle_generator.py` no tienen duplicados
- ✅ Formato SRT estándar (sin metadata extra)
- ✅ Timestamps únicos y válidos

---

### Debug Logging Implementado

**Feature:** Cada exportación guarda comando FFmpeg exacto

**Archivo:** `output/ffmpeg_commands_debug.log`

**Formato:**
```
================================================================================
CLIP: 1 | Face Tracking: True | Subtitles: True
================================================================================
ffmpeg -i reframed_temp.mp4 -ss 10.5 -i original.mp4 -t 30.2 -map 0:v -map 1:a ...

================================================================================
CLIP: 2 | Face Tracking: True | Subtitles: False
================================================================================
ffmpeg -i reframed_temp.mp4 -ss 45.3 -i original.mp4 -t 25.8 -map 0:v -map 1:a ...
```

**Uso:**
```bash
# Ver últimos comandos ejecutados
tail -n 50 output/ffmpeg_commands_debug.log

# Buscar comandos con subtítulos
grep "Subtitles: True" output/ffmpeg_commands_debug.log

# Copiar comando para testing manual
cat output/ffmpeg_commands_debug.log | tail -n 1
```

**Validación:**
- ✅ Log se crea automáticamente en exportaciones
- ✅ Formato legible y copiable
- ✅ Incluye metadata útil (clip_id, flags)

---

### Validación Manual Pipeline Completo

**Test realizado:** Exportar clip con face tracking + subtítulos

**Configuración:**
```
Video: "Storycraft in the Age of AI"
Clip: 30 segundos
Aspect ratio: 9:16 (vertical)
Face tracking: ENABLED (keep_in_frame)
Subtítulos: ENABLED (small style)
```

**Resultados:**

✅ **Audio:**
```bash
ffprobe output/video_id/1.mp4 -show_streams | grep codec_type=audio
# Output: codec_type=audio
# ✓ Audio presente en clip final
```

✅ **Subtítulos:**
- Se renderiza UN solo conjunto de subtítulos
- Estilo "small" aplicado correctamente (10px, amarillos)
- NO aparecen subtítulos blancos duplicados

✅ **Face Tracking:**
- Crop dinámico funcional
- Rostro visible durante todo el clip
- Movimiento suave (keep_in_frame strategy)

✅ **Integración:**
- Audio sincronizado con video
- Subtítulos alineados con timestamps
- Calidad de video preservada
- Archivo temporal limpiado automáticamente

---

### Regresión Testing

**Validación:** Pipeline SIN face tracking sigue funcionando

**Test:**
```
Video: Mismo
Clip: Mismo timestamp
Aspect ratio: 9:16
Face tracking: DISABLED
Subtítulos: ENABLED
```

**Resultados:**
- ✅ Audio presente (input único funciona)
- ✅ Subtítulos correctos (sintaxis `-vf` estándar)
- ✅ Crop estático centrado funcional
- ✅ Sin cambios en comportamiento anterior

---

### Conclusión Testing Session

**TODOS LOS BUG FIXES VALIDADOS:**

1. ✅ Audio mapping con face tracking: FUNCIONAL
2. ✅ Subtítulos sin duplicación: FUNCIONAL
3. ✅ Debug logging: IMPLEMENTADO
4. ✅ Tests diagnósticos: CREADOS
5. ✅ Regresión: SIN IMPACTO EN FLUJO NORMAL

**READY FOR PRODUCTION**

---

**Next Step:** `07-optimization.md` →
