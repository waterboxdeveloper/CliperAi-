# Step 03: Update Copy Schemas with Validation

**Objective:** Add new fields to `ClipCopy` model and validate opening words usage

**File to modify:**
- `src/models/copy_schemas.py`

**Time estimate:** 15 minutes

---

## Current Schema (What Exists)

```python
# src/models/copy_schemas.py (current)

class ClipCopy(BaseModel):
    clip_id: int
    copy_text: str
    style: Literal["viral", "educational", "storytelling"]
    engagement_score: float = Field(ge=0, le=10)
    viral_potential: float = Field(ge=0, le=10)

    @field_validator('copy_text')
    def validate_hashtag(cls, v):
        if '#AICDMX' not in v:
            raise ValueError("Copy must include #AICDMX")
        return v
```

**Current responsibility:**
- Validates copy format
- Ensures #AICDMX hashtag present
- Type checks all fields

---

## New Schema (Enhanced)

**Add three new fields:**

```python
# src/models/copy_schemas.py (enhanced)

class ClipCopy(BaseModel):
    # EXISTING FIELDS
    clip_id: int
    copy_text: str
    style: Literal["viral", "educational", "storytelling"]
    engagement_score: float = Field(ge=0, le=10)
    viral_potential: float = Field(ge=0, le=10)

    # NEW FIELDS (for opening words tracking)
    opening_words: str = ""                          # What we extracted from speaker
    opening_words_used: bool = False                 # Did LLM actually use them?
    speaker_hashtags_provided: List[str] = Field(default_factory=list)  # Which hashtags we suggested

    @field_validator('copy_text')
    def validate_hashtag(cls, v):
        """Existing: Ensure #AICDMX is present"""
        if '#AICDMX' not in v:
            raise ValueError("Copy must include #AICDMX")
        return v

    @field_validator('copy_text')
    def validate_opening_words_present(cls, v, info):
        """NEW: Ensure opening words appear in copy"""
        opening = info.data.get('opening_words', '')

        # If we provided opening words, they MUST appear in copy
        if opening and opening.lower() not in v.lower():
            raise ValueError(
                f"Copy must start with speaker's opening words: '{opening}'. "
                f"Got: '{v[:50]}...'"
            )

        return v
```

---

## Field Explanations

### `opening_words: str = ""`

**Purpose:** Track what we extracted from the transcript

**Example:**
```python
clip.opening_words = "La IA es revolucionaria"
```

**Why needed:**
- Audit trail (know what we asked LLM to use)
- Debugging (if validation fails, know what was expected)
- Analytics (track which opening words worked best)

**Default:** Empty string (backward compatible)

---

### `opening_words_used: bool = False`

**Purpose:** Track whether LLM actually used the opening words

**Set in copys_generator.py:**
```python
# After LLM generates copy, check if opening words are present
if clip.opening_words.lower() in copy_text.lower():
    clip.opening_words_used = True
else:
    clip.opening_words_used = False  # Validation should catch this
```

**Why needed:**
- Metrics (what % of copies start with opening words?)
- Quality feedback (if often False, opening words extraction may be wrong)
- Retry logic (if False, we can prompt LLM more strictly)

**Default:** False (assumes failure until proven otherwise)

---

### `speaker_hashtags_provided: List[str] = []`

**Purpose:** Track which hashtags we extracted from speaker

**Example:**
```python
clip.speaker_hashtags_provided = ["#AICDMX", "#Future", "#Tech"]
```

**Why needed:**
- Verify LLM used speaker's hashtags (vs. inventing new ones)
- Analytics (which speaker hashtags appear most in final copy)
- Fallback logic (if speaker mentioned no hashtags, we know to use LLM-generated ones)

**Default:** Empty list (backward compatible)

---

## Validation Logic Explanation

**Current validator (unchanged):**
```python
@field_validator('copy_text')
def validate_hashtag(cls, v):
    if '#AICDMX' not in v:
        raise ValueError("Copy must include #AICDMX")
    return v
```

This still runs and checks #AICDMX is present.

**New validator (added):**
```python
@field_validator('copy_text')
def validate_opening_words_present(cls, v, info):
    """NEW: Ensure opening words appear in copy"""
    opening = info.data.get('opening_words', '')

    if opening and opening.lower() not in v.lower():
        raise ValueError(
            f"Copy must start with speaker's opening words: '{opening}'. "
            f"Got: '{v[:50]}...'"
        )

    return v
```

**How it works:**
1. Get `opening_words` from model data
2. If opening_words is not empty AND
3. Opening words don't appear in copy (case-insensitive) THEN
4. Raise ValidationError with helpful message

**Example validation failures:**

```python
# FAIL: Opening words missing
try:
    clip = ClipCopy(
        clip_id=1,
        copy_text="Descubre cómo la IA cambia todo...",  # Missing opening
        opening_words="La IA es revolucionaria",  # But we provided this
        style="viral",
        engagement_score=8.0,
        viral_potential=9.0
    )
except ValidationError as e:
    print(e)
    # Output: Copy must start with speaker's opening words:
    #         'La IA es revolucionaria'. Got: 'Descubre cómo...'
```

```python
# PASS: Opening words present
clip = ClipCopy(
    clip_id=1,
    copy_text="La IA es revolucionaria. 3 ways it changes your work. #AICDMX",
    opening_words="La IA es revolucionaria",
    style="viral",
    engagement_score=8.0,
    viral_potential=9.0
)
# ✓ Validation passes
```

---

## Backward Compatibility

**Old code (without opening_words):**
```python
clip = ClipCopy(
    clip_id=1,
    copy_text="Descubre cómo la IA cambia...",
    style="viral",
    engagement_score=8.0,
    viral_potential=9.0
)
# Still works! opening_words defaults to ""
# Validator skips check (because opening_words is empty)
```

**New code (with opening_words):**
```python
clip = ClipCopy(
    clip_id=1,
    copy_text="La IA es revolucionaria...",
    opening_words="La IA es revolucionaria",
    style="viral",
    engagement_score=8.0,
    viral_potential=9.0,
    opening_words_used=True,
    speaker_hashtags_provided=["#AICDMX", "#Future"]
)
# Also works! New fields are optional
```

---

## Implementation Steps

**File: `src/models/copy_schemas.py`**

### Step 1: Add imports (if needed)
```python
from typing import List  # Make sure List is imported
```

### Step 2: Add new fields to ClipCopy class
```python
# After existing fields, add:

opening_words: str = ""
opening_words_used: bool = False
speaker_hashtags_provided: List[str] = Field(default_factory=list)
```

### Step 3: Add new validator
```python
@field_validator('copy_text')
def validate_opening_words_present(cls, v, info):
    """Ensure opening words appear in copy if provided"""
    opening = info.data.get('opening_words', '')

    if opening and opening.lower() not in v.lower():
        raise ValueError(
            f"Copy must start with speaker's opening words: '{opening}'. "
            f"Got: '{v[:50]}...'"
        )

    return v
```

### Step 4: Verify syntax
```bash
cd /Users/ee/Documents/opino.tech/Cliper
python -m py_compile src/models/copy_schemas.py
# Should output nothing if successful
```

---

## Testing the Schema

**After modification, test:**

```python
from src.models.copy_schemas import ClipCopy

# Test 1: Validation passes (opening words present)
clip = ClipCopy(
    clip_id=1,
    copy_text="La IA es revolucionaria. This is important. #AICDMX",
    opening_words="La IA es revolucionaria",
    style="viral",
    engagement_score=8.0,
    viral_potential=9.0,
    opening_words_used=True
)
print("✓ Test 1 passed")

# Test 2: Validation fails (opening words missing)
try:
    clip = ClipCopy(
        clip_id=2,
        copy_text="Discover AI innovations #AICDMX",
        opening_words="La IA es revolucionaria",
        style="viral",
        engagement_score=8.0,
        viral_potential=9.0
    )
    print("✗ Test 2 failed - should have raised ValidationError")
except ValueError as e:
    print(f"✓ Test 2 passed - caught error: {e}")

# Test 3: Backward compatibility (no opening_words)
clip = ClipCopy(
    clip_id=3,
    copy_text="Legacy copy without new fields #AICDMX",
    style="viral",
    engagement_score=8.0,
    viral_potential=9.0
)
print("✓ Test 3 passed - backward compatible")
```

---

## Next Steps

Once schema is updated:
→ Move to Step 04 (Integrate into LangGraph)
