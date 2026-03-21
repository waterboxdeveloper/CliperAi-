# PASO2 Enhancement: Quick Reference

**Feature:** AI Copywriting with Speaker's Opening Words Integration
**Total time:** ~90 minutes (for full implementation + testing)
**Risk level:** LOW (additive, no breaking changes)

---

## The Enhancement in 30 Seconds

**Problem:** Generated copies ignore what the speaker actually said in the opening
**Solution:** Extract first 5-10 seconds of speaker's exact words, force LLM to use them
**Result:** More authentic, higher engagement (speaker's own words = thumb-stopping)

---

## 5-Step Implementation Roadmap

### Step 01: Add Methods to SubtitleGenerator (20 min)
**File:** `src/subtitle_generator.py`
**What:** Add 2 new methods:
- `extract_opening_words_from_clip()` - Extract first 10 sec of words
- `extract_speaker_hashtags()` - Extract hashtags speaker mentions

**Exact location:** After existing methods in SubtitleGenerator class

---

### Step 02: Create Bilingual Prompts (20 min)
**Files to create (6 total):**
- `src/prompts/viral_prompt_ES.txt` (Rename from viral_prompt.txt + enhance)
- `src/prompts/viral_prompt_EN.txt` (NEW - English version)
- `src/prompts/educational_prompt_ES.txt` (Rename from educational_prompt.txt + enhance)
- `src/prompts/educational_prompt_EN.txt` (NEW - English version)
- `src/prompts/storytelling_prompt_ES.txt` (Rename from storytelling_prompt.txt + enhance)
- `src/prompts/storytelling_prompt_EN.txt` (NEW - English version)

**What:** Add constraint section to each (in corresponding language):
```
===== CRITICAL CONSTRAINT =====
The copy MUST BEGIN with these exact words:
"{opening_words}"

===== FORMAT EXAMPLE =====
[OPENING_WORDS]. [Your hook]. [Value prop]. {hashtags}
```

**IMPORTANT:** Spanish prompts in Spanish 🇪🇸, English prompts in English 🇺🇸

---

### Step 03: Update Copy Schema (15 min)
**File:** `src/models/copy_schemas.py`
**What:** Add 3 new fields to `ClipCopy` class:
- `opening_words: str = ""`
- `opening_words_used: bool = False`
- `speaker_hashtags_provided: List[str] = []`

**What:** Add validator to ensure opening words appear in copy

---

### Step 04: Add Node + Language-Aware Prompt Loading (25 min)
**File:** `src/copys_generator.py`
**What:** Add two things:

**1) New extraction node:**
- `_extract_opening_words_node()` - Extract opening words + hashtags
- Add language from transcript: `clip["language"] = transcript["language"]`
- Add to state before generation nodes

**2) Language-aware helper method:**
- `_load_language_specific_prompt(style, language)` - Load correct prompt file
- If language == "english" → load `viral_prompt_EN.txt`
- If language == "spanish" → load `viral_prompt_ES.txt`

**3) Update GENERATE_* nodes:**
- Load language-specific prompt using helper method
- Format prompt with opening_words and hashtags
- Pass to LLM

**Flow position:** GROUP_BY_STYLE → extract_opening_words → GENERATE_* (with language awareness)

---

### Step 05: Write Tests (25 min)
**Files:**
- `tests/test_opening_words_extraction.py`
- `tests/test_copy_with_opening_words.py`

**What:**
- Unit tests: Extraction logic, edge cases
- Schema tests: Validation, backward compatibility
- Manual tests: Real clip integration

---

## Files Modified Summary

```
MODIFIED (Additive):
├── src/subtitle_generator.py                 (+40 lines)
├── src/copys_generator.py                    (+35 lines - includes language helper)
└── src/models/copy_schemas.py                (+15 lines)

RENAMED & ENHANCED (Spanish):
├── src/prompts/viral_prompt.txt
│   → viral_prompt_ES.txt                     (+4 lines constraint section)
├── src/prompts/educational_prompt.txt
│   → educational_prompt_ES.txt               (+4 lines constraint section)
└── src/prompts/storytelling_prompt.txt
    → storytelling_prompt_ES.txt              (+4 lines constraint section)

CREATED NEW (English):
├── src/prompts/viral_prompt_EN.txt           (new file, ~30 lines)
├── src/prompts/educational_prompt_EN.txt    (new file, ~30 lines)
└── src/prompts/storytelling_prompt_EN.txt   (new file, ~30 lines)

CREATED (Tests):
├── tests/test_opening_words_extraction.py    (~80 lines)
└── tests/test_copy_with_opening_words.py     (~100 lines)

TOTAL: ~300 lines new + modified
BILINGUAL: Full Spanish + English support
RISK: MINIMAL (no breaking changes, all additive)
```

---

## Exact Implementation Steps

### Step 01A: Verify Assumptions
**Before writing code, ask user:**
- Where do clips get their transcript data?
- Are word timestamps in seconds?
- Is full transcript included with each clip?

### Step 01B: Implement Methods
**Location:** `src/subtitle_generator.py`, inside `SubtitleGenerator` class

```python
def extract_opening_words_from_clip(
    self,
    transcript: Dict,
    clip_start: float,
    clip_end: float,
    opening_duration: float = 10.0
) -> Dict[str, any]:
    """Extract first N seconds of speaker's words from clip"""
    # [User writes this with our detailed guidance]

def extract_speaker_hashtags(self, clip_text: str) -> List[str]:
    """Extract hashtags speaker mentioned"""
    # [User writes this - regex pattern: #\w+]
```

### Step 02A-02C: Edit Each Prompt File
**For each file (3 total):**
1. Open file in editor
2. Find role definition
3. Add CRITICAL CONSTRAINT section after role
4. Add FORMAT EXAMPLE section
5. Save file

**Template to use:**
```
[Role definition]

===== CRITICAL CONSTRAINT =====
The copy MUST BEGIN with: "{opening_words}"

===== FORMAT EXAMPLE =====
[Example with opening words]

[Rest of prompt]
```

### Step 03A-03C: Update Schema
**File:** `src/models/copy_schemas.py`

1. Add imports: `from typing import List`
2. Add fields to `ClipCopy` class (after existing fields):
```python
opening_words: str = ""
opening_words_used: bool = False
speaker_hashtags_provided: List[str] = Field(default_factory=list)
```

3. Add new validator:
```python
@field_validator('copy_text')
def validate_opening_words_present(cls, v, info):
    opening = info.data.get('opening_words', '')
    if opening and opening.lower() not in v.lower():
        raise ValueError(f"Copy must start with: {opening}")
    return v
```

### Step 04A-04B: Add LangGraph Node
**File:** `src/copys_generator.py`

1. Add method `_extract_opening_words_node()` to `CopysGenerator` class
2. Add to graph:
   - `graph.add_node("extract_opening_words", self._extract_opening_words_node)`
   - `graph.add_edge("group_by_style", "extract_opening_words")`
   - `graph.add_edge("extract_opening_words", "generate_viral")`

3. Update GENERATE_* nodes to use:
   ```python
   clip["opening_words"]  # From state
   clip["speaker_hashtags"]  # From state
   ```

### Step 05A-05B: Create Test Files
**File 1:** `tests/test_opening_words_extraction.py`
- Test extraction logic (basic, offset, limited duration, no words)
- Test hashtag extraction (basic, dedup, none, with numbers)

**File 2:** `tests/test_copy_with_opening_words.py`
- Test validation passes with opening words
- Test validation fails without opening words
- Test backward compatibility (no opening words specified)
- Test case-insensitive matching
- Test existing hashtag validation still works

---

## Detailed Implementation Documents

**Full details in these files (read in order):**

1. ✅ `paso2-enhancement-coments.md` - Architecture & decisions
2. ✅ `00-OVERVIEW.md` - 5-step plan overview
3. ✅ `01-transcript-extraction.md` - Step 1 (detailed)
4. ✅ `02-prompt-engineering.md` - Step 2 (detailed)
5. ✅ `03-copy-schemas-update.md` - Step 3 (detailed)
6. ✅ `04-langgraph-integration.md` - Step 4 (detailed)
7. ✅ `05-testing.md` - Step 5 (detailed)
8. ← `README-STEPS.md` - This file (quick reference)

---

## Validation Checklist

**After Step 01 (Subtitle Generator):**
- [ ] Methods added to SubtitleGenerator
- [ ] Methods have docstrings and type hints
- [ ] No syntax errors: `python -m py_compile src/subtitle_generator.py`

**After Step 02 (Prompts):**
- [ ] All 3 files have CRITICAL CONSTRAINT section
- [ ] All 3 files have FORMAT EXAMPLE
- [ ] Files are readable (no corruption)

**After Step 03 (Schema):**
- [ ] 3 new fields added to ClipCopy
- [ ] New validator added
- [ ] No syntax errors: `python -m py_compile src/models/copy_schemas.py`

**After Step 04 (LangGraph):**
- [ ] New node added to graph
- [ ] Node wired into flow (edges correct)
- [ ] GENERATE_* nodes updated to use opening_words
- [ ] No syntax errors: `python -m py_compile src/copys_generator.py`

**After Step 05 (Tests):**
- [ ] Both test files created
- [ ] Tests pass: `pytest tests/test_opening_words_extraction.py -v`
- [ ] Tests pass: `pytest tests/test_copy_with_opening_words.py -v`
- [ ] Manual test with real clip passes

---

## Success Looks Like

```
INPUT:
Clip transcript: "La IA es revolucionaria. Transforma cómo trabajamos. #AICDMX"

PASO2 PROCESSING:
1. Extraction: opening_words = "La IA es revolucionaria"
2. Extraction: speaker_hashtags = ["#AICDMX"]
3. Prompt: "Start with 'La IA es revolucionaria' and generate viral copy"
4. LLM: "La IA es revolucionaria. 3 ways it's changing every business TODAY. #AICDMX"
5. Validation: ✓ PASS (opening words present)

OUTPUT:
{
  "copy_text": "La IA es revolucionaria. 3 ways it's changing...",
  "opening_words": "La IA es revolucionaria",
  "opening_words_used": true,
  "speaker_hashtags_provided": ["#AICDMX"],
  "engagement_score": 8.7,
  "style": "viral"
}

✓ Feature complete!
```

---

## Rollback Plan (If Needed)

**If something breaks, you can:**
1. Revert subtitle_generator.py to last commit
2. Revert copys_generator.py to last commit
3. Remove new test files
4. System returns to original PASO2 behavior

**No permanent changes to data or state.**

---

## Timeline Estimate (Bilingual)

| Step | Time | Cumulative |
|------|------|-----------|
| 01: Extraction Methods | 20 min | 20 min |
| 02: Bilingual Prompts (6 files) | 20 min | 40 min |
| 03: Schema Changes | 15 min | 55 min |
| 04: LangGraph + Language Helper | 25 min | 80 min |
| 05: Testing | 25 min | 105 min |
| Total | | ~105 minutes |

**With thorough code review:** +30 minutes (total: ~2.5 hours)
**Time added by bilingual support:** +15 minutes (create 3 English prompts)

---

## Pre-Implementation Checklist

**Bilingual architecture confirmed:**
- ✅ Language metadata: `transcript["language"]` (from transcriber.py)
- ✅ 6 prompt files: 3 Spanish (_ES) + 3 English (_EN)
- ✅ Language-aware loading in copys_generator.py
- ✅ Both languages equally supported

**Questions before starting:**

1. **Prompt file locations:** Are `src/prompts/` files in the right place?
   - Confirm path: `src/prompts/viral_prompt_ES.txt`, etc.

2. **Encoding:** Make sure all prompt files are UTF-8 (for Spanish accents)
   - Spanish: "análisis", "único", "qué", etc.
   - Save as UTF-8, not ASCII

3. **Testing data:**
   - Spanish clips: "México y la guerra por los chips" ✓
   - English clips: Do you have any English test videos ready?

---

## Architecture Verified ✅

**Language detection:** Already built into transcriber.py
**Opening words extraction:** Language-agnostic (works for any language)
**Prompt loading:** Language-specific (_ES for Spanish, _EN for English)
**Quality:** Each language optimized in its native language

---

**Ready to start Step 01?** → `/01-transcript-extraction.md`
