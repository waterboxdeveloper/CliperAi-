# -*- coding: utf-8 -*-
"""
Local Video Importer - Importa videos locales desde ~/Downloads/

ARQUITECTURA:
- Detecta automáticamente .mp4, .mov, .mkv, .avi en ~/Downloads/
- Copia a downloads/ del proyecto
- Registra en state
- Cross-platform (macOS, Linux, Windows)
"""

from pathlib import Path
from typing import List, Dict, Optional
import shutil
import platform

from src.utils.logger import get_logger
from src.utils.state_manager import StateManager

logger = get_logger(__name__)


class LocalVideoImporter:
    """
    Importa videos locales desde la carpeta Downloads del sistema

    DECISIÓN: Auto-detectar carpeta Downloads por SO
    - macOS: ~/Downloads
    - Linux: ~/Downloads
    - Windows: %USERPROFILE%\Downloads

    VALIDACIONES:
    - Solo extensiones de video conocidas
    - Verificar que no exista en proyecto ya
    - Validar permisos de lectura
    """

    # Extensiones de video soportadas
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.flv', '.wmv', '.webm'}

    def __init__(self, downloads_dir: str = "downloads"):
        """
        Inicializa LocalVideoImporter

        Args:
            downloads_dir: Ruta a carpeta downloads del proyecto
        """
        self.project_downloads_dir = Path(downloads_dir)
        self.system_downloads_dir = self._detect_downloads_folder()
        self.state_manager = StateManager()

        logger.debug(
            f"LocalVideoImporter initialized: "
            f"system_downloads={self.system_downloads_dir}, "
            f"project_downloads={self.project_downloads_dir}"
        )

    def _detect_downloads_folder(self) -> Path:
        """
        Detecta carpeta Downloads según el SO

        Returns:
            Path a la carpeta Downloads del usuario
        """
        home = Path.home()
        system = platform.system()

        # Standard location para todos los SO
        downloads = home / "Downloads"

        if downloads.exists():
            logger.debug(f"Detected {system} Downloads folder: {downloads}")
            return downloads

        # Fallback (unlikely)
        logger.warning(f"Could not detect Downloads folder for {system}")
        return home / "Downloads"  # Retornar anyway

    def list_available_videos(self, limit: int = 15) -> List[Dict]:
        """
        Lista videos disponibles en ~/Downloads/

        DECISIÓN: Limitar a últimos N videos para no abrumar al usuario
        - Ordenados por fecha modificada (más recientes primero)
        - Solo extensiones de video válidas

        Args:
            limit: Máximo número de videos a mostrar

        Returns:
            Lista de dicts con: name, path, size_mb, modified_time
        """
        if not self.system_downloads_dir.exists():
            logger.warning(f"Downloads folder doesn't exist: {self.system_downloads_dir}")
            return []

        videos = []

        try:
            # Buscar archivos de video
            for video_file in self.system_downloads_dir.glob('*'):
                if not video_file.is_file():
                    continue

                # Verificar extensión
                if video_file.suffix.lower() not in self.VIDEO_EXTENSIONS:
                    continue

                try:
                    size_bytes = video_file.stat().st_size
                    size_mb = size_bytes / 1024 / 1024
                    mtime = video_file.stat().st_mtime

                    videos.append({
                        'name': video_file.name,
                        'path': video_file,
                        'size_mb': size_mb,
                        'mtime': mtime
                    })
                except Exception as e:
                    logger.warning(f"Could not get info for {video_file}: {e}")

            # Ordenar por fecha modificada (más recientes primero)
            videos = sorted(videos, key=lambda x: x['mtime'], reverse=True)

            # Limitar
            if len(videos) > limit:
                logger.info(f"Found {len(videos)} videos, showing {limit} most recent")
                videos = videos[:limit]

            logger.info(f"Found {len(videos)} videos in {self.system_downloads_dir}")
            return videos

        except PermissionError as e:
            logger.error(f"Permission denied reading Downloads folder: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing videos: {e}")
            return []

    def import_video(self, video_path: Path, state_manager: Optional[StateManager] = None) -> Optional[str]:
        """
        Importa un video a la carpeta downloads del proyecto

        PASOS:
        1. Validar que el archivo existe y es readable
        2. Validar que no existe ya en proyecto
        3. Copiar a downloads/
        4. Registrar en state
        5. Retornar path del proyecto

        Args:
            video_path: Path al archivo en ~/Downloads/
            state_manager: StateManager (si None, crea uno nuevo)

        Returns:
            Path al video en proyecto, o None si falló
        """
        # Validar que existe
        if not video_path.exists():
            logger.error(f"Video file doesn't exist: {video_path}")
            return None

        # Validar que es archivo
        if not video_path.is_file():
            logger.error(f"Path is not a file: {video_path}")
            return None

        # Validar extensión
        if video_path.suffix.lower() not in self.VIDEO_EXTENSIONS:
            logger.error(f"Invalid video extension: {video_path.suffix}")
            return None

        # Crear directorio downloads si no existe
        try:
            self.project_downloads_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create downloads directory: {e}")
            return None

        # Ruta destino
        dest_path = self.project_downloads_dir / video_path.name

        # Validar que no existe ya
        if dest_path.exists():
            logger.warning(f"Video already exists in project: {dest_path}")
            return None

        # Copiar archivo
        try:
            logger.info(f"Copying {video_path.name} to project...")
            shutil.copy2(video_path, dest_path)
            logger.info(f"Video copied successfully: {dest_path}")
        except PermissionError as e:
            logger.error(f"Permission denied copying file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error copying file: {e}")
            return None

        # Registrar en state
        try:
            sm = state_manager or self.state_manager
            video_id = dest_path.stem  # Nombre sin extensión

            sm.register_video(
                video_id=video_id,
                filename=dest_path.name,
                content_type="local_import",  # Marcar como importación local
                source="local"  # Metadata extra
            )

            logger.info(f"Registered in state: {video_id}")
        except Exception as e:
            logger.error(f"Error registering in state: {e}")
            # No fallar - el video fue copiado, pero no está registrado
            return None

        return str(dest_path)

    def validate_video_file(self, video_path: Path) -> tuple[bool, str]:
        """
        Valida un archivo de video

        Returns:
            (is_valid, error_message)
        """
        # Existe
        if not video_path.exists():
            return False, "Archivo no encontrado"

        # Es archivo
        if not video_path.is_file():
            return False, "No es un archivo"

        # Extensión válida
        if video_path.suffix.lower() not in self.VIDEO_EXTENSIONS:
            return False, f"Extensión no soportada: {video_path.suffix}"

        # Readable
        if not video_path.stat().st_mode & 0o400:
            return False, "Permisos insuficientes para leer"

        return True, ""
