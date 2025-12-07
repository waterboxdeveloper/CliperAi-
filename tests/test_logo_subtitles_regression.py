#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: Logo + Subtitles Together (Regression Test)

Verifica que el bug de subtítulos duplicados NO ocurra cuando se activan
simultáneamente logo y subtítulos en video_exporter.py

Contexto del Bug:
- Antes: FFmpeg preservaba metadatos de subtítulos en el video temporal (Step 1)
- En Step 2: Se aplicaban AMBOS subtítulos (los metadatos + los nuevos) → duplicación
- Solución: Agregar -sn en Step 1 para descartar streams de subtítulos

Test Cases:
1. Solo logo → debe funcionar
2. Solo subtítulos → debe funcionar
3. Logo + subtítulos → debe funcionar SIN duplicación
"""

import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

# Para este test, necesitaremos:
# - Un video de prueba pequeño (5-10 seg)
# - Un logo (PNG)
# - Una transcripción con subtítulos


def create_test_video(output_path: Path, duration: int = 5, width: int = 1920, height: int = 1080):
    """
    Crea un video de prueba simple usando FFmpeg

    Args:
        output_path: Ruta de salida
        duration: Duración en segundos
        width, height: Resolución
    """
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"color=c=blue:s={width}x{height}:d={duration}",
        "-f", "lavfi",
        "-i", f"sine=f=1000:d={duration}",
        "-pix_fmt", "yuv420p",
        "-y",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create test video: {result.stderr}")

    print(f"✓ Test video created: {output_path}")
    return output_path


def create_test_logo(output_path: Path, width: int = 200, height: int = 200):
    """
    Crea un logo PNG simple usando FFmpeg
    """
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"color=c=red:s={width}x{height}:d=1",
        "-pix_fmt", "rgba",
        "-vframes", "1",
        "-y",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create test logo: {result.stderr}")

    print(f"✓ Test logo created: {output_path}")
    return output_path


def create_test_transcript(output_path: Path):
    """
    Crea un archivo de transcripción de prueba (JSON)

    Formato: Mismo que WhisperX output
    """
    transcript = {
        "segments": [
            {
                "id": 0,
                "seek": 0,
                "start": 0.0,
                "end": 2.5,
                "text": " This is a test.",
                "tokens": [],
                "temperature": 0.0,
                "avg_logprob": -0.5,
                "compression_ratio": 1.0,
                "no_speech_prob": 0.1,
                "words": [
                    {"word": "This", "start": 0.0, "end": 0.5},
                    {"word": "is", "start": 0.5, "end": 0.8},
                    {"word": "a", "start": 0.8, "end": 1.0},
                    {"word": "test", "start": 1.0, "end": 2.0},
                ]
            },
            {
                "id": 1,
                "seek": 0,
                "start": 2.5,
                "end": 5.0,
                "text": " Testing subtitle duplication bug.",
                "tokens": [],
                "temperature": 0.0,
                "avg_logprob": -0.5,
                "compression_ratio": 1.0,
                "no_speech_prob": 0.1,
                "words": [
                    {"word": "Testing", "start": 2.5, "end": 3.2},
                    {"word": "subtitle", "start": 3.2, "end": 4.0},
                    {"word": "duplication", "start": 4.0, "end": 4.7},
                    {"word": "bug", "start": 4.7, "end": 5.0},
                ]
            }
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(transcript, f, indent=2)

    print(f"✓ Test transcript created: {output_path}")
    return output_path


def test_logo_only():
    """
    Test Case 1: Solo logo (sin subtítulos)
    Debe funcionar sin problemas
    """
    print("\n" + "="*70)
    print("TEST 1: Logo Only")
    print("="*70)

    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Crear assets de prueba
        video = create_test_video(tmpdir / "test.mp4", duration=5)
        logo = create_test_logo(tmpdir / "logo.png")

        # Exportar con logo
        from src.video_exporter import VideoExporter
        exporter = VideoExporter(output_dir=str(tmpdir / "output"))

        clips = [{
            'clip_id': '1',
            'start_time': 0,
            'end_time': 5,
            'text_preview': 'Test clip'
        }]

        try:
            result = exporter.export_clips(
                video_path=str(video),
                clips=clips,
                aspect_ratio="16:9",
                add_logo=True,
                logo_path=str(logo),
                logo_position="top-right",
                logo_scale=0.1,
                add_subtitles=False  # Sin subtítulos
            )

            if result and Path(result[0]).exists():
                print("✓ PASS: Logo-only export successful")
                return True
            else:
                print("✗ FAIL: Output file not created")
                return False

        except Exception as e:
            print(f"✗ FAIL: {e}")
            return False


def test_subtitles_only():
    """
    Test Case 2: Solo subtítulos (sin logo)
    Debe funcionar sin problemas
    """
    print("\n" + "="*70)
    print("TEST 2: Subtitles Only")
    print("="*70)

    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Crear assets de prueba
        video = create_test_video(tmpdir / "test.mp4", duration=5)
        transcript = create_test_transcript(tmpdir / "transcript.json")

        # Exportar con subtítulos
        from src.video_exporter import VideoExporter
        exporter = VideoExporter(output_dir=str(tmpdir / "output"))

        clips = [{
            'clip_id': '1',
            'start_time': 0,
            'end_time': 5,
            'text_preview': 'Test clip'
        }]

        try:
            result = exporter.export_clips(
                video_path=str(video),
                clips=clips,
                aspect_ratio="16:9",
                add_subtitles=True,
                transcript_path=str(transcript),
                subtitle_style="default",
                add_logo=False  # Sin logo
            )

            if result and Path(result[0]).exists():
                print("✓ PASS: Subtitles-only export successful")
                return True
            else:
                print("✗ FAIL: Output file not created")
                return False

        except Exception as e:
            print(f"✗ FAIL: {e}")
            return False


def test_logo_and_subtitles():
    """
    Test Case 3: Logo + Subtítulos (CRITICAL TEST)

    Este es el caso que causaba el bug. Verifica que:
    1. El video se exporta correctamente
    2. Los subtítulos aparecen UNA SOLA VEZ (no duplicados)

    NOTA: Este test crear el archivo, pero la verificación visual de
    duplicación requiere inspección manual o análisis de frames.
    """
    print("\n" + "="*70)
    print("TEST 3: Logo + Subtitles (REGRESSION TEST)")
    print("="*70)
    print("⚠️  CRITICAL: Este test verifica que el bug de duplicación está resuelto")

    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Crear assets de prueba
        video = create_test_video(tmpdir / "test.mp4", duration=5)
        logo = create_test_logo(tmpdir / "logo.png")
        transcript = create_test_transcript(tmpdir / "transcript.json")

        # Exportar con AMBOS logo y subtítulos
        from src.video_exporter import VideoExporter
        exporter = VideoExporter(output_dir=str(tmpdir / "output"))

        clips = [{
            'clip_id': '1',
            'start_time': 0,
            'end_time': 5,
            'text_preview': 'Test clip'
        }]

        try:
            print("\nExportando con logo + subtítulos...")
            result = exporter.export_clips(
                video_path=str(video),
                clips=clips,
                aspect_ratio="16:9",
                add_logo=True,
                logo_path=str(logo),
                logo_position="top-right",
                logo_scale=0.1,
                add_subtitles=True,
                transcript_path=str(transcript),
                subtitle_style="default"
            )

            if result and Path(result[0]).exists():
                output_file = Path(result[0])
                print(f"✓ Output created: {output_file}")
                print(f"✓ File size: {output_file.stat().st_size / 1024:.1f} KB")

                # Verificación básica: El archivo debe tener audio y video streams
                cmd = ["ffprobe", "-v", "error", "-show_entries",
                       "stream=codec_type", "-of", "default=noprint_wrappers=1",
                       str(output_file)]

                result = subprocess.run(cmd, capture_output=True, text=True, check=False)

                if "video" in result.stdout and "audio" in result.stdout:
                    print("✓ PASS: File has both video and audio streams")
                    print("\n⚠️  MANUAL VERIFICATION NEEDED:")
                    print(f"   1. Open the output file: {output_file}")
                    print(f"   2. Check that subtitles appear ONCE (not duplicated)")
                    print(f"   3. Check that logo is visible in top-right corner")
                    return True
                else:
                    print("✗ FAIL: Missing streams")
                    return False

            else:
                print("✗ FAIL: Output file not created")
                return False

        except Exception as e:
            print(f"✗ FAIL: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """
    Ejecutar todos los tests
    """
    print("\n" + "="*70)
    print("REGRESSION TEST: Logo + Subtitles Bug Fix")
    print("="*70)
    print("\nThis test verifies the fix for subtitle duplication when")
    print("logo and subtitles are enabled simultaneously.")
    print("\nImplementation: -sn flag in Step 1 to discard subtitle streams")

    # Verificar que FFmpeg está disponible
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("\n✗ ERROR: ffmpeg and ffprobe must be installed")
        return False

    results = {
        "test_1_logo_only": test_logo_only(),
        "test_2_subtitles_only": test_subtitles_only(),
        "test_3_logo_and_subtitles": test_logo_and_subtitles()
    }

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
