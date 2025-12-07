#!/usr/bin/env python3
"""
Diagnóstico de subtítulos duplicados

Este script ayuda a diagnosticar por qué aparecen subtítulos duplicados
(amarillos con estilo + blancos sin estilo).
"""
from pathlib import Path
import sys


def check_srt_file(srt_path: str):
    """
    Revisa un archivo SRT para detectar problemas comunes
    """
    print(f"\n{'='*80}")
    print(f"DIAGNÓSTICO: {srt_path}")
    print(f"{'='*80}\n")

    if not Path(srt_path).exists():
        print(f"❌ ERROR: Archivo no encontrado: {srt_path}")
        return

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    print(f"📊 ESTADÍSTICAS:")
    print(f"  - Total líneas: {len(lines)}")
    print(f"  - Total caracteres: {len(content)}")
    print(f"  - Encoding: utf-8")
    print()

    # Contar entradas SRT (números de subtítulo)
    subtitle_indices = [line for line in lines if line.strip().isdigit()]
    print(f"  - Total subtítulos: {len(subtitle_indices)}")
    print()

    # Detectar duplicados (mismo timestamp)
    timestamps = [line for line in lines if '-->' in line]
    timestamp_set = set(timestamps)

    if len(timestamps) != len(timestamp_set):
        print(f"⚠️  PROBLEMA DETECTADO: Timestamps duplicados")
        print(f"  - Total timestamps: {len(timestamps)}")
        print(f"  - Timestamps únicos: {len(timestamp_set)}")
        print(f"  - Duplicados: {len(timestamps) - len(timestamp_set)}")
        print()

        # Mostrar duplicados
        seen = set()
        duplicates = []
        for ts in timestamps:
            if ts in seen:
                duplicates.append(ts)
            else:
                seen.add(ts)

        if duplicates:
            print(f"  Timestamps duplicados:")
            for dup in duplicates[:5]:  # Mostrar solo primeros 5
                print(f"    - {dup}")
            if len(duplicates) > 5:
                print(f"    ... y {len(duplicates) - 5} más")
    else:
        print(f"✓ No hay timestamps duplicados")

    print()

    # Detectar metadata ASS/SSA (puede causar renderizado dual)
    has_ass_metadata = any('[Script Info]' in line or '[V4+ Styles]' in line for line in lines)
    if has_ass_metadata:
        print(f"⚠️  PROBLEMA DETECTADO: Metadata ASS/SSA encontrada")
        print(f"  El archivo tiene metadata de Advanced SubStation Alpha.")
        print(f"  Esto puede causar que FFmpeg renderice subtítulos dos veces:")
        print(f"    1. Una vez con estilo ASS (blanco por defecto)")
        print(f"    2. Otra vez con force_style (amarillo)")
        print()
    else:
        print(f"✓ No hay metadata ASS/SSA")

    print()

    # Mostrar primeras 3 entradas para inspección visual
    print(f"📄 PRIMERAS 3 ENTRADAS:")
    print(f"{'-'*80}")

    entry_count = 0
    current_entry = []

    for line in lines:
        if line.strip().isdigit() and current_entry:
            # Nueva entrada encontrada
            print('\n'.join(current_entry))
            print()
            entry_count += 1
            current_entry = [line]

            if entry_count >= 3:
                break
        else:
            current_entry.append(line)

    # Mostrar última entrada si no llegamos a 3
    if entry_count < 3 and current_entry:
        print('\n'.join(current_entry))

    print(f"{'-'*80}\n")

    # Recomendaciones
    print(f"💡 RECOMENDACIONES:")
    if len(timestamps) != len(timestamp_set):
        print(f"  1. El archivo SRT tiene duplicados - regenerar con subtitle_generator")
    elif has_ass_metadata:
        print(f"  1. Remover metadata ASS/SSA del archivo")
        print(f"  2. Usar formato SRT puro sin estilos embebidos")
    else:
        print(f"  1. El archivo SRT parece correcto")
        print(f"  2. El problema puede estar en el comando FFmpeg")
        print(f"  3. Revisar logs para ver comando FFmpeg ejecutado")

    print()


def generate_test_command():
    """
    Genera comando FFmpeg de prueba para validar subtítulos
    """
    print(f"\n{'='*80}")
    print(f"COMANDO DE PRUEBA - FFmpeg con Subtítulos")
    print(f"{'='*80}\n")

    print("Para validar que el filtro de subtítulos funciona correctamente,")
    print("ejecuta este comando en un video de prueba:\n")

    cmd = """ffmpeg \\
  -i input_video.mp4 \\
  -vf "subtitles='subtitles.srt':force_style='FontName=Arial,FontSize=18,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,Bold=0'" \\
  -c:v libx264 \\
  -c:a aac \\
  -t 10 \\
  -y test_output.mp4
"""

    print(cmd)
    print()
    print("Si este comando genera subtítulos duplicados, el problema es de FFmpeg.")
    print("Si NO genera duplicados, el problema está en video_exporter.py\n")


if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DE SUBTÍTULOS DUPLICADOS\n")

    if len(sys.argv) < 2:
        print("Uso: python diagnose_subtitles.py <archivo.srt>")
        print()
        print("Ejemplo:")
        print("  python diagnose_subtitles.py output/video_id/1.srt")
        print()

        # Buscar archivos SRT en output/
        output_dir = Path("output")
        if output_dir.exists():
            srt_files = list(output_dir.rglob("*.srt"))
            if srt_files:
                print("Archivos SRT encontrados:")
                for srt in srt_files[:5]:
                    print(f"  - {srt}")
                if len(srt_files) > 5:
                    print(f"  ... y {len(srt_files) - 5} más")
                print()
                print(f"Ejecuta: python {sys.argv[0]} {srt_files[0]}")

        generate_test_command()
        sys.exit(1)

    srt_path = sys.argv[1]
    check_srt_file(srt_path)
    generate_test_command()
