#!/usr/bin/env python3
"""
Test para generar comando FFmpeg con face tracking + subtítulos
y diagnosticar por qué los subtítulos se duplican.
"""

def simulate_ffmpeg_command_with_face_tracking():
    """
    Simula el comando FFmpeg que se genera cuando:
    - Face tracking: ENABLED
    - Subtítulos: ENABLED (small style)
    """
    # Simular variables
    video_reframed = "output/test/1_reframed_temp.mp4"
    video_original = "downloads/test_video.mp4"
    subtitle_file = "output/test/1.srt"
    output_file = "output/test/1.mp4"
    start_time = 10.5
    duration = 30.2

    # Simular subtitle_path_escaped
    subtitle_path_str = subtitle_file
    subtitle_path_escaped = subtitle_path_str.replace('\\', '\\\\').replace(':', '\\:')

    # Simular filtro de subtítulos (small style)
    subtitle_filter = f"subtitles='{subtitle_path_escaped}':force_style='"
    subtitle_filter += "FontName=Arial,"
    subtitle_filter += "FontSize=10,"
    subtitle_filter += "PrimaryColour=&H0000FFFF,"
    subtitle_filter += "OutlineColour=&H00000000,"
    subtitle_filter += "Outline=1,"
    subtitle_filter += "Shadow=1,"
    subtitle_filter += "Bold=0,"
    subtitle_filter += "Alignment=6,"
    subtitle_filter += "MarginV=100"
    subtitle_filter += "'"

    # Construir comando (CON FACE TRACKING)
    cmd = [
        "ffmpeg",
        "-i", str(video_reframed),      # [0] Video reframed (sin audio)
        "-ss", str(start_time),
        "-i", str(video_original),      # [1] Video original (con audio)
        "-t", str(duration),
        "-filter_complex", f"[0:v]{subtitle_filter}[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-y", str(output_file)
    ]

    print("="*80)
    print("COMANDO FFmpeg GENERADO (Face Tracking + Subtítulos):")
    print("="*80)
    print(' '.join(cmd))
    print()

    print("="*80)
    print("ANÁLISIS DEL FILTRO:")
    print("="*80)
    print(f"Filtro completo: {subtitle_filter}")
    print()

    # Detectar posibles problemas
    print("POSIBLES PROBLEMAS:")
    if "'" in subtitle_filter and '"' not in subtitle_filter:
        print("  ⚠️  Filtro usa solo comillas simples")
        print("     Esto puede causar problemas en filter_complex")
        print()

    # Generar alternativa SIN comillas en el path
    subtitle_filter_alt = f"subtitles={subtitle_path_escaped}:force_style='"
    subtitle_filter_alt += "FontName=Arial,"
    subtitle_filter_alt += "FontSize=10,"
    subtitle_filter_alt += "PrimaryColour=&H0000FFFF,"
    subtitle_filter_alt += "OutlineColour=&H00000000,"
    subtitle_filter_alt += "Outline=1,"
    subtitle_filter_alt += "Shadow=1,"
    subtitle_filter_alt += "Bold=0,"
    subtitle_filter_alt += "Alignment=6,"
    subtitle_filter_alt += "MarginV=100"
    subtitle_filter_alt += "'"

    print("="*80)
    print("SOLUCIÓN ALTERNATIVA (sin comillas en path):")
    print("="*80)
    print(f"Filtro alternativo: {subtitle_filter_alt}")
    print()

    cmd_alt = [
        "ffmpeg",
        "-i", str(video_reframed),
        "-ss", str(start_time),
        "-i", str(video_original),
        "-t", str(duration),
        "-filter_complex", f"[0:v]{subtitle_filter_alt}[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-y", str(output_file)
    ]

    print("COMANDO ALTERNATIVO:")
    print(' '.join(cmd_alt))
    print()

    # Otra alternativa: aplicar subtítulos DESPUÉS de mapear
    print("="*80)
    print("SOLUCIÓN ALTERNATIVA 2 (subtítulos fuera de filter_complex):")
    print("="*80)

    cmd_alt2 = [
        "ffmpeg",
        "-i", str(video_reframed),
        "-ss", str(start_time),
        "-i", str(video_original),
        "-t", str(duration),
        "-map", "0:v",         # Video reframed
        "-map", "1:a",         # Audio original
        "-vf", subtitle_filter,  # Subtítulos con -vf en lugar de filter_complex
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-y", str(output_file)
    ]

    print("COMANDO ALTERNATIVO 2:")
    print(' '.join(cmd_alt2))
    print()

    print("="*80)
    print("RECOMENDACIÓN:")
    print("="*80)
    print("Usar SOLUCIÓN ALTERNATIVA 2:")
    print("  - Mapear video y audio primero con -map")
    print("  - Aplicar subtítulos con -vf DESPUÉS del mapeo")
    print("  - Esto evita problemas de sintaxis en filter_complex")
    print()


if __name__ == "__main__":
    simulate_ffmpeg_command_with_face_tracking()
