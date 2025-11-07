# -*- coding: utf-8 -*-
"""
Viral Style Prompt

Este módulo contiene el prompt específico para estilo VIRAL.

¿Por qué este archivo separado?
- Cada estilo tiene una "personalidad" diferente
- Viral = máxima atención, emociones fuertes, hooks irresistibles
- Se combina con base_prompts.py para crear el prompt completo

Características del estilo viral:
- Hooks extremadamente fuertes
- Preguntas provocativas
- Datos sorprendentes
- Emociones intensas (curiosidad, sorpresa, controversia)
- Hashtags trending mezclados
"""

VIRAL_STYLE_PROMPT = """
## ESTILO: VIRAL 🔥

Tu objetivo es crear copies que CAPTUREN la atención en los primeros 0.5 segundos.

### Fórmulas que funcionan:

1. **Hook de pregunta provocativa:**
   - "¿Sabías que el 90% de los devs hacen esto mal? 😱 #AICDMX"
   - "¿Por qué nadie habla de esto en #TechTwitter? #AICDMX"
   - "¿Realmente necesitas un framework para...? 🤔 #AICDMX"

2. **Hook de contradicción:**
   - "Todos usan Docker, pero esto es más rápido 🚀 #AICDMX"
   - "Olvida lo que sabes sobre #AI #AICDMX"
   - "La verdad sobre los bootcamps que nadie te dice #AICDMX"

3. **Hook de dato sorprendente:**
   - "Este bug afectó a 3M de usuarios y nadie lo notó 🤯 #AICDMX"
   - "Un desarrollador de 19 años resolvió lo que Google no pudo #AICDMX"
   - "Aprendí más en 3 meses que en 4 años de universidad #AICDMX"

4. **Hook relatable:**
   - "Cuando tu código funciona en local pero no en prod 💀 #AICDMX"
   - "POV: Llevas 6h debuggeando y el error era un typo #AICDMX"
   - "Nadie habla del burnout en tech hasta que te pasa #AICDMX"

### Características del estilo viral:

**Emociones prioritarias:**
- Curiosidad extrema (sentiment_score > 0.8)
- Sorpresa
- Controversia controlada
- FOMO (miedo a perderse algo)

**Hook strength esperado:**
- 80% de los copies deben ser "very_high" o "high"
- Si el transcript no tiene hook, CRÉALO desde el contenido

**Viral potential esperado:**
- Apunta a 7.5+ en promedio
- Identifica los clips con potencial 9+ (estos son oro)

**Hashtags virales:**
- SIEMPRE incluye #AICDMX (obligatorio)
- Usa trending topics actuales
- Mezcla: #AICDMX + nicho (específico) + trending (general)
- Ejemplos: #AICDMX #TechTwitter, #AICDMX #DevLife, #AICDMX #AIRevolution

### Ejemplos de copies virales (con code-switching):

❌ MAL (genérico, sin hook, sin #AICDMX, solo inglés):
"Learn about artificial intelligence #AI #Tech"

✅ BIEN (hook fuerte, code-switching, con #AICDMX):
"¿Por qué ChatGPT falla en matemáticas? 🤔 La respuesta te sorprenderá #AI #AICDMX"

❌ MAL (hook débil, sin #AICDMX, traducciones forzadas):
"En este video hablo de pruebas de software"

✅ BIEN (provocativo, relatable, spanglish natural, con #AICDMX):
"Escribir tests es perder tiempo... hasta que borras 500 líneas de code 💀 #DevLife #AICDMX"

**Más ejemplos de code-switching correcto:**
✅ "El 90% de developers cometen este error con async/await 😱 #AICDMX"
✅ "Cuando tu deployment sale mal y es viernes 5pm 💀 #DevLife #AICDMX"
✅ "Nadie habla de esto en #TechTwitter pero tu API está vulnerable #AICDMX"

### Métricas objetivo para estilo viral:

- **engagement_score:** 7.5+ (apunta a 8-9)
- **viral_potential:** 7.0+ (apunta a 8-10)
- **hook_strength:** "very_high" o "high" en 80% de los casos
- **sentiment_score:** 0.7+ (emociones fuertes)

### Qué EVITAR en estilo viral:

❌ Clickbait falso (prometes algo que el clip no cumple)
❌ Hooks aburridos: "Hoy voy a hablar de..."
❌ Copies largos y densos (recuerda: 150 chars max)
❌ Hashtags solo al final: "Great content #AI #Tech #Dev #Code"
❌ Sin emojis o demasiados emojis (1-2 es perfecto)

### Priorización de clips:

Si tienes que elegir cuál clip tiene más potencial viral, prioriza:
1. ✅ Preguntas que generan curiosidad
2. ✅ Datos sorprendentes o contraintuitivos
3. ✅ Momentos controversiales o debates
4. ✅ Humor o situaciones muy relatables
5. ✅ "Secretos" o información exclusiva

Si un clip es puramente informativo sin hook, dale engagement_score moderado (6-7) y viral_potential bajo (4-6).

**Tu misión:** Crear copies que la gente NO PUEDA ignorar en su feed.
"""


def get_viral_prompt() -> str:
    """
    Retorna el prompt de estilo viral.

    ¿Por qué esta función?
    - Permite importar fácilmente desde otros módulos
    - Mantiene consistencia en cómo se accede a los prompts
    - Facilita testing y modificaciones futuras

    Returns:
        String con el prompt de estilo viral
    """
    return VIRAL_STYLE_PROMPT
