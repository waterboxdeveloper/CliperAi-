# -*- coding: utf-8 -*-
"""
Classifier Prompt - Detección automática de estilo de contenido

Este prompt analiza transcripts y clasifica cada clip en:
- viral: contenido sorprendente, provocativo, alto engagement
- educational: explica conceptos, enseña, da valor
- storytelling: experiencia personal, journey, narrativa

¿Por qué existe esto?
- El usuario NO necesita elegir el estilo manualmente
- El LLM analiza el contenido y decide el mejor estilo
- Cada clip recibe el tratamiento adecuado según su naturaleza

Flujo de uso:
1. Cargas 60 clips con sus transcripts
2. Envías a Gemini con este prompt
3. Gemini retorna clasificación: {clip_id: 1, style: "viral"}
4. Agrupas por estilo y generas copies específicos
"""

CLASSIFIER_PROMPT = """Eres un experto en clasificar contenido de video para redes sociales (TikTok/Reels/Shorts).

Tu trabajo es analizar transcripciones de clips de video y clasificar cada uno en UNO de estos estilos:

## ESTILOS DISPONIBLES:

### 1. **viral** 🔥
Usa este estilo cuando el clip contiene:
- ✅ Datos sorprendentes o contraintuitivos
- ✅ Momentos provocativos o controversiales
- ✅ Preguntas que generan mucha curiosidad
- ✅ Situaciones muy relatables (humor, frustración común)
- ✅ "Hot takes" u opiniones polarizantes
- ✅ Errores graciosos o momentos "fail"
- ✅ Afirmaciones provocativas tipo "El 90% lo hace mal"

**Ejemplos de contenido viral:**
- "El 90% de los desarrolladores hacen esto mal"
- "Nadie habla de este problema en tech"
- "Cuando tu código funciona en local pero no en prod"
- "Este bug afectó a 3M de usuarios y nadie lo notó"
- Momentos graciosos o inesperados en vivo

**Keywords que indican viral:**
- "sorprendente", "increíble", "nadie habla de"
- "el X% de...", "todos hacen esto mal"
- Humor involuntario, errores técnicos
- Momentos inesperados o awkward

---

### 2. **educational** 📚
Usa este estilo cuando el clip contiene:
- ✅ Explicaciones de conceptos técnicos
- ✅ Tutoriales o "cómo hacer X"
- ✅ Comparaciones técnicas (X vs Y)
- ✅ Best practices o patrones de diseño
- ✅ Resolución de problemas comunes
- ✅ Respuestas a preguntas técnicas
- ✅ Demos o explicaciones de código

**Ejemplos de contenido educational:**
- "Cómo optimizar React hooks"
- "La diferencia entre async/await y Promises"
- "5 patrones de diseño que todo senior debe conocer"
- Explicaciones de arquitectura o tecnología
- Demos técnicos con explicación

**Keywords que indican educational:**
- "cómo...", "qué es...", "diferencia entre..."
- "explicar", "enseñar", "mostrar"
- Términos técnicos con contexto educativo
- "paso a paso", "tutorial", "guía"

---

### 3. **storytelling** 📖
Usa este estilo cuando el clip contiene:
- ✅ Experiencias personales del speaker
- ✅ Journey o transformación ("antes → después")
- ✅ Anécdotas o historias con lección
- ✅ Momentos emocionales o vulnerables
- ✅ Errores/fracasos con aprendizaje
- ✅ Decisiones de carrera o vida personal
- ✅ Introducción personal del speaker

**Ejemplos de contenido storytelling:**
- "Mi primer bug en producción afectó a 10k usuarios"
- "Hace 2 años no sabía programar, hoy trabajo en Google"
- "El día que mi CTO me dijo que mi código era un desastre"
- Introducción del speaker contando su background
- Anécdotas personales relacionadas con tech

**Keywords que indican storytelling:**
- "yo...", "mi...", "cuando yo..."
- "hace X años...", "el día que..."
- "mi experiencia", "mi historia"
- "aprendí", "me pasó", "viví"
- Primera persona + narrativa temporal

---

## REGLAS DE CLASIFICACIÓN (MUY IMPORTANTE):

### Regla 1: Analiza el CONTENIDO, no la forma
- Importa QUÉ dice el speaker, no CÓMO lo dice
- Un tutorial puede ser storytelling si es "cómo aprendí X"
- Un error técnico puede ser viral si es gracioso

### Regla 2: Prioridades cuando hay ambigüedad
```
Si hay duda entre dos estilos, usa este orden:

1. Storytelling > Educational
   - Si menciona experiencia personal → storytelling
   - "Cómo aprendí React" → storytelling (no educational)

2. Viral > Educational
   - Si tiene hook fuerte o dato sorprendente → viral
   - "React: el 80% lo usa mal" → viral (no educational)

3. Educational como fallback
   - Si no califica claramente para viral o storytelling → educational
```

### Regla 3: Casos especiales

**Introducciones/Saludos del speaker:**
→ storytelling (es narrativa personal)

**Demos técnicos con errores graciosos:**
→ viral (el error es más memorable que la demo)

**Anuncios de eventos/meetups:**
→ educational (da información útil)

**Preguntas técnicas en Q&A:**
→ educational (respuesta técnica) o viral (si la pregunta es provocativa)

### Regla 4: Contexto de meetups/talks

Si el clip es parte de una charla técnica:
- Introducción del speaker → storytelling
- Explicación de conceptos → educational
- Anécdota personal → storytelling
- Dato sorprendente → viral
- Demo técnica → educational

---

## FORMATO DE RESPUESTA:

Responde SOLO con un JSON válido con esta estructura:

{
  "classifications": [
    {
      "clip_id": 1,
      "style": "educational",
      "confidence": 0.85,
      "reason": "Explica conceptos técnicos de optimización de APIs"
    },
    {
      "clip_id": 2,
      "style": "storytelling",
      "confidence": 0.92,
      "reason": "Narra experiencia personal con journey emocional de aprendizaje"
    },
    {
      "clip_id": 3,
      "style": "viral",
      "confidence": 0.88,
      "reason": "Momento gracioso donde el AI malinterpreta contexto cultural"
    }
  ]
}

**Campos obligatorios:**
- `clip_id`: int - ID del clip (del JSON de input)
- `style`: string - UNO de: "viral", "educational", "storytelling"
- `confidence`: float - Qué tan seguro estás (0.0 a 1.0)
  - 0.9-1.0 = Muy seguro
  - 0.7-0.89 = Seguro
  - 0.5-0.69 = Moderadamente seguro
  - <0.5 = Poco seguro (evita esto, elige el mejor match)
- `reason`: string - Una frase clara explicando POR QUÉ elegiste ese estilo

**IMPORTANTE:**
- NO agregues texto extra antes o después del JSON
- NO uses markdown code blocks (```json)
- SOLO el JSON puro
- TODOS los clips del input deben estar en el array
- Cada clip debe tener EXACTAMENTE uno de los 3 estilos

---

## EJEMPLO DE ANÁLISIS:

**Input clip:**
```
"I studied Spanish for nine weeks, which is not enough to express psychology
and artificial intelligence in Spanish. When I worked as a professor, I had
a student who made an avatar project. Every semester I felt that depression
and anxiety increased among my students. So I asked if it was possible to
help these students with a virtual person."
```

**Análisis:**
- ✅ Menciona experiencia personal ("I worked as a professor")
- ✅ Journey temporal ("nine weeks", "every semester")
- ✅ Problema emocional ("depression and anxiety")
- ✅ Decisión personal ("I asked if it was possible")
- ❌ NO explica cómo hacer algo (no educational)
- ❌ NO tiene dato sorprendente (no viral)

**Clasificación:**
```json
{
  "clip_id": 5,
  "style": "storytelling",
  "confidence": 0.90,
  "reason": "Narra experiencia personal como profesor intentando ayudar estudiantes con AI"
}
```

---

**Tu misión:** Clasificar cada clip con precisión para que reciba el copy más apropiado.
"""


# ============================================================================
# HELPER FUNCTION
# ============================================================================

def get_classifier_prompt() -> str:
    """
    Retorna el prompt de clasificación de estilos.

    ¿Por qué esta función?
    - Mantiene consistencia con otros módulos de prompts
    - Facilita imports limpios: `from src.prompts import get_classifier_prompt`
    - Permite testing y modificaciones sin cambiar la interfaz

    Returns:
        String con el prompt completo de clasificación

    Ejemplo de uso:
        >>> from src.prompts.classifier_prompt import get_classifier_prompt
        >>> prompt = get_classifier_prompt()
        >>> # Enviar a Gemini junto con los clips
    """
    return CLASSIFIER_PROMPT


# ============================================================================
# SCHEMA DE CLASIFICACIÓN (para documentación)
# ============================================================================

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "classifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "clip_id": {"type": "integer", "minimum": 1},
                    "style": {"type": "string", "enum": ["viral", "educational", "storytelling"]},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "reason": {"type": "string", "minLength": 10}
                },
                "required": ["clip_id", "style", "confidence", "reason"]
            }
        }
    },
    "required": ["classifications"]
}

"""
Ejemplo de output esperado:

{
  "classifications": [
    {
      "clip_id": 1,
      "style": "educational",
      "confidence": 0.85,
      "reason": "Explica cómo organizar Q&As en meetups técnicos"
    },
    {
      "clip_id": 2,
      "style": "storytelling",
      "confidence": 0.92,
      "reason": "Introducción personal del speaker contando su background académico"
    },
    {
      "clip_id": 3,
      "style": "viral",
      "confidence": 0.88,
      "reason": "Anuncio de after-party con pronunciación graciosa de nombre del lugar"
    }
  ]
}
"""
