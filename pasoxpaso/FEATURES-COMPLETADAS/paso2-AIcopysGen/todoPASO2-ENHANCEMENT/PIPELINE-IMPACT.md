# Pipeline Impact: Prompt Enhancement Integration

**Question:** Does this prompt enhancement affect other steps in the pipeline?
**Answer:** Minimal impact - prompts are loaded dynamically (no imports needed)

---

## Good News: No Python Imports Required ✅

**Prompts are text files, not Python modules:**

```python
# OLD (if it existed): from src.prompts import viral_prompt
# NEW: Just load the file at runtime
with open("src/prompts/viral_prompt_EN.txt", "r") as f:
    prompt = f.read()
```

**Why this matters:**
- No `from` or `import` statements needed
- No changes to `__init__.py` files
- No dependency graph updates
- Dynamic loading = flexible (can add languages anytime)

---

## Pipeline Impact Analysis

### 1. **Downloader.py** ✅ NO CHANGE
```python
# Role: Download videos from YouTube
# Impact: NONE
# Reason: Prompts are only used in PASO2 (downstream)
```

### 2. **Transcriber.py** ✅ NO CHANGE (Already captures language!)
```python
# Role: Transcribe audio with WhisperX
# Current output:
{
    "language": "spanish",  # Already there!
    "segments": [...]
}
# Impact: NONE (language detection already built-in)
```

### 3. **Clips_generator.py** ✅ NO CHANGE
```python
# Role: Detect clips with ClipsAI
# Impact: NONE
# Reason: Clips are detected before copy generation
```

### 4. **Video_exporter.py** ✅ NO CHANGE
```python
# Role: Export clips with FFmpeg
# Impact: NONE
# Reason: Runs after PASO2 (copy generation)
```

### 5. **Copys_generator.py** ⚠️ MODIFICATIONS NEEDED (Step 04)
```python
# Role: Generate copies with LLM
# CURRENT CODE:
def _generate_viral_node(self, state):
    prompt = self.viral_prompt_template  # Hardcoded
    copy = self.llm.invoke(prompt)

# NEW CODE:
def _generate_viral_node(self, state):
    language = clip.get("language", "es")
    prompt_text = self._load_language_specific_prompt("viral", language)
    copy = self.llm.invoke(prompt_text)

# Impact: YES - Add language-aware prompt loading
```

### 6. **Subtitle_generator.py** ⚠️ ADDITIONS NEEDED (Step 01)
```python
# Role: Generate subtitles
# NEW METHODS ADDED:
- extract_opening_words_from_clip()
- extract_speaker_hashtags()

# Impact: YES - Add 2 new methods (no existing code changes)
```

### 7. **Models/copy_schemas.py** ⚠️ SCHEMA UPDATE NEEDED (Step 03)
```python
# Role: Validate copy data
# NEW FIELDS:
- opening_words: str
- opening_words_used: bool
- speaker_hashtags_provided: List[str]

# Impact: YES - Add validation fields
```

---

## File Path Resolution

**Key question:** Where should prompts be loaded from?

**Answer: Relative to project root**

```python
# In copys_generator.py, when running from project root:
# /Users/ee/Documents/opino.tech/Cliper/

prompt_path = Path(f"src/prompts/{style}_prompt_{language_code}.txt")

# This resolves to:
# /Users/ee/Documents/opino.tech/Cliper/src/prompts/viral_prompt_ES.txt
```

**Ensure script is run from project root:**
```bash
# ✅ Correct (from Cliper directory)
cd /Users/ee/Documents/opino.tech/Cliper
python cliper.py

# ❌ Wrong (from subdirectory)
cd src/
python ../cliper.py  # Path resolution breaks
```

---

## Required File Movements

**Current state (before changes):**
```
src/prompts/
├── viral_prompt.txt
├── educational_prompt.txt
└── storytelling_prompt.txt
```

**After enhancement (rename + create):**
```
src/prompts/
├── viral_prompt_ES.txt              (renamed + enhanced)
├── viral_prompt_EN.txt              (new)
├── educational_prompt_ES.txt        (renamed + enhanced)
├── educational_prompt_EN.txt        (new)
├── storytelling_prompt_ES.txt       (renamed + enhanced)
└── storytelling_prompt_EN.txt       (new)
```

**Action items:**
1. Rename `viral_prompt.txt` → `viral_prompt_ES.txt`
2. Rename `educational_prompt.txt` → `educational_prompt_ES.txt`
3. Rename `storytelling_prompt.txt` → `storytelling_prompt_ES.txt`
4. Create 3 new English versions

---

## Code Changes Required: Summary

### File 1: `src/subtitle_generator.py` (Step 01)
```
- Add method: extract_opening_words_from_clip()
- Add method: extract_speaker_hashtags()
- No changes to existing methods
- No new imports
```

### File 2: `src/copys_generator.py` (Step 04)
```
- Add method: _load_language_specific_prompt(style, language)
- Modify: _extract_opening_words_node() to add language to state
- Modify: _generate_viral_node() to load language-specific prompt
- Modify: _generate_educational_node() to load language-specific prompt
- Modify: _generate_storytelling_node() to load language-specific prompt
- New import: from pathlib import Path (for file operations)
```

### File 3: `src/models/copy_schemas.py` (Step 03)
```
- Add field: opening_words: str = ""
- Add field: opening_words_used: bool = False
- Add field: speaker_hashtags_provided: List[str] = []
- Add validator: validate_opening_words_present()
```

### File 4: Prompt files (Step 02)
```
- Rename 3 files (add _ES suffix)
- Create 3 new files (_EN versions)
- Update content: Add CRITICAL CONSTRAINT section
- No code changes - just text files
```

---

## Imports: What's Already Needed vs. New

### Already in copys_generator.py:
```python
import json
from langchain.llms import ChatOpenAI  # or similar
from loguru import logger
```

### Need to add (Step 04):
```python
from pathlib import Path  # For file operations
```

**That's it!** No complex imports needed.

---

## Backward Compatibility Plan

**If old code references `viral_prompt.txt` directly:**

```python
# OLD CODE (deprecated):
with open("src/prompts/viral_prompt.txt") as f:
    prompt = f.read()

# NEW CODE (replacement):
language = clip.get("language", "es")
with open(f"src/prompts/viral_prompt_{language.upper()}.txt") as f:
    prompt = f.read()

# Or use the helper method:
prompt = self._load_language_specific_prompt("viral", language)
```

**Where to check for old references:**
- `cliper.py` (main CLI)
- Any test files that mock prompts
- Documentation that hardcodes prompt paths

---

## Error Handling for Missing Prompts

**Recommended defensive code (Step 04):**

```python
def _load_language_specific_prompt(self, style: str, language: str = "es") -> str:
    """Load prompt, with fallback to Spanish"""
    language_code = "ES" if language.lower().startswith("es") else "EN"
    prompt_file = Path(f"src/prompts/{style}_prompt_{language_code}.txt")

    # Try to load specific language
    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()

    # Fallback to Spanish if English not found
    if language_code == "EN":
        self.logger.warning(f"English prompt not found: {prompt_file}")
        self.logger.warning(f"Falling back to Spanish prompt")
        spanish_file = Path(f"src/prompts/{style}_prompt_ES.txt")
        with open(spanish_file, 'r', encoding='utf-8') as f:
            return f.read()

    # If Spanish also missing, raise error
    raise FileNotFoundError(f"No prompts found for style: {style}")
```

---

## Pipeline Dependency Graph (After Enhancement)

```
download.py
    ↓
transcriber.py [Adds language metadata]
    ↓
clips_generator.py
    ↓
copys_generator.py [Reads language, loads language-specific prompts]
    ├─ reads: src/prompts/viral_prompt_{ES|EN}.txt
    ├─ reads: src/prompts/educational_prompt_{ES|EN}.txt
    └─ reads: src/prompts/storytelling_prompt_{ES|EN}.txt
    ↓
video_exporter.py
    ↓
cleanup_manager.py
```

**New dependencies:**
- `copys_generator.py` now depends on prompt files (file path)
- No Python module dependencies added

---

## Deployment Checklist

**Before running enhanced PASO2:**

- [ ] Rename 3 Spanish prompt files (add `_ES`)
- [ ] Create 3 English prompt files (`_EN`)
- [ ] Verify all 6 files in `src/prompts/` directory
- [ ] Run from project root (for path resolution)
- [ ] All prompt files encoded in UTF-8
- [ ] Test with Spanish clip first (default language)
- [ ] Test with English clip (if available)

**After deployment:**

- [ ] Old `viral_prompt.txt` etc. no longer used (can be deleted)
- [ ] No import errors
- [ ] Prompts load correctly
- [ ] Language detection works
- [ ] Both Spanish and English copies generated correctly

---

## No Breaking Changes ✅

**This enhancement:**
- ✅ Doesn't break existing code
- ✅ Doesn't require dependency updates
- ✅ Doesn't add Python imports
- ✅ Just adds new files + methods
- ✅ Maintains backward compatibility

**Risk level: MINIMAL**

---

## Summary: Impact on Pipeline

| Component | Impact | Work Needed |
|-----------|--------|------------|
| downloader.py | None | - |
| transcriber.py | None (already has language) | - |
| clips_generator.py | None | - |
| copys_generator.py | Major (but additive) | Add language-aware prompt loading |
| subtitle_generator.py | Addition | Add 2 new methods |
| copy_schemas.py | Addition | Add 3 fields + validator |
| Prompt files | Rename + Create | 6 files total (3 ES + 3 EN) |
| video_exporter.py | None | - |

**Total code changes: ~90 lines (all additive)**
**Total file changes: 3 files modified, 6 files created/renamed**
**Pipeline compatibility: 100%**

