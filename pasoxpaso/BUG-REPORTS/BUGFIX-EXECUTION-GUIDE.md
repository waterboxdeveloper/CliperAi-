# Guía de Ejecución: Diagnóstico del Bug de Subtítulos Duplicados

**Objetivo:** Identificar la causa raíz del bug donde subtítulos aparecen duplicados cuando se habilita logo + subtítulos simultáneamente.

**Status del Bug:** UNRESOLVED - El intento anterior con `-sn` flag falló

---

## Contexto Rápido

### Problema
- Cuando `add_logo=True` y `add_subtitles=True`, los subtítulos aparecen **dos veces** en el video final
- El `-sn` flag (descartar streams de subtítulos) NO resolvió el problema
- Conclusión: La hipótesis original (metadata preservation) era **incorrecta**

### Arquitectura Actual
```
Step 1: FFmpeg filter_complex con logo overlay
        Output: temp.mp4 (con -sn flag)

Step 2: FFmpeg -vf subtitles
        Output: final.mp4
```

### Qué Probamos
- ❌ `-sn` flag para limpiar metadata de subtítulos
- Resultado: Bug persiste → El problema NO es metadata

### Hipótesis Nuevas a Investigar
1. **FFmpeg buffer/cache state** - FFmpeg mantiene estado entre pasos
2. **Frame timing desynchronization** - Mismatch entre video re-encoded y SRT timing
3. **FFmpeg subtitle filter bug** - Known issues en la versión actual de FFmpeg
4. **Single-pass alternative** - Combinar logo + subtítulos en UN comando FFmpeg

---

## Fase 1: Diagnóstico Básico (TODAY)

### Paso 1.1: Ejecutar Script de Diagnóstico

```bash
cd /Users/ee/Documents/opino.tech/Cliper

# Ejecutar el script de diagnóstico
python tests/diagnose_subtitle_duplication.py
```

**Qué hace:**
1. Verifica FFmpeg y FFprobe están instalados
2. Crea un video de prueba minimal (10 segundos, 1920x1080)
3. Genera subtítulos SRT simples (3 líneas)
4. Exporta con `add_logo=True` (si existe) + `add_subtitles=True`
5. Inspecciona metadata con ffprobe antes y después
6. Reporta hallazgos

**Esperado:**
```
✓ FFmpeg encontrado
✓ FFprobe encontrado
✓ Video de prueba creado
✓ Subtítulos creados
✓ Clip exportado
✓ Diagnóstico completado

Archivos generados:
  - temp/test_minimal.mp4
  - temp/test_subtitles.srt
  - output/diagnosis_test/test_001.mp4
```

### Paso 1.2: Verificación Manual

**Abre el video exportado:**
```bash
# macOS
open output/diagnosis_test/test_001.mp4

# Cualquier OS
vlc output/diagnosis_test/test_001.mp4
```

**Observa:**
1. ¿Aparecen subtítulos **una sola vez**? → BUG RESUELTO ✓
2. ¿Aparecen subtítulos **dos veces**? → BUG PERSISTE ✗
3. ¿El timing es correcto? → Nota si hay offset

**Documenta:** En qué momento exacto aparecen los subtítulos duplicados

### Paso 1.3: Inspección de Metadata (Si subtítulos duplicados)

```bash
# Inspeccionar el temp.mp4 generado (después de Step 1)
ffprobe -show_streams temp/temp_*.mp4 | grep -A5 -B5 "subtitle"

# Inspeccionar el output final
ffprobe -show_streams output/diagnosis_test/test_001.mp4 | grep -A5 -B5 "subtitle"

# Ver duración exacta
ffprobe -show_format output/diagnosis_test/test_001.mp4 | grep duration
```

**Qué buscar:**
- ¿Hay streams de subtítulos en el temp.mp4? (No debería - por `-sn`)
- ¿El timing del video coincide con el SRT?
- ¿Hay metadata oculta?

---

## Fase 2: Diagnóstico Profundo (Si necesario)

### Si Paso 1.3 no es conclusivo: FFmpeg Verbose Debug

```bash
# Ejecutar Step 2 manualmente con debug verbose
ffmpeg -loglevel debug \
  -i temp/temp_*.mp4 \
  -vf "subtitles='temp/test_subtitles.srt':force_style='FontSize=20'" \
  -c:a copy \
  debug_output.mp4 2>&1 | tee ffmpeg_debug.log

# Analizar el log
grep -i "subtitle\|codec\|stream\|duplicate" ffmpeg_debug.log
```

**Qué buscar en el debug log:**
- Mensajes sobre subtítulos múltiples
- Warnings o errors en codec processing
- Stream handling details

### Si Paso 1.2 muestra offset timing

```bash
# Verificar que duración sea idéntica
ffprobe -show_format temp/test_minimal.mp4 | grep duration
ffprobe -show_format temp/temp_*.mp4 | grep duration
ffprobe -show_format output/diagnosis_test/test_001.mp4 | grep duration

# Todas deberían ser 10.0 segundos
```

---

## Hipótesis y Pruebas Rápidas

### H1: FFmpeg Filter Bug (Más probable)

Si los subtítulos aún duplican en video final:

```bash
# Probar OPCIÓN A: Usar "ass" filter en lugar de "subtitles"
ffmpeg -i temp/temp_*.mp4 \
  -vf "ass='temp/test_subtitles.srt':force_style='...'" \
  -c:a copy \
  test_ass_filter.mp4

# Probar OPCIÓN B: Single-pass (logo + subtítulos en UN comando)
ffmpeg -i output/diagnosis_test/test_original.mp4 -i assets/logo.png \
  -filter_complex "[0:v]scale=1080:1920;[...]overlay=...;[...]subtitles='temp/test_subtitles.srt'[out]" \
  -map "[out]" -map 0:a \
  test_single_pass.mp4
```

**Evalúa:**
- ¿Opción A (ass filter) evita duplicación?
- ¿Opción B (single-pass) funciona correctamente?

### H2: Codec/Timing Mismatch

```bash
# Probar usar -c:v copy en Step 1 (sin re-encode)
# Esto previene desynchronization entre video y SRT

# Script para probar:
# 1. Modificar video_exporter.py temporalmente
# 2. Cambiar: "-c:v", "libx264" → "-c:v", "copy" en Step 1
# 3. Exportar y observar
```

### H3: FFmpeg Version Issue

```bash
# Verificar versión
ffmpeg -version | head -1

# Buscar en FFmpeg bugtracker:
# - "duplicate subtitles"
# - "subtitle filter regression"
# - "two-pass video encoding subtitle"
```

---

## Árbol de Decisión

```
┌─ Ejecutar diagnóstico
│
├─ ¿Subtítulos aparecen una sola vez?
│  └─→ ✓ BUG RESUELTO
│      (Algo en el environment cambió, o fue fix incidental)
│
└─ ¿Subtítulos duplicados en output?
   │
   ├─ ¿ffprobe muestra streams de subtítulos en temp.mp4?
   │  ├─→ SÍ: H1 o H3 (filter internals o version bug)
   │  │      → Probar ass filter y single-pass
   │  │
   │  └─→ NO: H2 o H4 (timing/codec issue)
   │         → Probar -c:v copy en Step 1
   │
   └─ Basado en resultado:
      → Implementar solución
```

---

## Después del Diagnóstico: Próximos Pasos

### Si H1 o H3: Filter/Version Bug

**Plan A: Three-Step Process**
```
Step 1: Logo overlay (limpio)
Step 2: Re-encode (limpio)
Step 3: Subtítulos (en video limpio)
```

**Plan B: Single-Pass Consolidation**
```
Step 1: Logo + Subtítulos + Aspect ratio (TODO EN UNO)
```

**Plan C: OpenCV Fallback**
```
Step 1: Logo + aspect ratio con FFmpeg
Step 2: Agregar subtítulos frame-by-frame con Python/PIL
```

### Si H2: Timing/Codec Issue

**Solution:**
```
Step 1: Usar -c:v copy (no re-encode)
        + Preservar timebase
Step 2: Subtítulos normales
```

---

## Validación Final

Una vez implementada una solución:

```bash
# Ejecutar suite de tests
python -m pytest tests/test_logo_subtitles_regression.py -v

# Probar con diferentes videos
python tests/diagnose_subtitle_duplication.py
# (Debería pasar sin duplicación)

# Validar performance
time python tests/diagnose_subtitle_duplication.py
# (Debería ser < 60 segundos total)
```

---

## Referencias Rápidas

**Código principal:**
- `src/video_exporter.py` - Lines 250-320 (la sección crítica)
- `src/video_exporter.py` - Lines 389-399 (`_get_subtitle_filter` method)

**Documentación:**
- `pasoxpaso/BUGFIX-subtitle-duplication.md` - Análisis del bug original
- `pasoxpaso/BUGFIX-PLAN-2025-12-07.md` - Plan completo de investigación

**Tests:**
- `tests/diagnose_subtitle_duplication.py` - Script de diagnóstico
- `tests/test_logo_subtitles_regression.py` - Suite de tests

---

## Comandos Útiles

```bash
# Ubicarse en raíz del proyecto
cd /Users/ee/Documents/opino.tech/Cliper

# Ejecutar diagnóstico
python tests/diagnose_subtitle_duplication.py

# Ver debug output de un clip específico
ffmpeg -loglevel debug -i input.mp4 ... 2>&1 | tee debug.log

# Inspeccionar streams
ffprobe -show_streams -print_format json input.mp4 | python -m json.tool

# Ver subtítulos exactos en SRT
cat temp/test_subtitles.srt

# Limpiar archivos temporales
rm -rf temp/temp_*.mp4 temp/test_*.mp4
```

---

## Notas Importantes

1. **NO hagas cambios a código** hasta que confirmes la causa raíz
2. **Documenta todos los hallazgos** - Esto será información crítica
3. **El diagnóstico es más importante que la velocidad** - Mejor lento y preciso
4. **Si encuentras algo inesperado** - Nota en la documentación

---

## ¿Listo para empezar?

```bash
python tests/diagnose_subtitle_duplication.py
```

Ejecuta esto y reporta los hallazgos. Basado en lo que encuentres, decidiremos el siguiente paso.

