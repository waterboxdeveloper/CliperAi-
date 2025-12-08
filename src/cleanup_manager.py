# -*- coding: utf-8 -*-
"""
Cleanup Manager - Gestiona eliminación de artifacts del proyecto

DECISIÓN ARQUITECTÓNICA:
- Módulo independiente (no integrado en StateManager)
- Responsabilidad única: gestión de filesystem cleanup
- Integración con StateManager para mantener state sincronizado

Responsabilidades:
- Listar artifacts existentes (videos, transcripts, clips, outputs)
- Eliminar artifacts de forma segura
- Actualizar state después de eliminación
- Dry run mode para simular sin eliminar
"""

from pathlib import Path
from typing import Dict, List, Optional
import shutil
from rich.console import Console
from rich.table import Table

from src.utils.logger import get_logger
from src.utils.state_manager import StateManager

logger = get_logger(__name__)


class CleanupManager:
    """
    Gestiona cleanup de artifacts del proyecto CLIPER

    ARQUITECTURA:
    - Se integra con StateManager (source of truth)
    - Opera sobre filesystem (downloads/, temp/, output/)
    - Actualiza state después de cada operación
    - Safety: confirmación requerida, dry run mode

    Example:
        >>> manager = CleanupManager()
        >>> artifacts = manager.get_video_artifacts("video_ABC123")
        >>> manager.delete_video_artifacts("video_ABC123", ["output"])
    """

    def __init__(
        self,
        downloads_dir: str = "downloads",
        temp_dir: str = "temp",
        output_dir: str = "output"
    ):
        """
        Inicializa CleanupManager

        Args:
            downloads_dir: Directorio de videos descargados
            temp_dir: Directorio de archivos temporales (transcripts, clips)
            output_dir: Directorio de clips exportados
        """
        self.downloads_dir = Path(downloads_dir)
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)

        self.state_manager = StateManager()
        self.console = Console()

        logger.debug(
            f"CleanupManager initialized: "
            f"downloads={self.downloads_dir}, "
            f"temp={self.temp_dir}, "
            f"output={self.output_dir}"
        )

    def get_video_artifacts(self, video_key: str) -> Dict[str, Dict]:
        """
        Retorna todos los artifacts de un video específico

        DECISIÓN: Estructura de datos con metadata completa
        - Incluye path, exists, size, type
        - Permite decisiones informadas (mostrar tamaños al usuario)

        Args:
            video_key: Clave del video en state (ej: "video_name_ID")

        Returns:
            Dict con paths y metadata de cada artifact:
            {
                'download': {'path': Path, 'size': int, 'exists': bool, 'type': str},
                'transcript': {...},
                'clips_metadata': {...},
                'output': {...}
            }
        """
        artifacts = {}

        # Obtener info del state
        state = self.state_manager.get_all_videos()
        video_state = state.get(video_key, {})

        if not video_state:
            logger.warning(f"Video {video_key} not found in state")
            return artifacts

        # 1. Downloaded video
        filename = video_state.get('filename')
        if filename:
            download_path = self.downloads_dir / filename
            artifacts['download'] = {
                'path': download_path,
                'exists': download_path.exists(),
                'size': download_path.stat().st_size if download_path.exists() else 0,
                'type': 'video'
            }

        # 2. Transcript
        transcript_path = video_state.get('transcript_path')
        if transcript_path:
            transcript_path = Path(transcript_path)
            artifacts['transcript'] = {
                'path': transcript_path,
                'exists': transcript_path.exists(),
                'size': transcript_path.stat().st_size if transcript_path.exists() else 0,
                'type': 'json'
            }

        # 3. Clips metadata
        clips_path_str = video_state.get('clips_metadata_path')
        if clips_path_str:
            clips_path = Path(clips_path_str)
            artifacts['clips_metadata'] = {
                'path': clips_path,
                'exists': clips_path.exists(),
                'size': clips_path.stat().st_size if clips_path.exists() else 0,
                'type': 'json'
            }

        # 4. Exported clips (directorio completo)
        output_clips = video_state.get('exported_clips', [])
        if output_clips or video_state.get('clips_generated'):
            # Calcular tamaño total del directorio de outputs
            output_video_dir = self.output_dir / video_key
            total_size = 0
            clip_count = 0

            if output_video_dir.exists():
                for clip_file in output_video_dir.rglob('*.mp4'):
                    if clip_file.exists():
                        total_size += clip_file.stat().st_size
                        clip_count += 1

            artifacts['output'] = {
                'path': output_video_dir,
                'exists': output_video_dir.exists(),
                'size': total_size,
                'type': 'directory',
                'clip_count': clip_count
            }

        # 5. Temporary files (orphaned *_temp.mp4 files from interrupted exports)
        # DECISIÓN: Detectar archivos temporales huérfanos para cleanup
        # - Estos archivos se generan durante face tracking
        # - Normalmente se eliminan automáticamente, pero pueden quedar si hay interrupciones
        # - Pueden acumular espacio significativo (17MB c/u)
        temp_files = []
        temp_total_size = 0

        output_video_dir = self.output_dir / video_key
        if output_video_dir.exists():
            for temp_file in output_video_dir.glob('*_temp.mp4'):
                if temp_file.exists():
                    temp_files.append(temp_file)
                    temp_total_size += temp_file.stat().st_size

        if temp_files:
            artifacts['temp_files'] = {
                'path': temp_files,  # Lista de paths
                'exists': True,
                'size': temp_total_size,
                'type': 'temp_videos',
                'file_count': len(temp_files)
            }

        return artifacts

    def delete_video_artifacts(
        self,
        video_key: str,
        artifact_types: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> Dict[str, bool]:
        """
        Elimina artifacts específicos de un video

        DECISIÓN: Granularidad + Safety
        - Permite eliminar tipos específicos (no todo-o-nada)
        - Dry run para simular sin riesgo
        - State se actualiza automáticamente

        Args:
            video_key: Clave del video
            artifact_types: Lista de tipos a eliminar: ['download', 'transcript', 'clips_metadata', 'output', 'temp_files']
                           Si None, elimina TODO
            dry_run: Si True, solo simula (no elimina nada)

        Returns:
            Dict con resultado de cada eliminación: {'download': True, 'transcript': False, ...}
        """
        if artifact_types is None:
            artifact_types = ['download', 'transcript', 'clips_metadata', 'output', 'temp_files']

        artifacts = self.get_video_artifacts(video_key)
        results = {}

        for artifact_type in artifact_types:
            artifact_info = artifacts.get(artifact_type)

            if not artifact_info:
                logger.debug(f"No {artifact_type} artifact for {video_key}")
                results[artifact_type] = True  # Nada que eliminar = éxito
                continue

            artifact_path = artifact_info['path']

            if not artifact_info['exists']:
                logger.warning(f"{artifact_type} path doesn't exist: {artifact_path}")
                results[artifact_type] = True  # Ya no existe = éxito
                continue

            # Dry run: solo reportar
            if dry_run:
                size_mb = artifact_info['size'] / 1024 / 1024
                logger.info(f"[DRY RUN] Would delete {artifact_type}: {artifact_path} ({size_mb:.2f} MB)")
                results[artifact_type] = True
                continue

            # Eliminar
            try:
                if artifact_info['type'] == 'directory':
                    shutil.rmtree(artifact_path)
                    logger.info(
                        f"Deleted directory {artifact_path} "
                        f"({artifact_info.get('clip_count', 0)} clips)"
                    )
                else:
                    artifact_path.unlink()
                    logger.info(f"Deleted {artifact_path}")

                results[artifact_type] = True

            except PermissionError as e:
                logger.error(f"Permission denied deleting {artifact_path}: {e}")
                results[artifact_type] = False
            except Exception as e:
                logger.error(f"Failed to delete {artifact_path}: {e}")
                results[artifact_type] = False

        # Actualizar state si no es dry run
        if not dry_run and any(results.values()):
            self._update_state_after_cleanup(video_key, artifact_types, results)

        return results

    def _update_state_after_cleanup(
        self,
        video_key: str,
        deleted_types: List[str],
        results: Dict[str, bool]
    ):
        """
        Actualiza project_state.json después de eliminar artifacts

        DECISIÓN: State debe reflejar filesystem real
        - Marca stages como no completados si archivos eliminados
        - Elimina video del state si TODO fue eliminado
        - Sincronización explícita (no automática)
        """
        # Acceder al state interno de StateManager
        if video_key not in self.state_manager.state:
            logger.warning(f"Video {video_key} not in state, skipping update")
            return

        video_state = self.state_manager.state[video_key]

        # Marcar como no completado según lo eliminado
        if 'download' in deleted_types and results.get('download'):
            video_state['downloaded'] = False
            video_state['filename'] = None
            logger.debug(f"Marked {video_key} as not downloaded in state")

        if 'transcript' in deleted_types and results.get('transcript'):
            video_state['transcribed'] = False
            video_state['transcript_path'] = None
            video_state['transcription_path'] = None  # Legacy field
            logger.debug(f"Marked {video_key} as not transcribed in state")

        if 'clips_metadata' in deleted_types and results.get('clips_metadata'):
            video_state['clips_generated'] = False
            video_state['clips'] = []
            video_state['clips_metadata_path'] = None
            logger.debug(f"Marked {video_key} clips as not generated in state")

        if 'output' in deleted_types and results.get('output'):
            video_state['exported_clips'] = []
            logger.debug(f"Cleared exported clips for {video_key} in state")

        # Si eliminamos TODO, remover video del state completamente
        all_types = ['download', 'transcript', 'clips_metadata', 'output']
        if all(t in deleted_types for t in all_types):
            del self.state_manager.state[video_key]
            logger.info(f"Removed {video_key} from state (all artifacts deleted)")
        else:
            self.state_manager.state[video_key] = video_state

        # Persistir cambios
        self.state_manager._save_state()

    def delete_all_project_data(self, dry_run: bool = False) -> Dict[str, bool]:
        """
        Elimina TODOS los artifacts del proyecto (fresh start)

        DECISIÓN: Operación nuclear con confirmación externa
        - Esta función NO pide confirmación (responsabilidad del caller)
        - Elimina directorios completos y los recrea vacíos
        - Reset total de state
        - ESPECÍFICO: Limpia archivos temporales de caché, FFmpeg, etc.

        Args:
            dry_run: Si True, solo simula

        Returns:
            Dict con resultados: {'downloads': True, 'temp': True, 'output': True, 'cache': True, 'state': True}
        """
        results = {}

        directories = {
            'downloads': self.downloads_dir,
            'temp': self.temp_dir,
            'output': self.output_dir
        }

        for dir_name, dir_path in directories.items():
            if not dir_path.exists():
                logger.info(f"{dir_name}/ doesn't exist (already clean)")
                results[dir_name] = True
                continue

            # Calcular tamaño antes de eliminar
            total_size = 0
            try:
                total_size = sum(
                    f.stat().st_size
                    for f in dir_path.rglob('*')
                    if f.is_file()
                )
            except Exception as e:
                logger.warning(f"Could not calculate size of {dir_name}/: {e}")

            size_mb = total_size / 1024 / 1024

            if dry_run:
                logger.info(f"[DRY RUN] Would delete {dir_name}/ ({size_mb:.2f} MB)")
                results[dir_name] = True
                continue

            try:
                shutil.rmtree(dir_path)
                dir_path.mkdir(parents=True, exist_ok=True)  # Recrear vacío
                logger.info(f"Cleaned {dir_name}/ ({size_mb:.2f} MB freed)")
                results[dir_name] = True
            except PermissionError as e:
                logger.error(f"Permission denied cleaning {dir_name}/: {e}")
                results[dir_name] = False
            except Exception as e:
                logger.error(f"Failed to clean {dir_name}/: {e}")
                results[dir_name] = False

        # Limpiar caché y archivos temporales residuales
        if not dry_run:
            results['cache'] = self._clean_cache_and_residuals()
        else:
            logger.info("[DRY RUN] Would clean cache and residual temporary files")
            results['cache'] = True

        # Reset state
        if not dry_run:
            try:
                self.state_manager.state = {}
                self.state_manager._save_state()
                logger.info("Reset project state")
                results['state'] = True
            except Exception as e:
                logger.error(f"Failed to reset state: {e}")
                results['state'] = False
        else:
            logger.info("[DRY RUN] Would reset project state")
            results['state'] = True

        return results

    def _clean_cache_and_residuals(self) -> bool:
        """
        Limpia caché y archivos temporales residuales que pueden interferir

        ESPECÍFICO:
        - Archivos de caché de FFmpeg
        - Archivos lock (.lock)
        - Archivos temporales en /tmp
        - Copys sin SRT (huérfanos)
        - Logs antiguos
        - Temporales de video_exporter (temp_*.mp4, temp_reframed_*.mp4)

        Returns:
            bool: True si limpió exitosamente
        """
        try:
            cleaned_count = 0
            cleaned_size = 0

            # 1. Limpiar archivos lock en temp/
            lock_patterns = ['*.lock', '.lock']
            for pattern in lock_patterns:
                for lock_file in self.temp_dir.glob(pattern):
                    try:
                        size = lock_file.stat().st_size
                        lock_file.unlink()
                        cleaned_count += 1
                        cleaned_size += size
                        logger.debug(f"Removed lock file: {lock_file.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove lock file {lock_file}: {e}")

            # 2. Limpiar archivos temporales de FFmpeg/video_exporter
            # (Estos NO deberían estar acá si todo limpió bien, pero por si acaso)
            temp_patterns = ['temp_*.mp4', 'temp_reframed_*.mp4', '*_temp.mp4']
            for pattern in temp_patterns:
                for temp_file in self.output_dir.rglob(pattern):
                    try:
                        size = temp_file.stat().st_size
                        temp_file.unlink()
                        cleaned_count += 1
                        cleaned_size += size
                        logger.debug(f"Removed residual temp file: {temp_file.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove temp file {temp_file}: {e}")

            # 3. Limpiar SRTs huérfanos (clips sin .mp4 correspondiente)
            for srt_file in self.output_dir.rglob('*.srt'):
                try:
                    mp4_file = srt_file.with_suffix('.mp4')
                    if not mp4_file.exists():
                        size = srt_file.stat().st_size
                        srt_file.unlink()
                        cleaned_count += 1
                        cleaned_size += size
                        logger.debug(f"Removed orphaned SRT: {srt_file.name}")
                except Exception as e:
                    logger.warning(f"Could not process SRT file {srt_file}: {e}")

            # 4. Limpiar __pycache__ solo en src/ y tests/ (caché Python compilado)
            # ESPECÍFICO: Solo en directorios conocidos donde realmente se genera
            source_dirs = [
                self.downloads_dir.parent / 'src',
                self.downloads_dir.parent / 'tests'
            ]

            for source_dir in source_dirs:
                if source_dir.exists():
                    for pycache_dir in source_dir.rglob('__pycache__'):
                        try:
                            shutil.rmtree(pycache_dir)
                            cleaned_count += 1
                            logger.debug(f"Removed Python cache: {pycache_dir}")
                        except Exception as e:
                            logger.warning(f"Could not remove __pycache__: {e}")

            # 5. Limpiar .DS_Store solo en output/ (residuales de macOS)
            # ESPECÍFICO: Solo donde puede quedar basura de Finder
            for ds_store in self.output_dir.rglob('.DS_Store'):
                try:
                    size = ds_store.stat().st_size
                    ds_store.unlink()
                    cleaned_count += 1
                    cleaned_size += size
                    logger.debug(f"Removed macOS cache: {ds_store.name}")
                except Exception as e:
                    logger.warning(f"Could not remove .DS_Store: {e}")

            cleaned_size_mb = cleaned_size / 1024 / 1024
            if cleaned_count > 0:
                logger.info(f"Cleaned {cleaned_count} cache/residual files ({cleaned_size_mb:.2f} MB)")
            else:
                logger.info("No cache or residual files found")

            return True

        except Exception as e:
            logger.error(f"Error cleaning cache and residuals: {e}")
            return False

    def display_cleanable_artifacts(self, video_key: Optional[str] = None):
        """
        Muestra tabla de artifacts que se pueden limpiar

        DECISIÓN: Rich table para UX profesional
        - Tamaños en MB para decisiones informadas
        - Total por video para ver impacto
        - Visual claro de qué se puede eliminar

        Args:
            video_key: Si se provee, muestra solo ese video. Si None, muestra todos.
        """
        state = self.state_manager.get_all_videos()

        if video_key:
            video_keys = [video_key] if video_key in state else []
        else:
            video_keys = list(state.keys())

        if not video_keys:
            self.console.print("[yellow]No videos found in project[/yellow]")
            return

        table = Table(title="Cleanable Artifacts")
        table.add_column("Video", style="cyan", no_wrap=False)
        table.add_column("Download", justify="right")
        table.add_column("Transcript", justify="right")
        table.add_column("Clips Meta", justify="right")
        table.add_column("Output", justify="right")
        table.add_column("Total", justify="right", style="bold")

        for vkey in video_keys:
            artifacts = self.get_video_artifacts(vkey)

            def format_size(size_bytes):
                if size_bytes == 0:
                    return "-"
                mb = size_bytes / 1024 / 1024
                if mb < 0.1:
                    return f"{size_bytes / 1024:.1f} KB"
                return f"{mb:.1f} MB"

            download_size = artifacts.get('download', {}).get('size', 0)
            transcript_size = artifacts.get('transcript', {}).get('size', 0)
            clips_size = artifacts.get('clips_metadata', {}).get('size', 0)
            output_size = artifacts.get('output', {}).get('size', 0)

            total_size = download_size + transcript_size + clips_size + output_size

            # Nombre corto del video (primeras 40 chars)
            video_name = vkey[:40] + "..." if len(vkey) > 40 else vkey

            table.add_row(
                video_name,
                format_size(download_size),
                format_size(transcript_size),
                format_size(clips_size),
                format_size(output_size),
                format_size(total_size)
            )

        self.console.print(table)
