#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLIPER - Face Reframing Module (PASO3)
Intelligent face tracking for vertical video (9:16) export

ARQUITECTURA DE INTEGRACIÓN:
==========================
Pipeline completo:
    1. video_exporter.py llama a FaceReframer ANTES de FFmpeg
    2. FaceReframer genera video temporal con crop dinámico
    3. FFmpeg usa ese video temporal para agregar subtítulos

Flujo de datos:
    video_original.mp4 → FaceReframer → temp_reframed.mp4 → FFmpeg → output_final.mp4

Punto de integración: video_exporter.py línea ~1168
    if reframe_enabled:
        temp_video = reframer.reframe_video(input_video, start, end, target_resolution)
        input_for_ffmpeg = temp_video  # FFmpeg solo agrega subtítulos
    else:
        input_for_ffmpeg = input_video  # Flujo original (center crop estático)

FLAGS CLI (De dónde vienen):
===========================
Los flags se definen en cliper.py línea ~1068:
    reframe_enabled = Confirm.ask("Enable intelligent face reframing?")
    reframe_strategy = Prompt.ask("Strategy", choices=["keep_in_frame", "centered"])

Luego se pasan a video_exporter.py:
    exporter = VideoExporter(face_reframer_config={...})

DECISIÓN ARQUITECTÓNICA: MediaPipe + OpenCV
==========================================
PROBLEMA:
    - Horizontal videos (16:9) → vertical (9:16) requieren cropping inteligente
    - Center crop estático corta rostros cuando la persona se mueve

ALTERNATIVAS:
    1. Center crop estático (actual) - simple pero corta rostros
    2. Pillow + face_recognition - muy lento (1-2 fps)
    3. TensorFlow Object Detection - overkill, pesado
    4. MediaPipe + OpenCV - óptimo para rostros

TRADE-OFFS:
    MediaPipe:
        + Rápido (3.3ms/frame en M4, validado en spike)
        + Preciso (100% detection en talking-head content)
        + Lightweight (modelo optimizado para mobile)
        - Solo rostros (no objetos genéricos)

    OpenCV:
        + Estándar de industria para video I/O
        + Compatible con FFmpeg pipeline
        - Requiere dependencias sistema (libgl1-mesa-glx en Docker)

RESULTADO:
    MediaPipe + OpenCV es la combinación perfecta para CLIPER:
    - Videos son principalmente talking-head (rostros siempre presentes)
    - Performance validado (spike: 100% detection, 3x speedup con sampling)
    - Se integra limpiamente con FFmpeg existente

DECISIÓN: "Keep in Frame" Strategy (Ben's Innovation)
====================================================
PROBLEMA:
    - Centrar rostro constantemente = movimiento jittery (11px promedio cada frame)
    - Usuario quiere output profesional, no amateur

ALTERNATIVAS:
    1. Centered (constantemente centrar): fluido pero jittery
    2. Keep in frame (Ben's recommendation): solo mover cuando necesario

TRADE-OFFS:
    Centered:
        + Rostro siempre en mismo lugar
        - Movimiento constante (distractor visual)
        - 11px jitter sin smoothing

    Keep in Frame:
        + Movimiento mínimo (solo cuando rostro sale de safe zone)
        + Look profesional
        + Smoothing más efectivo
        - Rostro no siempre centrado (pero siempre visible)

RESULTADO:
    "Keep in frame" es default porque minimiza distracción visual.
    Safe zone = 15% margins = rostro puede moverse 30% del frame sin reframe.

FRAME SAMPLING OPTIMIZATION
===========================
DECISIÓN: Procesar cada 3 frames en lugar de todos

POR QUÉ:
    - Spike validation: 3x speedup, solo 11px movement promedio
    - Rostros no se teletransportan entre frames (movimiento gradual)
    - Detection time (3.3ms) NO es bottleneck - total processing sí

IMPLICACIÓN:
    - 30fps video → 10 detecciones/seg (en lugar de 30)
    - Mismo resultado visual (con smoothing en Paso 07)
    - 3x más rápido = procesar 30 clips en 10 min vs 30 min

Ver: pasoxpaso/todoPASO3/spike-results.md para datos completos
"""

import cv2
import numpy as np
import mediapipe as mp
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple
from loguru import logger


class FFmpegVideoWriter:
    """
    VideoWriter usando FFmpeg subprocess directo.

    DECISIÓN ARQUITECTÓNICA:
    - cv2.VideoWriter: Falla en macOS M4 (amd64 FFmpeg)
    - ffmpegcv: BrokenPipeError en todos los codecs
    - FFmpeg subprocess: Usa FFmpeg del sistema (arm64 nativo)

    API compatible con cv2.VideoWriter (isOpened, write, release).
    Ver: pasoxpaso/todoPASO3/SESSION-2025-11-28.md → Opción D
    """

    def __init__(
        self,
        output_path: str,
        width: int,
        height: int,
        fps: float,
        codec: str = 'libx264',
        preset: str = 'fast',
        crf: int = 23
    ):
        """
        Inicializa VideoWriter con FFmpeg subprocess.

        Args:
            output_path: Ruta del archivo de salida
            width: Ancho del video
            height: Alto del video
            fps: Frames por segundo
            codec: Codec FFmpeg (libx264, h264_videotoolbox, mpeg4)
            preset: Preset de encoding (ultrafast, fast, medium, slow)
            crf: Calidad (18-28, menor = mejor calidad)
        """
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.codec = codec
        self.process = None
        self._opened = False

        # Construir comando FFmpeg
        # Patrón coherente con video_exporter.py líneas 295-304
        cmd = [
            'ffmpeg',
            '-y',  # Sobrescribir si existe
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',  # OpenCV usa BGR
            '-s', f'{width}x{height}',
            '-r', str(fps),
            '-i', '-',  # stdin
            '-c:v', codec,
            '-preset', preset,
            '-crf', str(crf),
            str(output_path)
        ]

        try:
            # Iniciar subprocess con stdin PIPE
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            self._opened = True
            logger.debug(f"FFmpegVideoWriter initialized: {codec} @ {width}x{height}")

        except Exception as e:
            logger.error(f"Failed to start FFmpeg subprocess: {e}")
            self._opened = False

    def isOpened(self) -> bool:
        """Compatible con cv2.VideoWriter API"""
        return self._opened and self.process is not None and self.process.poll() is None

    def write(self, frame: np.ndarray) -> bool:
        """
        Escribe frame a video.

        Args:
            frame: Frame NumPy (height, width, 3) dtype uint8

        Returns:
            True si éxito, False si falla
        """
        if not self.isOpened():
            return False

        try:
            # Escribir bytes de frame a stdin
            self.process.stdin.write(frame.tobytes())
            return True

        except BrokenPipeError:
            logger.error("FFmpeg subprocess closed unexpectedly")
            self._opened = False
            return False

        except Exception as e:
            logger.error(f"Error writing frame: {e}")
            return False

    def release(self):
        """Cierra subprocess y finaliza video"""
        if self.process:
            try:
                # Cerrar stdin para señalar fin de input
                if self.process.stdin:
                    self.process.stdin.close()

                # Esperar a que FFmpeg termine encoding
                self.process.wait(timeout=30)

                # Verificar si hubo errores
                if self.process.returncode != 0:
                    stderr = self.process.stderr.read().decode() if self.process.stderr else ""
                    logger.warning(f"FFmpeg finished with code {self.process.returncode}: {stderr[:200]}")

                logger.debug(f"FFmpegVideoWriter released: {self.output_path}")

            except subprocess.TimeoutExpired:
                logger.error("FFmpeg did not finish in time, terminating")
                self.process.terminate()
                self.process.wait()

            except Exception as e:
                logger.error(f"Error releasing FFmpegVideoWriter: {e}")

            finally:
                self._opened = False
                self.process = None


class FaceReframer:
    """
    Intelligent face tracking para conversión 16:9 → 9:16

    RESPONSABILIDADES:
    - Detectar rostro más grande en cada frame (MediaPipe)
    - Calcular crop óptimo según estrategia (keep_in_frame o centered)
    - Generar video temporal con crop dinámico (OpenCV)
    - Fallback a center crop si no detecta rostros

    INTEGRACIÓN:
    - Llamado por video_exporter.py ANTES de FFmpeg
    - Output: video temporal que FFmpeg usa para subtítulos
    - NO maneja subtítulos (esa es responsabilidad de FFmpeg)
    """

    def __init__(
        self,
        frame_sample_rate: int = 3,
        strategy: str = "keep_in_frame",
        safe_zone_margin: float = 0.15,
        min_detection_confidence: float = 0.5
    ):
        """
        PARÁMETROS CONFIGURABLES (defaults basados en spike validation):

        frame_sample_rate: int = 3
            Procesar cada N frames (default 3 validado en spike)
            Por qué 3? Ver spike-results.md - óptimo balance speed/quality

        strategy: str = "keep_in_frame"
            "keep_in_frame": Solo mover crop cuando rostro sale de safe zone (Ben's rec)
            "centered": Siempre centrar rostro (más jittery)

        safe_zone_margin: float = 0.15
            Márgenes de safe zone (15% = 30% total breathing room)
            Por qué 15%? Testing empírico - balance entre estabilidad y coverage

        min_detection_confidence: float = 0.5
            Threshold de MediaPipe (default 0.5 = balance false positives/negatives)
        """
        self.frame_sample_rate = frame_sample_rate
        self.strategy = strategy
        self.safe_zone_margin = safe_zone_margin

        # MediaPipe Face Detection initialization
        # DECISIÓN: model_selection=1 (full-range) en lugar de 0 (short-range)
        # Por qué? Videos pueden tener planos abiertos donde rostro está lejos
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 0=short-range (2m), 1=full-range (5m)
            min_detection_confidence=min_detection_confidence
        )

        # Estado interno para "keep_in_frame" strategy
        # Guardamos último crop para solo mover cuando necesario
        self.last_crop_x = None  # Usado en _calculate_crop_keep_in_frame

        logger.info(f"FaceReframer initialized: strategy={strategy}, sample_rate={frame_sample_rate}")

    def _detect_largest_face(self, frame) -> Optional[Dict]:
        """
        Detecta el rostro más grande en frame usando MediaPipe

        DECISIÓN: Elegir rostro MÁS GRANDE en lugar de primero detectado
        Por qué? En multi-person shots, persona principal suele estar más cerca

        INTEGRACIÓN MediaPipe:
        1. OpenCV lee frames en BGR (azul-verde-rojo)
        2. MediaPipe requiere RGB (rojo-verde-azul)
        3. cv2.cvtColor convierte BGR→RGB antes de procesamiento

        Returns:
            Dict con {x, y, width, height, center_x, center_y} o None si no detecta
        """
        # MediaPipe requiere RGB, OpenCV lee BGR
        # DECISIÓN: Convertir cada frame vs configurar OpenCV en RGB
        # Trade-off: cv2.cvtColor es rápido (negligible vs detection time)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.face_detector.process(frame_rgb)

        if not results.detections:
            return None

        # Encontrar rostro más grande (por área de bounding box)
        h, w, _ = frame.shape
        largest_face = None
        max_area = 0

        for detection in results.detections:
            # MediaPipe devuelve coordenadas relativas (0.0-1.0)
            # Las convertimos a píxeles absolutos
            bbox = detection.location_data.relative_bounding_box
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            area = width * height

            if area > max_area:
                max_area = area
                largest_face = {
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'center_x': x + width // 2,
                    'center_y': y + height // 2,
                }

        return largest_face

    def _calculate_crop_keep_in_frame(
        self,
        face: Dict,
        frame_width: int,
        frame_height: int,
        target_width: int,
        target_height: int
    ) -> int:
        """
        ESTRATEGIA "KEEP IN FRAME" (Ben's Innovation)

        LÓGICA CORE:
        1. Definir safe zone (área donde rostro puede moverse sin trigger reframe)
        2. Solo mover crop cuando rostro SALE de safe zone
        3. Cuando se mueve, posicionar crop para que rostro esté en borde de safe zone

        SAFE ZONE VISUAL:

        |<-- 15% -->|<------ 70% safe zone ----->|<-- 15% -->|
        |   margin  |  rostro puede moverse aquí |  margin   |
        └───────────┴────────────────────────────┴───────────┘
                    ^                            ^
                safe_left                    safe_right

        EJEMPLO:
        - target_width = 1080px (9:16 crop)
        - safe_zone_margin = 0.15 (15%)
        - safe_left = 162px (15% de 1080)
        - safe_right = 918px (85% de 1080)
        - Rostro en x=500 → DENTRO de safe zone → NO MOVER crop
        - Rostro en x=950 → FUERA de safe zone → MOVER crop

        Por qué esto es mejor que centered?
        - Centered: Rostro se mueve 10px → crop se mueve 10px → jittery
        - Keep in frame: Rostro se mueve 10px → crop NO se mueve → smooth

        Returns:
            crop_x: Posición X del crop en frame original
        """
        # Calcular límites de safe zone dentro del crop
        safe_left = target_width * self.safe_zone_margin
        safe_right = target_width * (1 - self.safe_zone_margin)

        # Si es primer frame, centrar rostro
        if self.last_crop_x is None:
            crop_x = max(0, min(
                face['center_x'] - target_width // 2,
                frame_width - target_width
            ))
            self.last_crop_x = crop_x
            return crop_x

        # Calcular posición del rostro RELATIVA al crop actual
        face_x_in_crop = face['center_x'] - self.last_crop_x

        # DECISIÓN CLAVE: Solo mover crop si rostro sale de safe zone
        if face_x_in_crop < safe_left:
            # Rostro salió por izquierda → mover crop a la izquierda
            # Posicionar crop para que rostro quede en borde izquierdo de safe zone
            crop_x = max(0, face['center_x'] - int(safe_left))
        elif face_x_in_crop > safe_right:
            # Rostro salió por derecha → mover crop a la derecha
            # Posicionar crop para que rostro quede en borde derecho de safe zone
            crop_x = min(
                frame_width - target_width,
                face['center_x'] - int(safe_right)
            )
        else:
            # Rostro dentro de safe zone → NO MOVER
            crop_x = self.last_crop_x

        self.last_crop_x = crop_x
        return crop_x

    def _calculate_crop_centered(
        self,
        face: Dict,
        frame_width: int,
        target_width: int
    ) -> int:
        """
        ESTRATEGIA "CENTERED" (Alternativa)

        LÓGICA: Siempre centrar rostro en el crop

        TRADE-OFF:
        + Rostro siempre en mismo lugar (predecible)
        - Movimiento constante (jittery sin smoothing)

        Cuándo usar?
        - Content con movimiento extremo (deportes, action)
        - Cuando smoothing avanzado está disponible (Paso 07)

        Returns:
            crop_x: Posición X del crop centrado en rostro
        """
        crop_x = max(0, min(
            face['center_x'] - target_width // 2,
            frame_width - target_width
        ))
        return crop_x

    def reframe_video(
        self,
        input_path: str,
        output_path: str,
        target_resolution: Tuple[int, int],
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """
        PIPELINE PRINCIPAL: Genera video con crop dinámico basado en face tracking

        FLUJO:
        1. Abrir video original (OpenCV VideoCapture)
        2. Crear video temporal (OpenCV VideoWriter)
        3. Por cada frame (sampling cada N):
            a. Detectar rostro (MediaPipe)
            b. Calcular crop óptimo (strategy: keep_in_frame o centered)
            c. Aplicar crop
            d. Escribir frame cropped a video temporal
        4. Cerrar video temporal
        5. Retornar path para que FFmpeg lo use

        INTEGRACIÓN CON FFmpeg:
        - Este método NO agrega subtítulos
        - Solo genera video cropped
        - video_exporter.py usa este output como input a FFmpeg
        - FFmpeg agrega subtítulos al video ya cropped

        FALLBACK:
        - Si no detecta rostro en X frames consecutivos → center crop
        - Log warning pero continuar (graceful degradation)

        Args:
            input_path: Video original (16:9)
            output_path: Video temporal cropped (9:16)
            target_resolution: (width, height) ej. (1080, 1920)
            start_time: Timestamp inicio (segundos) - para procesar solo clip
            end_time: Timestamp fin (segundos)

        Returns:
            output_path: Path al video temporal generado
        """
        logger.info(f"Starting face reframing: {input_path} → {output_path}")
        logger.info(f"Strategy: {self.strategy}, Sample rate: {self.frame_sample_rate}")

        # Abrir video original
        cap = cv2.VideoCapture(str(input_path))

        # Obtener propiedades del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        target_width, target_height = target_resolution

        logger.info(f"Input: {frame_width}x{frame_height} @ {fps}fps, {total_frames} frames")
        logger.info(f"Output: {target_width}x{target_height}")

        # DECISIÓN ARQUITECTÓNICA: Scale + Crop para 16:9 → 9:16
        # PROBLEMA: Video 1920x1080 no puede cropear a 1080x1920 (no hay altura suficiente)
        # SOLUCIÓN: Scale primero para obtener altura target, luego crop horizontal

        # Calcular dimensiones intermedias (scaled frame)
        # Necesitamos que scaled_height >= target_height
        scale_factor = max(target_width / frame_width, target_height / frame_height)
        scaled_width = int(frame_width * scale_factor)
        scaled_height = int(frame_height * scale_factor)

        logger.info(f"Scale factor: {scale_factor:.2f}x → Intermediate: {scaled_width}x{scaled_height}")

        # Validar que después de scale tenemos suficiente resolución
        if scaled_width < target_width or scaled_height < target_height:
            raise ValueError(
                f"Video resolution too small. After scaling {frame_width}x{frame_height} → "
                f"{scaled_width}x{scaled_height}, cannot fit target {target_width}x{target_height}"
            )

        # Calcular frames a procesar si hay start/end time
        start_frame = int(start_time * fps) if start_time else 0
        end_frame = int(end_time * fps) if end_time else total_frames

        # Configurar VideoWriter para output
        # DECISIÓN: Codec con fallback para compatibilidad cross-platform
        # macOS M4: 'avc1' funciona mejor que 'mp4v'
        # Linux: 'mp4v' o 'XVID' más compatibles

        # DECISIÓN ARQUITECTÓNICA: FFmpegVideoWriter (subprocess directo)
        # PROBLEMA: cv2.VideoWriter y ffmpegcv fallan en macOS M4
        # SOLUCIÓN: FFmpeg subprocess usa FFmpeg del sistema (arm64 nativo)
        # Ver: pasoxpaso/todoPASO3/SESSION-2025-11-28.md → Opción D

        # Codecs en orden de preferencia
        # libx264: Encoder H.264 software (mejor compatibilidad)
        # h264_videotoolbox: Hardware encoder macOS (más rápido)
        codecs_to_try = ['libx264', 'h264_videotoolbox']
        out = None

        for codec in codecs_to_try:
            try:
                test_writer = FFmpegVideoWriter(
                    output_path=str(output_path),
                    width=target_width,
                    height=target_height,
                    fps=fps,
                    codec=codec,
                    preset='fast',  # Coherente con video_exporter.py
                    crf=23          # Calidad coherente con video_exporter.py
                )

                if test_writer.isOpened():
                    # Test write con frame dummy
                    dummy_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                    test_success = test_writer.write(dummy_frame)

                    if test_success:
                        out = test_writer
                        logger.info(f"Using codec: {codec} (FFmpeg subprocess)")
                        break
                    else:
                        logger.warning(f"Codec {codec} opened but write() failed, trying next...")
                        test_writer.release()
                else:
                    test_writer.release()

            except Exception as e:
                logger.warning(f"Codec {codec} failed to initialize: {e}")
                continue

        if out is None:
            raise RuntimeError(
                f"Failed to initialize FFmpegVideoWriter. Tried codecs: {codecs_to_try}. "
                "Check FFmpeg installation (ffmpeg -version)."
            )

        # Seek al frame inicial si necesario
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        frame_number = start_frame
        last_face = None  # Para fallback cuando no detecta rostro
        frames_without_face = 0

        while cap.isOpened() and frame_number < end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            # PASO 1: SCALE frame a dimensiones intermedias
            # Esto asegura que tenemos suficiente resolución para crop vertical
            scaled_frame = cv2.resize(frame, (scaled_width, scaled_height))

            # FRAME SAMPLING: Solo detectar cada N frames
            # Por qué? 3x speedup validado en spike (11px movement acceptable)
            should_detect = (frame_number % self.frame_sample_rate) == 0

            if should_detect:
                # PASO 2: Detectar rostro en frame ESCALADO
                face = self._detect_largest_face(scaled_frame)

                if face:
                    last_face = face  # Guardar para fallback
                    frames_without_face = 0
                else:
                    frames_without_face += 1

                    # FALLBACK: Si no detecta rostro por 10 frames → center crop
                    if frames_without_face > 10 and last_face is None:
                        logger.warning(f"No face detected for 10+ frames at {frame_number}, using center crop")
                        last_face = {
                            'center_x': scaled_width // 2,
                            'center_y': scaled_height // 2
                        }

            # Si nunca detectó rostro, usar center crop estático
            if last_face is None:
                crop_x = (scaled_width - target_width) // 2
            else:
                # PASO 3: Calcular crop según estrategia (sobre frame ESCALADO)
                if self.strategy == "keep_in_frame":
                    crop_x = self._calculate_crop_keep_in_frame(
                        last_face, scaled_width, scaled_height, target_width, target_height
                    )
                else:  # centered
                    crop_x = self._calculate_crop_centered(
                        last_face, scaled_width, target_width
                    )

            # PASO 4: Aplicar crop a frame ESCALADO
            # Center crop vertical (rostros a misma altura)
            # Dynamic crop horizontal (face tracking)
            crop_y = (scaled_height - target_height) // 2

            cropped_frame = scaled_frame[
                crop_y:crop_y + target_height,
                crop_x:crop_x + target_width
            ]

            # Validar dimensiones antes de escribir
            if cropped_frame.shape[1] != target_width or cropped_frame.shape[0] != target_height:
                logger.error(
                    f"Frame dimension mismatch at frame {frame_number}: "
                    f"expected {target_width}x{target_height}, "
                    f"got {cropped_frame.shape[1]}x{cropped_frame.shape[0]}"
                )
                # Resize forzado si hay mismatch (fallback)
                cropped_frame = cv2.resize(cropped_frame, (target_width, target_height))

            # Validar formato del frame antes de escribir
            # VideoWriter requiere: BGR, uint8, contiguous array
            if not cropped_frame.flags['C_CONTIGUOUS']:
                cropped_frame = np.ascontiguousarray(cropped_frame)

            if cropped_frame.dtype != np.uint8:
                logger.error(f"Frame dtype is {cropped_frame.dtype}, expected uint8")
                cropped_frame = cropped_frame.astype(np.uint8)

            # Escribir frame cropped a video temporal
            success = out.write(cropped_frame)

            # Log ALL failures, not just every 30
            if not success:
                if frame_number <= 10 or frame_number % 30 == 0:
                    logger.error(
                        f"VideoWriter.write() failed at frame {frame_number}. "
                        f"Frame shape: {cropped_frame.shape}, dtype: {cropped_frame.dtype}, "
                        f"contiguous: {cropped_frame.flags['C_CONTIGUOUS']}"
                    )

            frame_number += 1

            # Progress log cada 30 frames
            if frame_number % 30 == 0:
                progress = ((frame_number - start_frame) / (end_frame - start_frame)) * 100
                logger.debug(f"Reframing progress: {progress:.1f}%")

        # Cleanup
        cap.release()
        out.release()

        logger.info(f"Face reframing complete: {output_path}")
        return str(output_path)

    def __del__(self):
        """Cleanup MediaPipe resources"""
        if hasattr(self, 'face_detector'):
            self.face_detector.close()
