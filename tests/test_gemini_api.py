#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script para verificar que la API de Gemini funciona correctamente.

Este script prueba:
1. Que la API key esté configurada
2. Que el modelo gemini-2.5-flash funcione
3. Que pueda generar respuestas JSON válidas
4. Que respete el formato solicitado

Uso:
    uv run python tests/test_gemini_api.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir src al path para importar
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_google_genai import ChatGoogleGenerativeAI


def test_api_key():
    """Test 1: Verificar que la API key esté configurada"""
    print("=" * 60)
    print("TEST 1: API Key Configuration")
    print("=" * 60)

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("❌ FAIL: GOOGLE_API_KEY no está configurada en .env")
        return False

    print(f"✓ API Key encontrada: {api_key[:20]}...")
    return True


def test_basic_connection():
    """Test 2: Verificar que podemos conectarnos al modelo"""
    print("\n" + "=" * 60)
    print("TEST 2: Basic Model Connection")
    print("=" * 60)

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1
        )

        response = llm.invoke("Say 'Hello World' in one sentence.")
        print(f"✓ Modelo inicializado correctamente")
        print(f"✓ Respuesta: {response.content}")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error al conectar con el modelo")
        print(f"   Error: {e}")
        return False


def test_json_generation():
    """Test 3: Verificar que puede generar JSON válido"""
    print("\n" + "=" * 60)
    print("TEST 3: JSON Generation")
    print("=" * 60)

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3
        )

        prompt = """Generate a JSON object with the following structure:
{
  "name": "John Doe",
  "age": 30,
  "city": "New York"
}

Respond ONLY with valid JSON (no markdown, no explanations):"""

        response = llm.invoke(prompt)
        response_text = response.content.strip()

        # Limpiar respuesta si viene con markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        response_text = response_text.strip()

        print(f"Raw response:\n{response_text}\n")

        # Intentar parsear JSON
        data = json.loads(response_text)

        print(f"✓ JSON válido generado")
        print(f"✓ Datos parseados: {data}")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ FAIL: El modelo no generó JSON válido")
        print(f"   Error: {e}")
        print(f"   Response: {response_text}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error al generar JSON")
        print(f"   Error: {e}")
        return False


def test_clip_classification():
    """Test 4: Simular clasificación de un clip (caso real)"""
    print("\n" + "=" * 60)
    print("TEST 4: Clip Classification (Real Use Case)")
    print("=" * 60)

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7
        )

        # Simular un clip real
        clip_data = {
            "clip_id": 1,
            "transcript": "Hoy vamos a hablar sobre React hooks. Los hooks son una forma de usar state y otras características de React sin escribir una clase. El hook más común es useState.",
            "duration": 45
        }

        prompt = f"""Clasifica este clip de video en uno de estos estilos: viral, educational, storytelling.

Clip:
{json.dumps(clip_data, indent=2, ensure_ascii=False)}

Responde SOLO con JSON en este formato (sin markdown):
{{
  "clip_id": 1,
  "style": "viral",
  "confidence": 0.85,
  "reason": "Brief explanation"
}}"""

        response = llm.invoke(prompt)
        response_text = response.content.strip()

        # Limpiar respuesta
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        response_text = response_text.strip()

        print(f"Raw response:\n{response_text}\n")

        # Parsear JSON
        classification = json.loads(response_text)

        # Validar estructura
        required_fields = ["clip_id", "style", "confidence", "reason"]
        for field in required_fields:
            if field not in classification:
                print(f"❌ FAIL: Falta el campo '{field}' en la respuesta")
                return False

        # Validar que style sea válido
        valid_styles = ["viral", "educational", "storytelling"]
        if classification["style"] not in valid_styles:
            print(f"❌ FAIL: Style '{classification['style']}' no es válido")
            return False

        print(f"✓ Clasificación correcta generada")
        print(f"✓ Style: {classification['style']}")
        print(f"✓ Confidence: {classification['confidence']}")
        print(f"✓ Reason: {classification['reason']}")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error en clasificación")
        print(f"   Error: {e}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return False


def test_copy_generation():
    """Test 5: Generar un copy para un clip (caso real)"""
    print("\n" + "=" * 60)
    print("TEST 5: Copy Generation (Real Use Case)")
    print("=" * 60)

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.8
        )

        # Simular un clip real
        clip_data = {
            "clip_id": 1,
            "transcript": "Hoy vamos a hablar sobre React hooks. Los hooks son una forma de usar state y otras características de React sin escribir una clase.",
            "duration": 45
        }

        prompt = f"""Genera un copy viral para este clip de video sobre tecnología.

Requisitos:
- Mezcla español e inglés (code-switching)
- Máximo 150 caracteres
- Incluye emojis relevantes
- DEBE incluir el hashtag #AICDMX
- Genera engagement

Clip:
{json.dumps(clip_data, indent=2, ensure_ascii=False)}

Responde SOLO con JSON (sin markdown):
{{
  "clip_id": 1,
  "copy": "El copy aquí con #AICDMX",
  "metadata": {{
    "sentiment": "curious_educational",
    "engagement_score": 8.5,
    "viral_potential": 7.8,
    "primary_topics": ["React", "hooks"]
  }}
}}"""

        response = llm.invoke(prompt)
        response_text = response.content.strip()

        # Limpiar respuesta
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        response_text = response_text.strip()

        print(f"Raw response:\n{response_text}\n")

        # Parsear JSON
        copy_data = json.loads(response_text)

        # Validar estructura
        if "copy" not in copy_data:
            print(f"❌ FAIL: Falta el campo 'copy'")
            return False

        # Validar que tenga #AICDMX
        if "#AICDMX" not in copy_data["copy"].upper():
            print(f"❌ FAIL: El copy no incluye #AICDMX")
            print(f"   Copy: {copy_data['copy']}")
            return False

        print(f"✓ Copy generado correctamente")
        print(f"✓ Copy: {copy_data['copy']}")
        print(f"✓ Metadata: {copy_data.get('metadata', {})}")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error generando copy")
        print(f"   Error: {e}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "GEMINI API TEST SUITE" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    tests = [
        test_api_key,
        test_basic_connection,
        test_json_generation,
        test_clip_classification,
        test_copy_generation
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            import traceback
            print(traceback.format_exc())
            results.append(False)

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - Test {i}: {test.__name__}")

    print()
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron! La API de Gemini está funcionando correctamente.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) fallaron. Revisa la configuración.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
