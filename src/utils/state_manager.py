# -*- coding: utf-8 -*-
"""
State Manager - Guarda el progreso del pipeline para cada video

Este módulo me permite:
- Saber qué videos ya están descargados
- Saber qué videos ya están transcritos
- Saber qué clips ya generé
- Continuar donde me quedé si cierro el programa
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class StateManager:
    """
    Manejo el estado/progreso de todos los videos en el proyecto

    Guardo un archivo JSON con info de cada video:
    {
        "video_id": {
            "filename": "nombre.mp4",
            "downloaded": true,
            "transcribed": false,
            "transcription_path": null,
            "clips_generated": false,
            "clips": [],
            "last_updated": "2025-10-23 22:30:00"
        }
    }
    """

    def __init__(self, state_file: str = "temp/project_state.json"):
        # Donde guardo el estado del proyecto
        self.state_file = Path(state_file)

        # Me aseguro de que la carpeta temp/ exista
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Cargo el estado actual (o creo uno vacío)
        self.state = self._load_state()


    def _load_state(self) -> Dict:
        """
        Cargo el estado desde el archivo JSON
        Si no existe, retorno un dict vacío
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Si el JSON está corrupto, empiezo de cero
                return {}
        else:
            # Primera vez, archivo no existe
            return {}


    def _save_state(self):
        """
        Guardo el estado actual al archivo JSON
        """
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)


    def register_video(
        self,
        video_id: str,
        filename: str,
        content_type: str = "tutorial",
        preset: Dict = None
    ) -> None:
        """
        Registro un nuevo video en el sistema

        Args:
            video_id: ID único del video
            filename: Nombre del archivo
            content_type: Tipo de contenido (podcast, tutorial, livestream, etc.)
            preset: Preset de configuración completo
        """
        if video_id not in self.state:
            self.state[video_id] = {
                'filename': filename,
                'downloaded': True,
                'transcribed': False,
                'transcription_path': None,
                'transcript_path': None,  # Alias para compatibilidad
                'clips_generated': False,
                'clips': [],
                'clips_metadata_path': None,
                'content_type': content_type,  # Nuevo: tipo de contenido
                'preset': preset if preset else {},  # Nuevo: configuración
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self._save_state()


    def mark_transcribed(self, video_id: str, transcription_path: str) -> None:
        """
        Marco un video como transcrito y guardo la ruta del archivo de transcripción
        """
        if video_id in self.state:
            self.state[video_id]['transcribed'] = True
            self.state[video_id]['transcription_path'] = transcription_path
            self.state[video_id]['transcript_path'] = transcription_path  # Alias
            self.state[video_id]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_state()


    def mark_clips_generated(
        self,
        video_id: str,
        clips: List[Dict],
        clips_metadata_path: Optional[str] = None
    ) -> None:
        """
        Marco que ya generé clips para este video

        Args:
            video_id: ID del video
            clips: Lista de dicts con info de cada clip
            clips_metadata_path: Ruta al JSON con metadata de clips
        """
        if video_id in self.state:
            self.state[video_id]['clips_generated'] = True
            self.state[video_id]['clips'] = clips
            self.state[video_id]['clips_metadata_path'] = clips_metadata_path
            self.state[video_id]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_state()


    def mark_clips_exported(
        self,
        video_id: str,
        exported_paths: List[str],
        aspect_ratio: Optional[str] = None
    ) -> None:
        """
        Marco que ya exporté los clips a archivos de video

        Args:
            video_id: ID del video
            exported_paths: Lista de rutas a los clips exportados
            aspect_ratio: Aspect ratio usado (9:16, 1:1, etc.)
        """
        if video_id in self.state:
            self.state[video_id]['clips_exported'] = True
            self.state[video_id]['exported_clips'] = exported_paths
            self.state[video_id]['export_aspect_ratio'] = aspect_ratio
            self.state[video_id]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_state()


    def get_video_state(self, video_id: str) -> Optional[Dict]:
        """
        Obtengo el estado de un video específico
        Retorno None si el video no está registrado
        """
        return self.state.get(video_id)


    def get_all_videos(self) -> Dict:
        """
        Obtengo todos los videos registrados
        """
        return self.state


    def is_transcribed(self, video_id: str) -> bool:
        """
        Verifico si un video ya está transcrito
        """
        video_state = self.get_video_state(video_id)
        if video_state:
            return video_state.get('transcribed', False)
        return False


    def get_next_step(self, video_id: str) -> str:
        """
        Determino cuál es el siguiente paso para este video

        Retorno: "transcribe", "generate_clips", "export", "done"
        """
        video_state = self.get_video_state(video_id)

        if not video_state:
            return "unknown"

        if not video_state['transcribed']:
            return "transcribe"
        elif not video_state['clips_generated']:
            return "generate_clips"
        elif not video_state.get('clips_exported', False):
            return "export"
        else:
            return "done"


    def clear_video_state(self, video_id: str) -> None:
        """
        Elimino el estado de un video (útil si borro el video)
        """
        if video_id in self.state:
            del self.state[video_id]
            self._save_state()


# Función helper para obtener el state manager global
_state_manager_instance = None

def get_state_manager() -> StateManager:
    """
    Obtengo la instancia global del StateManager
    Patrón Singleton - solo una instancia en todo el programa
    """
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = StateManager()
    return _state_manager_instance
