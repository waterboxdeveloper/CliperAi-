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
        clip_styles: Optional[Dict[int, str]] = None
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
                    subtitle_style=subtitle_style
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
        subtitle_style: str = "default"
    ) -> Optional[Path]:
        """
        Exporto un solo clip

        Args:
            video_path: Ruta al video original
            clip: Dict con start_time, end_time, clip_id
            video_name: Nombre base
            aspect_ratio: Aspect ratio a convertir (opcional)

        Returns:
            Path al clip exportado, o None si falló
        """
        clip_id = clip['clip_id']
        start_time = clip['start_time']
        end_time = clip['end_time']
        duration = end_time - start_time

        # Nombre del archivo de salida (simple: 1.mp4, 2.mp4, etc.)
        output_filename = f"{clip_id}.mp4"
        output_path = output_dir / output_filename

        # Genero subtítulos si se requiere
        subtitle_file = None
        if add_subtitles and transcript_path:
            # Genero archivo SRT para este clip específico (también con nombre simple)
            subtitle_filename = f"{clip_id}.srt"
            subtitle_file = output_dir / subtitle_filename

            self.subtitle_generator.generate_srt_for_clip(
                transcript_path=transcript_path,
                clip_start=start_time,
                clip_end=end_time,
                output_path=str(subtitle_file)
            )

        # Comando ffmpeg básico (corte preciso)
        cmd = [
            "ffmpeg",
            "-ss", str(start_time),           # Start time
            "-i", str(video_path),            # Input video
            "-t", str(duration),              # Duration
        ]

        # Construyo el filtro completo (aspect ratio + subtítulos)
        filters = []

        # Filtro de aspect ratio
        if aspect_ratio:
            aspect_filter = self._get_aspect_ratio_filter(aspect_ratio)
            if aspect_filter:
                filters.append(aspect_filter)

        # Filtro de subtítulos (quemados en el video)
        if add_subtitles and subtitle_file and subtitle_file.exists():
            # Escapo el path del subtitle para ffmpeg
            subtitle_path_escaped = str(subtitle_file).replace('\\', '\\\\').replace(':', '\\:')

            # Obtengo el estilo de subtítulos
            subtitle_filter = self._get_subtitle_filter(subtitle_path_escaped, subtitle_style)
            filters.append(subtitle_filter)

        # Aplico filtros si hay
        if filters:
            filter_string = ','.join(filters)
            cmd.extend(["-vf", filter_string])

        # Codec y calidad
        cmd.extend([
            "-c:v", "libx264",                # Video codec
            "-c:a", "aac",                    # Audio codec
            "-preset", "fast",                # Encoding speed
            "-crf", "23",                     # Quality (18-28, lower = better)
        ])

        # Output file (sobrescribe si existe)
        cmd.extend(["-y", str(output_path)])

        try:
            # Ejecuto ffmpeg (silencioso)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logger.error(f"Error exporting clip {clip_id}: {result.stderr}")
                return None

            logger.info(f"✓ Exported clip {clip_id}: {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting clip {clip_id}: {e}")
            return None


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
        subtitle_filter = f"subtitles={subtitle_path}:force_style='"
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
