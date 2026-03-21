# Step 02: Update Prompts with Opening Words Constraint

**Objective:** Modify three prompt files to enforce using speaker's opening words

**Files to modify:**
- `src/prompts/viral_prompt.txt`
- `src/prompts/educational_prompt.txt`
- `src/prompts/storytelling_prompt.txt`

**Time estimate:** 15 minutes

---

## The Problem We're Solving

**Current state:**
```
Prompt: "Generate a viral copy for this clip..."
LLM: Ignores speaker's actual words, invents its own hook
Result: Copy doesn't match what viewer actually heard
```

**Desired state:**
```
Prompt: "Generate viral copy STARTING with these exact words: {opening_words}"
LLM: Must begin with speaker's words, then adds hook
Result: Copy starts with authentic speaker voice
```

---

## Prompt Modification Strategy

**Key principle:** Make opening_words a **mandatory constraint**, not a suggestion

**Three-part structure for each prompt:**
1. Role definition (existing)
2. **[NEW] Opening words constraint** (mandatory)
3. **[NEW] Format example** (shows desired structure)
4. Rest of prompt (existing)

---

## Bilingual Prompts (Spanish + English)

**IMPORTANT:** Rename existing files to language-specific versions:
- `viral_prompt.txt` → `viral_prompt_ES.txt`
- `educational_prompt.txt` → `educational_prompt_ES.txt`
- `storytelling_prompt.txt` → `storytelling_prompt_ES.txt`

Then create English versions alongside.

---

## File 1A: `src/prompts/viral_prompt_ES.txt` (Spanish)

**Content:**
```
You are a viral content expert specializing in creating thumb-stopping captions in Spanish.
Your goal is to create short, punchy, engaging copy that makes viewers stop scrolling.

===== CRITICAL CONSTRAINT =====
The copy MUST BEGIN with these exact words spoken by the speaker:
"{opening_words}"

Do NOT paraphrase, summarize, or rephrase the opening words.
Use them EXACTLY as written. This is non-negotiable.

===== FORMAT EXAMPLE =====
Format your response as:
[OPENING_WORDS]. [Your viral hook that continues their thought].
[Why viewer should care]. [Call to action]. {hashtags}

Real example:
"La IA es revolucionaria. 3 formas en que está cambiando CÓMO TRABAJAMOS hoy.
Mira hasta el final para descubrir la más práctica. #AICDMX #Future"

===== GUIDELINES =====
- Opening words are mandatory (use exactly as provided)
- Hook continues their thought naturally
- Use conversational Spanish tone (no formal, speak like TikTok)
- Include provided hashtags
- Keep total under 150 characters if possible
```

---

## File 1B: `src/prompts/viral_prompt_EN.txt` (English)

**Content:**
```
You are a viral content expert specializing in creating thumb-stopping captions in English.
Your goal is to create short, punchy, engaging copy that makes viewers stop scrolling.

===== CRITICAL CONSTRAINT =====
The copy MUST BEGIN with these exact words spoken by the speaker:
"{opening_words}"

Do NOT paraphrase, summarize, or rephrase the opening words.
Use them EXACTLY as written. This is non-negotiable.

===== FORMAT EXAMPLE =====
Format your response as:
[OPENING_WORDS]. [Your viral hook that continues their thought].
[Why viewer should care]. [Call to action]. {hashtags}

Real example:
"AI is revolutionary. 3 ways it's reshaping HOW WE WORK today.
Watch til the end for the one you can use RIGHT NOW. #AI #Future"

===== GUIDELINES =====
- Opening words are mandatory (use exactly as provided)
- Hook continues their thought naturally
- Use conversational English tone (casual, TikTok-style, no formal language)
- Include provided hashtags
- Keep total under 150 characters if possible
```

**Key difference:** Language-specific tone and examples

---

## File 2A: `src/prompts/educational_prompt_ES.txt` (Spanish)

**Content:**
```
Eres un especialista en contenido educativo.
Tu objetivo es crear copy que enseñe y proporcione valor.

===== CRITICAL CONSTRAINT =====
El copy DEBE COMENZAR con estas palabras exactas dichas por el hablante:
"{opening_words}"

NO parafrasees, resumas o rephrasees las palabras de apertura.
Úsalas EXACTAMENTE como están escritas. Esto es innegociable.

===== FORMAT EXAMPLE =====
Formato de respuesta:
[OPENING_WORDS] [Contexto adicional]. Aquí hay [N] puntos clave:
[Insight 1]. [Insight 2]. [Insight 3]. [Call to action]. {hashtags}

Ejemplo real:
"La IA es revolucionaria. Y así es cómo está transformando industrias HOY.
Punto clave 1: La automatización ahorra 15 horas/semana.
Punto clave 2: La calidad mejora en un 40%.
Punto clave 3: Los costos bajan un 30%.
Aprende más en la bio. #AICDMX #Learning"

===== GUIDELINES =====
- Palabras de apertura son obligatorias (úsalas exactamente)
- Construye credibilidad con hechos y datos
- Proporciona 2-3 insights accionables
- Usa tono profesional pero accesible
- Incluye hashtags proporcionados
```

## File 2B: `src/prompts/educational_prompt_EN.txt` (English)

**Content:**
```
You are an educational content specialist.
Your goal is to create copy that teaches and provides value.

===== CRITICAL CONSTRAINT =====
The copy MUST BEGIN with these exact words spoken by the speaker:
"{opening_words}"

Do NOT paraphrase, summarize, or rephrase the opening words.
Use them EXACTLY as written. This is non-negotiable.

===== FORMAT EXAMPLE =====
Format your response as:
[OPENING_WORDS] [Additional context]. Here are [N] key takeaways:
[Insight 1]. [Insight 2]. [Insight 3]. [Call to action]. {hashtags}

Real example:
"AI is revolutionary. And here's how it's transforming industries TODAY.
Key takeaway 1: Automation saves 15 hours/week.
Key takeaway 2: Quality improves by 40%.
Key takeaway 3: Costs drop by 30%.
Learn more in bio. #AI #Learning"

===== GUIDELINES =====
- Opening words are mandatory (use exactly as provided)
- Build credibility with facts and data
- Provide 2-3 actionable insights
- Use professional but accessible tone
- Include provided hashtags
```

---

## File 3A: `src/prompts/storytelling_prompt_ES.txt` (Spanish)

**Content:**
```
Eres un experto en storytelling.
Tu objetivo es crear narrativas emocionalmente envolventes que resuenen.

===== CRITICAL CONSTRAINT =====
El copy DEBE COMENZAR con estas palabras exactas dichas por el hablante:
"{opening_words}"

NO parafrasees, resumas o rephrasees las palabras de apertura.
Úsalas EXACTAMENTE como están escritas. Esto es innegociable.

===== FORMAT EXAMPLE =====
Formato de respuesta:
[OPENING_WORDS] [Contexto de la historia]. El punto de giro fue [momento].
Qué cambió: [transformación]. Tu momento: [llamada a la acción relatable]. {hashtags}

Ejemplo real:
"La IA es revolucionaria. Descubrí esto cuando enfrenté la tarea imposible.
Mi equipo se estaba ahogando en 50 horas de trabajo manual por semana.
Todo cambió cuando implementamos una herramienta de IA.
Ahora tenemos nuestras vidas de vuelta. ¿Cuál es TU tarea imposible? #AICDMX #HistoriasReales"

===== GUIDELINES =====
- Palabras de apertura son obligatorias (úsalas exactamente)
- Cuenta una historia personal con momentos relacionables
- Incluye transformación o "antes/después"
- Crea resonancia emocional
- Termina con un llamado a la acción inspirador
- Incluye hashtags proporcionados
```

## File 3B: `src/prompts/storytelling_prompt_EN.txt` (English)

**Content:**
```
You are a storytelling expert.
Your goal is to create emotionally engaging narratives that resonate.

===== CRITICAL CONSTRAINT =====
The copy MUST BEGIN with these exact words spoken by the speaker:
"{opening_words}"

Do NOT paraphrase, summarize, or rephrase the opening words.
Use them EXACTLY as written. This is non-negotiable.

===== FORMAT EXAMPLE =====
Format your response as:
[OPENING_WORDS] [Context of the story]. The turning point was [moment].
What changed: [transformation]. Your moment: [relatable call to action]. {hashtags}

Real example:
"AI is revolutionary. I discovered this when I faced the impossible task.
My team was drowning in 50 hours of manual work per week.
Everything changed when we implemented one AI tool.
Now we have our lives back. What's YOUR impossible task? #AI #RealStories"

===== GUIDELINES =====
- Opening words are mandatory (use exactly as provided)
- Tell a personal story with relatable moments
- Include transformation or "before/after"
- Create emotional resonance
- End with empowering call to action
- Include provided hashtags
```

---

## Implementation Checklist

**For Spanish prompts (rename existing files + add constraint):**
- [ ] Rename `viral_prompt.txt` → `viral_prompt_ES.txt`
- [ ] Rename `educational_prompt.txt` → `educational_prompt_ES.txt`
- [ ] Rename `storytelling_prompt.txt` → `storytelling_prompt_ES.txt`
- [ ] Add CRITICAL CONSTRAINT section to each (EN ESPAÑOL)
- [ ] Add FORMAT EXAMPLE section to each (Spanish examples)
- [ ] Update guidelines in Spanish
- [ ] Save files
- [ ] Verify encoding is UTF-8

**For English prompts (create new files):**
- [ ] Create `viral_prompt_EN.txt` (copy structure from _ES version, translate to English)
- [ ] Create `educational_prompt_EN.txt` (translate to English)
- [ ] Create `storytelling_prompt_EN.txt` (translate to English)
- [ ] All contain `{opening_words}` placeholder
- [ ] All have "CRITICAL CONSTRAINT" section (in English)
- [ ] All have format examples (with English examples)
- [ ] Save all files
- [ ] Verify encoding is UTF-8

---

## Verification

**After all 6 files are created/modified:**
- [ ] Spanish files (_ES): All prompts in Spanish, examples in Spanish
- [ ] English files (_EN): All prompts in English, examples in English
- [ ] Both sets contain `{opening_words}` placeholder
- [ ] Both sets have "CRITICAL CONSTRAINT" section
- [ ] Both sets have "FORMAT EXAMPLE" section
- [ ] All files use UTF-8 encoding
- [ ] No broken characters or encoding issues
- [ ] Tone matches platform (TikTok-style, conversational)

---

## Format Template (Reusable)

If any prompts already exist with different structure, use this template:

```
[Your prompt role and goal]

===== CRITICAL CONSTRAINT =====
The copy MUST BEGIN with these exact words spoken by the speaker:
"{opening_words}"

Do NOT paraphrase or rephrase. Use EXACTLY as written.

===== FORMAT EXAMPLE =====
[Show format with example using opening words]

===== GUIDELINES =====
[Your style-specific guidelines]
```

---

## Why This Approach Works

**Explicit constraint > implicit hope:**
- Some LLMs might ignore a gentle suggestion
- "CRITICAL CONSTRAINT" makes it unmissable
- Format example shows exactly what we want
- Multiple reminders = higher compliance

**Tested pattern:**
- OpenAI docs recommend explicit constraints
- Format examples reduce hallucination
- Repetition improves instruction-following

---

## Next Steps

Once all three prompt files are updated:
→ Move to Step 03 (Update copy schemas for validation)
