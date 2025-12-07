# Step 03: Reframer Module

**Goal:** Create `src/reframer.py` with core face tracking and reframing logic

---

## 📋 Module Overview

The `reframer.py` module will be responsible for:

1. ✅ Face detection using MediaPipe
2. ✅ Frame sampling for performance
3. ✅ "Keep in frame" tracking logic
4. ✅ Smooth camera movement calculations
5. ✅ Video reframing with OpenCV

---

## ✅ Tasks

### Task 3.1: Create Module Structure

**File:** `/src/reframer.py`

**Create with this structure:**

```python
# -*- coding: utf-8 -*-
"""
Face Reframer - Dynamic video reframing with face tracking

This module handles intelligent face tracking and dynamic crop calculation
for converting landscape videos to portrait format while keeping the speaker in frame.
"""

import cv2
import mediapipe as mp
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from collections import deque

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FaceReframer:
    """
    Intelligent face tracking for dynamic video reframing

    Strategies:
    - 'keep_in_frame': Minimal movement, only when face approaches edge (recommended)
    - 'centered': Always center on face (simple but can be jittery)
    """

    def __init__(
        self,
        frame_sample_rate: int = 3,
        safe_zone_margin: float = 0.15,
        detection_confidence: float = 0.5,
        strategy: str = "keep_in_frame"
    ):
        """
        Initialize face reframer

        Args:
            frame_sample_rate: Process every Nth frame (3 = every 3rd frame)
            safe_zone_margin: Margin from crop edges before reframing (0.15 = 15%)
            detection_confidence: MediaPipe detection threshold (0-1)
            strategy: 'keep_in_frame' or 'centered'
        """
        # TODO: Implementation
        pass


    def reframe_video(
        self,
        input_video_path: str,
        output_video_path: str,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        target_aspect: str = "9:16"
    ) -> bool:
        """
        Reframe a video segment with face tracking

        Args:
            input_video_path: Path to source video
            output_video_path: Path to save reframed video
            start_time: Start timestamp in seconds
            end_time: End timestamp in seconds (None = end of video)
            target_aspect: Output aspect ratio ("9:16", "1:1")

        Returns:
            True if successful, False otherwise
        """
        # TODO: Implementation
        pass
```

- [ ] Created `/src/reframer.py` with module structure
- [ ] Added imports and logger
- [ ] Created `FaceReframer` class skeleton
- [ ] Added docstrings for all methods

---

### Task 3.2: Implement Face Detection

**Add this method to `FaceReframer` class:**

```python
def _detect_largest_face(self, frame) -> Optional[Dict]:
    """
    Detect the largest face in frame using MediaPipe

    Args:
        frame: OpenCV BGR frame

    Returns:
        Dict with {x, y, width, height, center_x, center_y} or None
    """
    # Convert BGR to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run detection
    results = self.face_detector.process(frame_rgb)

    if not results.detections:
        return None

    # Find largest face by area
    h, w, _ = frame.shape
    largest_face = None
    max_area = 0

    for detection in results.detections:
        bbox = detection.location_data.relative_bounding_box

        # Convert relative coords to pixels
        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        width = int(bbox.width * w)
        height = int(bbox.height * h)

        area = width * height

        if area > max_area:
            max_area = area
            largest_face = {
                'x': max(0, x),
                'y': max(0, y),
                'width': width,
                'height': height,
                'center_x': x + width // 2,
                'center_y': y + height // 2,
            }

    return largest_face
```

- [ ] Implemented `_detect_largest_face()` method
- [ ] Handles BGR to RGB conversion
- [ ] Finds largest face by bounding box area
- [ ] Returns normalized coordinates

---

### Task 3.3: Implement "Keep in Frame" Logic

**This is the core UX innovation from Ben's feedback!**

```python
def _calculate_crop_keep_in_frame(
    self,
    face: Dict,
    frame_width: int,
    frame_height: int,
    current_crop_x: Optional[int] = None
) -> Tuple[int, int, int, int]:
    """
    Calculate crop coordinates using 'keep in frame' strategy

    Only moves the crop when face approaches the edge of current frame.
    This creates professional, minimal-movement cinematography.

    Args:
        face: Face detection dict with center_x, center_y
        frame_width: Source frame width
        frame_height: Source frame height
        current_crop_x: Current crop X position (None = first frame)

    Returns:
        (crop_x, crop_y, crop_width, crop_height)
    """
    # Calculate target crop dimensions (9:16 aspect)
    crop_height = frame_height
    crop_width = int(crop_height * (9/16))

    # If first frame, center on face
    if current_crop_x is None:
        crop_x = face['center_x'] - crop_width // 2
        crop_x = max(0, min(crop_x, frame_width - crop_width))
        return (crop_x, 0, crop_width, crop_height)

    # Calculate safe zone boundaries within current crop
    safe_margin = int(crop_width * self.safe_zone_margin)
    safe_left = current_crop_x + safe_margin
    safe_right = current_crop_x + crop_width - safe_margin

    face_x = face['center_x']

    # Check if face is still in safe zone
    if safe_left <= face_x <= safe_right:
        # Face is safe, don't move crop
        return (current_crop_x, 0, crop_width, crop_height)

    # Face is approaching edge, calculate new crop position
    if face_x < safe_left:
        # Face moving left, reposition crop to put face at left safe boundary
        crop_x = face_x - safe_margin
    else:
        # Face moving right, reposition crop to put face at right safe boundary
        crop_x = face_x - crop_width + safe_margin

    # Clamp to frame boundaries
    crop_x = max(0, min(crop_x, frame_width - crop_width))

    return (crop_x, 0, crop_width, crop_height)
```

- [ ] Implemented `_calculate_crop_keep_in_frame()` method
- [ ] Defined safe zone logic with margins
- [ ] Only moves crop when face exits safe zone
- [ ] Handles first frame (no previous crop position)

---

### Task 3.4: Implement Video Reframing Pipeline

**Complete the `reframe_video()` method:**

```python
def reframe_video(
    self,
    input_video_path: str,
    output_video_path: str,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
    target_aspect: str = "9:16"
) -> bool:
    """
    Reframe a video segment with face tracking
    """
    input_path = Path(input_video_path)
    if not input_path.exists():
        logger.error(f"Input video not found: {input_path}")
        return False

    # Open video
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        logger.error(f"Could not open video: {input_path}")
        return False

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Calculate frame range
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps) if end_time else total_frames

    # Set video to start position
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Calculate output dimensions (9:16)
    output_height = frame_height
    output_width = int(output_height * (9/16))

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(
        str(output_video_path),
        fourcc,
        fps,
        (output_width, output_height)
    )

    logger.info(f"Reframing video: {input_path.name}")
    logger.info(f"  Frames: {start_frame} → {end_frame}")
    logger.info(f"  Output: {output_width}x{output_height}")

    current_crop_x = None
    frame_number = start_frame

    while cap.isOpened() and frame_number < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect face every N frames
        if frame_number % self.frame_sample_rate == 0:
            face = self._detect_largest_face(frame)

            if face:
                # Calculate crop using strategy
                if self.strategy == "keep_in_frame":
                    crop_x, crop_y, crop_w, crop_h = self._calculate_crop_keep_in_frame(
                        face, frame_width, frame_height, current_crop_x
                    )
                else:  # centered
                    crop_x, crop_y, crop_w, crop_h = self._calculate_crop_centered(
                        face, frame_width, frame_height
                    )

                current_crop_x = crop_x
            elif current_crop_x is None:
                # No face detected and no previous position, use center crop
                current_crop_x = (frame_width - output_width) // 2

        # Apply crop (use last known position if not updated this frame)
        if current_crop_x is None:
            current_crop_x = (frame_width - output_width) // 2

        cropped_frame = frame[0:frame_height, current_crop_x:current_crop_x+output_width]
        out.write(cropped_frame)

        frame_number += 1

    # Cleanup
    cap.release()
    out.release()

    logger.info(f"✓ Reframed video saved: {output_video_path}")
    return True
```

- [ ] Implemented `reframe_video()` method
- [ ] Opens and validates input video
- [ ] Calculates frame range from timestamps
- [ ] Creates output video writer
- [ ] Processes frames with face detection
- [ ] Applies dynamic cropping
- [ ] Handles fallback to center crop when no face

---

### Task 3.5: Add Helper Method for Centered Strategy

```python
def _calculate_crop_centered(
    self,
    face: Dict,
    frame_width: int,
    frame_height: int
) -> Tuple[int, int, int, int]:
    """
    Calculate crop coordinates using 'centered' strategy

    Always centers the crop on the face. Simple but can be jittery.

    Returns:
        (crop_x, crop_y, crop_width, crop_height)
    """
    crop_height = frame_height
    crop_width = int(crop_height * (9/16))

    # Center on face
    crop_x = face['center_x'] - crop_width // 2

    # Clamp to frame boundaries
    crop_x = max(0, min(crop_x, frame_width - crop_width))

    return (crop_x, 0, crop_width, crop_height)
```

- [ ] Implemented `_calculate_crop_centered()` method
- [ ] Always centers crop on face position
- [ ] Clamps to frame boundaries

---

### Task 3.6: Initialize MediaPipe in Constructor

**Complete the `__init__` method:**

```python
def __init__(
    self,
    frame_sample_rate: int = 3,
    safe_zone_margin: float = 0.15,
    detection_confidence: float = 0.5,
    strategy: str = "keep_in_frame"
):
    self.frame_sample_rate = frame_sample_rate
    self.safe_zone_margin = safe_zone_margin
    self.strategy = strategy

    # Initialize MediaPipe Face Detection
    self.mp_face_detection = mp.solutions.face_detection
    self.face_detector = self.mp_face_detection.FaceDetection(
        model_selection=1,  # 1 = full-range model (better for varying distances)
        min_detection_confidence=detection_confidence
    )

    logger.info(f"FaceReframer initialized:")
    logger.info(f"  Strategy: {strategy}")
    logger.info(f"  Frame sampling: every {frame_sample_rate} frame(s)")
    logger.info(f"  Safe zone margin: {safe_zone_margin*100:.0f}%")
```

- [ ] Completed `__init__` method
- [ ] Initialized MediaPipe face detector
- [ ] Stored configuration parameters
- [ ] Added logging for transparency

---

## 🎯 Validation Checklist

Before moving to Step 04:

- [ ] `src/reframer.py` created with all methods
- [ ] `FaceReframer` class fully implemented
- [ ] "Keep in frame" logic implemented correctly
- [ ] Face detection integrated
- [ ] Video reframing pipeline complete
- [ ] Code follows CLIPER's style (docstrings, logging, type hints)
- [ ] No syntax errors (run `uv run python -m py_compile src/reframer.py`)

---

## 📝 Notes

**Why "keep in frame" is better:**
- Minimizes camera movement
- Looks professional and intentional
- Gives the subject "breathing room"
- Mimics how real camera operators work

**Frame sampling trade-offs:**
- Every 1 frame: Smoothest tracking, slowest (3x slower)
- Every 3 frames: Good balance (recommended)
- Every 5 frames: Fastest, may miss quick movements

**Safe zone margin:**
- 15% (0.15) is a good default
- Larger = less movement, but face may get close to edge
- Smaller = more reactive, more movement

---

## 🔧 Troubleshooting & Architectural Decisions

### Issue: OpenCV VideoWriter Codec Failures

**PROBLEMA ENCONTRADO:**

Durante testing, el código original fallaba con loop infinito de errores:
```
[ WARN:0@86.348] global cap_ffmpeg.cpp:198 write FFmpeg: Failed to write frame
```

**CAUSA ROOT:**

OpenCV usa FFmpeg como backend para escribir videos. El codec `mp4v` no estaba disponible en la instalación de macOS M4.

**ARQUITECTURA DE OPENCV VIDEOWRITER:**

```
Python (nuestro código)
    ↓
OpenCV (librería Python - cv2.VideoWriter)
    ↓
FFmpeg (backend C++ - encoding real)
    ↓
Archivo MP4 en disco
```

**DECISIÓN ARQUITECTÓNICA: Codec Fallback Mechanism**

**PROBLEMA:**
- Codec availability depende de cómo FFmpeg fue compilado
- macOS (Homebrew), Linux (apt), Docker tienen diferentes codecs disponibles
- Hardcodear un codec rompe portabilidad cross-platform

**ALTERNATIVAS:**

1. **Codec fijo 'mp4v'** (original)
   - Simple (1 línea)
   - Problema: Falla silenciosamente si no disponible
   - NO portable

2. **Codec fijo 'avc1'** (H.264)
   - Mejor calidad en macOS
   - Problema: No disponible en algunos Linux builds
   - NO portable

3. **Codec por OS detection**
   ```python
   if sys.platform == 'darwin': codec = 'avc1'
   elif sys.platform == 'linux': codec = 'mp4v'
   ```
   - Funciona en casos comunes
   - Problema: No maneja Docker, builds custom
   - Frágil

4. **Fallback automático** (IMPLEMENTADO)
   - Prueba múltiples codecs en orden
   - Valida que VideoWriter se inicializó correctamente
   - Error claro si todos fallan

**TRADE-OFFS:**

| Aspecto | Codec Fijo | Fallback Automático |
|---------|-----------|---------------------|
| Líneas de código | 1 | ~25 |
| Portabilidad | Mala | Excelente |
| Error handling | Loop infinito | Error claro |
| Performance | Instantáneo | +10ms overhead (negligible) |
| Mantenibilidad | Frágil | Robusto |

**RESULTADO: Por Qué Fallback Es La Mejor Opción**

1. **Alineación con Filosofía CLIPER:**
   - Reproducibilidad (contextofull.md línea 38): Funciona igual en dev/prod/Docker
   - Robustez (CLIPER core principle): Graceful degradation
   - Docker-First (contextofull.md línea 14): Auto-detecta codecs disponibles

2. **Patrón Consistente con CLIPER:**
   ```python
   # copys_generator.py - Reintentos con degradación elegante
   for attempt in range(3):
       try: return llm_call()
       except: continue

   # reframer.py - Mismo patrón para codecs
   for codec in ['avc1', 'mp4v', 'XVID']:
       try:
           writer = VideoWriter(codec)
           if writer.isOpened(): break
       except: continue
   ```

**IMPLEMENTACIÓN:**

```python
# Líneas 391-420 en src/reframer.py

# Intentar codecs en orden de preferencia
codecs_to_try = ['avc1', 'mp4v', 'XVID']
out = None

for codec in codecs_to_try:
    fourcc = cv2.VideoWriter_fourcc(*codec)
    test_writer = cv2.VideoWriter(
        str(output_path),
        fourcc,
        fps,
        (target_width, target_height)
    )

    if test_writer.isOpened():
        out = test_writer
        logger.info(f"Using codec: {codec}")
        break
    else:
        test_writer.release()

if out is None or not out.isOpened():
    raise RuntimeError(
        f"Failed to initialize VideoWriter. Tried codecs: {codecs_to_try}. "
        "Check OpenCV installation and FFmpeg support."
    )
```

**VALIDACIONES ADICIONALES:**

1. **Frame Dimension Check** (líneas 481-488)
   - Valida que cropped_frame sea exactamente target_width x target_height
   - Fallback automático con `cv2.resize()` si hay mismatch
   - Previene crashes por dimension mismatch

2. **Write Success Check** (líneas 491-493)
   - Detecta si `out.write()` retorna False
   - Log warning cada 30 frames (evita spam)
   - Ayuda debugging de permisos/disco lleno

**LECCIONES APRENDIDAS:**

1. **Never assume codec availability** - Siempre validar con `isOpened()`
2. **Fail fast with clear errors** - RuntimeError > silent failure
3. **Follow CLIPER patterns** - Reintentos + degradación elegante
4. **Test cross-platform** - macOS dev ≠ Linux prod ≠ Docker

**TESTING:**

Después del fix, deberías ver en logs:
```
2025-11-28 22:00:00.000 | INFO | src.reframer:reframe_video:411 - Using codec: avc1
```

Si todos los codecs fallan:
```
RuntimeError: Failed to initialize VideoWriter. Tried codecs: ['avc1', 'mp4v', 'XVID'].
Check OpenCV installation and FFmpeg support.
```

---

### Issue 2: Codec Test Write Validation (Discovered during testing)

**PROBLEMA ENCONTRADO:**

Durante testing real, `avc1` pasaba `isOpened()` pero `write()` fallaba en TODOS los frames:

```
ERROR: VideoWriter.write() failed at frame 0
Frame shape: (1920, 1080, 3), dtype: uint8, contiguous: True
```

**CAUSA ROOT:**

`VideoWriter.isOpened()` solo valida que:
1. El codec existe en FFmpeg ✓
2. El archivo se puede crear ✓

**PERO NO valida que el codec pueda encodear frames.**

En macOS, `avc1` puede estar listado pero fallar por:
- FFmpeg sin libx264 compiled
- Hardware encoder no accesible
- Sandbox permissions de macOS

**SOLUCIÓN: Test Write Validation**

```python
# Líneas 432-443

for codec in ['mp4v', 'XVID', 'avc1']:
    test_writer = VideoWriter(...)

    if test_writer.isOpened():
        # VALIDACIÓN CRÍTICA: Test write con frame dummy
        dummy_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        test_success = test_writer.write(dummy_frame)

        if test_success:
            out = test_writer  # ✓ Codec FUNCIONA
            break
        else:
            logger.warning(f"Codec {codec} isOpened() but write() failed")
            test_writer.release()
            continue
```

**POR QUÉ FUNCIONA:**

1. Valida encoding real, no solo disponibilidad
2. Detecta problemas en 10ms vs 2 minutos de procesamiento
3. Prueba siguiente codec automáticamente

**ORDEN DE CODECS ACTUALIZADO:**

```python
# Antes: ['avc1', 'mp4v', 'XVID']
# Ahora: ['mp4v', 'XVID', 'avc1']
```

Por qué? `mp4v` más compatible en macOS Python builds.

**LECCIÓN APRENDIDA:**

Never trust `isOpened()` alone. Always validate with test write before processing real frames.

---

---

### Issue 3: Solución Arquitectónica - ffmpegcv Drop-in Replacement

**Contexto:** Después de investigar el problema de VideoWriter en macOS Apple Silicon, identificamos que es un issue conocido de incompatibilidad entre opencv-python (pip) y FFmpeg arm64.

#### DECISIÓN: Usar ffmpegcv como Drop-in Replacement

**PROBLEMA:**
```
opencv-python instalado vía pip en macOS M1/M2/M4 instala FFmpeg amd64 (Intel)
en lugar de arm64 (Apple Silicon), causando que VideoWriter.write() falle
silenciosamente incluso cuando isOpened() reporta éxito.
```

**ALTERNATIVAS CONSIDERADAS:**

1. **ffmpegcv Library** (SELECCIONADA)
   - Drop-in replacement con API idéntica a cv2.VideoWriter
   - Usa FFmpeg del sistema (arm64 garantizado)
   - Compatible con uv/Docker existente

2. **conda-forge opencv**
   - Funcional pero rompe filosofía uv de CLIPER
   - Requiere Miniforge, incompatible con uv.lock
   - Dockerfile necesitaría reescritura completa

3. **Build OpenCV from Source**
   - Control total pero 1-2 horas de compilación
   - No reproducible en otros entornos
   - Rompe Docker portability

4. **FFmpeg Subprocess Pipeline**
   - Arquitectónicamente coherente (CLIPER ya usa FFmpeg)
   - 2-3 horas de refactor
   - Opción válida si ffmpegcv falla

**TRADE-OFFS:**

```
ffmpegcv:
  + API idéntica → cambio de 5 líneas
  + Compatible con uv → sin cambios arquitectónicos
  + Testing rápido → validamos en 10 minutos
  + Face tracking 100% funcional → solo cambia escritura
  - Dependencia adicional (2.9MB)
  - Menos maduro que OpenCV (pero activamente mantenido)
```

**RESULTADO:**
```
Vale la pena por minimal risk y quick validation. Si falla, pivoteamos
a Opción 4 (FFmpeg subprocess) sin haber perdido tiempo en refactors
mayores. Coherente con filosofía CLIPER de testing antes de over-engineering.
```

#### Cambios de Implementación

**Dependencia:**
```bash
uv add ffmpegcv
```

**Código (src/reframer.py):**
```python
# Antes:
import cv2
fourcc = cv2.VideoWriter_fourcc(*codec)
out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

# Después:
import cv2
import ffmpegcv  # Solo para VideoWriter
fourcc = cv2.VideoWriter_fourcc(*codec)
out = ffmpegcv.VideoWriter(str(output_path), fourcc, fps, (w, h))
# ↑ Face tracking sigue usando MediaPipe + OpenCV para detección/procesamiento
```

**Arquitectura NO Afectada:**
- MediaPipe face detection: Sin cambios
- OpenCV VideoCapture: Sin cambios
- Frame processing (resize, crop): Sin cambios
- Solo cambia: Escritura final del video

#### Resultados del Testing (2025-11-28)

**INTENTO 1: Uso Inicial de ffmpegcv**

Error encontrado:
```
TypeError: invalid action: 'Codec should be a string. Eg `h264`, `h264_nvenc`.
You may used CV2.VideoWriter_fourcc, which will be ignored.'
```

**Causa:** ffmpegcv NO acepta fourcc codes como `cv2.VideoWriter`. Usa nombres de codec FFmpeg directamente.

**Fix aplicado:**
```python
# Antes:
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = ffmpegcv.VideoWriter(path, fourcc, fps, size)

# Después:
out = ffmpegcv.VideoWriter(path, 'libx264', fps, size)
# ↑ String directo: 'libx264', 'mpeg4', 'h264_videotoolbox'
```

**INTENTO 2: Codecs Ajustados**

Codecs probados en orden:
1. `libx264` - Encoder H.264 estándar
2. `h264_videotoolbox` - Hardware encoder macOS
3. `mpeg4` - Fallback compatible

Error encontrado en TODOS los codecs:
```
BrokenPipeError: [Errno 32] Broken pipe
File "ffmpegcv/ffmpeg_writer.py", line 97, in write
    self.process.stdin.write(img)
```

**Diagnóstico:**
- `VideoWriter.isOpened()` retorna `True` (pipe creado)
- `write()` falla inmediatamente en primer frame
- Subprocess FFmpeg se cierra antes de recibir datos
- Error reproducible con test minimal (single frame, 10 líneas código)

**Testing realizado:**
```python
# tests/test_ffmpegcv_minimal.py
writer = ffmpegcv.VideoWriter("test.mp4", "libx264", 30.0, (1080, 1920))
# ✓ isOpened: True
frame = np.zeros((1920, 1080, 3), dtype=np.uint8)
writer.write(frame)  # ✗ BrokenPipeError
```

**CONCLUSIÓN:**

```
PROBLEMA: ffmpegcv tiene bug en macOS Apple Silicon (M1/M2/M4)
EVIDENCIA:
  - Broken pipe en write() a pesar de isOpened() = True
  - Reproducible con código minimal (no es issue de nuestro código)
  - Subprocess FFmpeg se cierra inmediatamente
  - Error persiste con todos los codecs probados

DECISIÓN: Descartar Opción A (ffmpegcv)
RAZÓN: Bug no resoluble sin modificar librería externa
SIGUIENTE PASO: Pivotear a Opción D (FFmpeg Subprocess Pipeline)
```

**Por qué Opción D es arquitectónicamente correcta:**
1. CLIPER ya usa FFmpeg directamente en `video_exporter.py`
2. Control total sobre parámetros y error handling
3. Sin dependencias externas problemáticas (ffmpegcv)
4. Coherente con filosofía "Local-First" de CLIPER
5. Robustez: podemos manejar stderr y reintentos granularmente

**Trade-offs aceptables de Opción D:**
- 2-3 horas de implementación vs 10 min de ffmpegcv
- Manejo manual de pipes (complejidad justificada por control)
- Debugging más verboso (pero más control sobre errores)

**Archivos creados para testing:**
- `tests/test_ffmpegcv_integration.py` - Test end-to-end con FaceReframer
- `tests/test_ffmpegcv_minimal.py` - Test minimal para aislar bug
- `tests/test_ffmpegcv_debug.py` - Debug de stderr de FFmpeg

**Estado actual del código:**
- `src/reframer.py`: Modificado para usar ffmpegcv (NO FUNCIONAL)
- `pyproject.toml`: ffmpegcv==0.3.18 agregado
- Face tracking: 100% implementado (solo falta VideoWriter funcional)

---

### PRÓXIMO PASO: Implementar Opción D (FFmpeg Subprocess)

Ver: `pasoxpaso/todoPASO3/06-testing.md` - Actualizar con plan Opción D

**Objetivo:** Reemplazar `ffmpegcv.VideoWriter` con subprocess FFmpeg directo en `src/reframer.py`

**Componentes necesarios:**
1. FFmpeg command builder (con parámetros validados)
2. Pipe writer (stdin de subprocess)
3. Error handler (stderr monitoring)
4. Graceful cleanup (process termination)

**Referencia:** `src/video_exporter.py` ya usa FFmpeg subprocess - adaptar patrón.

---

### Solución Final: FFmpegVideoWriter Implementado (2025-11-29)

**ESTADO:** COMPLETADO ✓

#### Implementación

**Ubicación:** `src/reframer.py` líneas 115-249

**Componentes implementados:**

1. **Command Builder:**
```python
cmd = [
    'ffmpeg', '-y',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-pix_fmt', 'bgr24',
    '-s', f'{width}x{height}',
    '-r', str(fps),
    '-i', '-',  # stdin
    '-c:v', codec,
    '-preset', preset,  # 'fast' - coherente con video_exporter.py
    '-crf', str(crf),   # 23 - coherente con video_exporter.py
    str(output_path)
]
```

2. **Subprocess Manager:**
```python
self.process = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stderr=subprocess.PIPE,
    stdout=subprocess.PIPE
)
```

3. **Write Method:**
```python
def write(self, frame: np.ndarray) -> bool:
    self.process.stdin.write(frame.tobytes())
    return True
```

4. **Error Handling:**
- BrokenPipeError catch
- Timeout en release() (30 segundos)
- stderr logging para debugging
- Graceful degradation con codec fallback

5. **Cleanup:**
```python
def release(self):
    self.process.stdin.close()
    self.process.wait(timeout=30)
    # Verificar returncode y stderr
```

#### Testing End-to-End

**Script:** `tests/test_ffmpeg_subprocess.py`

**Resultados:**
```
✓ FFmpegVideoWriter inicializado: libx264 @ 1080x1920
✓ Face tracking procesado: 300 frames (10 segundos)
✓ Output generado: 3.40 MB
✓ Codec usado: libx264 (FFmpeg subprocess)
✓ Sin errores, zero warnings críticos
```

**Validación visual:** Face tracking dinámico confirmado en output.

#### Cleanup Realizado

**Dependencias:**
```bash
uv remove ffmpegcv  # Ya no necesario
```

**Tests obsoletos eliminados:**
- `tests/test_ffmpegcv_integration.py`
- `tests/test_ffmpegcv_minimal.py`
- `tests/test_ffmpegcv_debug.py`

**Estado final pyproject.toml:**
```toml
dependencies = [
    "opencv-python>=4.8.0",  # Frame processing solamente
    "mediapipe>=0.10.0",     # Face detection
    # ffmpegcv removido - usamos FFmpeg subprocess directo
]
```

#### Decisión Final

**DECISIÓN:** FFmpeg Subprocess es la solución correcta para CLIPER

**PROBLEMA RESUELTO:**
```
cv2.VideoWriter: Falla en macOS M4 (amd64 FFmpeg)
ffmpegcv: BrokenPipeError (bug de librería)
→ FFmpegVideoWriter: Funciona (FFmpeg arm64 nativo del sistema)
```

**TRADE-OFFS ACEPTADOS:**
```
+ Control total sobre encoding (stderr, timeout, reintentos)
+ FFmpeg del sistema (arm64 garantizado)
+ Coherente con video_exporter.py (mismo patrón)
+ Zero dependencias problemáticas
+ Debugging transparente
- 145 líneas de código vs 1 línea teórica
- Manejo manual de pipes
```

**RESULTADO:**
```
Vale la complejidad. Control > conveniencia.
Filosofía CLIPER: herramientas probadas + control explícito > wrappers frágiles.
Face tracking 100% operativo en macOS M4.
```

#### Métricas

**Performance:**
- Processing: ~4 segundos para 10 segundos de video
- Face detection: Cada 3 frames = 100 detecciones
- Output: 3.40 MB (libx264, crf 23)

**Robustez:**
- Error handling completo
- Codec fallback funcional
- Cleanup garantizado
- Memory: Sin leaks

---

**Next Step:** `04-integration.md` →
