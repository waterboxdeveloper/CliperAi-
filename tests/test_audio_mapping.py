#!/usr/bin/env python3
"""
Test para validar comando FFmpeg con mapeo de audio
cuando se usa video reframed sin audio.

PROBLEMA:
- Video reframed (generado por FaceReframer) NO tiene audio
- FFmpeg necesita mapear audio del video original

SOLUCIÓN:
- Usar 2 inputs: [0] video reframed, [1] video original
- Mapear: video de [0], audio de [1]
"""
import subprocess
from pathlib import Path


def test_ffmpeg_command_with_audio_mapping():
    """
    Genera comando FFmpeg correcto para:
    - Video source: video reframed (sin audio)
    - Audio source: video original
    - Subtitles: quemados en video
    """

    # Paths de ejemplo
    video_reframed = "output/test_video/1_reframed_temp.mp4"  # Sin audio
    video_original = "downloads/test_video.mp4"  # Con audio
    subtitle_file = "output/test_video/1.srt"
    output_file = "output/test_video/1.mp4"

    # COMANDO CORRECTO con 2 inputs
    cmd_correct = [
        "ffmpeg",
        "-i", str(video_reframed),    # [0] = Video reframed (sin audio)
        "-i", str(video_original),    # [1] = Video original (con audio)

        # Filtro de subtítulos aplicado a [0:v]
        "-filter_complex",
        f"[0:v]subtitles='{subtitle_file}':force_style='FontSize=18,PrimaryColour=&H0000FFFF'[v]",

        # Mapear streams
        "-map", "[v]",         # Video procesado (con subtítulos)
        "-map", "1:a",         # Audio del video original [1]

        # Codecs
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",

        "-y", str(output_file)
    ]

    print("✓ COMANDO CORRECTO (con audio):")
    print(" ".join(cmd_correct))
    print()

    # COMANDO INCORRECTO (actual)
    cmd_incorrect = [
        "ffmpeg",
        "-i", str(video_reframed),    # Solo 1 input (sin audio)
        "-vf", f"subtitles='{subtitle_file}'",
        "-c:v", "libx264",
        "-c:a", "aac",         # ← Esto falla porque no hay audio stream
        "-preset", "fast",
        "-crf", "23",
        "-y", str(output_file)
    ]

    print("✗ COMANDO INCORRECTO (sin audio):")
    print(" ".join(cmd_incorrect))
    print()

    print("DIFERENCIA CLAVE:")
    print("- Correcto: 2 inputs (-i reframed -i original), mapea audio de [1:a]")
    print("- Incorrecto: 1 input (reframed sin audio), no puede encodear audio")

    return cmd_correct


def test_ffmpeg_without_face_tracking():
    """
    Cuando NO se usa face tracking, el comando es más simple
    porque el video original YA tiene audio.
    """
    video_original = "downloads/test_video.mp4"
    subtitle_file = "output/test_video/1.srt"
    output_file = "output/test_video/1.mp4"
    start_time = 10.5
    duration = 30.2

    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-i", str(video_original),    # Video con audio
        "-t", str(duration),

        # Filtros (crop + subtítulos)
        "-vf", f"crop=ih*9/16:ih,scale=1080:1920,subtitles='{subtitle_file}'",

        # Codecs (audio y video en el mismo input)
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",

        "-y", str(output_file)
    ]

    print("✓ COMANDO SIN FACE TRACKING (audio ya incluido):")
    print(" ".join(cmd))
    print()


if __name__ == "__main__":
    print("=" * 80)
    print("TEST: Audio Mapping con Face Tracking")
    print("=" * 80)
    print()

    test_ffmpeg_command_with_audio_mapping()
    print()
    print("-" * 80)
    print()
    test_ffmpeg_without_face_tracking()

    print("=" * 80)
    print("CONCLUSIÓN:")
    print("- Face tracking ON: Necesita 2 inputs + mapeo de audio")
    print("- Face tracking OFF: 1 input (ya tiene audio)")
    print("=" * 80)
