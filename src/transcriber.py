# -*- coding: utf-8 -*-
"""
Transcriber - Convierte audio de video a texto con timestamps

Usa WhisperX para obtener transcripciones precisas que después
me permiten detectar dónde cortar los clips
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, List
import whisperx
import gc
import torch

from .utils.logger import setup_logger


class Transcriber:
    """
    Manejo la transcripción de videos usando WhisperX

    WhisperX me da timestamps super precisos (nivel de palabra)
    que son críticos para generar buenos clips después
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "int8"
    ):
        """
        Inicializo el transcriber

        Args:
            model_size: Tamaño del modelo Whisper
                - tiny: más rápido, menos preciso
                - base: balance (RECOMENDADO para empezar)
                - small: más preciso, más lento
                - medium: muy preciso, muy lento
                - large-v2: máxima precisión, muy lento

            device: Dispositivo a usar
                - "auto": detecta automáticamente (CPU o MPS para Mac)
                - "cpu": fuerza CPU
                - "mps": fuerza Metal Performance Shaders (Apple Silicon)

            compute_type: Tipo de cómputo
                - "int8": más rápido, usa menos RAM (recomendado)
                - "float16": más preciso pero más lento
        """
        self.logger = setup_logger("transcriber")
        self.model_size = model_size

        # Detecto el device óptimo para tu Mac M4
        # Nota: WhisperX tiene problemas con MPS en Pyannote, usamos CPU
        # El CPU del M4 sigue siendo muy rápido para transcripción
        if device == "auto":
            self.device = "cpu"
            self.logger.info("Usando CPU (optimizado para Apple Silicon M4)")
        else:
            self.device = device
            if device == "mps":
                self.logger.warning("⚠️  MPS puede causar errores. Recomendado: CPU")

        self.compute_type = compute_type

        # Cargo el modelo de Whisper
        self.logger.info(f"Cargando modelo Whisper ({model_size})...")
        self.model = whisperx.load_model(
            self.model_size,
            self.device,
            compute_type=self.compute_type
        )
        self.logger.info("Modelo cargado exitosamente")


    def _extract_audio(self, video_path: str, output_audio_path: str) -> bool:
        """
        Extraigo el audio del video usando ffmpeg

        ¿Por qué extraer el audio?
        - WhisperX solo procesa audio
        - El audio es más ligero que el video completo
        - Puedo guardarlo en temp/ para no reprocesar

        Returns:
            True si se extrajo correctamente, False si falló
        """
        try:
            self.logger.info(f"Extrayendo audio de: {video_path}")

            # Comando ffmpeg para extraer audio
            # -i: input
            # -vn: no video (solo audio)
            # -acodec: codec de audio
            # -ar: sample rate (16000 es óptimo para Whisper)
            # -ac: canales de audio (1 = mono)
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # Sin video
                '-acodec', 'pcm_s16le',  # WAV formato
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Sobrescribir si existe
                output_audio_path
            ]

            # Ejecuto el comando
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                self.logger.info(f"Audio extraído: {output_audio_path}")
                return True
            else:
                self.logger.error(f"Error extrayendo audio: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Excepción al extraer audio: {e}")
            return False


    def transcribe(
        self,
        video_path: str,
        language: Optional[str] = None,
        skip_if_exists: bool = True
    ) -> Optional[str]:
        """
        Transcribo un video completo

        Flujo:
        1. Extraigo audio del video → temp/video_audio.wav
        2. Transcribo con WhisperX
        3. Alinear timestamps (precisión mejorada)
        4. Guardo JSON → temp/video_transcript.json
        5. Retorno ruta del JSON

        Args:
            video_path: Ruta del video a transcribir
            language: Idioma del audio (None = auto-detectar)
                - "es": español
                - "en": inglés
                - None: detecta automáticamente
            skip_if_exists: Si True y ya existe transcripción, no reprocesa

        Returns:
            Ruta del archivo JSON con la transcripción, o None si falla
        """
        video_file = Path(video_path)

        if not video_file.exists():
            self.logger.error(f"Video no encontrado: {video_path}")
            return None

        # Genero nombres de archivos en temp/
        video_id = video_file.stem  # Nombre sin extensión
        audio_path = Path("temp") / f"{video_id}_audio.wav"
        transcript_path = Path("temp") / f"{video_id}_transcript.json"

        # Me aseguro de que temp/ exista
        Path("temp").mkdir(parents=True, exist_ok=True)

        # Si ya existe transcripción y skip_if_exists=True, la retorno
        if skip_if_exists and transcript_path.exists():
            self.logger.info(f"Transcripción ya existe: {transcript_path}")
            return str(transcript_path)

        try:
            # PASO 1: Extraer audio
            if not audio_path.exists():
                if not self._extract_audio(str(video_file), str(audio_path)):
                    return None
            else:
                self.logger.info(f"Audio ya existe: {audio_path}")

            # PASO 2: Transcribir con WhisperX
            self.logger.info("Iniciando transcripción con WhisperX...")
            self.logger.info("Esto puede tardar varios minutos dependiendo de la duración del video")

            audio = whisperx.load_audio(str(audio_path))
            result = self.model.transcribe(
                audio,
                batch_size=16,  # Ajusta según tu RAM
                language=language
            )

            detected_language = result.get("language", "unknown")
            self.logger.info(f"Idioma detectado: {detected_language}")

            # PASO 3: Alinear para timestamps precisos
            self.logger.info("Alineando timestamps para mayor precisión...")

            # Mapeo de nombres de idiomas completos a códigos ISO
            # WhisperX a veces devuelve nombres completos (e.g. 'english')
            # pero load_align_model necesita códigos ISO (e.g. 'en')
            language_code_map = {
                'english': 'en',
                'spanish': 'es',
                'french': 'fr',
                'german': 'de',
                'italian': 'it',
                'portuguese': 'pt',
                'chinese': 'zh',
                'japanese': 'ja',
                'korean': 'ko',
                'russian': 'ru',
                'arabic': 'ar',
                'hindi': 'hi',
            }

            # Convierto a código ISO si es necesario
            align_language = language_code_map.get(detected_language.lower(), detected_language)
            self.logger.info(f"Usando código de idioma para alineación: {align_language}")

            # Cargo modelo de alineación
            model_a, metadata = whisperx.load_align_model(
                language_code=align_language,
                device=self.device
            )

            # Alineo
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )

            # Libero memoria del modelo de alineación
            del model_a
            gc.collect()
            if self.device == "mps":
                torch.mps.empty_cache()

            # PASO 4: Formatear y guardar transcripción
            transcript_data = {
                "video_id": video_id,
                "video_path": str(video_file),
                "audio_path": str(audio_path),
                "language": detected_language,
                "segments": result["segments"],
                "word_segments": result.get("word_segments", [])
            }

            # Guardo como JSON
            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Transcripción guardada: {transcript_path}")
            self.logger.info(f"Total de segmentos: {len(result['segments'])}")

            return str(transcript_path)

        except Exception as e:
            self.logger.error(f"Error durante transcripción: {e}")
            return None


    def load_transcript(self, transcript_path: str) -> Optional[Dict]:
        """
        Cargo una transcripción ya existente

        Útil cuando ya transcribí antes y solo quiero leer el JSON
        """
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando transcripción: {e}")
            return None


    def get_transcript_summary(self, transcript_path: str) -> Optional[Dict]:
        """
        Obtengo un resumen de la transcripción sin cargar todo

        Útil para mostrar info rápida en la UI
        """
        transcript = self.load_transcript(transcript_path)

        if not transcript:
            return None

        segments = transcript.get("segments", [])

        if not segments:
            return None

        # Calculo duración total
        last_segment = segments[-1]
        total_duration = last_segment.get("end", 0)

        # Cuento palabras totales
        total_words = sum(len(seg.get("text", "").split()) for seg in segments)

        return {
            "language": transcript.get("language"),
            "num_segments": len(segments),
            "total_duration": total_duration,
            "total_words": total_words,
            "first_text": segments[0].get("text", "")[:100] + "..." if segments else ""
        }


# Función helper para uso rápido
def transcribe_video(
    video_path: str,
    model_size: str = "base",
    language: Optional[str] = None
) -> Optional[str]:
    """
    Función de conveniencia para transcribir rápidamente

    Ejemplo:
        transcript_path = transcribe_video("downloads/video.mp4")
    """
    transcriber = Transcriber(model_size=model_size)
    return transcriber.transcribe(video_path, language=language)
