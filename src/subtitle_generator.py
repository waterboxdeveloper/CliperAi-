# -*- coding: utf-8 -*-
"""
Subtitle Generator - Genera subtítulos SRT desde transcripciones de WhisperX

Este módulo toma la transcripción con timestamps y la convierte a formato SRT.
Los subtítulos pueden quemarse en el video (hard-coded) o agregarse como pista (soft-coded).
"""

import json
import re
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


    def extract_opening_words_from_clip(
        self,
        transcript: Dict,
        clip_start: float,
        clip_end: float,
        opening_duration: float = 10.0
    ) -> Dict[str, any]:
        """
        Extract speaker's opening words from a clip (first 5-10 seconds).

        This method extracts the exact words the speaker says at the beginning of a clip.
        Used for viral copy generation - starting with speaker's own words creates
        authenticity and improves engagement.

        Args:
            transcript: WhisperX transcript dict with word-level timestamps
            clip_start: Clip start time in seconds (e.g., 15.0)
            clip_end: Clip end time in seconds (e.g., 80.0)
            opening_duration: How many seconds to extract from clip start (default 10)

        Returns:
            Dict with keys:
            - opening_words: str (e.g., "La IA es revolucionaria")
            - opening_duration_actual: float (actual seconds captured)
            - word_count: int (number of words extracted)
            - timestamp_range: tuple (start, end) of extracted words
            - success: bool (whether extraction succeeded)

        Example:
            >>> result = subtitle_gen.extract_opening_words_from_clip(
            ...     transcript=clip["transcript"],
            ...     clip_start=15.0,
            ...     clip_end=80.0,
            ...     opening_duration=10.0
            ... )
            >>> print(result)
            {
                'opening_words': 'La IA es revolucionaria',
                'opening_duration_actual': 2.34,
                'word_count': 4,
                'timestamp_range': (15.0, 17.34),
                'success': True
            }
        """
        try:
            segments = transcript.get("segments", [])

            if not segments:
                self.logger.warning(f"No segments found in transcript")
                return {
                    "opening_words": "",
                    "opening_duration_actual": 0.0,
                    "word_count": 0,
                    "timestamp_range": (clip_start, clip_start),
                    "success": False
                }

            # Define time window for opening words
            opening_end = clip_start + opening_duration

            # Collect words within the opening window
            opening_words_list = []
            actual_start_time = None
            actual_end_time = None

            for segment in segments:
                words = segment.get("words", [])

                for word_obj in words:
                    word_text = word_obj.get("word", "").strip()
                    word_start = word_obj.get("start", 0)
                    word_end = word_obj.get("end", 0)

                    # Check if word falls within opening window
                    if word_start >= clip_start and word_start < opening_end:
                        opening_words_list.append(word_text)

                        # Track actual start/end times
                        if actual_start_time is None:
                            actual_start_time = word_start
                        actual_end_time = word_end

            # Build result
            opening_words = " ".join(opening_words_list)
            actual_duration = (actual_end_time - actual_start_time) if actual_start_time else 0.0

            if opening_words:
                self.logger.info(
                    f"Extracted opening words ({len(opening_words_list)} words, "
                    f"{actual_duration:.2f}sec): '{opening_words}'"
                )
                return {
                    "opening_words": opening_words,
                    "opening_duration_actual": actual_duration,
                    "word_count": len(opening_words_list),
                    "timestamp_range": (actual_start_time, actual_end_time),
                    "success": True
                }
            else:
                self.logger.warning(
                    f"No words found in opening window ({clip_start}-{opening_end})"
                )
                return {
                    "opening_words": "",
                    "opening_duration_actual": 0.0,
                    "word_count": 0,
                    "timestamp_range": (clip_start, clip_start),
                    "success": False
                }

        except Exception as e:
            self.logger.error(f"Error extracting opening words: {e}")
            return {
                "opening_words": "",
                "opening_duration_actual": 0.0,
                "word_count": 0,
                "timestamp_range": (clip_start, clip_start),
                "success": False
            }


    def extract_speaker_hashtags(self, clip_text: str) -> List[str]:
        r"""
        Extract hashtags speaker mentioned in clip.

        Scans the clip text for hashtags (pattern: #\w+) and returns unique ones.
        Used to preserve speaker's actual hashtags in generated copies rather than
        inventing new ones.

        Args:
            clip_text: Full text of the clip (can be reconstructed from segments)

        Returns:
            List of hashtags found (e.g., ["#AICDMX", "#Future"])
            Empty list if no hashtags found

        Example:
            >>> text = "La IA es revolucionaria #AICDMX #Future #Tech"
            >>> hashtags = subtitle_gen.extract_speaker_hashtags(text)
            >>> print(hashtags)
            ['#AICDMX', '#Future', '#Tech']
        """
        try:
            if not clip_text:
                return []

            # Pattern: # followed by one or more word characters
            pattern = r'#\w+'

            # Find all matches
            matches = re.findall(pattern, clip_text)

            # Deduplicate while preserving order
            seen = set()
            unique_hashtags = []
            for hashtag in matches:
                if hashtag not in seen:
                    seen.add(hashtag)
                    unique_hashtags.append(hashtag)

            if unique_hashtags:
                self.logger.info(f"Extracted hashtags: {unique_hashtags}")

            return unique_hashtags

        except Exception as e:
            self.logger.error(f"Error extracting hashtags: {e}")
            return []


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


    # ==================== ASS FORMAT GENERATION (Phase 3b - Multicolor Support) ====================

    def generate_ass_for_clip(
        self,
        transcript_path: str,
        clip_start: float,
        clip_end: float,
        output_path: str,
        subtitle_position: str = "bottom",
        emphasis_keywords: Optional[List[str]] = None,
        max_chars_per_line: int = 42,
        max_duration: float = 5.0
    ) -> Optional[str]:
        """
        Generate ASS (Advanced SubStation Alpha) subtitle file for a clip with multicolor support.

        ASS format advantages:
        - All styling metadata in one file (position, color, font)
        - Support for per-word color override tags
        - No need for ffmpeg -vf filter (cleaner)
        - Professional subtitle format (anime/professional standard)

        Args:
            transcript_path: Path to WhisperX JSON transcript
            clip_start: Clip start time in seconds
            clip_end: Clip end time in seconds
            output_path: Path to output .ass file
            subtitle_position: "bottom" (default), "middle", or "very_high"
            emphasis_keywords: Optional list of words to highlight in different color
            max_chars_per_line: Max characters per subtitle line
            max_duration: Max duration for a single subtitle

        Returns:
            Path to generated ASS file, or None if failed
        """
        try:
            # Load transcript
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)

            segments = transcript_data.get('segments', [])

            # Filter segments for this clip
            clip_segments = []
            for segment in segments:
                seg_start = segment.get('start', 0)
                seg_end = segment.get('end', 0)

                if seg_start < clip_end and seg_end > clip_start:
                    adjusted_segment = segment.copy()

                    # Adjust word timestamps if they exist
                    if 'words' in segment:
                        adjusted_words = []
                        for word in segment['words']:
                            word_start = word.get('start', 0)
                            word_end = word.get('end', 0)

                            if word_start >= clip_start and word_end <= clip_end:
                                adjusted_word = word.copy()
                                adjusted_word['start'] = word_start - clip_start
                                adjusted_word['end'] = word_end - clip_start
                                adjusted_words.append(adjusted_word)

                        adjusted_segment['words'] = adjusted_words

                    # Adjust segment timestamps
                    adjusted_segment['start'] = max(0, seg_start - clip_start)
                    adjusted_segment['end'] = min(clip_end - clip_start, seg_end - clip_start)
                    clip_segments.append(adjusted_segment)

            if not clip_segments:
                self.logger.warning(f"No segments found for clip {clip_start}-{clip_end}")
                return None

            # Build ASS header with position and styling info
            ass_header = self._build_ass_header(subtitle_position)

            # Build ASS events with optional keyword highlighting
            ass_events = self._build_ass_events(
                clip_segments,
                subtitle_position=subtitle_position,
                emphasis_keywords=emphasis_keywords,
                max_chars_per_line=max_chars_per_line,
                max_duration=max_duration
            )

            # Write complete ASS file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ass_header)
                f.write("\n[Events]\n")
                f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                for event in ass_events:
                    f.write(event)

            self.logger.info(f"ASS subtitles generated: {output_path} (position: {subtitle_position})")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error generating ASS subtitles: {e}")
            return None


    def _build_ass_header(self, subtitle_position: str = "bottom") -> str:
        """
        Build ASS file header with V4+ Styles section.

        Position mappings (ASS Alignment values use numpad layout):
        - bottom (2): 20px from bottom
        - middle (5): centered vertically
        - very_high (8): 10px from top

        All styles: 8px Arial, yellow color (#FFFF00), no outline/shadow
        """
        # TODO(human): Verify alignment values and margins are correct
        # The alignment numbers come from ASS spec (numpad: 1-9)
        # Test with actual video to ensure positioning matches expectations

        styles_config = {
            "bottom": {
                "alignment": "2",
                "margin_v": "20",
                "desc": "Bottom-center (waist level)"
            },
            "middle": {
                "alignment": "5",
                "margin_v": "0",
                "desc": "Middle-center (frame center)"
            },
            "very_high": {
                "alignment": "8",
                "margin_v": "10",
                "desc": "Top-center (10px from top)"
            }
        }

        config = styles_config.get(subtitle_position, styles_config["bottom"])

        # ASS Header (v4.00+ format)
        header = f"""[Script Info]
Title: Clip Subtitles
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {subtitle_position},Arial,8,&H0000FFFF,&H80FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,{config['alignment']},0,0,{config['margin_v']},1
"""
        return header


    def _build_ass_events(
        self,
        segments: List[Dict],
        subtitle_position: str = "bottom",
        emphasis_keywords: Optional[List[str]] = None,
        max_chars_per_line: int = 42,
        max_duration: float = 5.0
    ) -> List[str]:
        r"""
        Build ASS event lines with word-level coloring support.

        Converts subtitle lines to ASS format Dialogue entries with optional
        per-word color highlighting using ASS override tags.

        Example output:
        Dialogue: 0,0:00:00.00,0:00:02.50,bottom,,0,0,0,,
        Hola {\c&HFF00FF&}mundo{\c}, ¿cómo estás?
        """
        # TODO(human): Decide on color scheme for emphasis
        # Currently: Yellow default, Magenta for keywords
        # Could be configurable (red, cyan, green, etc.)
        # Also consider if outline/shadow should be added for emphasis words

        events = []
        subtitle_index = 1

        # Normalize keywords to lowercase for case-insensitive matching
        keywords_lower = [kw.lower() for kw in (emphasis_keywords or [])]

        for segment in segments:
            if 'words' in segment and segment['words']:
                words = segment['words']

                # Group words into subtitle lines (same logic as SRT)
                current_line_words = []
                current_line_chars = 0
                line_start_time = None

                for word_obj in words:
                    word_text = word_obj.get('word', '').strip()
                    word_start = word_obj.get('start', 0)
                    word_end = word_obj.get('end', 0)

                    if not word_text:
                        continue

                    if line_start_time is None:
                        line_start_time = word_start

                    word_length = len(word_text) + 1

                    # Check if we need to break to a new line
                    if (current_line_chars + word_length > max_chars_per_line or
                        (line_start_time and word_end - line_start_time > max_duration)):

                        # Create ASS event with current line
                        if current_line_words:
                            line_text = self._apply_keyword_highlighting(
                                current_line_words,
                                keywords_lower
                            )
                            line_end_time = current_line_words[-1].get('end', word_start)

                            event = self._format_ass_event(
                                subtitle_index,
                                line_start_time,
                                line_end_time,
                                subtitle_position,
                                line_text
                            )
                            events.append(event)
                            subtitle_index += 1

                        # Start new line
                        current_line_words = [word_obj]
                        current_line_chars = word_length
                        line_start_time = word_start
                    else:
                        current_line_words.append(word_obj)
                        current_line_chars += word_length

                # Process last line if any
                if current_line_words:
                    line_text = self._apply_keyword_highlighting(
                        current_line_words,
                        keywords_lower
                    )
                    line_end_time = current_line_words[-1].get('end', line_start_time + 1.0)

                    event = self._format_ass_event(
                        subtitle_index,
                        line_start_time,
                        line_end_time,
                        subtitle_position,
                        line_text
                    )
                    events.append(event)
                    subtitle_index += 1

            else:
                # Fallback: use full segment text
                text = segment.get('text', '').strip()
                start = segment.get('start', 0)
                end = segment.get('end', 0)

                if text:
                    lines = self._split_text_into_lines(text, max_chars_per_line)
                    duration = end - start
                    time_per_line = duration / len(lines) if lines else duration

                    for i, line in enumerate(lines):
                        line_start = start + (i * time_per_line)
                        line_end = start + ((i + 1) * time_per_line)

                        event = self._format_ass_event(
                            subtitle_index,
                            line_start,
                            line_end,
                            subtitle_position,
                            line
                        )
                        events.append(event)
                        subtitle_index += 1

        return events


    def _apply_keyword_highlighting(
        self,
        word_objects: List[Dict],
        keywords_lower: List[str]
    ) -> str:
        r"""
        Apply keyword highlighting with ASS color override tags.

        Converts word objects to colored text using ASS override syntax:
        - Regular words: Yellow (#FFFF00 in BGR = &H0000FFFF)
        - Keyword matches: Magenta (#FF00FF in BGR = &HFF00FF)

        Example:
        Input: [{"word": "Hola"}, {"word": "mundo"}, {"word": "fascinante"}]
               keywords: ["mundo"]
        Output: "Hola {\c&HFF00FF&}mundo{\c} fascinante"
                 Yellow  [Magenta]        Yellow
        """
        colored_words = []

        for word_obj in word_objects:
            word_text = word_obj.get('word', '').strip()

            if not word_text:
                continue

            # Check if word matches any keyword (case-insensitive)
            if word_text.lower() in keywords_lower:
                # Magenta color: &HFF00FF (BGR format)
                colored = f"{{\\c&HFF00FF&}}{word_text}{{\\c}}"
            else:
                # Normal text (yellow default will be applied by style)
                colored = word_text

            colored_words.append(colored)

        return " ".join(colored_words)


    def _format_ass_event(
        self,
        index: int,
        start_time: float,
        end_time: float,
        style_name: str,
        text: str
    ) -> str:
        """
        Format an ASS Dialogue event line.

        Args:
            index: Subtitle sequence number (for reference)
            start_time: Start time in seconds
            end_time: End time in seconds
            style_name: Name of the style to use (must exist in [V4+ Styles])
            text: Dialogue text (may contain ASS override tags)

        Returns:
            Complete Dialogue line ready to write to ASS file
        """
        start_str = self._seconds_to_ass_time(start_time)
        end_str = self._seconds_to_ass_time(end_time)

        # Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        dialogue = f"Dialogue: 0,{start_str},{end_str},{style_name},,0,0,0,,{text}\n"
        return dialogue


    def _seconds_to_ass_time(self, seconds: float) -> str:
        r"""
        Convert seconds to ASS time format (H:MM:SS.CC).

        Args:
            seconds: Time in seconds (float)

        Returns:
            String in ASS format (e.g., "0:00:02.50")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        # Round centiseconds to avoid precision issues
        centisecs = round((seconds % 1) * 100) % 100

        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
