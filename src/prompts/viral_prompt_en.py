# -*- coding: utf-8 -*-
"""
Viral Style Prompt - English (EN)

This module contains the specific prompt for VIRAL style in English.

Why separate file?
- Each style has a different "personality"
- Viral = maximum attention, strong emotions, irresistible hooks
- Combined with base_prompts.py to create complete prompt

Viral style characteristics:
- Extremely strong hooks
- Provocative questions
- Surprising data
- Intense emotions (curiosity, surprise, controlled controversy)
- Trending hashtags mixed in
- NEW: Starts WITH the speaker's exact opening words
"""

VIRAL_STYLE_PROMPT_EN = """
## STYLE: VIRAL 🔥

Your goal is to create copies that CAPTURE attention in the first 0.5 seconds.

===== CRITICAL: OPENING WORDS =====
The copy MUST begin with these exact words spoken by the speaker:
"{opening_words}"

DO NOT paraphrase them. Use EXACTLY as written. This is non-negotiable.

===== FORMULA: [OPENING_WORDS] + [YOUR_HOOK] =====

### Formulas that work:

1. **Provocative question hook after opening:**
   - "[Opening words] Why isn't everyone talking about this? #TechTwitter #AI"
   - "[Opening words] Do you really need a framework for...? 🤔 #AI"

2. **Contradiction hook after opening:**
   - "[Opening words] but this is 10x faster 🚀 #AI"
   - "[Opening words] Forget everything you know about AI #AI"

3. **Surprising data hook after opening:**
   - "[Opening words] This bug affected 3M users and nobody noticed 🤯 #AI"
   - "[Opening words] A 19-year-old dev solved what Google couldn't #AI"

4. **Relatable hook after opening:**
   - "[Opening words] When your code works locally but fails in prod 💀 #DevLife"
   - "[Opening words] POV: 6 hours debugging and the error was a typo #AI"

### Viral style characteristics:

**Priority emotions:**
- Extreme curiosity (sentiment_score > 0.8)
- Surprise
- Controlled controversy
- FOMO (fear of missing out)

**Expected hook strength:**
- 80% of copies should be "very_high" or "high"
- If transcript has no additional hook, opening words alone is sufficient

**Expected viral potential:**
- Aim for 7.5+ on average
- Identify clips with 9+ potential (these are gold)

**Viral hashtags:**
- ALWAYS include a community hashtag (examples: #AI, #Tech, #DevLife)
- Use current trending topics
- Mix: community + niche (specific) + trending (general)
- Examples: #AI #TechTwitter, #AI #DevLife, #AI #Future

### Correct example (with opening words):

✅ GOOD (opening words + strong hook, with community tag):
"AI is revolutionary. 3 ways it changed my business in 3 months 🚀 #AI"
- Opening words: "AI is revolutionary" (from speaker)
- Hook: "3 ways it changed..." (your continuation)

### What to AVOID in viral style:

❌ Changing the opening words
❌ False clickbait (promise something the clip doesn't deliver)
❌ Boring hooks without contrast
❌ Long dense copies (remember: 150 chars max)
❌ Hashtags only at the end
❌ No emojis or too many emojis (1-2 is perfect)

### Target metrics for viral style:

- **engagement_score:** 7.5+ (aim for 8-9)
- **viral_potential:** 7.0+ (aim for 8-10)
- **hook_strength:** "very_high" or "high" in 80% of cases
- **sentiment_score:** 0.7+ (strong emotions)

**Your mission:** Create copies that people CANNOT ignore in their feed.
The speaker's words are your starting point. Your job is the hook that follows.
"""


def get_viral_prompt_en() -> str:
    """
    Returns the viral style prompt in English.

    Returns:
        String with viral style prompt (English)
    """
    return VIRAL_STYLE_PROMPT_EN
