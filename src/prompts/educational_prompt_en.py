# -*- coding: utf-8 -*-
"""
Educational Style Prompt - English (EN)

This module contains the specific prompt for EDUCATIONAL style in English.

Why separate file?
- Educational has different goals than viral
- Prioritizes clarity and educational value over shock value
- Combined with base_prompts.py to create complete prompt
- NEW: Starts WITH the speaker's exact opening words

Educational style characteristics:
- Hooks based on learning
- Promises of concrete knowledge
- Clear and direct structure
- Focus on utility and takeaways
"""

EDUCATIONAL_STYLE_PROMPT_EN = """
## STYLE: EDUCATIONAL 📚

Your goal is to create copies that promise CLEAR AND SPECIFIC educational value.

===== CRITICAL: OPENING WORDS =====
The copy MUST begin with these exact words spoken by the speaker:
"{opening_words}"

DO NOT paraphrase them. Use EXACTLY as written. This is non-negotiable.

===== FORMULA: [OPENING_WORDS] + [YOUR_HOOK] =====

### Formulas that work:

1. **Direct learning hook:**
   - "[Opening words] 3 ways to optimize React hooks you didn't know #React"
   - "[Opening words] How to debug memory leaks in 5 minutes #JavaScript"
   - "[Opening words] The difference between async/await and Promises explained simply #JS"

2. **Problem → solution hook:**
   - "[Opening words] Is your API slow? This technique reduced latency by 80% #Backend"
   - "[Opening words] How I avoided 3 hours of debugging with this one rule #DevTips"
   - "[Opening words] The TypeScript error everyone makes (and how to fix it) #TypeScript"

3. **List or framework hook:**
   - "[Opening words] 5 design patterns every senior should know #SoftwareDesign"
   - "[Opening words] The code review checklist I use in production #DevLife"
   - "[Opening words] 4 clean code principles with real examples #CleanCode"

4. **"Learn what I learned" hook:**
   - "[Opening words] What I learned after 100 technical interviews #TechInterviews"
   - "[Opening words] I migrated 1M users to microservices: this didn't work #Architecture"
   - "[Opening words] Lessons learned: 2 years as a tech lead #Leadership"

### Educational style characteristics:

**Priority emotions:**
- Educational curiosity (sentiment: "curious_educational")
- Confidence ("I'll learn something useful")
- Clarity (copy must be crystal clear)

**Expected hook strength:**
- 70% should be "high" or "medium"
- Hook must promise a concrete takeaway
- Avoid sensationalist hooks, prioritize specificity

**Expected engagement score:**
- Aim for 7.0-8.5 on average
- Educational gets fewer shares than viral, but more saves
- More engaged audience (higher watch time)

**Expected viral potential:**
- More moderate: 6.0-8.0 is perfect
- Not all educational content should be viral
- Prioritize utility over shock value

**Educational hashtags:**
- Mix community + niche (specific) + trend tags
- Examples: #LearnToCode, #DevTips, #CodeNewbie, #Programming
- No generic tags alone: #programming #code #tech

### Examples of educational copies:

❌ BAD (too vague, no clear value):
"Learn about APIs #coding"

✅ GOOD (specific, promises value, clear takeaway):
"How to structure REST APIs that scale to millions of requests #Backend"

❌ BAD (clickbait without substance):
"This CSS trick will blow your mind 🤯"

✅ GOOD (clear promise, actionable):
"3 CSS properties that replace JavaScript (with examples) #FrontendDev"

❌ BAD (weak hook, no clear learning):
"Talking about testing in Python today"

✅ GOOD (problem + solution, specific):
"Your tests take 10 minutes? pytest-xdist cuts it to 2 #Python"

**More educational copy examples:**
✅ "How to debug memory leaks in React in 5 steps #React"
✅ "The difference between async/await and Promises explained simply #JavaScript"
✅ "Why your API is slow: 3 optimization techniques #BackendDev"

### Target metrics for educational style:

- **engagement_score:** 7.0-8.5 (sustained engagement)
- **viral_potential:** 6.0-8.0 (doesn't need to be extreme)
- **hook_strength:** "high" or "medium" mostly
- **sentiment:** Prioritize "educational" and "curious_educational"
- **sentiment_score:** 0.6-0.8 (confidence and clarity)

### What to AVOID in educational style:

❌ Vague promises: "Improve your code"
❌ Clickbait without substance: "The secret seniors don't want you to know"
❌ Emotional hooks without content: "This made me cry 😭"
❌ Copies without clear takeaway
❌ Generic hashtags: #programming #code #tech

### What to PRIORITIZE:

✅ Specificity: "React hooks" > "React" > "JavaScript"
✅ Concrete numbers: "3 techniques" > "some techniques"
✅ Clear problem/solution
✅ Frameworks or lists (humans love structure)
✅ Direct language without fluff

### Clip prioritization:

If you must choose which clip has more educational potential, prioritize:
1. ✅ Explains a complex concept in simple terms
2. ✅ Solves a common problem (debugging, optimization, etc.)
3. ✅ Shares experiences with concrete takeaways
4. ✅ Compares options (X vs Y: when to use each)
5. ✅ Common mistakes and how to avoid them

If a clip is pure entertainment without educational value, give it a low engagement_score (5-6) for this style.

**Your mission:** Create copies that make people say "I need to save this for later".
"""


def get_educational_prompt_en() -> str:
    """
    Returns the educational style prompt in English.

    Returns:
        String with educational style prompt (English)
    """
    return EDUCATIONAL_STYLE_PROMPT_EN
