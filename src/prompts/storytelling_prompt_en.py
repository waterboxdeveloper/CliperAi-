# -*- coding: utf-8 -*-
"""
Storytelling Style Prompt - English (EN)

This module contains the specific prompt for STORYTELLING style in English.

Why separate file?
- Storytelling uses narrative structure (beginning, development, conclusion)
- Prioritizes emotional connection and personal journey
- Combined with base_prompts.py to create complete prompt
- NEW: Starts WITH the speaker's exact opening words

Storytelling style characteristics:
- Hooks that initiate a story
- Clear narrative arc
- Emotional connection with audience
- Relatability through personal experiences
"""

STORYTELLING_STYLE_PROMPT_EN = """
## STYLE: STORYTELLING 📖

Your goal is to create copies that INITIATE A STORY the audience wants to follow.

===== CRITICAL: OPENING WORDS =====
The copy MUST begin with these exact words spoken by the speaker:
"{opening_words}"

DO NOT paraphrase them. Use EXACTLY as written. This is non-negotiable.

===== FORMULA: [OPENING_WORDS] + [YOUR_HOOK] =====

### Formulas that work:

1. **"Before vs after" hook:**
   - "[Opening words] 2 years ago I couldn't code. Now I work at Google 🚀 #DevJourney"
   - "[Opening words] My first production deploy broke everything. Here's what I learned #DevLife"
   - "[Opening words] From bootcamp to $150k/year: the untold journey #TechCareer"

2. **Crucial moment hook:**
   - "[Opening words] The day my CTO said: 'Your code is a disaster' #DevStory"
   - "[Opening words] 5 minutes before demo, the server crashed... #DevLife"
   - "[Opening words] I quit my job without another one. This is what happened #CareerChange"

3. **Personal journey hook:**
   - "[Opening words] 200 rejections later, this is what changed #DevJourney"
   - "[Opening words] How I went from tutorials hell to my first freelance #Learning"
   - "[Opening words] The interview question that made me doubt everything #TechInterviews"

4. **Lesson learned hook:**
   - "[Opening words] I lost 3 months on a project nobody used. Expensive lesson #Startup"
   - "[Opening words] My mentor told me something that changed my tech career #Mentorship"
   - "[Opening words] The junior mistake I made as a senior (and how I fixed it) #Leadership"

### Storytelling style characteristics:

**Priority emotions:**
- Relatability (sentiment: "relatable")
- Inspiration (sentiment: "inspirational")
- Personal narrative (sentiment: "storytelling")

**Expected hook strength:**
- 75% should be "very_high" or "high"
- Hook must promise a journey or transformation
- Must create curiosity: "What happened next?"

**Expected engagement score:**
- Aim for 7.5-9.0 on average
- Storytelling generates high retention (people want to see the ending)
- More comments because audience shares their own stories

**Expected viral potential:**
- Moderate-high: 7.0-9.0
- Inspirational or highly relatable stories are extremely shareable
- Depends on universality of the experience

**Storytelling hashtags:**
- Mix community + journey + people tags
- Examples: #DevJourney, #TechStories, #CareerChange, #DevCommunity
- Avoid purely technical tags: #JavaScript #API #Backend

### Examples of storytelling copies:

❌ BAD (no narrative, just technical):
"Learn React with this tutorial #React"

✅ GOOD (personal journey, transformation promise):
"I spent 6 months learning React. This would've changed everything #DevJourney"

❌ BAD (no emotion, generic):
"Implemented a new feature today"

✅ GOOD (moment of tension, emotional):
"3am, production deploy, everything breaks. My first all-nighter 💀 #DevLife"

❌ BAD (technical hook without story):
"How to use hooks in React"

✅ GOOD (transformation, journey):
"Went from hating React hooks to never living without them #React #DevJourney"

**More storytelling examples:**
✅ "My first production bug affected 10k users 😱 Here's what I learned #DevLife"
✅ "2 years ago I couldn't code. Now I work at Google 🚀 #DevJourney"
✅ "The day my CTO said: 'Your code is a disaster' #TechStory"

### Target metrics for storytelling style:

- **engagement_score:** 7.5-9.0 (high retention)
- **viral_potential:** 7.0-9.0 (depends on relatability)
- **hook_strength:** "very_high" or "high" in 75%
- **sentiment:** Prioritize "storytelling", "relatable", "inspirational"
- **sentiment_score:** 0.7-0.9 (strong but positive emotions)

### What to AVOID in storytelling style:

❌ Spoil the ending in the copy: "I quit and got a better job"
❌ Stories without conflict or tension
❌ Copies that don't initiate the narrative
❌ Being generic: "My story as a developer"
❌ Purely technical hashtags: #JavaScript #API #Backend

### What to PRIORITIZE:

✅ Start with a specific moment: "The day...", "2 years ago..."
✅ Create curiosity about outcome: "Here's what I learned"
✅ Use concrete numbers: "200 rejections", "6 months", "$150k"
✅ Moments of transformation: before/after, lessons learned
✅ Relatability: experiences your audience has lived

### Narrative structure in 150 characters:

Since you only have 150 chars, use this compressed structure:

**[Setup + Conflict + Promise of resolution]**

Examples:
- "My first production bug affected 10k users 😱 Here's what I learned #DevLife"
  - Setup: first production bug
  - Conflict: 10k users affected
  - Promise: "here's what I learned"

- "From tutorials to my first freelance in 3 months. The journey was NOT easy #DevJourney"
  - Setup: tutorials → freelance journey
  - Implicit conflict: "was NOT easy"
  - Promise: see what actually happened

### Clip prioritization:

If you must choose which clip has more storytelling potential, prioritize:
1. ✅ Personal experiences with conflict/resolution
2. ✅ Moments of transformation or learning
3. ✅ Errors or failures with lessons
4. ✅ Journey from beginner to expert
5. ✅ Difficult decisions and their consequences

If a clip is purely technical without personal story, give it a moderate engagement_score (6-7) for this style.

**Your mission:** Create copies that make people say "This happened to me too" or "I need to know how it ends".
"""


def get_storytelling_prompt_en() -> str:
    """
    Returns the storytelling style prompt in English.

    Returns:
        String with storytelling style prompt (English)
    """
    return STORYTELLING_STYLE_PROMPT_EN
