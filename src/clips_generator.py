# -*- coding: utf-8 -*-
"""
Clips Generator - Detecta automáticamente dónde cortar clips usando ClipsAI

ClipsAI analiza la transcripción y detecta cambios de tema usando
algoritmo TextTiling con BERT embeddings para marcar puntos de corte.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from clipsai import ClipFinder, Transcription

from .utils.logger import setup_logger


class ClipsGenerator:
    """
    Genero clips automáticamente detectando cambios de tema en la transcripción

    Flujo:
    1. Cargo transcripción de WhisperX (temp/video_transcript.json)
    2. La convierto al formato que ClipsAI espera
    3. ClipsAI detecta cambios de tema usando IA
    4. Me retorna timestamps de cada clip
    5. Guardo metadata de clips para editarlos después
    """

    def __init__(
        self,
        min_clip_duration: int = 30,
        max_clip_duration: int = 90
    ):
        """
        Inicializo el generador de clips

        Args:
            min_clip_duration: Duración mínima de cada clip en segundos
                - 30s es ideal para reels/shorts
            max_clip_duration: Duración máxima de cada clip en segundos
                - 90s funciona bien para redes sociales
                - Instagram Reels: max 90s
                - TikTok: max 10min (pero 60s es óptimo)
                - YouTube Shorts: max 60s
        """
        self.logger = setup_logger("clips_generator")

        self.min_clip_duration = min_clip_duration
        self.max_clip_duration = max_clip_duration

        # Creo el ClipFinder de ClipsAI
        # Este es el motor que detecta los cambios de tema
        # NOTE: Para videos largos con pocos cambios de tema (livestreams, charlas),
        # puede que ClipsAI no encuentre suficientes clips con parámetros restrictivos.
        # En ese caso, considera aumentar max_clip_duration o usar cortes por tiempo fijo.
        self.clip_finder = ClipFinder(
            min_clip_duration=min_clip_duration,
            max_clip_duration=max_clip_duration
        )

        self.logger.info(
            f"ClipsGenerator inicializado "
            f"(clips: {min_clip_duration}s - {max_clip_duration}s)"
        )


    def _load_transcript(self, transcript_path: str) -> Optional[Dict]:
        """
        Cargo la transcripción generada por WhisperX

        Formato esperado (generado por transcriber.py):
        {
            "video_id": "video_abc123",
            "language": "es",
            "segments": [
                {"start": 0.0, "end": 5.2, "text": "Hola mundo"},
                {"start": 5.2, "end": 10.1, "text": "Este es un test"}
            ]
        }
        """
        try:
            transcript_file = Path(transcript_path)

            if not transcript_file.exists():
                self.logger.error(f"Transcripción no encontrada: {transcript_path}")
                return None

            with open(transcript_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.logger.info(f"Transcripción cargada: {len(data.get('segments', []))} segmentos")

            return data

        except Exception as e:
            self.logger.error(f"Error cargando transcripción: {e}")
            return None


    def _convert_to_clipsai_format(self, whisperx_data: Dict) -> Optional[Transcription]:
        """
        Convierto la transcripción de WhisperX al formato de ClipsAI

        ClipsAI requiere campos adicionales que WhisperX no genera:
        - time_created: timestamp de creación
        - source_software: "whisperx"
        - num_speakers: número de hablantes
        - char_info: info de caracteres con timestamps

        Construyo estos campos a partir de los segmentos de WhisperX.
        """
        from datetime import datetime

        segments = whisperx_data.get("segments", [])

        if not segments:
            self.logger.error("No hay segmentos en la transcripción")
            return None

        try:
            # Construyo char_info a partir de los segmentos
            # char_info es una lista de caracteres con timestamps
            char_info = []

            for seg in segments:
                words = seg.get("words", [])

                if not words:
                    # Si no hay words, uso el segmento completo
                    text = seg.get("text", "").strip()
                    if text:
                        for char in text:
                            char_info.append({
                                "char": char,
                                "start_time": seg.get("start", 0.0),
                                "end_time": seg.get("end", 0.0),
                                "speaker": "SPEAKER_00"  # Default speaker
                            })
                else:
                    # Si hay words, uso esas para mayor precisión
                    for word_obj in words:
                        word_text = word_obj.get("word", "")
                        word_start = word_obj.get("start", 0.0)
                        word_end = word_obj.get("end", 0.0)

                        for char in word_text:
                            char_info.append({
                                "char": char,
                                "start_time": word_start,
                                "end_time": word_end,
                                "speaker": "SPEAKER_00"  # Default speaker
                            })

            # Construyo el dict con el formato que ClipsAI espera
            clipsai_dict = {
                "time_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "source_software": "whisperx",
                "language": whisperx_data.get("language", "en"),
                "num_speakers": 1,  # WhisperX no hace diarization por defecto
                "char_info": char_info
            }

            # Creo el objeto Transcription
            transcription = Transcription(clipsai_dict)

            self.logger.info(
                f"Transcripción convertida: {len(segments)} segmentos, "
                f"{len(char_info)} caracteres"
            )

            return transcription

        except Exception as e:
            self.logger.error(f"Error creando objeto Transcription: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None


    def _generate_fixed_time_clips(
        self,
        whisperx_data: Dict,
        clip_duration: int,
        max_clips: int = 10
    ) -> Optional[List[Dict]]:
        """
        Genero clips dividiendo el video en segmentos de tiempo fijo

        Útil como fallback cuando ClipsAI no encuentra cambios de tema naturales.
        Ideal para livestreams, charlas largas, o contenido muy homogéneo.

        Args:
            whisperx_data: Datos de transcripción de WhisperX
            clip_duration: Duración de cada clip en segundos
            max_clips: Máximo de clips a generar

        Returns:
            Lista de clips con timestamps fijos
        """
        segments = whisperx_data.get("segments", [])

        if not segments:
            self.logger.error("No hay segmentos en la transcripción")
            return None

        # Calculo duración total
        total_duration = segments[-1].get("end", 0)

        self.logger.info(
            f"Generando clips de tiempo fijo: {clip_duration}s cada uno"
        )
        self.logger.info(f"Duración total: {total_duration:.1f}s")

        formatted_clips = []
        current_time = 0.0
        clip_id = 1

        while current_time < total_duration and clip_id <= max_clips:
            start_time = current_time
            end_time = min(current_time + clip_duration, total_duration)
            duration = end_time - start_time

            # Solo creo el clip si tiene al menos 30 segundos
            if duration >= 30:
                # Extraigo el texto para este rango
                clip_text = self._get_text_for_timerange(
                    whisperx_data,
                    start_time,
                    end_time
                )

                # Preview
                text_preview = (
                    clip_text[:100] + "..."
                    if len(clip_text) > 100
                    else clip_text
                )

                formatted_clips.append({
                    "clip_id": clip_id,
                    "start_time": round(start_time, 2),
                    "end_time": round(end_time, 2),
                    "duration": round(duration, 2),
                    "text_preview": text_preview,
                    "full_text": clip_text,
                    "method": "fixed_time"  # Marco que fue generado por tiempo fijo
                })

                self.logger.info(
                    f"  Clip {clip_id}: {duration:.1f}s "
                    f"({self._format_time(start_time)} → {self._format_time(end_time)})"
                )

                clip_id += 1

            current_time += clip_duration

        self.logger.info(f"✅ {len(formatted_clips)} clips generados (tiempo fijo)")

        return formatted_clips if formatted_clips else None


    def generate_clips(
        self,
        transcript_path: str,
        min_clips: int = 3,
        max_clips: int = 10
    ) -> Optional[List[Dict]]:
        """
        Genero clips detectando automáticamente cambios de tema

        Args:
            transcript_path: Ruta al JSON de transcripción (de WhisperX)
            min_clips: Mínimo de clips esperados (default: 3)
                - Si encuentra menos, avisa pero retorna lo que hay
            max_clips: Máximo de clips a retornar (default: 10)
                - Útil para limitar procesamiento posterior

        Returns:
            Lista de clips con formato:
            [
                {
                    "clip_id": 1,
                    "start_time": 0.0,
                    "end_time": 45.5,
                    "duration": 45.5,
                    "text_preview": "Primeras palabras...",
                    "full_text": "Texto completo del clip"
                },
                ...
            ]

            O None si falla
        """
        self.logger.info(f"Generando clips de: {transcript_path}")

        # PASO 1: Cargo la transcripción de WhisperX
        whisperx_data = self._load_transcript(transcript_path)

        if not whisperx_data:
            return None

        # PASO 2: Convierto al formato que ClipsAI entiende
        clipsai_transcript = self._convert_to_clipsai_format(whisperx_data)

        if not clipsai_transcript:
            return None

        try:
            # PASO 3: Uso ClipsAI para detectar puntos de corte
            self.logger.info("🤖 Analizando transcripción con ClipsAI...")
            self.logger.info("Detectando cambios de tema...")

            # find_clips retorna una lista de objetos Clip
            # Cada Clip tiene: start_time, end_time
            # Nota: debe ser argumento posicional, no keyword
            clips_found = self.clip_finder.find_clips(clipsai_transcript)

            if not clips_found:
                self.logger.warning("ClipsAI no encontró clips válidos")
                self.logger.info(
                    "Posibles razones: "
                    "video muy corto, sin cambios de tema claros, "
                    "o configuración de min/max_duration muy restrictiva"
                )

                # FALLBACK: Uso cortes de tiempo fijo
                self.logger.info("🔄 Usando método de respaldo: cortes de tiempo fijo")

                # Uso la duración máxima configurada como duración de cada clip
                return self._generate_fixed_time_clips(
                    whisperx_data=whisperx_data,
                    clip_duration=self.max_clip_duration,
                    max_clips=max_clips
                )

            self.logger.info(f"✓ ClipsAI detectó {len(clips_found)} clips potenciales")

            # PASO 4: Formateo los clips para guardarlos
            formatted_clips = []

            for idx, clip in enumerate(clips_found[:max_clips], 1):
                # Extraigo timestamps
                start = clip.start_time
                end = clip.end_time
                duration = end - start

                # Busco el texto correspondiente a este rango de tiempo
                clip_text = self._get_text_for_timerange(
                    whisperx_data,
                    start,
                    end
                )

                # Preview: primeras 100 caracteres para mostrar en UI
                text_preview = (
                    clip_text[:100] + "..."
                    if len(clip_text) > 100
                    else clip_text
                )

                formatted_clips.append({
                    "clip_id": idx,
                    "start_time": round(start, 2),
                    "end_time": round(end, 2),
                    "duration": round(duration, 2),
                    "text_preview": text_preview,
                    "full_text": clip_text,
                    "method": "clipsai"  # Generado por ClipsAI (cambio de tema detectado)
                })

                self.logger.info(
                    f"  Clip {idx}: {duration:.1f}s "
                    f"({self._format_time(start)} → {self._format_time(end)})"
                )

            # Verifico si cumplimos el mínimo esperado
            if len(formatted_clips) < min_clips:
                self.logger.warning(
                    f"⚠️  Solo se encontraron {len(formatted_clips)} clips "
                    f"(mínimo esperado: {min_clips}). "
                    f"Considera ajustar min_clip_duration={self.min_clip_duration}s "
                    f"o max_clip_duration={self.max_clip_duration}s"
                )

            self.logger.info(f"✅ {len(formatted_clips)} clips generados exitosamente")

            return formatted_clips

        except Exception as e:
            self.logger.error(f"❌ Error durante generación de clips: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None


    def _get_text_for_timerange(
        self,
        transcript_data: Dict,
        start_time: float,
        end_time: float
    ) -> str:
        """
        Extraigo el texto de la transcripción en un rango de tiempo específico

        Útil para:
        - Mostrar preview del contenido del clip
        - Generar títulos automáticos (futuro)
        - Análisis de contenido
        """
        segments = transcript_data.get("segments", [])

        clip_text_parts = []

        for seg in segments:
            seg_start = seg.get("start", 0.0)
            seg_end = seg.get("end", 0.0)

            # Si el segmento se solapa con el rango, lo incluyo
            # Uso >= y <= para incluir bordes
            if seg_start < end_time and seg_end > start_time:
                text = seg.get("text", "").strip()
                if text:
                    clip_text_parts.append(text)

        return " ".join(clip_text_parts)


    def _format_time(self, seconds: float) -> str:
        """
        Formateo segundos a MM:SS para logs legibles

        Ejemplo: 125.5 → "02:05"
        """
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"


    def save_clips_metadata(
        self,
        clips: List[Dict],
        video_id: str,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Guardo la metadata de los clips en un JSON

        Esto me permite:
        - No regenerar clips cada vez
        - Editarlos manualmente si es necesario
        - Usarlos en la Fase 4 (resize/edición)

        Args:
            clips: Lista de clips generados
            video_id: ID único del video
            output_path: Ruta personalizada (default: temp/{video_id}_clips.json)

        Returns:
            Ruta del archivo guardado, o None si falla
        """
        if not output_path:
            output_path = f"temp/{video_id}_clips.json"

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        metadata = {
            "video_id": video_id,
            "num_clips": len(clips),
            "min_clip_duration": self.min_clip_duration,
            "max_clip_duration": self.max_clip_duration,
            "clips": clips
        }

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self.logger.info(f"📝 Metadata guardada: {output_file}")

            return str(output_file)

        except Exception as e:
            self.logger.error(f"Error guardando metadata: {e}")
            return None


    def load_clips_metadata(self, metadata_path: str) -> Optional[Dict]:
        """
        Cargo metadata de clips previamente generados

        Útil para:
        - Evitar regenerar clips
        - Continuar donde quedé
        - Editar clips manualmente y recargarlos
        """
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando metadata: {e}")
            return None


# Función helper para uso rápido sin instanciar la clase
def generate_clips_from_transcript(
    transcript_path: str,
    min_clips: int = 3,
    max_clips: int = 10,
    min_duration: int = 30,
    max_duration: int = 90
) -> Optional[List[Dict]]:
    """
    Función de conveniencia para generar clips rápidamente

    Ejemplo de uso:
        clips = generate_clips_from_transcript(
            "temp/video_abc123_transcript.json",
            min_clips=5,
            max_clips=15
        )

        for clip in clips:
            print(f"Clip {clip['clip_id']}: {clip['duration']}s")
            print(f"  {clip['text_preview']}")
    """
    generator = ClipsGenerator(
        min_clip_duration=min_duration,
        max_clip_duration=max_duration
    )

    return generator.generate_clips(
        transcript_path=transcript_path,
        min_clips=min_clips,
        max_clips=max_clips
    )
