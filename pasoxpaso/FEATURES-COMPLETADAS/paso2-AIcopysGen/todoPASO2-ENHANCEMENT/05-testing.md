# Step 05: Testing Opening Words Enhancement

**Objective:** Create test cases to verify extraction, validation, and integration

**Files to create:**
- `tests/test_opening_words_extraction.py`
- `tests/test_copy_with_opening_words.py`

**Time estimate:** 25 minutes

---

## Test Strategy

**Three levels of testing:**

1. **Unit Tests** (test_opening_words_extraction.py)
   - Opening words extraction logic
   - Hashtag extraction logic
   - Edge cases (no words, partial words, etc.)

2. **Schema Tests** (test_copy_with_opening_words.py)
   - Pydantic validation
   - Opening words presence check
   - Backward compatibility

3. **Integration Tests** (manual with real data)
   - Full PASO2 with enhancement
   - Real clip from "México y la guerra por los chips"
   - Verify output matches expected format

---

## Test 1: Unit Tests - Extraction Logic

**File:** `tests/test_opening_words_extraction.py`

```python
import pytest
from src.subtitle_generator import SubtitleGenerator


class TestOpeningWordsExtraction:
    """Unit tests for opening words extraction from transcripts"""

    @pytest.fixture
    def subtitle_gen(self):
        """Create SubtitleGenerator instance for testing"""
        return SubtitleGenerator()

    @pytest.fixture
    def sample_transcript(self):
        """Mock WhisperX transcript with word-level timestamps"""
        return {
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.34,
                    "text": "La IA es revolucionaria",
                    "words": [
                        {"word": "La", "start": 0.0, "end": 0.3},
                        {"word": "IA", "start": 0.3, "end": 0.6},
                        {"word": "es", "start": 0.6, "end": 0.9},
                        {"word": "revolucionaria", "start": 0.9, "end": 2.34}
                    ]
                },
                {
                    "id": 1,
                    "start": 2.4,
                    "end": 5.6,
                    "text": "Transforma cómo trabajamos",
                    "words": [
                        {"word": "Transforma", "start": 2.4, "end": 3.2},
                        {"word": "cómo", "start": 3.2, "end": 3.9},
                        {"word": "trabajamos", "start": 3.9, "end": 5.6}
                    ]
                }
            ]
        }

    def test_extract_opening_words_basic(self, subtitle_gen, sample_transcript):
        """Test basic opening words extraction"""
        result = subtitle_gen.extract_opening_words_from_clip(
            transcript=sample_transcript,
            clip_start=0.0,
            clip_end=30.0,
            opening_duration=10.0
        )

        assert result["opening_words"] == "La IA es revolucionaria Transforma cómo trabajamos"
        assert result["word_count"] == 7
        assert result["success"] is True

    def test_extract_opening_words_from_clip_start(self, subtitle_gen, sample_transcript):
        """Test extraction from middle of video"""
        # Transcript offset: words at 0-5.6 sec are now at 15-20.6 sec
        offset_transcript = {
            "segments": [
                {
                    "id": 0,
                    "start": 15.0,  # Offset
                    "end": 17.34,
                    "text": "La IA es revolucionaria",
                    "words": [
                        {"word": "La", "start": 15.0, "end": 15.3},
                        {"word": "IA", "start": 15.3, "end": 15.6},
                        {"word": "es", "start": 15.6, "end": 15.9},
                        {"word": "revolucionaria", "start": 15.9, "end": 17.34}
                    ]
                }
            ]
        }

        result = subtitle_gen.extract_opening_words_from_clip(
            transcript=offset_transcript,
            clip_start=15.0,  # Clip starts at 15 sec
            clip_end=80.0,
            opening_duration=10.0
        )

        assert "La IA es revolucionaria" in result["opening_words"]
        assert result["success"] is True

    def test_extract_opening_words_limited_duration(self, subtitle_gen, sample_transcript):
        """Test when opening duration exceeds available words"""
        result = subtitle_gen.extract_opening_words_from_clip(
            transcript=sample_transcript,
            clip_start=0.0,
            clip_end=3.0,  # Clip ends after 3 seconds
            opening_duration=10.0  # Request 10 seconds
        )

        # Should get whatever is available (< 10 seconds)
        assert result["opening_duration_actual"] < 10.0
        assert result["word_count"] > 0
        assert result["success"] is True

    def test_extract_no_words_in_window(self, subtitle_gen):
        """Test when no words found in time window"""
        transcript = {
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 2.0}
                    ]
                }
            ]
        }

        result = subtitle_gen.extract_opening_words_from_clip(
            transcript=transcript,
            clip_start=50.0,  # No words at 50-60 seconds
            clip_end=100.0,
            opening_duration=10.0
        )

        assert result["opening_words"] == ""
        assert result["word_count"] == 0
        assert result["success"] is False


class TestHashtagExtraction:
    """Unit tests for hashtag extraction"""

    @pytest.fixture
    def subtitle_gen(self):
        return SubtitleGenerator()

    def test_extract_hashtags_basic(self, subtitle_gen):
        """Test basic hashtag extraction"""
        text = "La IA es revolucionaria #AICDMX #Future #Tech"

        hashtags = subtitle_gen.extract_speaker_hashtags(text)

        assert hashtags == ["#AICDMX", "#Future", "#Tech"]

    def test_extract_hashtags_no_duplicates(self, subtitle_gen):
        """Test deduplication of hashtags"""
        text = "La IA #AICDMX is revolutionary. #AICDMX is the key. #Future"

        hashtags = subtitle_gen.extract_speaker_hashtags(text)

        assert hashtags == ["#AICDMX", "#Future"]
        assert len(hashtags) == len(set(hashtags))  # No duplicates

    def test_extract_no_hashtags(self, subtitle_gen):
        """Test when no hashtags present"""
        text = "La IA es revolucionaria sin hashtags"

        hashtags = subtitle_gen.extract_speaker_hashtags(text)

        assert hashtags == []

    def test_extract_hashtags_with_numbers(self, subtitle_gen):
        """Test hashtags with numbers"""
        text = "#AI2026 #Web3 #Future"

        hashtags = subtitle_gen.extract_speaker_hashtags(text)

        assert "#AI2026" in hashtags
        assert "#Web3" in hashtags
```

---

## Test 2: Schema Tests - Validation

**File:** `tests/test_copy_with_opening_words.py`

```python
import pytest
from pydantic import ValidationError
from src.models.copy_schemas import ClipCopy


class TestClipCopyWithOpeningWords:
    """Test ClipCopy schema with opening words validation"""

    def test_copy_with_opening_words_valid(self):
        """Test valid copy that uses opening words"""
        clip = ClipCopy(
            clip_id=1,
            copy_text="La IA es revolucionaria. 3 ways it changes everything. #AICDMX",
            opening_words="La IA es revolucionaria",
            style="viral",
            engagement_score=8.5,
            viral_potential=9.0,
            opening_words_used=True,
            speaker_hashtags_provided=["#AICDMX"]
        )

        assert clip.clip_id == 1
        assert "La IA es revolucionaria" in clip.copy_text
        assert clip.opening_words_used is True

    def test_copy_without_opening_words_fails(self):
        """Test that copy MUST include opening words if provided"""
        with pytest.raises(ValidationError) as exc_info:
            ClipCopy(
                clip_id=1,
                copy_text="Discover AI innovations today. #AICDMX",  # Missing opening words
                opening_words="La IA es revolucionaria",  # But we specified this
                style="viral",
                engagement_score=8.5,
                viral_potential=9.0
            )

        assert "opening words" in str(exc_info.value).lower()

    def test_copy_backward_compatible_no_opening_words(self):
        """Test backward compatibility when opening_words not provided"""
        clip = ClipCopy(
            clip_id=1,
            copy_text="Discover AI innovations today. #AICDMX",
            style="viral",
            engagement_score=8.5,
            viral_potential=9.0
            # opening_words not provided - should default to ""
        )

        assert clip.opening_words == ""
        # Validation should pass (opening_words is empty, so no check)

    def test_opening_words_case_insensitive(self):
        """Test that opening words check is case-insensitive"""
        clip = ClipCopy(
            clip_id=1,
            copy_text="LA IA ES REVOLUCIONARIA. 3 ways it changes everything. #AICDMX",
            opening_words="La IA es revolucionaria",  # lowercase in original
            style="viral",
            engagement_score=8.5,
            viral_potential=9.0
        )

        # Should pass (case-insensitive match)
        assert clip.copy_text is not None

    def test_hashtag_validation_still_works(self):
        """Test that existing #AICDMX validation still works"""
        with pytest.raises(ValidationError) as exc_info:
            ClipCopy(
                clip_id=1,
                copy_text="La IA es revolucionaria. Amazing content.",  # Missing #AICDMX
                opening_words="La IA es revolucionaria",
                style="viral",
                engagement_score=8.5,
                viral_potential=9.0
            )

        assert "#AICDMX" in str(exc_info.value)

    def test_all_fields_present(self):
        """Test that all new fields are accessible"""
        clip = ClipCopy(
            clip_id=1,
            copy_text="La IA es revolucionaria. #AICDMX #Future",
            opening_words="La IA es revolucionaria",
            opening_words_used=True,
            speaker_hashtags_provided=["#AICDMX", "#Future"],
            style="viral",
            engagement_score=8.5,
            viral_potential=9.0
        )

        assert clip.opening_words == "La IA es revolucionaria"
        assert clip.opening_words_used is True
        assert clip.speaker_hashtags_provided == ["#AICDMX", "#Future"]
```

---

## Test 3: Integration Test (Manual)

**Steps to run manual integration test:**

```bash
# 1. Use real clip from "México y la guerra por los chips"
# 2. Extract opening words manually to verify
# 3. Run PASO2 with enhancement enabled
# 4. Check output:

# Expected output format:
# clip_0_copy.json:
{
  "clip_id": 0,
  "copy_text": "México enfrenta una guerra silenciosa... [AI-generated hook] #AICDMX",
  "opening_words": "México enfrenta una guerra silenciosa",
  "opening_words_used": true,
  "style": "viral",
  "engagement_score": 8.7,
  ...
}

# Verify:
# ✓ opening_words extracted correctly
# ✓ opening_words appear at START of copy_text
# ✓ Copy continues naturally from opening words
# ✓ engagement_score >= 7.5
```

---

## Running Tests

```bash
# Run unit tests only
cd /Users/ee/Documents/opino.tech/Cliper
pytest tests/test_opening_words_extraction.py -v
pytest tests/test_copy_with_opening_words.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Success Criteria

**Tests pass if:**
- ✓ Unit tests: 100% pass (extraction, validation, edge cases)
- ✓ Schema tests: 100% pass (validation logic works)
- ✓ Integration: Real clip produces correct format
- ✓ No breaking changes (backward compatibility maintained)

**Quality metrics:**
- ✓ All opening words appear in final copy
- ✓ Hashtags from speaker are used
- ✓ Engagement scores >= 7.5
- ✓ No ValidationErrors for valid input

---

## Next: Manual Testing Checklist

After all code changes, run this checklist:

- [ ] Create test files (test_opening_words_extraction.py, test_copy_with_opening_words.py)
- [ ] Run unit tests: `pytest tests/test_opening_words_extraction.py -v`
- [ ] Run schema tests: `pytest tests/test_copy_with_opening_words.py -v`
- [ ] Download real clip "México y la guerra por los chips"
- [ ] Run: `uv run python cliper.py --download [URL]`
- [ ] Run: `uv run python cliper.py --process`
- [ ] Check output folder for copy format
- [ ] Verify opening words in first line of every copy
- [ ] Check engagement scores are >= 7.5

---

**Once all tests pass → Feature complete!**
