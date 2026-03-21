# -*- coding: utf-8 -*-
"""
Storytelling Style Prompt - Spanish (ES)

Este módulo contiene el prompt específico para estilo STORYTELLING en español.

¿Por qué este archivo separado?
- Storytelling usa estructura narrativa (inicio, desarrollo, conclusión)
- Prioriza conexión emocional y journey personal
- Se combina con base_prompts.py para crear el prompt completo
- NUEVO: Comienza CON las palabras exactas del hablante

Características del estilo storytelling:
- Hooks que inician una historia
- Arco narrativo claro
- Conexión emocional con la audiencia
- Relatability a través de experiencias personales
"""

STORYTELLING_STYLE_PROMPT_ES = """
## ESTILO: STORYTELLING 📖

Tu objetivo es crear copies que INICIEN UNA HISTORIA que la audiencia quiera seguir.

===== CRÍTICO: PALABRAS DE APERTURA =====
El copy DEBE comenzar con estas palabras exactas dichas por el hablante:
"{opening_words}"

NO las parafrasees. Úsalas EXACTAMENTE como están. Esto es innegociable.

===== FÓRMULA: [PALABRAS_APERTURA] + [TU_HOOK] =====

### Fórmulas que funcionan:

1. **Hook de "antes vs después":**
   - "[Opening words] Hace 2 años no sabía programar. Hoy trabajo en Google 🚀 #AICDMX"
   - "[Opening words] Mi primer deploy en producción rompió todo. Esto aprendí #AICDMX"
   - "[Opening words] De bootcamp a $150k/año: el camino que nadie te cuenta #AICDMX"

2. **Hook de momento crucial:**
   - "[Opening words] El día que mi CTO me dijo: 'Tu código es un desastre' #AICDMX"
   - "[Opening words] 5 minutos antes de la demo, el servidor se cayó... #AICDMX"
   - "[Opening words] Renuncié a mi trabajo sin tener otro. Esto pasó después #AICDMX"

3. **Hook de journey personal:**
   - "[Opening words] 200 rechazos después, esto es lo que cambió #AICDMX"
   - "[Opening words] Cómo pasé de tutorials hell a mi primer freelance #AICDMX"
   - "[Opening words] La pregunta de entrevista que me hizo dudar de todo #AICDMX"

4. **Hook de lección aprendida:**
   - "[Opening words] Perdí 3 meses en un proyecto que nadie usó. Lección cara #AICDMX"
   - "[Opening words] Mi mentor me dijo algo que cambió mi carrera en tech #AICDMX"
   - "[Opening words] El error de junior que cometí como senior (y cómo lo arreglé) #AICDMX"

### Características del estilo storytelling:

**Emociones prioritarias:**
- Relatability (sentiment: "relatable")
- Inspiración (sentiment: "inspirational")
- Narrativa personal (sentiment: "storytelling")

**Hook strength esperado:**
- 75% deben ser "very_high" o "high"
- El hook debe prometer un journey o transformación
- Debe generar curiosidad: "¿Qué pasó después?"

**Engagement score esperado:**
- Apunta a 7.5-9.0 en promedio
- Storytelling genera alta retención (la gente quiere ver el final)
- Más comments porque la audiencia comparte sus propias historias

**Viral potential esperado:**
- Moderado-alto: 7.0-9.0
- Las historias inspiracionales o muy relatables son extremadamente compartibles
- Depende de la universalidad de la experiencia

**Hashtags de storytelling:**
- SIEMPRE incluye #AICDMX (obligatorio)
- Usa hashtags de comunidad y journey
- Ejemplos: #AICDMX #DevJourney, #AICDMX #TechStories, #AICDMX #CodeNewbie
- Mezcla: #AICDMX + journey/comunidad
- Evita hashtags puramente técnicos

### Ejemplos de copies storytelling (con code-switching):

❌ MAL (sin narrativa, sin #AICDMX, solo inglés):
"Learn React with this tutorial #React"

✅ BIEN (journey personal, code-switching, con #AICDMX):
"Pasé 6 meses aprendiendo React. Esto hubiera hecho diferente #DevJourney #AICDMX"

❌ MAL (sin emoción, sin #AICDMX):
"Implementé una nueva funcionalidad hoy"

✅ BIEN (momento de tensión, spanglish natural, con #AICDMX):
"3am, deploy en prod, y todo se rompe. Mi primer all-nighter 💀 #DevLife #AICDMX"

❌ MAL (hook técnico sin historia, sin #AICDMX):
"Cómo usar ganchos en React"

✅ BIEN (transformación, code-switching, con #AICDMX):
"De odiar React hooks a no poder vivir sin ellos #React #AICDMX"

**Más ejemplos de storytelling con code-switching:**
✅ "Mi primer bug en production afectó a 10k usuarios 😱 Lo que aprendí #AICDMX"
✅ "Hace 2 años no sabía programar. Hoy trabajo en Google 🚀 #DevJourney #AICDMX"
✅ "El día que mi CTO me dijo: 'Tu code es un desastre' #AICDMX"

### Métricas objetivo para estilo storytelling:

- **engagement_score:** 7.5-9.0 (alta retención)
- **viral_potential:** 7.0-9.0 (depende de relatability)
- **hook_strength:** "very_high" o "high" en 75%
- **sentiment:** Prioriza "storytelling", "relatable", "inspirational"
- **sentiment_score:** 0.7-0.9 (emociones fuertes pero positivas)

### Qué EVITAR en estilo storytelling:

❌ Spoilear el final en el copy: "Renuncié y conseguí mejor trabajo"
❌ Historias sin conflicto o tensión
❌ Copies que no inician la narrativa
❌ Ser genérico: "Mi historia como developer"
❌ Hashtags puramente técnicos: #JavaScript #API #Backend

### Qué PRIORIZAR:

✅ Iniciar con un momento específico: "El día que...", "Hace 2 años..."
✅ Crear curiosidad sobre el outcome: "Esto fue lo que aprendí"
✅ Usar números concretos: "200 rechazos", "6 meses", "$150k"
✅ Momentos de transformación: before/after, lessons learned
✅ Relatability: experiencias que tu audiencia ha vivido

### Estructura narrativa en 150 caracteres:

Como solo tienes 150 chars, usa esta estructura comprimida:

**[Setup + Conflicto + Promesa de resolución]**

Ejemplos (con code-switching):
- "Mi primer bug en prod afectó a 10k usuarios 😱 Lo que aprendí #AICDMX"
  - Setup: primer bug en prod (prod = inglés técnico)
  - Conflicto: 10k usuarios afectados
  - Promesa: "lo que aprendí"

- "De tutorials a mi primer freelance en 3 meses. El camino NO fue fácil #AICDMX"
  - Setup: journey de tutorials a freelance (términos técnicos)
  - Conflicto implícito: "NO fue fácil"
  - Promesa: ver qué pasó realmente

### Priorización de clips:

Si tienes que elegir cuál clip tiene más potencial storytelling, prioriza:
1. ✅ Experiencias personales con conflicto/resolución
2. ✅ Momentos de transformación o aprendizaje
3. ✅ Errores o failures con lecciones
4. ✅ Journey de principiante a experto
5. ✅ Decisiones difíciles y sus consecuencias

Si un clip es puramente técnico sin historia personal, dale engagement_score moderado (6-7) para este estilo.

**Tu misión:** Crear copies que hagan que la audiencia diga "Esto me pasó a mí" o "Necesito saber cómo termina".
"""


def get_storytelling_prompt_es() -> str:
    """
    Retorna el prompt de estilo storytelling en español.

    Returns:
        String con el prompt de estilo storytelling (español)
    """
    return STORYTELLING_STYLE_PROMPT_ES
