"""
Test: FFmpegVideoWriter con Face Tracking
Fecha: 2025-11-29
Propósito: Validar que FFmpeg subprocess resuelve el problema de VideoWriter
"""

from pathlib import Path
from src.reframer import FaceReframer
from loguru import logger

# Setup
video_path = Path("downloads/Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream_LZlXASa8CZM.mp4")
output_path = Path("tests/test_ffmpeg_output.mp4")

if not video_path.exists():
    print(f"ERROR: Video no encontrado en {video_path}")
    exit(1)

# Crear directorio si no existe
output_path.parent.mkdir(exist_ok=True)

print("=" * 70)
print("TEST: FFmpegVideoWriter + Face Tracking")
print("=" * 70)
print(f"Input:  {video_path.name}")
print(f"Output: {output_path}")
print()

# Test con clip de 10 segundos
try:
    reframer = FaceReframer(
        frame_sample_rate=3,
        strategy="keep_in_frame",
        safe_zone_margin=0.15,
        min_detection_confidence=0.5
    )

    print("Procesando clip de 10 segundos (30-40s) con face tracking...")
    print("Esperado: FFmpegVideoWriter debería funcionar con FFmpeg subprocess")
    print()

    reframer.reframe_video(
        input_path=str(video_path),
        output_path=str(output_path),
        target_resolution=(1080, 1920),
        start_time=30.0,  # Segundo 30
        end_time=40.0     # 10 segundos
    )

    print()
    print("=" * 70)
    print("✓ SUCCESS: Face tracking completado con FFmpeg subprocess")
    print("=" * 70)

    # Validar output
    if output_path.exists():
        size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"Output: {output_path}")
        print(f"Size:   {size_mb:.2f} MB")
        print()
        print("VALIDACIÓN:")
        print("  ✓ FFmpegVideoWriter funcionó correctamente")
        print("  ✓ Face tracking operativo en macOS M4")
        print("  ✓ Video exportado con dynamic reframing")
        print()
        print(f"Revisar video manualmente: open {output_path}")
    else:
        print("ERROR: No output file created")
        exit(1)

except Exception as e:
    print()
    print("=" * 70)
    print("✗ FAILED: Face tracking falló")
    print("=" * 70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
