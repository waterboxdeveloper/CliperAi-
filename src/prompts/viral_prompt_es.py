# -*- coding: utf-8 -*-
"""
Viral Style Prompt - Spanish (ES)

Este módulo contiene el prompt específico para estilo VIRAL en español.

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
- NUEVO: Comienza CON las palabras exactas del hablante
"""

VIRAL_STYLE_PROMPT_ES = """
## ESTILO: VIRAL 🔥

Tu objetivo es crear copies que CAPTUREN la atención en los primeros 0.5 segundos.

===== CRÍTICO: PALABRAS DE APERTURA =====
El copy DEBE comenzar con estas palabras exactas dichas por el hablante:
"{opening_words}"

NO las parafrasees. Úsalas EXACTAMENTE como están. Esto es innegociable.

===== FÓRMULA: [PALABRAS_APERTURA] + [TU_HOOK] =====

### Fórmulas que funcionan:

1. **Hook de pregunta provocativa después de apertura:**
   - "[Opening words] ¿Por qué nadie habla de esto en #TechTwitter? {mandatory_hashtags}"
   - "[Opening words] ¿Realmente necesitas un framework para...? 🤔 {mandatory_hashtags}"

2. **Hook de contradicción después de apertura:**
   - "[Opening words] pero esto es más rápido 🚀 {mandatory_hashtags}"
   - "[Opening words] Olvida lo que sabes sobre #AI {mandatory_hashtags}"

3. **Hook de dato sorprendente después de apertura:**
   - "[Opening words] Este bug afectó a 3M de usuarios y nadie lo notó 🤯 {mandatory_hashtags}"
   - "[Opening words] Un desarrollador de 19 años resolvió lo que Google no pudo {mandatory_hashtags}"

4. **Hook relatable después de apertura:**
   - "[Opening words] Cuando tu código funciona en local pero no en prod 💀 {mandatory_hashtags}"
   - "[Opening words] POV: Llevas 6h debuggeando y el error era un typo {mandatory_hashtags}"

### Características del estilo viral:

**Emociones prioritarias:**
- Curiosidad extrema (sentiment_score > 0.8)
- Sorpresa
- Controversia controlada
- FOMO (miedo a perderse algo)

**Hook strength esperado:**
- 80% de los copies deben ser "very_high" o "high"
- Si el transcript no tiene hook adicional, el opening words es suficiente

**Viral potential esperado:**
- Apunta a 7.5+ en promedio
- Identifica los clips con potencial 9+ (estos son oro)

**Hashtags virales:**
- SIEMPRE incluye {mandatory_hashtags} (obligatorio)
- Usa trending topics actuales
- Mezcla: {mandatory_hashtags} + nicho (específico) + trending (general)
- Ejemplos: {hashtag_example}

### Ejemplo correcto (con opening words):

✅ BIEN (opening words + hook fuerte, con {mandatory_hashtags}):
"La IA es revolucionaria. 3 formas en que cambió mi negocio en 3 meses 🚀 #AI {hashtag_example}"
- Opening words: "La IA es revolucionaria" (del speaker)
- Hook: "3 formas en que cambió..." (tu continuación)

### Qué EVITAR en estilo viral:

❌ Cambiar las palabras de apertura
❌ Clickbait falso (prometes algo que el clip no cumple)
❌ Hooks aburridos sin contraposición
❌ Copies largos y densos (recuerda: 150 chars max)
❌ Sin emojis o demasiados emojis (1-2 es perfecto)

### Métricas objetivo para estilo viral:

- **engagement_score:** 7.5+ (apunta a 8-9)
- **viral_potential:** 7.0+ (apunta a 8-10)
- **hook_strength:** "very_high" o "high" en 80% de los casos
- **sentiment_score:** 0.7+ (emociones fuertes)

**Tu misión:** Crear copies que la gente NO PUEDA ignorar en su feed.
Las palabras del hablante son tu punto de partida. Tu job es el hook que sigue.
"""


def get_viral_prompt_es() -> str:
    """
    Retorna el prompt de estilo viral en español.

    Returns:
        String con el prompt de estilo viral (español)
    """
    return VIRAL_STYLE_PROMPT_ES
