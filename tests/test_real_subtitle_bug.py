#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test REAL del bug de subtítulos duplicados
Usa datos reales del proyecto (transcripción + video)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(PROJECT_ROOT))

from src.video_exporter import VideoExporter


def main():
    # Encontrar transcripción y video reales
    transcripts = list((PROJECT_ROOT / "temp").glob("*_transcript.json"))

    if not transcripts:
        print("❌ No se encontraron transcripciones")
        return False

    transcript_path = transcripts[0]
    print(f"Encontrada transcripción: {transcript_path.name}")

    # Encontrar video correspondiente
    video_id = transcript_path.name.replace("_transcript.json", "")
    downloads_dir = PROJECT_ROOT / "downloads"

    # Buscar video con ese ID
    matching_videos = list(downloads_dir.glob(f"*{video_id[-10:]}*.mp4"))

    if not matching_videos:
        print(f"❌ No se encontró video para {video_id}")
        print(f"   Buscando en: {downloads_dir}")
        return False

    video_path = matching_videos[0]
    print(f"Encontrado video: {video_path.name}")

    # Crear exporter
    output_dir = PROJECT_ROOT / "output" / "bugfix_test"
    exporter = VideoExporter(output_dir=str(output_dir))

    # Test: Exportar UN clip con logo + subtítulos
    clips = [
        {
            "clip_id": "test_with_subs",
            "start_time": 30,
            "end_time": 45,  # 15 segundos
            "text_preview": "Testing subtitle duplication"
        }
    ]

    print("\n" + "="*70)
    print("EXPORTANDO CON LOGO + SUBTÍTULOS (Reproducir bug)")
    print("="*70 + "\n")

    exported = exporter.export_clips(
        video_path=str(video_path),
        clips=clips,
        aspect_ratio="9:16",
        video_name="bug_test",
        add_subtitles=True,
        transcript_path=str(transcript_path),
        subtitle_style="default",
        add_logo=True,
        logo_path="assets/logo.png",
        logo_position="top-right",
        logo_scale=0.1
    )

    if not exported or not exported[0]:
        print("\n❌ Error exportando clip")
        return False

    output_video = Path(exported[0])
    print(f"\n✓ Clip exportado: {output_video}")
    print(f"\n📋 INSTRUCCIONES PARA VERIFICAR:")
    print(f"1. Abre el video:")
    print(f"   open '{output_video}'")
    print(f"\n2. Observa en los segundos 30-45:")
    print(f"   - ¿Aparecen subtítulos normalmente (1 vez)?")
    print(f"   - ¿Aparecen DUPLICADOS (2 veces)?")
    print(f"   - ¿Al mismo tiempo o con offset?")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
