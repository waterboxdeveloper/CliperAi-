# PASO2 Enhancement: Opening Words Integration

**Full Architecture for Speaker Authenticity**

---

## Problem we're solving

Current state: Copy generated entirely by Gemini (ignores speaker's actual opening)
Desired state: Copy starts with speaker's EXACT words (first 5-10 sec)

Result: Higher engagement (viewer recognizes words) + Authenticity (speaker's own voice)

---

## The 5-Step Implementation Plan

### Step 01: Extract Opening Words from Transcript
**File:** `src/subtitle_generator.py` (or new `src/utils/transcript_extractor.py`)

**What:**
- Function to extract words from WhisperX JSON transcript
- Given clip timestamps (start, end), extract words from first 5-10 seconds
- Also extract hashtags speaker mentions (#mentions in transcript)

**Input:**
```
clip = {
    "start": 15.0,
    "end": 80.0,
    "transcript": "..."  # from WhisperX
}
opening_duration = 10  # seconds
```

**Output:**
```
{
    "opening_words": "La IA es revolucionaria",
    "opening_duration_actual": 2.3,  # seconds actually used
    "speaker_hashtags": ["#AICDMX", "#Future"],
    "word_count": 4
}
```

**Complexity:** LOW - Just JSON scanning + regex

---

### Step 02: Update Prompts with Opening Words Constraint
**Files:**
- `src/prompts/viral_prompt.txt`
- `src/prompts/educational_prompt.txt`
- `src/prompts/storytelling_prompt.txt`

**What:**
- Add placeholder: `{opening_words}`
- Add constraint: "MUST start copy with these exact words"
- Add template example showing desired format

**Before:**
```
You are a viral content expert...
Generate a short, punchy copy...
```

**After:**
```
You are a viral content expert...

CRITICAL: Start the copy with these EXACT words spoken by the speaker:
"{opening_words}"

Then continue with your hook and value proposition.

Format example:
[OPENING_WORDS]. [Your punchy hook]. [Why viewer should care] {hashtags}

Example:
"La IA es revolucionaria. And here's why THIS moment matters. 3 ways you can use it today. #AICDMX #Future"

[rest of original prompt]
```

**Complexity:** LOW - Just text editing

---

### Step 03: Add Validation to Copy Schema
**File:** `src/models/copy_schemas.py`

**What:**
- Add new fields to `ClipCopy` model
- Add validator to check opening words actually appear in copy

**Before:**
```python
class ClipCopy(BaseModel):
    clip_id: int
    copy_text: str
    style: Literal["viral", "educational", "storytelling"]
    engagement_score: float
```

**After:**
```python
class ClipCopy(BaseModel):
    clip_id: int
    copy_text: str
    style: Literal["viral", "educational", "storytelling"]
    engagement_score: float

    # NEW FIELDS
    opening_words: str                      # What we extracted from transcript
    opening_words_used: bool = False        # Did LLM actually use them?
    speaker_hashtags_provided: List[str] = [] # Which hashtags we suggested

    @field_validator('copy_text')
    def validate_opening_words_used(cls, v, info):
        """Ensure opening words appear in copy"""
        opening = info.data.get('opening_words', '')
        if opening and opening.lower() not in v.lower():
            raise ValueError(
                f"Copy must begin with speaker's opening words: '{opening}'"
            )
        return v
```

**Complexity:** LOW - Just adding fields + simple validator

---

### Step 04: Integrate into LangGraph (10-node flow)
**File:** `src/copys_generator.py`

**What:**
- Add new node between GROUP_BY_STYLE and GENERATE_* nodes
- Extract opening words for all clips
- Pass to generation nodes via state

**Architecture:**
```
CLASSIFY_CLIPS
    ↓
GROUP_BY_STYLE
    ↓
[NEW] EXTRACT_OPENING_WORDS ← Extracts for all clips
    ↓
GENERATE_VIRAL (receives opening_words in state)
GENERATE_EDUCATIONAL (receives opening_words in state)
GENERATE_STORYTELLING (receives opening_words in state)
    ↓
[rest of graph unchanged]
```

**New node function:**
```python
def _extract_opening_words_node(self, state):
    """Extract speaker's opening words and hashtags from clips"""
    clips = state["clips"]

    # For each clip, extract opening words
    for clip in clips:
        opening_info = self.transcript_extractor.extract_opening_words(
            transcript=clip["transcript"],
            clip_start=clip["start"],
            clip_end=clip["end"],
            duration_seconds=10
        )
        clip["opening_words"] = opening_info["opening_words"]
        clip["speaker_hashtags"] = opening_info["speaker_hashtags"]

    state["clips"] = clips
    logger.info(f"Extracted opening words for {len(clips)} clips")
    return state
```

**Complexity:** MEDIUM - Need to understand LangGraph node structure

---

### Step 05: Test & Validate
**Files to create:**
- `tests/test_opening_words_extraction.py`
- `tests/test_copy_with_opening_words.py`

**What to test:**

**Test 1: Extraction accuracy**
```
Given: Transcript with word timestamps
When: Extract first 10 seconds from clip starting at 15s
Then: Get exactly "La IA es revolucionaria" (verified against manually-checked transcript)
```

**Test 2: Copy validation**
```
Given: Generated copy with opening_words="La IA es revolucionaria"
When: Validate with Pydantic
Then: Should pass (opening words appear in copy)

Given: Generated copy WITHOUT opening words
When: Validate with Pydantic
Then: Should fail with clear error
```

**Test 3: Integration test**
```
Given: Real clip from "México y la guerra por los chips"
When: Run full PASO2 with enhancement
Then:
  - Opening words extracted correctly
  - Copy starts with those words
  - Hashtags used from speaker's transcript
  - Engagement score >= 7.5
```

**Complexity:** MEDIUM - Need to write test cases

---

## File Dependency Tree

```
subtitle_generator.py → extract_opening_words()
        ↓
copys_generator.py → Uses extraction in new node
        ↓
prompts/*.txt → Pass opening_words as {placeholder}
        ↓
models/copy_schemas.py → Validate opening_words present in copy
        ↓
Tests → Verify all connections work
```

**Key insight:** Changes are additive (no breaking changes to existing flow)

---

## Implementation Sequence

**User's involvement level HIGH:**
- We modify each file together
- You review exact changes before applying
- You understand what each line does

**Process:**
1. Create `src/utils/transcript_extractor.py` (new file) - you review
2. Modify `src/subtitle_generator.py` - you review
3. Modify `src/prompts/` (3 files) - you review
4. Modify `src/models/copy_schemas.py` - you review
5. Modify `src/copys_generator.py` - you review
6. Create test files - you review

**Estimated time:** 30-40 minutes (with thorough review)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| LLM ignores opening_words constraint | Validation catches → retry with stricter prompt |
| Speaker says no hashtags | Fall back to LLM-generated hashtags |
| Opening words < 5 sec duration | Still use them (better authentic than nothing) |
| Engagement score drops | A/B test against original copies |
| Copy becomes robotic | Prompt template gives flexibility in hook |

---

## Success Looks Like

```
Input clip (0-15 seconds):
"La IA es revolucionaria. Transforma cómo trabajamos.
Te muestro 3 casos de uso en 60 segundos. #AICDMX"

Generated copy output:
"La IA es revolucionaria. 3 ways it changes everything you do today.
Watch til the end for the most practical example. #AICDMX #Future #Tech"

✓ Opens with speaker's exact words
✓ Maintains authentic voice
✓ Uses speaker's hashtags
✓ Viral hook added by AI
✓ Engagement score: 8.2/10
```

---

## Files Affected Summary

```
src/
├── subtitle_generator.py               [MODIFY - ~40 lines added]
│   ├── extract_opening_words_from_clip()     [NEW METHOD]
│   └── extract_speaker_hashtags()            [NEW METHOD]
├── copys_generator.py                  [MODIFY - ~35 lines added]
│   ├── _extract_opening_words_node()   [NEW NODE]
│   └── _load_language_specific_prompt()     [NEW METHOD]
├── models/
│   └── copy_schemas.py                 [MODIFY - ~15 lines added]
└── prompts/
    ├── viral_prompt_ES.txt             [MODIFY - 4 lines added]
    ├── viral_prompt_EN.txt             [NEW - same as ES, English version]
    ├── educational_prompt_ES.txt       [MODIFY - 4 lines added]
    ├── educational_prompt_EN.txt       [NEW - English version]
    ├── storytelling_prompt_ES.txt      [MODIFY - 4 lines added]
    └── storytelling_prompt_EN.txt      [NEW - English version]

tests/
├── test_opening_words_extraction.py    [CREATE NEW - ~80 lines]
└── test_copy_with_opening_words.py     [CREATE NEW - ~100 lines]
```

**Total new code:** ~220 lines (6 new prompt files, language-aware methods)
**Total modified existing:** ~100 lines
**Risk to existing code:** MINIMAL (additive, no breaking changes)
**Architecture advantage:** Bilingual support with zero transcript overhead (language already detected)

---

Ready to proceed step-by-step? Start with Step 01?
