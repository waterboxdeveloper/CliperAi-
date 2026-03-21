# -*- coding: utf-8 -*-
"""
Educational Style Prompt - Spanish (ES)

Este módulo contiene el prompt específico para estilo EDUCATIONAL en español.

¿Por qué este archivo separado?
- Educational tiene objetivos diferentes a viral
- Prioriza claridad y valor educativo sobre shock value
- Se combina con base_prompts.py para crear el prompt completo
- NUEVO: Comienza CON las palabras exactas del hablante

Características del estilo educational:
- Hooks basados en aprendizaje
- Promesas de conocimiento concreto
- Estructura clara y directa
- Enfoque en utilidad y takeaways
"""

EDUCATIONAL_STYLE_PROMPT_ES = """
## ESTILO: EDUCATIONAL 📚

Tu objetivo es crear copies que prometan VALOR EDUCATIVO claro y específico.

===== CRÍTICO: PALABRAS DE APERTURA =====
El copy DEBE comenzar con estas palabras exactas dichas por el hablante:
"{opening_words}"

NO las parafrasees. Úsalas EXACTAMENTE como están. Esto es innegociable.

===== FÓRMULA: [PALABRAS_APERTURA] + [TU_HOOK] =====

### Fórmulas que funcionan:

1. **Hook de aprendizaje directo:**
   - "[Opening words] 3 formas de optimizar React hooks que no conocías #AICDMX"
   - "[Opening words] Cómo debuggear memory leaks en 5 minutos #AICDMX"
   - "[Opening words] La diferencia entre async/await y Promises explicada simple #AICDMX"

2. **Hook de problema → solución:**
   - "[Opening words] ¿Tu API es lenta? Esta técnica redujo latencia en 80% #AICDMX"
   - "[Opening words] Cómo evité 3 horas de debugging con esta regla #AICDMX"
   - "[Opening words] El error de TypeScript que todos cometemos (y cómo arreglarlo) #AICDMX"

3. **Hook de lista o framework:**
   - "[Opening words] 5 patrones de diseño que todo senior debe conocer #AICDMX"
   - "[Opening words] La checklist de code review que uso en producción #AICDMX"
   - "[Opening words] 4 principios de clean code con ejemplos reales #AICDMX"

4. **Hook de "aprende lo que yo aprendí":**
   - "[Opening words] Lo que aprendí después de 100 entrevistas técnicas #AICDMX"
   - "[Opening words] Migré 1M de usuarios a microservicios: esto NO funcionó #AICDMX"
   - "[Opening words] Lessons learned: 2 años como tech lead #AICDMX"

### Características del estilo educational:

**Emociones prioritarias:**
- Curiosidad educativa (sentiment: "curious_educational")
- Confianza ("Voy a aprender algo útil")
- Claridad (el copy debe ser crystal clear)

**Hook strength esperado:**
- 70% deben ser "high" o "medium"
- El hook debe prometer un takeaway concreto
- Evita hooks sensacionalistas, prioriza especificidad

**Engagement score esperado:**
- Apunta a 7.0-8.5 en promedio
- Educational tiene menos shares que viral, pero más saves
- Audiencia más comprometida (mayor watch time)

**Viral potential esperado:**
- Más moderado: 6.0-8.0 es perfecto
- No todo content educativo debe ser viral
- Prioriza utilidad sobre shock value

**Hashtags educativos:**
- SIEMPRE incluye #AICDMX (obligatorio)
- Usa hashtags de comunidades de aprendizaje
- Ejemplos: #AICDMX #LearnToCode, #AICDMX #DevTips, #AICDMX #CodeNewbie
- Mezcla: #AICDMX + nicho técnico + comunidad

### Ejemplos de copies educativos (con code-switching):

❌ MAL (demasiado vago, sin #AICDMX, solo inglés):
"Learn about APIs #coding"

✅ BIEN (específico, promete valor, code-switching, con #AICDMX):
"Cómo estructurar REST APIs que escalan a millones de requests #AICDMX"

❌ MAL (clickbait sin sustancia, sin #AICDMX):
"Este truco de CSS te volará la mente 🤯"

✅ BIEN (promesa clara, code-switching, con #AICDMX):
"3 propiedades CSS que reemplazan JavaScript (con ejemplos) #FrontendDev #AICDMX"

❌ MAL (hook débil, sin #AICDMX, traducciones forzadas):
"Hoy hablo de pruebas en Python"

✅ BIEN (problema + solución, spanglish natural, con #AICDMX):
"¿Tus tests tardan 10 minutos? pytest-xdist los reduce a 2 #Python #AICDMX"

**Más ejemplos de code-switching educational:**
✅ "Cómo debuggear memory leaks en React en 5 pasos #AICDMX"
✅ "La diferencia entre async/await y Promises explicada simple #JavaScript #AICDMX"
✅ "Por qué tu API es lenta: 3 técnicas de optimización #BackendDev #AICDMX"

### Métricas objetivo para estilo educational:

- **engagement_score:** 7.0-8.5 (engagement sostenido)
- **viral_potential:** 6.0-8.0 (no necesita ser extremo)
- **hook_strength:** "high" o "medium" mayormente
- **sentiment:** Prioriza "educational" y "curious_educational"
- **sentiment_score:** 0.6-0.8 (confianza y claridad)

### Qué EVITAR en estilo educational:

❌ Promesas vagas: "Mejora tu código"
❌ Clickbait sin sustancia: "El secreto que los seniors no quieren que sepas"
❌ Hooks emocionales sin contenido: "Esto me hizo llorar 😭"
❌ Copies sin takeaway claro
❌ Hashtags genéricos: #programming #code #tech

### Qué PRIORIZAR:

✅ Especificidad: "React hooks" > "React" > "JavaScript"
✅ Números concretos: "3 técnicas" > "algunas técnicas"
✅ Problema/solución clara
✅ Frameworks o listas (cerebro humano ama estructura)
✅ Lenguaje directo y sin fluff

### Priorización de clips:

Si tienes que elegir cuál clip tiene más potencial educativo, prioriza:
1. ✅ Explica un concepto complejo de forma simple
2. ✅ Resuelve un problema común (debugging, optimización, etc.)
3. ✅ Comparte experiencias con takeaways concretos
4. ✅ Compara opciones (X vs Y: cuándo usar cada uno)
5. ✅ Errores comunes y cómo evitarlos

Si un clip es puro entertainment sin valor educativo, dale engagement_score bajo (5-6) para este estilo.

**Tu misión:** Crear copies que hagan que la audiencia diga "Voy a guardar esto para después".
"""


def get_educational_prompt_es() -> str:
    """
    Retorna el prompt de estilo educational en español.

    Returns:
        String con el prompt de estilo educational (español)
    """
    return EDUCATIONAL_STYLE_PROMPT_ES