#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico de Bug de Subtítulos Duplicados
Ejecutar: python tests/diagnose_subtitle_duplication.py

Este script:
1. Crea un video de prueba minimal
2. Genera subtítulos para ese video
3. Exporta con logo + subtítulos
4. Inspecciona metadata con ffprobe
5. Reporta hallazgos
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import timedelta

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMP_DIR = PROJECT_ROOT / "temp"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Create directories if needed
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(PROJECT_ROOT))

from src.video_exporter import VideoExporter
from src.subtitle_generator import SubtitleGenerator


def print_section(title):
    """Imprimir encabezado de sección"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_ffmpeg():
    """Verificar si ffmpeg y ffprobe están disponibles"""
    print_section("1. Verificando FFmpeg y FFprobe")

    try:
        ffmpeg_result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=False
        )
        ffmpeg_version = ffmpeg_result.stdout.split('\n')[0]
        print(f"✓ FFmpeg encontrado: {ffmpeg_version}")
    except FileNotFoundError:
        print("✗ FFmpeg NO encontrado. Instala con:")
        print("  - macOS: brew install ffmpeg")
        print("  - Linux: apt install ffmpeg")
        return False

    try:
        ffprobe_result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            check=False
        )
        ffprobe_version = ffprobe_result.stdout.split('\n')[0]
        print(f"✓ FFprobe encontrado: {ffprobe_version}")
    except FileNotFoundError:
        print("✗ FFprobe NO encontrado (viene con FFmpeg)")
        return False

    return True


def create_test_video():
    """Crear un video de prueba minimal con ffmpeg"""
    print_section("2. Creando video de prueba minimal")

    test_video = TEMP_DIR / "test_minimal.mp4"

    if test_video.exists():
        print(f"✓ Video ya existe: {test_video}")
        return test_video

    print("Generando video de 10 segundos con FFmpeg...")

    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "color=c=blue:s=1920x1080:d=10",
        "-f", "lavfi",
        "-i", "sine=f=1000:d=10",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-y",
        str(test_video)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ Video de prueba creado: {test_video}")
        return test_video
    else:
        print(f"✗ Error creando video de prueba:")
        print(result.stderr)
        return None


def create_test_subtitle():
    """Crear un archivo SRT de prueba"""
    print_section("3. Creando subtítulos de prueba")

    srt_file = TEMP_DIR / "test_subtitles.srt"

    # Contenido SRT simple
    content = """1
00:00:01,000 --> 00:00:03,000
Subtitle Line 1

2
00:00:03,500 --> 00:00:06,000
Subtitle Line 2

3
00:00:06,500 --> 00:00:09,000
Subtitle Line 3
"""

    srt_file.write_text(content)
    print(f"✓ Subtítulos creados: {srt_file}")
    print("\nContenido del SRT:")
    print(content)

    return srt_file


def create_test_logo():
    """Verificar o crear un logo de prueba"""
    print_section("4. Verificando logo de prueba")

    logo_path = ASSETS_DIR / "logo.png"

    if logo_path.exists():
        print(f"✓ Logo encontrado: {logo_path}")
        return logo_path

    print(f"⚠ Logo no encontrado en {logo_path}")
    print("Continuando sin logo (necesario para diagnóstico)")

    return None


def inspect_with_ffprobe(video_path, stage_name):
    """Inspeccionar un video con ffprobe"""
    print(f"\n--- Inspección de {stage_name} ---\n")

    # Mostrar streams
    cmd = ["ffprobe", "-show_streams", "-print_format", "json", str(video_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"✗ Error inspectando con ffprobe: {result.stderr}")
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("✗ Error parseando output de ffprobe")
        return None

    # Analizar streams
    print(f"Streams encontrados en {video_path.name}:")

    for i, stream in enumerate(data.get("streams", [])):
        codec_type = stream.get("codec_type", "unknown")
        codec_name = stream.get("codec_name", "unknown")
        duration = stream.get("duration", "unknown")

        print(f"\n  Stream #{i}:")
        print(f"    - Tipo: {codec_type}")
        print(f"    - Codec: {codec_name}")
        print(f"    - Duración: {duration} s")

        if codec_type == "subtitle":
            print(f"    ⚠️ SUBTITLE STREAM DETECTED!")

    # Mostrar información general
    print(f"\nFormato general:")
    format_info = data.get("format", {})
    print(f"  - Duración: {format_info.get('duration', 'unknown')} s")
    print(f"  - Bitrate: {format_info.get('bit_rate', 'unknown')} bps")

    return data


def export_test_clips(test_video, srt_file, logo_path):
    """Exportar clips con logo + subtítulos"""
    print_section("5. Exportando clips CON logo + subtítulos (two-step process)")

    try:
        exporter = VideoExporter(output_dir=str(OUTPUT_DIR))

        clips = [
            {
                "clip_id": "test_001",
                "start_time": 0,
                "end_time": 10,
                "text_preview": "Full test clip"
            }
        ]

        print("Iniciando export con:")
        print(f"  - Video: {test_video}")
        print(f"  - Subtítulos: {srt_file}")
        print(f"  - Logo: {logo_path if logo_path else 'NINGUNO (diagnóstico)'}")
        print(f"  - Aspect ratio: 9:16")

        exported = exporter.export_clips(
            video_path=str(test_video),
            clips=clips,
            aspect_ratio="9:16",
            video_name="diagnosis_test",
            add_subtitles=True,
            transcript_path=str(srt_file),
            subtitle_style="default",
            add_logo=bool(logo_path),
            logo_path=str(logo_path) if logo_path else None,
            logo_position="top-right",
            logo_scale=0.1
        )

        if exported and exported[0]:
            output_video = Path(exported[0])
            print(f"\n✓ Clip exportado: {output_video}")
            return output_video
        else:
            print(f"\n✗ Error exportando clip")
            return None

    except Exception as e:
        print(f"\n✗ Excepción durante export: {e}")
        import traceback
        traceback.print_exc()
        return None


def inspect_temp_files():
    """Inspeccionar archivos temporales si existen"""
    print_section("6. Inspeccionar archivos temporales")

    temp_videos = list(TEMP_DIR.glob("*.mp4"))

    if not temp_videos:
        print("No hay archivos MP4 temporales")
        return

    # Buscar temp files de video_exporter
    for temp_file in temp_videos:
        if "temp" in temp_file.name and temp_file.name != "test_minimal.mp4":
            print(f"\nEncontrado: {temp_file.name}")
            inspect_with_ffprobe(temp_file, f"TEMP: {temp_file.name}")


def main():
    """Ejecutar diagnóstico completo"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + "  DIAGNÓSTICO: BUG DE SUBTÍTULOS DUPLICADOS".center(68) + "║")
    print("║" + "  Fecha: 2025-12-07".center(68) + "║")
    print("╚" + "="*68 + "╝")

    # Paso 1: Verificar FFmpeg
    if not check_ffmpeg():
        print("\n✗ FFmpeg no disponible. Instalación requerida.")
        return False

    # Paso 2-4: Crear archivos de prueba
    test_video = create_test_video()
    if not test_video:
        return False

    srt_file = create_test_subtitle()
    logo_path = create_test_logo()

    # Paso 5: Inspeccionar video original
    print_section("Inspección PRE-EXPORT")
    inspect_with_ffprobe(test_video, "VIDEO ORIGINAL")

    # Paso 6: Exportar
    output_video = export_test_clips(test_video, srt_file, logo_path)

    if not output_video:
        print("\n✗ Diagnóstico fallido - no se pudo exportar clip")
        return False

    # Paso 7: Inspeccionar salida final
    print_section("Inspección POST-EXPORT")
    inspect_with_ffprobe(output_video, "VIDEO FINAL EXPORTADO")

    # Paso 8: Inspeccionar archivos temporales
    inspect_temp_files()

    # Resumen y next steps
    print_section("RESUMEN Y PRÓXIMOS PASOS")

    print(f"\n✓ Diagnóstico completado")
    print(f"\nArchivos generados:")
    print(f"  - Test video: {test_video}")
    print(f"  - Test subtítulos: {srt_file}")
    print(f"  - Output final: {output_video}")

    print(f"\n📋 VERIFICACIÓN MANUAL REQUERIDA:")
    print(f"\n1. Abre el video final en un player:")
    print(f"   open '{output_video}'  # macOS")
    print(f"   vlc '{output_video}'    # Cualquier OS")

    print(f"\n2. Observa los subtítulos:")
    print(f"   ✓ ¿Aparecen una sola vez? → BUG RESUELTO")
    print(f"   ✗ ¿Aparecen duplicados? → Continuar investigación")
    print(f"   ? ¿Offset de tiempo? → Problema de timing")

    print(f"\n3. Si duplicados, nota:")
    print(f"   - ¿Aparecen al mismo tiempo o con delay?")
    print(f"   - ¿Son idénticos o diferentes?")
    print(f"   - ¿Posición relativa (superpuesto/lado a lado)?")

    print(f"\n4. Copia esta información en el issue")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
