# -*- coding: utf-8 -*-
"""
Video Exporter - Corta videos en clips usando ffmpeg

Este módulo toma los clips generados y los exporta a archivos de video reales.
Usa ffmpeg para cortar con precisión y opcionalmente cambiar aspect ratio.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.progress import Progress, TaskID

from src.utils.logger import get_logger
from src.subtitle_generator import SubtitleGenerator
from src.reframer import FaceReframer

logger = get_logger(__name__)


class VideoExporter:
    """
    Exporto clips de video usando ffmpeg

    Características:
    - Corte preciso por timestamps
    - Conversión de aspect ratio (16:9 → 9:16 para redes sociales)
    - Progress tracking
    - Nombres descriptivos para clips
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()
        self.subtitle_generator = SubtitleGenerator()

        # Verifico que ffmpeg esté instalado
        if not self._check_ffmpeg():
            raise RuntimeError(
                "ffmpeg no está instalado. "
                "Instala con: brew install ffmpeg (macOS) o apt install ffmpeg (Linux)"
            )


    def _check_ffmpeg(self) -> bool:
        """
        Verifico si ffmpeg está disponible en el sistema
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False


    def export_clips(
        self,
        video_path: str,
        clips: List[Dict],
        aspect_ratio: Optional[str] = None,
        video_name: Optional[str] = None,
        add_subtitles: bool = False,
        transcript_path: Optional[str] = None,
        subtitle_style: str = "default",
        organize_by_style: bool = False,
        clip_styles: Optional[Dict[int, str]] = None,
        # Face tracking parameters (PASO3)
        enable_face_tracking: bool = False,
        face_tracking_strategy: str = "keep_in_frame",
        face_tracking_sample_rate: int = 3,
        # Branding parameters (PASO4 - Logo)
        add_logo: bool = False,
        logo_path: Optional[str] = "assets/logo.png",
        logo_position: str = "top-right",
        logo_scale: float = 0.1
    ) -> List[str]:
        """
        Exporto todos los clips de un video

        Args:
            video_path: Ruta al video original
            clips: Lista de dicts con {clip_id, start_time, end_time, text_preview}
            aspect_ratio: "16:9", "9:16", "1:1", o None (mantener original)
            video_name: Nombre base para los archivos (default: nombre del video)
            add_subtitles: Si True, quema subtítulos en el video
            transcript_path: Ruta al archivo de transcripción (requerido si add_subtitles=True)
            subtitle_style: Estilo de subtítulos ("default", "bold", "yellow")
            organize_by_style: Si True, organiza clips en subcarpetas por estilo
            clip_styles: Dict mapping clip_id → style ("viral", "educational", "storytelling")
            enable_face_tracking: Si True, usa detección de rostros para reencuadre dinámico (9:16 only)
            face_tracking_strategy: "keep_in_frame" (menos movimiento) o "centered" (siempre centrado)
            face_tracking_sample_rate: Procesar cada N frames (default: 3 = 3x speedup)
            add_logo: Si True, superpone el logo en el video.
            logo_path: Ruta al archivo del logo (ej. "assets/logo.png").
            logo_position: Posición del logo ("top-right", "top-left", "bottom-right", "bottom-left").
            logo_scale: Escala del logo relativa al ancho del video (0.1 = 10%).

        Returns:
            Lista de rutas a los clips exportados
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        # Nombre base para los clips
        if video_name is None:
            video_name = video_path.stem

        # Creo una subcarpeta específica para este video
        video_output_dir = self.output_dir / video_name
        video_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exportando clips a: {video_output_dir}")

        exported_clips = []

        # Progress bar
        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]Exporting {len(clips)} clips...",
                total=len(clips)
            )

            for clip in clips:
                # Determinar carpeta de salida según estilo (si aplica)
                clip_output_dir = video_output_dir

                if organize_by_style and clip_styles:
                    clip_id = clip['clip_id']
                    style = clip_styles.get(clip_id, 'unclassified')

                    # Crear subcarpeta por estilo
                    clip_output_dir = video_output_dir / style
                    clip_output_dir.mkdir(parents=True, exist_ok=True)

                clip_path = self._export_single_clip(
                    video_path=video_path,
                    clip=clip,
                    video_name=video_name,
                    output_dir=clip_output_dir,
                    aspect_ratio=aspect_ratio,
                    add_subtitles=add_subtitles,
                    transcript_path=transcript_path,
                    subtitle_style=subtitle_style,
                    enable_face_tracking=enable_face_tracking,
                    face_tracking_strategy=face_tracking_strategy,
                    face_tracking_sample_rate=face_tracking_sample_rate,
                    add_logo=add_logo,
                    logo_path=logo_path,
                    logo_position=logo_position,
                    logo_scale=logo_scale
                )

                if clip_path:
                    exported_clips.append(str(clip_path))

                progress.update(task, advance=1)

        return exported_clips


    def _export_single_clip(
        self,
        video_path: Path,
        clip: Dict,
        video_name: str,
        output_dir: Path,
        aspect_ratio: Optional[str] = None,
        add_subtitles: bool = False,
        transcript_path: Optional[str] = None,
        subtitle_style: str = "default",
        enable_face_tracking: bool = False,
        face_tracking_strategy: str = "keep_in_frame",
        face_tracking_sample_rate: int = 3,
        add_logo: bool = False,
        logo_path: Optional[str] = "assets/logo.png",
        logo_position: str = "top-right",
        logo_scale: float = 0.1
    ) -> Optional[Path]:
        clip_id = clip['clip_id']
        start_time = clip['start_time']
        end_time = clip['end_time']
        duration = end_time - start_time

        output_filename = f"{clip_id}.mp4"
        output_path = output_dir / output_filename
        
        # Define paths for temporary files
        temp_path_step1 = output_dir / f"{clip_id}_step1_temp.mp4"
        temp_reframed_path = output_dir / f"{clip_id}_reframed_temp.mp4"
        
        subtitle_file = None
        if add_subtitles and transcript_path:
            subtitle_filename = f"{clip_id}.srt"
            subtitle_file = output_dir / subtitle_filename
            self.subtitle_generator.generate_srt_for_clip(
                transcript_path=transcript_path,
                clip_start=start_time,
                clip_end=end_time,
                output_path=str(subtitle_file)
            )

        video_to_process = video_path
        aspect_ratio_original = aspect_ratio

        if enable_face_tracking and aspect_ratio == "9:16":
            logger.info(f"Face tracking enabled for clip {clip_id} (strategy: {face_tracking_strategy})")
            try:
                reframer = FaceReframer(frame_sample_rate=face_tracking_sample_rate, strategy=face_tracking_strategy)
                reframer.reframe_video(
                    input_path=str(video_path),
                    output_path=str(temp_reframed_path),
                    target_resolution=(1080, 1920),
                    start_time=start_time,
                    end_time=end_time
                )
                video_to_process = temp_reframed_path
                aspect_ratio = None
                logger.info(f"Face tracking completed for clip {clip_id}")
            except Exception as e:
                logger.warning(f"Face tracking failed for clip {clip_id}: {e}, falling back to static crop.")
                video_to_process = video_path
        
        # Architectural Decision: Use a two-step process when both logo and subtitles are enabled.
        needs_two_steps = add_logo and logo_path and Path(logo_path).exists() and add_subtitles and subtitle_file and subtitle_file.exists()
        
        # Determine the output target for the first command
        first_step_output = temp_path_step1 if needs_two_steps else output_path

        try:
            # --- STEP 1: Process all filters EXCEPT subtitles ---
            inputs, video_filters, filter_chains = [], [], []
            using_face_tracking = (video_to_process == temp_reframed_path and temp_reframed_path.exists())
            video_input_idx, audio_input_idx = (0, 1) if using_face_tracking else (0, 0)
            
            if using_face_tracking:
                inputs.extend(["-i", str(video_to_process)])
                inputs.extend(["-ss", str(start_time), "-t", str(duration), "-i", str(video_path)])
            else:
                inputs.extend(["-ss", str(start_time), "-t", str(duration), "-i", str(video_path)])
            
            logo_input_idx = -1
            if add_logo and logo_path and Path(logo_path).exists():
                inputs.extend(["-i", str(logo_path)])
                logo_input_idx = audio_input_idx + 1
                logger.info(f"Adding logo from {logo_path}")

            last_video_stream = f"[{video_input_idx}:v]"
            
            # Add filters that can be chained simply
            simple_filters = []
            if aspect_ratio and not using_face_tracking:
                aspect_filter = self._get_aspect_ratio_filter(aspect_ratio)
                if aspect_filter: simple_filters.append(aspect_filter)
            
            # If we are NOT doing two steps, add subtitles here
            if not needs_two_steps and add_subtitles and subtitle_file and subtitle_file.exists():
                 subtitle_path_escaped = str(subtitle_file).replace('\\', '\\\\').replace(':', '\\:')
                 subtitle_filter = self._get_subtitle_filter(subtitle_path_escaped, subtitle_style)
                 simple_filters.append(subtitle_filter)

            cmd = ["ffmpeg"] + inputs
            
            # If a logo is present, we must use filter_complex
            if logo_input_idx != -1:
                # Apply simple filters first, if any
                if simple_filters:
                    filter_chains.append(f"{last_video_stream}{','.join(simple_filters)}[v_filtered]")
                    last_video_stream = "[v_filtered]"
                
                positions = {"top-right": "W-w-20:20", "top-left": "20:20", "bottom-right": "W-w-20:H-h-20", "bottom-left": "20:H-h-20"}
                pos_str = positions.get(logo_position, positions["top-right"])
                
                # Chain the overlay
                filter_chains.append(f"{last_video_stream}[{logo_input_idx}:v]overlay={pos_str}[v_out]")
                last_video_stream = "[v_out]"
                
                cmd.extend(["-filter_complex", ";".join(filter_chains), "-map", last_video_stream])

            elif simple_filters:
                cmd.extend(["-vf", ",".join(simple_filters), "-map", f"{video_input_idx}:v"])
            else:
                 cmd.extend(["-map", f"{video_input_idx}:v"])

            # BUGFIX: Add -sn flag when doing two-step processing to discard any subtitle streams
            # This prevents FFmpeg from preserving subtitle metadata that would cause duplication in Step 2
            if needs_two_steps:
                cmd.extend(["-sn"])  # Discard subtitle streams

            cmd.extend(["-map", f"{audio_input_idx}:a?", "-c:v", "libx264", "-c:a", "aac", "-preset", "fast", "-crf", "23", "-y", str(first_step_output)])

            result1 = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result1.returncode != 0:
                logger.error(f"Error in video processing (Step 1) for clip {clip_id}: {result1.stderr}")
                return None

            # --- STEP 2: Add subtitles if required in a separate, safe step ---
            if needs_two_steps:
                logger.info("Applying subtitles in a second step to avoid duplication bug.")
                subtitle_path_escaped = str(subtitle_file).replace('\\', '\\\\').replace(':', '\\:')
                subtitle_filter = self._get_subtitle_filter(subtitle_path_escaped, subtitle_style)
                cmd2 = ["ffmpeg", "-i", str(first_step_output), "-vf", subtitle_filter, "-c:a", "copy", "-y", str(output_path)]
                
                result2 = subprocess.run(cmd2, capture_output=True, text=True, check=False)
                if result2.returncode != 0:
                    logger.error(f"Error adding subtitles (Step 2) for clip {clip_id}: {result2.stderr}")
                    first_step_output.rename(output_path) # Fallback to the version without subtitles
                    return None
            
            logger.info(f"✓ Exported clip {clip_id}: {output_path.name}")
            return output_path

        finally:
            # Cleanup all temporary files
            if temp_path_step1.exists(): temp_path_step1.unlink()
            if temp_reframed_path and temp_reframed_path.exists(): temp_reframed_path.unlink()


    def _get_logo_overlay_filter(
        self,
        position: str = "top-right",
        scale: float = 0.1
    ) -> str:
        """
        Genera el string del filtro FFmpeg para superponer un logo.

        Args:
            position: Posición del logo ("top-right", "top-left", "bottom-right", "bottom-left").
            scale: Escala del logo relativa al ancho del video (0.1 = 10%).

        Returns:
            String del filtro para FFmpeg.
        """
        positions = {
            "top-right": "W-w-20:20",
            "top-left": "20:20",
            "bottom-right": "W-w-20:H-h-20",
            "bottom-left": "20:H-h-20"
        }
        pos = positions.get(position, positions["top-right"])

        # El filtro escala el logo y luego lo superpone.
        # [1:v] es el input del logo, se escala a (ancho_video * escala) y alto automático (-1).
        # Luego, [0:v] (video principal) y [logo_scaled] se usan en el overlay.
        return f"scale2ref=w=oh*mdar:h=ih*{scale}[logo_scaled][video];[video][logo_scaled]overlay={pos}"

    def _get_aspect_ratio_filter(self, aspect_ratio: str) -> Optional[str]:
        """
        Genero el filtro de ffmpeg para cambiar aspect ratio

        Estrategia: Crop inteligente + scale
        - 16:9 → 9:16: Crop vertical y resize
        - 16:9 → 1:1: Crop a cuadrado

        Args:
            aspect_ratio: "9:16", "1:1", etc.

        Returns:
            String de filtro para ffmpeg, o None si no se reconoce
        """
        if aspect_ratio == "9:16":
            # Vertical (para Instagram Reels, TikTok, YouTube Shorts)
            # Crop al centro y resize a 1080x1920
            return "crop=ih*9/16:ih,scale=1080:1920"

        elif aspect_ratio == "1:1":
            # Cuadrado (para Instagram post)
            # Crop al centro y resize a 1080x1080
            return "crop=ih:ih,scale=1080:1080"

        elif aspect_ratio == "16:9":
            # Horizontal estándar (ya suele ser así, pero por si acaso)
            return "scale=1920:1080"

        else:
            logger.warning(f"Aspect ratio '{aspect_ratio}' no reconocido, manteniendo original")
            return None


    def _get_subtitle_filter(self, subtitle_path: str, style: str = "default") -> str:
        """
        Genero el filtro de ffmpeg para quemar subtítulos en el video

        Args:
            subtitle_path: Ruta al archivo SRT (escapada para ffmpeg)
            style: Estilo de subtítulos ("default", "bold", "yellow", "tiktok")

        Returns:
            String de filtro para ffmpeg
        """
        # Estilos predefinidos para subtítulos
        # TODOS con texto AMARILLO para máxima visibilidad
        styles = {
            "default": {
                "FontName": "Arial",
                "FontSize": "18",
                "PrimaryColour": "&H0000FFFF",  # AMARILLO
                "OutlineColour": "&H00000000",  # Negro
                "Outline": "2",
                "Shadow": "1",
                "Bold": "0"
            },
            "bold": {
                "FontName": "Arial",
                "FontSize": "22",
                "PrimaryColour": "&H0000FFFF",  # AMARILLO
                "OutlineColour": "&H00000000",
                "Outline": "2",
                "Shadow": "1",
                "Bold": "-1"
            },
            "yellow": {
                "FontName": "Arial",
                "FontSize": "20",
                "PrimaryColour": "&H0000FFFF",  # AMARILLO
                "OutlineColour": "&H00000000",
                "Outline": "2",
                "Shadow": "1",
                "Bold": "-1"
            },
            "tiktok": {
                "FontName": "Arial",
                "FontSize": "20",
                "PrimaryColour": "&H0000FFFF",  # AMARILLO
                "OutlineColour": "&H00000000",
                "Outline": "2",
                "Shadow": "2",
                "Bold": "-1",
                "Alignment": "10"  # Centro arriba
            },
            "small": {
                "FontName": "Arial",
                "FontSize": "10",
                "PrimaryColour": "&H0000FFFF",  # AMARILLO
                "OutlineColour": "&H00000000",
                "Outline": "1",
                "Shadow": "1",
                "Bold": "0",
                "Alignment": "6",  # Centro medio-arriba
                "MarginV": "100"
            },
            "tiny": {
                "FontName": "Arial",
                "FontSize": "8",
                "PrimaryColour": "&H0000FFFF",  # AMARILLO
                "OutlineColour": "&H00000000",
                "Outline": "1",
                "Shadow": "0",
                "Bold": "0",
                "Alignment": "6",  # Centro medio-arriba
                "MarginV": "100"
            }
        }

        selected_style = styles.get(style, styles["default"])

        # Construyo el filtro subtitles con el estilo
        # subtitles filter quema los subtítulos directamente en el video
        # Wrapeamos el path con comillas simples para manejar espacios
        subtitle_filter = f"subtitles='{subtitle_path}':force_style='"
        subtitle_filter += f"FontName={selected_style['FontName']},"
        subtitle_filter += f"FontSize={selected_style['FontSize']},"
        subtitle_filter += f"PrimaryColour={selected_style['PrimaryColour']},"
        subtitle_filter += f"OutlineColour={selected_style['OutlineColour']},"
        subtitle_filter += f"Outline={selected_style['Outline']},"
        subtitle_filter += f"Shadow={selected_style['Shadow']},"
        subtitle_filter += f"Bold={selected_style['Bold']}"

        if "Alignment" in selected_style:
            subtitle_filter += f",Alignment={selected_style['Alignment']}"

        if "MarginV" in selected_style:
            subtitle_filter += f",MarginV={selected_style['MarginV']}"

        subtitle_filter += "'"

        return subtitle_filter


    def get_video_info(self, video_path: str) -> Dict:
        """
        Obtengo información del video usando ffprobe

        Returns:
            Dict con duration, width, height, fps, etc.
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)

            # Extraigo info relevante del video stream
            video_stream = next(
                (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                None
            )

            if not video_stream:
                return {}

            return {
                'duration': float(data['format'].get('duration', 0)),
                'width': video_stream.get('width'),
                'height': video_stream.get('height'),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),  # "30/1" → 30.0
                'codec': video_stream.get('codec_name'),
            }

        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
