# -*- coding: utf-8 -*-
"""
Subtitle Generator - Genera subtítulos SRT desde transcripciones de WhisperX

Este módulo toma la transcripción con timestamps y la convierte a formato SRT.
Los subtítulos pueden quemarse en el video (hard-coded) o agregarse como pista (soft-coded).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SubtitleGenerator:
    """
    Genero subtítulos en formato SRT desde transcripciones de WhisperX

    Características:
    - Formato SRT estándar (compatible con todos los players)
    - Agrupación inteligente de palabras (max 42 caracteres por línea)
    - Sincronización perfecta con timestamps de WhisperX
    - Soporte para múltiples idiomas
    """

    def __init__(self):
        self.console = Console()
        self.logger = logger


    def generate_srt_from_transcript(
        self,
        transcript_path: str,
        output_path: Optional[str] = None,
        max_chars_per_line: int = 42,
        max_duration: float = 5.0
    ) -> Optional[str]:
        """
        Genero archivo SRT desde transcripción de WhisperX

        Args:
            transcript_path: Ruta al JSON de transcripción
            output_path: Ruta de salida para el SRT (opcional)
            max_chars_per_line: Máximo de caracteres por línea de subtítulo
            max_duration: Duración máxima de un subtítulo en segundos

        Returns:
            Ruta al archivo SRT generado, o None si falla
        """
        try:
            # Cargo la transcripción
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)

            segments = transcript_data.get('segments', [])

            if not segments:
                self.logger.error("No se encontraron segmentos en la transcripción")
                return None

            # Genero el path de salida si no se especificó
            if output_path is None:
                transcript_file = Path(transcript_path)
                output_path = transcript_file.with_suffix('.srt')

            # Genero las entradas SRT
            srt_entries = self._create_srt_entries(
                segments,
                max_chars_per_line=max_chars_per_line,
                max_duration=max_duration
            )

            # Escribo el archivo SRT
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_entries))

            self.logger.info(f"Subtítulos generados: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error generando subtítulos: {e}")
            return None


    def generate_srt_for_clip(
        self,
        transcript_path: str,
        clip_start: float,
        clip_end: float,
        output_path: str,
        max_chars_per_line: int = 42,
        max_duration: float = 5.0
    ) -> Optional[str]:
        """
        Genero archivo SRT para un clip específico

        Args:
            transcript_path: Ruta al JSON de transcripción completa
            clip_start: Tiempo de inicio del clip en segundos
            clip_end: Tiempo de fin del clip en segundos
            output_path: Ruta de salida para el SRT
            max_chars_per_line: Máximo de caracteres por línea
            max_duration: Duración máxima de un subtítulo

        Returns:
            Ruta al archivo SRT generado, o None si falla
        """
        try:
            # Cargo la transcripción
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)

            segments = transcript_data.get('segments', [])

            # Filtro solo los segmentos que están dentro del clip
            clip_segments = []
            for segment in segments:
                seg_start = segment.get('start', 0)
                seg_end = segment.get('end', 0)

                # Si el segmento se solapa con el clip, lo incluyo
                if seg_start < clip_end and seg_end > clip_start:
                    # Ajusto los timestamps relativos al inicio del clip
                    adjusted_segment = segment.copy()

                    # Ajusto palabras si existen
                    if 'words' in segment:
                        adjusted_words = []
                        for word in segment['words']:
                            word_start = word.get('start', 0)
                            word_end = word.get('end', 0)

                            # Solo incluyo palabras dentro del rango del clip
                            if word_start >= clip_start and word_end <= clip_end:
                                adjusted_word = word.copy()
                                adjusted_word['start'] = word_start - clip_start
                                adjusted_word['end'] = word_end - clip_start
                                adjusted_words.append(adjusted_word)

                        adjusted_segment['words'] = adjusted_words

                    # Ajusto los timestamps del segmento
                    adjusted_segment['start'] = max(0, seg_start - clip_start)
                    adjusted_segment['end'] = min(clip_end - clip_start, seg_end - clip_start)

                    clip_segments.append(adjusted_segment)

            if not clip_segments:
                self.logger.warning(f"No se encontraron segmentos para el clip {clip_start}-{clip_end}")
                return None

            # Genero las entradas SRT
            srt_entries = self._create_srt_entries(
                clip_segments,
                max_chars_per_line=max_chars_per_line,
                max_duration=max_duration
            )

            # Escribo el archivo SRT
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_entries))

            self.logger.info(f"Subtítulos del clip generados: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error generando subtítulos del clip: {e}")
            return None


    def _create_srt_entries(
        self,
        segments: List[Dict],
        max_chars_per_line: int = 42,
        max_duration: float = 5.0
    ) -> List[str]:
        """
        Creo las entradas en formato SRT desde segmentos

        Formato SRT:
        1
        00:00:00,000 --> 00:00:03,500
        This is the first subtitle line

        2
        00:00:03,500 --> 00:00:07,000
        This is the second subtitle line
        """
        srt_entries = []
        subtitle_index = 1

        for segment in segments:
            # Uso palabras si están disponibles (mejor sincronización)
            if 'words' in segment and segment['words']:
                words = segment['words']

                # Agrupo palabras en líneas de subtítulos
                current_line_words = []
                current_line_chars = 0
                line_start_time = None

                for word_obj in words:
                    word_text = word_obj.get('word', '').strip()
                    word_start = word_obj.get('start', 0)
                    word_end = word_obj.get('end', 0)

                    if not word_text:
                        continue

                    # Inicio de nueva línea
                    if line_start_time is None:
                        line_start_time = word_start

                    # Verifico si agregar esta palabra excede el límite
                    word_length = len(word_text) + 1  # +1 por el espacio

                    if (current_line_chars + word_length > max_chars_per_line or
                        (line_start_time and word_end - line_start_time > max_duration)):

                        # Creo entrada SRT con las palabras actuales
                        if current_line_words:
                            line_text = ' '.join([w.get('word', '').strip() for w in current_line_words])
                            line_end_time = current_line_words[-1].get('end', word_start)

                            srt_entry = self._format_srt_entry(
                                subtitle_index,
                                line_start_time,
                                line_end_time,
                                line_text
                            )
                            srt_entries.append(srt_entry)
                            subtitle_index += 1

                        # Inicio nueva línea
                        current_line_words = [word_obj]
                        current_line_chars = word_length
                        line_start_time = word_start
                    else:
                        # Agrego palabra a la línea actual
                        current_line_words.append(word_obj)
                        current_line_chars += word_length

                # Proceso última línea si quedó algo
                if current_line_words:
                    line_text = ' '.join([w.get('word', '').strip() for w in current_line_words])
                    line_end_time = current_line_words[-1].get('end', line_start_time + 1.0)

                    srt_entry = self._format_srt_entry(
                        subtitle_index,
                        line_start_time,
                        line_end_time,
                        line_text
                    )
                    srt_entries.append(srt_entry)
                    subtitle_index += 1

            else:
                # Fallback: uso el texto completo del segmento
                text = segment.get('text', '').strip()
                start = segment.get('start', 0)
                end = segment.get('end', 0)

                if text:
                    # Divido texto largo en líneas
                    lines = self._split_text_into_lines(text, max_chars_per_line)
                    duration = end - start
                    time_per_line = duration / len(lines) if lines else duration

                    for i, line in enumerate(lines):
                        line_start = start + (i * time_per_line)
                        line_end = start + ((i + 1) * time_per_line)

                        srt_entry = self._format_srt_entry(
                            subtitle_index,
                            line_start,
                            line_end,
                            line
                        )
                        srt_entries.append(srt_entry)
                        subtitle_index += 1

        return srt_entries


    def _format_srt_entry(
        self,
        index: int,
        start_time: float,
        end_time: float,
        text: str
    ) -> str:
        """
        Formateo una entrada SRT

        Args:
            index: Número de subtítulo
            start_time: Tiempo de inicio en segundos
            end_time: Tiempo de fin en segundos
            text: Texto del subtítulo

        Returns:
            String con formato SRT
        """
        start_str = self._seconds_to_srt_time(start_time)
        end_str = self._seconds_to_srt_time(end_time)

        return f"{index}\n{start_str} --> {end_str}\n{text}\n"


    def _seconds_to_srt_time(self, seconds: float) -> str:
        """
        Convierto segundos a formato SRT (HH:MM:SS,mmm)

        Args:
            seconds: Tiempo en segundos

        Returns:
            String en formato SRT
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


    def _split_text_into_lines(self, text: str, max_chars: int) -> List[str]:
        """
        Divido texto largo en líneas respetando límite de caracteres

        Intenta cortar en espacios para no partir palabras

        Args:
            text: Texto a dividir
            max_chars: Máximo de caracteres por línea

        Returns:
            Lista de líneas
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 por el espacio

            if current_length + word_length > max_chars:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += word_length

        # Agrego última línea
        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]
