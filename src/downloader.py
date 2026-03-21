# -*- coding: utf-8 -*-
"""
Downloader de YouTube usando yt-dlp
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

import yt_dlp

from .utils.logger import setup_logger


class YoutubeDownloader:
    """
    Mi clase principal para descargar videos de YouTube
    """

    def __init__(self, download_dir: str = "downloads"):
        # Aquí guardo dónde voy a poner los videos
        self.download_dir = Path(download_dir)

        # Creo mi logger para ver qué pasa
        self.logger = setup_logger("downloader")

        # Me aseguro de que la carpeta exista
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"✓ Downloader listo. Videos en: {self.download_dir.absolute()}")


    def validate_url(self, url: str) -> bool:
        """
        Aquí verifico que la URL sea válida de YouTube
        Retorno True si es válida, False si no
        """
        try:
            # Uso este regex para aceptar todos los formatos de YouTube
            # youtube.com/watch?v=... o youtu.be/...
            youtube_regex = (
                r'(https?://)?(www\.)?'
                r'(youtube\.com|youtu\.be)/'
                r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
            )

            match = re.match(youtube_regex, url)

            if match:
                self.logger.debug(f"✓ URL válida: {url}")
                return True
            else:
                self.logger.warning(f"✗ URL inválida: {url}")
                return False

        except Exception as e:
            self.logger.error(f"Error al validar URL: {e}")
            return False


    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Necesito el ID del video (esos 11 caracteres únicos)
        para nombrar archivos y evitar duplicados
        """
        try:
            # Caso youtube.com/watch?v=VIDEO_ID
            if "youtube.com" in url:
                parsed = urlparse(url)
                video_id = parse_qs(parsed.query).get('v')
                if video_id:
                    return video_id[0]

            # Caso youtu.be/VIDEO_ID
            elif "youtu.be" in url:
                return url.split('/')[-1].split('?')[0]

            return None

        except Exception as e:
            self.logger.error(f"Error al extraer video ID: {e}")
            return None


    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """
        yt-dlp llama a esto mientras descarga
        Lo uso para mostrar el progreso en tiempo real
        """
        if d['status'] == 'downloading':
            # Extraigo la info de progreso que me da yt-dlp
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')

            self.logger.info(f"📥 {percent} | ⚡ {speed} | ⏱️  ETA: {eta}")

        elif d['status'] == 'finished':
            self.logger.info("✓ Descarga completada. Procesando...")


    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Obtengo la info del video SIN descargarlo
        Me sirve para validar y ver preview
        """
        if not self.validate_url(url):
            self.logger.error("URL inválida")
            return None

        try:
            # Configuro yt-dlp para que solo extraiga info
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.logger.info(f"📋 Obteniendo info de: {url}")

                # download=False → solo info, no descarga
                info = ydl.extract_info(url, download=False)

                # Extraigo lo que me interesa
                video_info = {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description'),
                    'thumbnail': info.get('thumbnail'),
                }

                self.logger.info(f"📺 {video_info['title']}")
                self.logger.info(f"⏱️  {video_info['duration']}s")

                return video_info

        except Exception as e:
            self.logger.error(f"Error al obtener info: {e}")
            return None


    def download(
        self,
        url: str,
        quality: str = "best",
        output_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Mi función principal de descarga
        Recibo: URL, calidad opcional, nombre opcional
        Retorno: path del archivo o None si falla
        """

        # Primero valido la URL
        if not self.validate_url(url):
            self.logger.error("URL inválida, aborto")
            return None

        try:
            # Extraigo el ID por si lo necesito
            video_id = self._extract_video_id(url)

            # Decido cómo nombrar el archivo
            if output_filename:
                # Si me dieron un nombre, lo limpio de caracteres raros
                safe_filename = re.sub(r'[<>:"/\\|?*]', '', output_filename)
                outtmpl = str(self.download_dir / f"{safe_filename}_%(id)s.%(ext)s")
            else:
                # Si no, uso título + ID automáticamente
                outtmpl = str(self.download_dir / "%(title)s_%(id)s.%(ext)s")

            # Mapeo las calidades a formato de yt-dlp
            format_map = {
                'best': 'bestvideo+bestaudio/best',
                '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            }

            selected_format = format_map.get(quality, format_map['best'])

            # Configuro yt-dlp con todas las opciones
            ydl_opts = {
                'format': selected_format,
                'outtmpl': outtmpl,
                'progress_hooks': [self._progress_hook],  # Mi función de progreso
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'quiet': False,
                'no_warnings': False,
                # Manejo robusto de conexión (SSL + reintentos)
                'socket_timeout': 30,  # Timeout explícito para evitar cuelgues
                'retries': 3,  # Reintentos automáticos simples
            }

            # ¡A descargar!
            self.logger.info(f"🚀 Descargando: {url}")
            self.logger.info(f"🎥 Calidad: {quality}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Esto descarga el video
                info = ydl.extract_info(url, download=True)

                # DECISIÓN ARQUITECTÓNICA (yt-dlp 2026+ compatibility):
                # En lugar de confiar en prepare_filename() (que falla con caracteres especiales),
                # buscamos por video_id. Esto evita problemas de encoding (ej: caracteres chinos).
                # yt-dlp 2026+ cambió cómo maneja filenames después de merge, causando:
                # - Caracteres especiales (： chino) → encoding corruption
                # - prepare_filename() → retorna paths inválidos
                # Solución: Buscar archivo por video_id en downloads/ (garantiza correctitud)

                video_id = info.get('id')

                # Buscar archivo MP4 por video_id (evita encoding issues)
                # sorted() por mtime garantiza el más reciente si hay múltiples
                mp4_files = sorted(
                    self.download_dir.glob(f'*{video_id}.mp4'),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

                if mp4_files:
                    final_path = mp4_files[0]  # El más reciente
                    self.logger.info(f"✅ Descargado: {final_path}")
                    return str(final_path)
                else:
                    # Fallback: buscar cualquier MP4 descargado recientemente
                    # (por si el video_id cambió o algún otro edge case)
                    all_mp4s = sorted(
                        self.download_dir.glob('*.mp4'),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )

                    if all_mp4s:
                        final_path = all_mp4s[0]
                        self.logger.info(f"✅ Descargado (fallback): {final_path}")
                        return str(final_path)
                    else:
                        self.logger.error(f"No encuentro archivo MP4 para video_id: {video_id}")
                        return None

        except yt_dlp.utils.DownloadError as e:
            self.logger.error(f"❌ Error de descarga: {e}")
            return None

        except Exception as e:
            self.logger.error(f"❌ Error inesperado: {e}")
            return None


    def download_audio_only(self, url: str) -> Optional[str]:
        """
        Descargo solo el audio en MP3
        Lo voy a usar después para transcripción
        """
        if not self.validate_url(url):
            return None

        try:
            video_id = self._extract_video_id(url)
            outtmpl = str(self.download_dir / "%(title)s_%(id)s.%(ext)s")

            # Opciones para solo audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
                'progress_hooks': [self._progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                # Manejo robusto de conexión (SSL + reintentos)
                'socket_timeout': 30,
                'retries': 3,
            }

            self.logger.info(f"🎵 Descargando audio: {url}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info.get('id')

                # Mismo fix que download(): buscar por video_id para evitar encoding issues
                mp3_files = sorted(
                    self.download_dir.glob(f'*{video_id}.mp3'),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

                if mp3_files:
                    final_path = mp3_files[0]
                    self.logger.info(f"✅ Audio: {final_path}")
                    return str(final_path)
                else:
                    # Fallback: buscar cualquier MP3 reciente
                    all_mp3s = sorted(
                        self.download_dir.glob('*.mp3'),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )

                    if all_mp3s:
                        final_path = all_mp3s[0]
                        self.logger.info(f"✅ Audio (fallback): {final_path}")
                        return str(final_path)
                    else:
                        self.logger.error(f"No encuentro archivo MP3 para video_id: {video_id}")
                        return None

        except Exception as e:
            self.logger.error(f"Error: {e}")
            return None


# Función helper para uso rápido sin instanciar la clase
def download_video(url: str, quality: str = "best") -> Optional[str]:
    """
    Atajo rápido: creo el downloader y descargo de una
    """
    downloader = YoutubeDownloader()
    return downloader.download(url, quality=quality)
