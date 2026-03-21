# Step 01: CleanupManager Module

**Goal:** Crear módulo `src/cleanup_manager.py` con lógica de eliminación de artifacts

---

## 📋 Tasks

### Task 1.1: Crear estructura básica del CleanupManager

- [ ] Crear archivo `src/cleanup_manager.py`
- [ ] Importar dependencias necesarias
- [ ] Definir clase `CleanupManager` con `__init__`

**Código base:**

```python
# src/cleanup_manager.py
"""
Cleanup Manager - Gestiona eliminación de artifacts del proyecto

Responsabilidades:
- Listar artifacts existentes (videos, transcripts, clips, outputs)
- Eliminar artifacts de forma segura
- Integrar con StateManager para actualizar state
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
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
    """

    def __init__(
        self,
        downloads_dir: str = "downloads",
        temp_dir: str = "temp",
        output_dir: str = "output"
    ):
        self.downloads_dir = Path(downloads_dir)
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)

        self.state_manager = StateManager()
        self.console = Console()
```

---

### Task 1.2: Implementar método para listar artifacts

- [ ] Crear método `get_video_artifacts(video_key: str) -> Dict`
- [ ] Listar todos los archivos asociados a un video
- [ ] Calcular tamaños de archivos

**Código:**

```python
def get_video_artifacts(self, video_key: str) -> Dict[str, Dict]:
    """
    Retorna todos los artifacts de un video específico

    Args:
        video_key: Clave del video en state (ej: "video_name_ID")

    Returns:
        Dict con paths y metadata de cada artifact:
        {
            'download': {'path': Path, 'size': int, 'exists': bool},
            'transcript': {...},
            'clips': {...},
            'output': {...}
        }
    """
    artifacts = {}

    # Obtener info del state
    state = self.state_manager.get_state()
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
    if output_clips:
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

    return artifacts
```

---

### Task 1.3: Implementar método para eliminar artifacts

- [ ] Crear método `delete_video_artifacts(video_key: str, artifact_types: List[str])`
- [ ] Eliminar archivos seleccionados de forma segura
- [ ] Actualizar state después de eliminación

**Código:**

```python
def delete_video_artifacts(
    self,
    video_key: str,
    artifact_types: Optional[List[str]] = None,
    dry_run: bool = False
) -> Dict[str, bool]:
    """
    Elimina artifacts específicos de un video

    Args:
        video_key: Clave del video
        artifact_types: Lista de tipos a eliminar: ['download', 'transcript', 'clips_metadata', 'output']
                       Si None, elimina TODO
        dry_run: Si True, solo simula (no elimina nada)

    Returns:
        Dict con resultado de cada eliminación: {'download': True, 'transcript': False, ...}
    """
    if artifact_types is None:
        artifact_types = ['download', 'transcript', 'clips_metadata', 'output']

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
                logger.info(f"✓ Deleted directory {artifact_path} ({artifact_info.get('clip_count', 0)} clips)")
            else:
                artifact_path.unlink()
                logger.info(f"✓ Deleted {artifact_path}")

            results[artifact_type] = True

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
    """
    state = self.state_manager.get_state()

    if video_key not in state:
        return

    video_state = state[video_key]

    # Marcar como no completado según lo eliminado
    if 'download' in deleted_types and results.get('download'):
        video_state['downloaded'] = False
        video_state['filename'] = None

    if 'transcript' in deleted_types and results.get('transcript'):
        video_state['transcribed'] = False
        video_state['transcript_path'] = None

    if 'clips_metadata' in deleted_types and results.get('clips_metadata'):
        video_state['clips_generated'] = False
        video_state['clips'] = []
        video_state['clips_metadata_path'] = None

    if 'output' in deleted_types and results.get('output'):
        video_state['exported_clips'] = []

    # Si eliminamos TODO, remover video del state completamente
    if all(t in deleted_types for t in ['download', 'transcript', 'clips_metadata', 'output']):
        del state[video_key]
        logger.info(f"Removed {video_key} from state (all artifacts deleted)")
    else:
        state[video_key] = video_state

    self.state_manager.save_state(state)
```

---

### Task 1.4: Implementar cleanup total del proyecto

- [ ] Crear método `delete_all_project_data(dry_run: bool)`
- [ ] Limpiar downloads/, temp/, output/ completos
- [ ] Reset state a {}

**Código:**

```python
def delete_all_project_data(self, dry_run: bool = False) -> Dict[str, bool]:
    """
    Elimina TODOS los artifacts del proyecto (fresh start)

    Args:
        dry_run: Si True, solo simula

    Returns:
        Dict con resultados: {'downloads': True, 'temp': True, 'output': True, 'state': True}
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
        total_size = sum(
            f.stat().st_size
            for f in dir_path.rglob('*')
            if f.is_file()
        )
        size_mb = total_size / 1024 / 1024

        if dry_run:
            logger.info(f"[DRY RUN] Would delete {dir_name}/ ({size_mb:.2f} MB)")
            results[dir_name] = True
            continue

        try:
            shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)  # Recrear vacío
            logger.info(f"✓ Cleaned {dir_name}/ ({size_mb:.2f} MB freed)")
            results[dir_name] = True
        except Exception as e:
            logger.error(f"Failed to clean {dir_name}/: {e}")
            results[dir_name] = False

    # Reset state
    if not dry_run:
        self.state_manager.save_state({})
        logger.info("✓ Reset project state")
        results['state'] = True
    else:
        logger.info("[DRY RUN] Would reset project state")
        results['state'] = True

    return results
```

---

### Task 1.5: Implementar helper para mostrar artifacts

- [ ] Crear método `display_cleanable_artifacts(video_key: Optional[str])`
- [ ] Usar Rich table para mostrar artifacts con tamaños

**Código:**

```python
def display_cleanable_artifacts(self, video_key: Optional[str] = None):
    """
    Muestra tabla de artifacts que se pueden limpiar

    Args:
        video_key: Si se provee, muestra solo ese video. Si None, muestra todos.
    """
    state = self.state_manager.get_state()

    if video_key:
        video_keys = [video_key] if video_key in state else []
    else:
        video_keys = list(state.keys())

    if not video_keys:
        self.console.print("[yellow]No videos found in project[/yellow]")
        return

    table = Table(title="Cleanable Artifacts")
    table.add_column("Video", style="cyan")
    table.add_column("Download", justify="right")
    table.add_column("Transcript", justify="right")
    table.add_column("Clips Meta", justify="right")
    table.add_column("Output", justify="right")
    table.add_column("Total", justify="right", style="bold")

    for vkey in video_keys:
        artifacts = self.get_video_artifacts(vkey)

        def format_size(size_bytes):
            mb = size_bytes / 1024 / 1024
            return f"{mb:.1f} MB" if mb > 0 else "-"

        download_size = artifacts.get('download', {}).get('size', 0)
        transcript_size = artifacts.get('transcript', {}).get('size', 0)
        clips_size = artifacts.get('clips_metadata', {}).get('size', 0)
        output_size = artifacts.get('output', {}).get('size', 0)

        total_size = download_size + transcript_size + clips_size + output_size

        # Nombre corto del video
        video_name = vkey.split('_')[0][:30]  # Primeras 30 chars

        table.add_row(
            video_name,
            format_size(download_size),
            format_size(transcript_size),
            format_size(clips_size),
            format_size(output_size),
            format_size(total_size)
        )

    self.console.print(table)
```

---

## ✅ Validation Checklist

- [ ] CleanupManager se puede instanciar sin errores
- [ ] `get_video_artifacts()` retorna estructura correcta
- [ ] `delete_video_artifacts()` elimina archivos correctamente
- [ ] State se actualiza después de cleanup
- [ ] `delete_all_project_data()` limpia proyecto completo
- [ ] `display_cleanable_artifacts()` muestra tabla Rich
- [ ] Dry run NO elimina archivos
- [ ] Manejo de errores (permisos, archivos missing)

---

**Next:** `02-cli-integration.md` - Integrar CleanupManager en cliper.py
