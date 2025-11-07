# -*- coding: utf-8 -*-
"""
Test completo del generador de copys con threshold ajustado
"""
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.copys_generator import generate_copys_for_video


def test_full_generation():
    """
    Test completo: clasificación → agrupación → generación → guardado
    """
    print("\n" + "="*80)
    print("TEST: Generación completa de copys (con threshold 0.75)")
    print("="*80 + "\n")

    video_id = "AI CDMX Live Stream_gjPVlCHU9OM"
    model = "gemini-2.0-flash-exp"

    print(f"📹 Video ID: {video_id}")
    print(f"🤖 Model: {model}")
    print()

    result = generate_copys_for_video(
        video_id=video_id,
        model=model
    )

    print("\n" + "="*80)
    print("RESULTADO:")
    print("="*80)

    if result['success']:
        print(f"✅ SUCCESS")
        print(f"   Total copies: {result['metrics']['total_copies']}")
        print(f"   Avg engagement: {result['metrics']['average_engagement']}/10")
        print(f"   Avg viral potential: {result['metrics']['average_viral_potential']}/10")
        print(f"\n   Distribution:")
        print(f"   - Viral: {result['metrics']['distribution']['viral']}")
        print(f"   - Educational: {result['metrics']['distribution']['educational']}")
        print(f"   - Storytelling: {result['metrics']['distribution']['storytelling']}")
        print(f"\n   Output: {result['output_file']}")

        # Verificar que ningún copy exceda 150 caracteres
        from pathlib import Path
        import json

        output_path = Path(result['output_file'])
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"\n🔍 Validación de longitud de copys:")
            over_limit = []
            for clip in data['clips']:
                copy_len = len(clip['copy'])
                if copy_len > 150:
                    over_limit.append((clip['clip_id'], copy_len, clip['copy']))

            if over_limit:
                print(f"   ❌ {len(over_limit)} copys exceden 150 caracteres:")
                for clip_id, length, copy in over_limit:
                    print(f"      Clip {clip_id}: {length} chars")
                    print(f"      Copy: {copy}")
            else:
                print(f"   ✅ Todos los copys están dentro del límite de 150 caracteres")
    else:
        print(f"❌ FAILED")
        print(f"   Error: {result.get('error_message', 'Unknown error')}")
        if 'logs' in result:
            print(f"\n   Logs:")
            for log in result['logs']:
                print(f"      {log}")

    print("\n" + "="*80 + "\n")

    return result


if __name__ == "__main__":
    test_full_generation()
