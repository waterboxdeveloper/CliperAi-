**Objective:** Build a utility module to extract speaker's opening words from WhisperX transcript
# Enhancement: Speaker's Opening Words Integration

**Feature:** AI Copywriting Enhancement - Authenticity Hook
**Date:** 2026-03-21
**Status:** PLANNING (Ready for Implementation)
**Priority:** HIGH (Affects viral coefficient directly)

---

## Problem Statement

**Current Behavior:**
```
Clip detected by ClipsAI
  ↓
LangGraph extracts clip timestamps (start, end)
  ↓
Gemini generates copy FROM SCRATCH
  ↓
Result: AI-generated hook (may diverge from speaker's opening)
```

**Issue:**
- Copy lacks speaker's authentic voice
- LLM invents hooks instead of using proven engagement opener
- Missing hashtags speaker actually mentions
- Reduced "thumb-stopping" power (viewer recognizes words or not)

**Content Strategy Insight:**
Viral content rule: **First 3 words determine if viewer continues**
- If viewer hears their own words → immediate credibility
- If AI paraphrase → cognitive friction → swipe away

---

## Solution: Opening Words Anchor

**New Behavior:**
```
Clip detected (timestamps: 0:15 - 1:20)
  ↓
Extract EXACT words from first 5-10 seconds
  (Use WhisperX word-level timestamps from transcript)
  ↓
Scan for hashtags speaker actually mentions
  ↓
LangGraph generates copy WITH opening words as hook
  ↓
Result: [EXACT WORDS] + [AI continuation] = Authentic + Viral
```

**Example:**
```
Transcript (0-10 sec):
"La IA es revolucionaria. Transforma cómo trabajamos. Te muestro cómo..."

Current copy (BAD):
"Descubre cómo la inteligencia artificial cambia el mundo 🚀 #AI"

Enhanced copy (GOOD):
"La IA es revolucionaria. Transforma cómo trabajamos y aquí te digo exactamente
por qué deberías prestarle atención... [rest of AI generation] #AI"
```

**Why it works:**
- `"La IA es revolucionaria"` = Speaker's exact words (proven hook)
- Viewer recognizes = immediate engagement
- AI fills rest = professional continuation
- Hashtag = what speaker actually said (not invented)

---

## Architectural Decision: Language Detection & Bilingual Support

### DECISION: Leverage WhisperX Language Detection for Bilingual Prompts

**Finding:** WhisperX already detects and stores language in transcript JSON

**Implementation:**
- `transcript["language"]` contains detected language ("spanish", "english", etc.)
- Load language-specific prompts dynamically
- Same extraction logic works for all languages

**Architecture:**
```
Clip → Transcript with language metadata
  ↓
Check: transcript["language"]
  ↓
Load prompt:
  - If "spanish" → src/prompts/viral_prompt_ES.txt
  - If "english" → src/prompts/viral_prompt_EN.txt
  ↓
Extract opening words (language-agnostic)
  ↓
Generate with language-appropriate prompt
```

**Cost:** Zero overhead (metadata already captured by transcriber.py)
**Benefit:** Support both Spanish and English clips with optimal quality

---

## Architectural Decision: Where to Extract

### DECISION: Extract from WhisperX Transcript (Not Audio Re-processing)

**Problem:**
We need opening words for each clip. Two approaches:

**Option A: Audio Re-processing (Rejected)**
```
Video file → ffmpeg extract segment [0:00-0:10] → whisperx transcribe → get text
```
- ❌ Wasteful: Re-transcribe content already transcribed
- ❌ Slow: WhisperX on 10-sec segments per clip (30+ clips = 30 new transcriptions)
- ❌ Duplicate processing
- ✅ Pros: Independent accuracy

**Option B: Reuse WhisperX Output (CHOSEN)**
```
WhisperX already provided: word-level timestamps
  Example: [
    {"word": "La", "start": 0.0, "end": 0.3},
    {"word": "IA", "start": 0.3, "end": 0.6},
    ...
  ]

For clip (start=15s, end=80s):
  Extract words where: word["start"] >= 15.0 AND word["start"] <= 15.0+10
  Result: ["La", "IA", "es", "revolucionaria", ...]
```
- ✅ Instant (O(n) scan of existing transcript)
- ✅ No re-processing
- ✅ Accurate (already aligned by WhisperX)
- ✅ Coherent with architecture (one source of truth)

**Trade-off:**
```
Option A: Better accuracy, worse performance
Option B: Good accuracy, instant performance ← CHOSEN
Decision: Accuracy good enough (already word-level from WhisperX)
```

**RESULT:** Extract from existing WhisperX JSON, no new model calls

---

## Architectural Decision: Hashtag Extraction

### DECISION: Scan Full Clip Transcript for #mentions

**Problem:**
How to get relevant hashtags for the copy?

**Option A: LLM-generated hashtags (Current)**
```
Gemini: "Generate 3 relevant hashtags for: [transcript]"
Result: ["#AI", "#Technology", "#Innovation"]
```
- ✅ Intelligent topic detection
- ✅ Professional hashtags
- ❌ Not what speaker actually said
- ❌ Risk: LLM invents hashtags speaker wouldn't use

**Option B: Speaker's actual #mentions (CHOSEN)**
```
Scan full clip transcript for pattern: #\w+
Example from transcript: "#AICDMX #Future #Tech"
Result: ["#AICDMX", "#Future", "#Tech"]
```
- ✅ Authentic (speaker's own hashtags)
- ✅ Consistent with speaker's voice
- ✅ Instant (regex scan)
- ❌ Limited to what speaker mentions
- ❌ May be few if speaker doesn't mention hashtags

**Hybrid Approach (if speaker mentions no hashtags):**
```
If speaker_hashtags found: use them
Else: use 1-2 LLM-generated hashtags + #AICDMX (required by schema)
```

**RESULT:** Speaker's hashtags when available, LLM fallback otherwise

---

## LangGraph Integration Point

**Current 10-node flow:**
```
1. CLASSIFY_CLIPS → Determine style (viral/educational/storytelling)
2. GROUP_BY_STYLE → Partition clips
3. GENERATE_VIRAL → LLM: "Generate viral copy"
4. GENERATE_EDUCATIONAL → LLM: "Generate educational copy"
5. GENERATE_STORYTELLING → LLM: "Generate storytelling copy"
6. MERGE_COPIES → Combine results
7. VALIDATE_COPIES → Pydantic validation
8. ANALYZE_QUALITY → Check engagement score
9. SAVE_COPIES → Write output
10. HANDLE_RETRY → Retry on failure
```

**New step: INSERT between GROUP_BY_STYLE and GENERATE_*:**
```
0.5. EXTRACT_OPENING_WORDS_AND_HASHTAGS → Extract from transcript
     → Add to state: opening_words, speaker_hashtags
     → Pass to generation nodes
```

**Why here:**
- After style classification (we know clip context)
- Before generation (nodes need this info)
- Parallel extraction (one call, not per-style)

---

## System Prompt Modification Strategy

**Current prompt structure:**
```
viral_prompt.txt:
"You are a viral content expert. Generate a short, punchy copy..."
```

**New structure:**
```
viral_prompt.txt:
"You are a viral content expert. Generate a short, punchy copy.

CRITICAL CONSTRAINT:
- MUST start copy with these exact words (from speaker): {opening_words}
- THEN add hook and value proposition
- Include these hashtags: {speaker_hashtags}
- Example format: '[OPENING_WORDS]. [Your hook]. [Value prop] {hashtags}'

[rest of prompt]
"
```

**Why this approach:**
- Explicit constraint (not hope LLM uses words)
- Template example (shows desired format)
- Three-part structure clear (opening + hook + value)

---

## Validation Strategy

**Current validation (copy_schemas.py):**
```python
class ClipCopy(BaseModel):
    copy_text: str
    style: Literal["viral", "educational", "storytelling"]
    engagement_score: float  # 0-10

    @field_validator('copy_text')
    def validate_hashtag(cls, v):
        if '#AICDMX' not in v:
            raise ValueError("Copy must include #AICDMX")
        return v
```

**New validation:**
```python
class ClipCopy(BaseModel):
    copy_text: str
    style: Literal["viral", "educational", "storytelling"]
    engagement_score: float
    opening_words: str                    # [NEW] What we extracted
    opening_words_used: bool = False      # [NEW] Did LLM use it?
    speaker_hashtags_used: List[str] = [] # [NEW] Which hashtags were used?

    @field_validator('copy_text')
    def validate_opening_words_present(cls, v, info):
        # Check if opening_words appear in copy_text
        opening = info.data.get('opening_words', '')
        if opening and opening.lower() not in v.lower():
            raise ValueError(f"Copy must start with: {opening}")
        return v
```

**Why validate:**
- Ensures opening words actually appear (not just in prompt)
- Track which hashtags ended up in copy
- Audit trail (know if LLM followed constraint)

---

## Impact Analysis

### Files to Modify
```
src/
├── subtitle_generator.py           [NEW] extract_opening_words_from_clip()
├── copys_generator.py              [MODIFY] Add extraction node + pass to nodes
├── models/
│   └── copy_schemas.py             [MODIFY] Add validation fields
└── prompts/
    ├── viral_prompt.txt            [MODIFY] Add {opening_words} constraint
    ├── educational_prompt.txt      [MODIFY] Add {opening_words} constraint
    └── storytelling_prompt.txt     [MODIFY] Add {opening_words} constraint
```

### Zero Dependencies Added
- WhisperX output already used
- Regex for hashtag detection (standard lib)
- No new libraries required
- No new models to download
- No new API calls

### Performance Impact
- Per-clip extraction: ~1ms (regex scan of JSON)
- 30 clips = 30ms additional overhead
- Negligible compared to LLM call time (~2-5 sec per clip)

### Risk Assessment
```
Risk: LLM ignores opening_words in prompt
Mitigation: Validation catches it → retry with stricter prompt

Risk: Speaker says no hashtags
Mitigation: Fallback to LLM-generated + #AICDMX

Risk: Opening words incoherent in context
Mitigation: 5-10 sec is long enough for coherent phrase
         Example: "La IA es revolucionaria" (4 words, ~2 sec)
```

---

## Success Criteria

**Feature considered successful if:**

1. **Functional:**
   - Opening words extracted accurately from clip timestamps
   - Opening words appear in generated copy
   - Speaker hashtags detected from transcript
   - Copy format: `[OPENING] [HOOK] [VALUE] [HASHTAGS]` ✓

2. **Quality:**
   - Engagement score stays >= 7.5 (not degraded by constraint)
   - Copy readability maintained (no awkward phrasings)
   - Authenticity score: 9/10 (speaker's own words)

3. **Robustness:**
   - Edge case: speaker says no hashtags → fallback works
   - Edge case: opening words < 5 words → still used
   - Edge case: LLM ignores constraint → validation catches → retry

4. **Integration:**
   - No breaking changes to existing PASO2 nodes
   - State manager still works
   - Cleanup still works
   - CLI flags optional (backward compatible)

---

## Next Steps

1. **Documentation:** Create todoPASO2-ENHANCEMENT/ folder with step-by-step implementation
2. **User Approval:** Review architecture, ask questions
3. **Implementation:** Modify files in sequence (transcript → prompts → validation → langgraph → test)
4. **Testing:** Validate with real clips ("México y la guerra", etc.)
5. **Deployment:** Integrate into main pipeline

---

**Status:** Architecture documented, awaiting approval before implementation
**Estimated effort:** 3-4 hours (extraction, prompts, validation, testing)
**Risk level:** LOW (additive, not breaking existing code)
