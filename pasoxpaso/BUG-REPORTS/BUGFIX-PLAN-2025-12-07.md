# Plan de Investigación y Resolución: Bug de Subtítulos Duplicados
**Fecha:** 2025-12-07
**Status:** Nuevo plan de investigación
**Prioridad:** ALTA - Bloquea PASO4 (Branding)

---

## Resumen Ejecutivo

El bug de subtítulos duplicados persiste a pesar del intento con `-sn` flag. El documento anterior indicaba que la hipótesis sobre "preservación de metadata de subtítulos" era **incorrecta**. Necesitamos una investigación más profunda para identificar la verdadera raíz del problema.

**Hipótesis Actual:** El problema NO es metadata preservation, sino algo más profundo en cómo FFmpeg procesa subtítulos entre pasos de re-encoding.

---

## Fase 1: Diagnóstico Profundo

### 1.1 - Investigación con FFProbe

**Objetivo:** Entender exactamente qué está pasando en cada paso FFmpeg

**Tareas:**
- [ ] Crear test video con subtítulos originales
- [ ] Ejecutar Step 1 (logo overlay) con `-sn` flag
- [ ] Ejecutar `ffprobe` en temp.mp4 para inspecionar streams exactos
- [ ] Ejecutar `ffprobe` en el output final
- [ ] Documentar diferencias de metadata y timing

**Comandos de diagnóstico:**
```bash
# Inspeccionar streams completos
ffprobe -show_streams output.mp4

# Ver timing exacto de cada subtitle
ffprobe -show_entries stream=codec_type,duration,time_base output.mp4
```

**Esperado:** Revelar si hay streams ocultos o metadata preserve que `-sn` no limpió.

---

### 1.2 - Inspección Manual del SRT vs Timing

**Objetivo:** Verificar si el problema es de timing o de renderizado múltiple

**Tareas:**
- [ ] Generar SRT con timestamps precisos desde transcripción
- [ ] Reproducir video manualmente y medir:
  - Tiempo de aparición de subtítulos duplicados
  - ¿Aparecen ambos al mismo tiempo o con offset?
  - ¿El texto es idéntico o diferente?
  - ¿Uno se superpone al otro o son lado a lado?

**Por qué importa:**
- Si offset: Problema de synchronization/timing
- Si idéntico y superpuesto: Posible renderizado doble del mismo SRT
- Si diferente: Quizás hay múltiples fuentes de subtítulos

---

### 1.3 - Prueba con FFmpeg Filters Alternativos

**Objetivo:** Confirmar si el problema está en `-vf subtitles` filter

**Variaciones a probar:**
```bash
# Opción A: Usar ass (Advanced SubStation Alpha) directamente
ffmpeg -i temp.mp4 -vf "ass='subtitles.srt'" output.mp4

# Opción B: Usar subtitles filter con force_style
ffmpeg -i temp.mp4 -vf "subtitles='subtitles.srt':force_style='...'" output.mp4

# Opción C: Usar libass con stream copy
ffmpeg -i temp.mp4 -filter_complex "[0:v]subtitles='subtitles.srt'[out]" \
  -map "[out]" -map 0:a -c:v libx264 -c:a copy output.mp4
```

**Esperado:** Detectar si alguna variante evita la duplicación.

---

## Fase 2: Investigación de Causas Raíz Alternativas

### 2.1 - Hypothesis A: FFmpeg Buffering/Cache Issue

**Planteamiento:** FFmpeg mantiene estado entre pasos que causa renderizado doble

**Prueba:**
- [ ] Ejecutar Step 2 con diferentes niveles de verbosidad FFmpeg
- [ ] Buscar en stderr mensajes de "duplicate", "conflict", o "overlapping"
- [ ] Investigar si hay opciones de cache clearing (e.g., `-fflush_packets`, `-max_muxing_queue_size`)

**Si es verdad:**
```bash
ffmpeg -i temp.mp4 -vf subtitles='...' \
  -max_muxing_queue_size 9999 \  # Force flush
  -fflush_packets 1 \             # Explicit flushing
  output.mp4
```

---

### 2.2 - Hypothesis B: Frame Timing Desynchronization

**Planteamiento:** La duración o timestamps del video re-encoded en Step 1 no coinciden con el SRT timing

**Prueba:**
- [ ] Comparar duración de video original vs temp.mp4
- [ ] Comparar duración vs SRT duration
- [ ] Verificar si FFmpeg ajustó timebase durante re-encoding
- [ ] Inspeccionar con `ffprobe -show_format`

**Si es verdad:**
- Necesitamos usar `-c:v copy` en Step 1 (mantener codec original)
- O regenerar el SRT con timing ajustado

---

### 2.3 - Hypothesis C: FFmpeg Version-Specific Bug

**Planteamiento:** Versión de FFmpeg en sistema tiene bug conocido con subtítulos

**Prueba:**
- [ ] Verificar versión exacta de FFmpeg: `ffmpeg -version`
- [ ] Buscar en FFmpeg bug tracker por "duplicate subtitles"
- [ ] Probar con versión diferente de FFmpeg si disponible

**Referencia:** FFmpeg subtitle filter es notoriamente problemático (documentado en el BUGFIX anterior)

---

## Fase 3: Soluciones Alternativas

Si el diagnóstico confirma que el problema NO es metadata preservation, estas son las opciones viables:

### 3.1 - Opción A: Tres-Step Process (Aislamiento Máximo)

**Arquitectura:**
```
Step 1: Logo overlay (sin subtítulos, sin re-encoding si posible)
  Input:  original.mp4
  Output: temp_with_logo.mp4

Step 2: Re-encode limpio (solo codec, sin filtros)
  Input:  temp_with_logo.mp4
  Output: temp_clean.mp4

Step 3: Subtítulos en video completamente limpio
  Input:  temp_clean.mp4
  Output: final.mp4
```

**Ventajas:**
- Máximo aislamiento entre operaciones
- Cada paso tiene responsabilidad clara
- Fácil de debuggear

**Desventajas:**
- 3 pasadas FFmpeg = 3x lento
- Más archivos temporales

**Viabilidad:** MEDIA - Solo si hipótesis de caching es verdadera

---

### 3.2 - Opción B: Subtítulos con OpenCV (Python)

**Arquitectura:**
```
FFmpeg: Logo + aspect ratio conversion
  Output: temp.mp4

Python/OpenCV:
  - Lee frame por frame
  - Calcula posición de subtítulos basado en SRT timing
  - Dibuja texto con PIL o cv2.putText
  - Escribe video final
```

**Ventajas:**
- Control total sobre renderizado de subtítulos
- Evita FFmpeg subtitle filter completamente
- Determinístico (no depende de FFmpeg internals)

**Desventajas:**
- MUCHO más lento (procesamiento frame-by-frame en Python)
- Requiere dependencias nuevas (PIL, OpenCV avanzado)
- Complejidad de código aumenta

**Viabilidad:** BAJA - No es práctica para clips de duración variable

---

### 3.3 - Opción C: Usar FFmpeg Concat (Demuxer Approach)

**Idea:** En lugar de `-vf subtitles`, usar demuxer para "inyectar" subtítulos como stream

**Arquitectura:**
```bash
ffmpeg -i temp_with_logo.mp4 -i subtitles.srt \
  -c:v copy -c:a copy \
  -c:s srt \  # Copy subtitle codec
  output.mp4
```

**Ventajas:**
- No usa filter complex (evita FFmpeg filter bugs)
- Muy rápido (solo copia de streams)

**Desventajas:**
- Subtítulos no se "queman" (burn-in) - se empotra como stream
- El usuario tiene que seleccionar subtítulos en el player
- No cumple requisito de CLIPER de quemar subtítulos

**Viabilidad:** BAJA - No cumple el objetivo de quemar subtítulos

---

### 3.4 - Opción D: Single-Pass Consolidation (Arquitectura Completa)

**Idea:** Si es posible, hacer todo en UN solo comando FFmpeg

**Arquitectura:**
```bash
ffmpeg -i video.mp4 -i logo.png \
  -filter_complex "[0:v]scale=...;[...]overlay=...;[...]subtitles='...'[out]" \
  -map "[out]" -map 0:a \
  output.mp4
```

**Ventajas:**
- UN paso = UN pasada FFmpeg
- Sin archivos intermedios
- Sin problema de synchronization entre pasos

**Desventajas:**
- Filter complex MUCHO más complicado
- Si uno falla, todo falla
- FFmpeg subtitle filter sigue siendo problemático

**Viabilidad:** MEDIA - Solo si subtítulos en filter_complex evita el bug

---

## Fase 4: Plan de Ejecución Secuencial

### Sprint 1: Diagnóstico (Hoy)

**Tarea 1.1:** Crear test video minimal
```python
# tests/test_subtitle_diagnosis.py
- Video: 10 segundos
- Subtítulos: 3-5 líneas espaciadas
- Logo: assets/logo.png
- Ejecutar export_clips con add_logo=True, add_subtitles=True
```

**Tarea 1.2:** Ejecutar FFprobe inspection
```bash
# Antes Step 2
ffprobe -show_streams temp_*.mp4 | grep -E "codec_type|duration"

# Después Step 2
ffprobe -show_streams output_*.mp4 | grep -E "codec_type|duration"
```

**Tarea 1.3:** Inspeccionar manually con VLC/QuickTime
- Observar si subtítulos duplicados aparecen
- Documentar timing exacto
- Screenshot de duplicación si es posible

### Sprint 2: Diagnosis Profundo (Si necesario)

**Tarea 2.1:** Ejecutar FFmpeg con verbose output
```bash
ffmpeg -loglevel debug -i temp.mp4 -vf "subtitles='...'" output.mp4 2>&1 | tee ffmpeg_debug.log
```

**Tarea 2.2:** Analizar logs por:
- Mensajes de "subtitle"
- Menciones de "codec" o "stream"
- Warnings o errors

### Sprint 3: Implementación de Fix (Basado en Diagnóstico)

**Opción 1:** Si es problema de codec/timing
- Cambiar a `-c:v copy` en Step 1
- Implementar timing adjustment en SRT generation

**Opción 2:** Si es problema de filter
- Implementar Three-Step Process
- Agregar delay o flushing entre pasos

**Opción 3:** Si es problema de FFmpeg versión
- Documentar workaround para versión actual
- Actualizar FFmpeg requirements

---

## Criterios de Éxito

✅ **CUANDO LO CONSIDERAMOS RESUELTO:**
1. Export clip con logo + subtítulos
2. Reproducir en VLC/QuickTime/Player browser
3. Subtítulos aparecen **UNA SOLA VEZ** (no duplicados)
4. Timing correcto
5. Test cases pasen (automated + manual verification)

❌ **FALLO:**
- Subtítulos aún duplicados después de fix
- Performance degradation > 20% vs antes
- Require cambios al API público de export_clips

---

## Documentación de Hipótesis a Validar

### H1: FFmpeg Metadata Preservation (Ya probada - FALSA)
- Status: ❌ DESCARTADA
- Evidence: `-sn` flag no resolvió el problema
- Conclusión: No es metadata preservation

### H2: FFmpeg Buffer/Cache State
- Status: ⏳ PENDIENTE
- Test method: Verbose output inspection + FFmpeg options
- Riesgo: Media

### H3: Frame Timing Desynchronization
- Status: ⏳ PENDIENTE
- Test method: ffprobe duration comparison + timing analysis
- Riesgo: Media

### H4: FFmpeg Version Bug
- Status: ⏳ PENDIENTE
- Test method: Version check + bug tracker research
- Riesgo: Baja (problema conocido documentado)

### H5: Subtítulos Filter Internals
- Status: ⏳ PENDIENTE
- Test method: Alternativas filter + single-pass approach
- Riesgo: Alta (complejidad de implementación)

---

## Próximos Pasos Inmediatos

1. **Hoy:** Ejecutar Sprint 1 (Diagnóstico básico)
2. **Aprobación del usuario:** Confirmar dirección basada en hallazgos
3. **Después:** Ejecutar Sprint 2 si diagnóstico no es conclusivo
4. **Implementación:** Basada en causa raíz identificada

---

## Referencias y Contexto

- **Bug report original:** pasoxpaso/BUGFIX-subtitle-duplication.md
- **Código actual:** src/video_exporter.py (lines 250-320)
- **Test suite:** tests/test_logo_subtitles_regression.py (si existe)
- **FFmpeg docs:** https://ffmpeg.org/ffmpeg-filters.html#subtitles-1

---

## Notas Arquitectónicas

**IMPORTANTE:** Cualquier solución debe mantener:
1. **Modularidad:** La responsabilidad de cada módulo debe ser clara
2. **Performance:** No degradar más de 20% vs versión sin logo/subtítulos
3. **User API:** El signature de `export_clips()` debe permanecer compatible
4. **Robustez:** Graceful degradation si subtítulos fallan

**Principio:** Si Step 2 falla, debemos entregar el output de Step 1 (con logo, sin subtítulos) en lugar de error completo.

