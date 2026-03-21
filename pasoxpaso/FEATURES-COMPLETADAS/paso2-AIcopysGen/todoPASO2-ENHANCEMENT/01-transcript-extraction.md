# Step 01: Add Opening Words Methods to SubtitleGenerator

**Objective:** Add two new methods to `SubtitleGenerator` class to extract opening words and hashtags

**File to modify:**
- `src/subtitle_generator.py`

**Time estimate:** 20 minutes

---

## Why SubtitleGenerator?

**Architectural fit:**
- SubtitleGenerator already parses WhisperX transcripts
- Already handles word-level timestamps
- Already has methods that work with transcript data
- Natural place to add opening word extraction

**Benefit:** No new files, reuses existing transcript logic

---

## Understanding WhisperX Output Format

**WhisperX provides word-level timestamps:**

```json
{
  "segments": [
    {
      "id": 0,
      "seek": 0,
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
      "words": [...]
    }
  ]
}
```

**For our use case:**
- Clip starts at timestamp `15.0` seconds
- Extract words where: `word["start"] >= 15.0` AND `word["start"] < 25.0` (10-sec window)
- Join into string: `"La IA es revolucionaria"`

---

## Method 1: `extract_opening_words_from_clip()`

**Signature:**
```python
def extract_opening_words_from_clip(
    self,
    transcript: Dict,
    clip_start: float,
    clip_end: float,
    opening_duration: float = 10.0
) -> Dict[str, any]:
```

**Input:**
```python
transcript = {  # WhisperX output
    "segments": [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.34,
            "words": [
                {"word": "La", "start": 0.0, "end": 0.3},
                ...
            ]
        }
    ]
}
clip_start = 15.0  # Clip starts at 15 seconds
clip_end = 80.0    # Clip ends at 80 seconds
opening_duration = 10.0  # Extract first 10 seconds
```

**Output:**
```python
{
    "opening_words": "La IA es revolucionaria",
    "opening_duration_actual": 2.34,  # How many seconds we actually captured
    "word_count": 4,
    "timestamp_range": (15.0, 17.34),
    "success": True
}
```

**Logic:**
```
1. Find clip's temporal window: [clip_start, clip_start + opening_duration]
2. Iterate through all segments in transcript
3. For each segment's words:
   - If word["start"] >= clip_start AND word["start"] < (clip_start + opening_duration)
   - Add word to list
4. Join words with spaces
5. Return with metadata
```

**Edge cases:**
- No words in opening window → return empty string with `success: False`
- Clip starts mid-word → include that word
- Opening duration < 10 sec (clip ends early) → use what's available

---

## Method 2: `extract_speaker_hashtags()`

**Signature:**
```python
def extract_speaker_hashtags(self, clip_text: str) -> List[str]:
```

**Input:**
```python
clip_text = "La IA es revolucionaria. Transforma cómo trabajamos. #AICDMX #Future #Tech"
```

**Output:**
```python
["#AICDMX", "#Future", "#Tech"]
```

**Logic:**
```
1. Use regex pattern: #\w+
2. Find all matches in clip_text
3. Deduplicate (in case speaker says #AI twice)
4. Return as list
```

**Edge cases:**
- No hashtags found → return empty list `[]`
- Hashtag at end of sentence → still captured
- Hashtag at line break → still captured

---

## Implementation Pattern

**Both methods are added to `SubtitleGenerator` class:**

```python
# src/subtitle_generator.py

class SubtitleGenerator:
    def __init__(self, ...existing params...):
        # existing initialization
        pass

    # ... existing methods (generate_srt, etc.) ...

    # ========== NEW METHODS ==========

    def extract_opening_words_from_clip(
        self,
        transcript: Dict,
        clip_start: float,
        clip_end: float,
        opening_duration: float = 10.0
    ) -> Dict[str, any]:
        """
        Extract speaker's opening words from a clip's transcript.

        Args:
            transcript: WhisperX transcript dict with word-level timestamps
            clip_start: Clip start time in seconds (e.g., 15.0)
            clip_end: Clip end time in seconds (e.g., 80.0)
            opening_duration: How many seconds to extract (default 10)

        Returns:
            Dict with keys:
            - opening_words: str (e.g., "La IA es revolucionaria")
            - opening_duration_actual: float (actual seconds captured)
            - word_count: int (number of words extracted)
            - timestamp_range: tuple (start, end) of extracted words
            - success: bool (whether extraction succeeded)

        Example:
            result = subtitle_gen.extract_opening_words_from_clip(
                transcript=clip["transcript"],
                clip_start=15.0,
                clip_end=80.0,
                opening_duration=10.0
            )
            # Returns: {"opening_words": "La IA es...", "word_count": 4, ...}
        """
        # TODO: Implementation (you'll write this)
        pass

    def extract_speaker_hashtags(self, clip_text: str) -> List[str]:
        """
        Extract hashtags speaker mentioned in clip.

        Args:
            clip_text: Full text of the clip

        Returns:
            List of hashtags found (e.g., ["#AICDMX", "#Future"])
            Empty list if no hashtags found

        Example:
            hashtags = subtitle_gen.extract_speaker_hashtags(
                "La IA es revolucionaria #AICDMX #Future"
            )
            # Returns: ["#AICDMX", "#Future"]
        """
        # TODO: Implementation (you'll write this)
        pass
```

---

## Questions Before Implementation

**I need to verify these to write correct code:**

1. **WhisperX integration:**
   - When clips are created in `clips_generator.py`, does each clip include the full `transcript` dict?
   - Or is transcript loaded separately?

2. **Transcript structure confirmation:**
   - Does transcript always have `["segments"]` with `words` field?
   - Are `word["start"]` and `word["end"]` always present?
   - What if a segment has no "words" field?

3. **Clip text data:**
   - When we need to extract hashtags, do we have the full clip text available?
   - Or do we need to reconstruct it from segments?

4. **Edge case behavior:**
   - If clip starts at 15s but first word starts at 16s: still include it?
   - If opening duration doesn't complete (clip ends), use partial?

**CONFIRMED FINDINGS (from transcriber.py analysis):**
- ✅ Clip includes `transcript` dict (WhisperX output)
- ✅ All words have `start`/`end` in seconds
- ✅ Extract exactly first 10 seconds of words from clip start
- ✅ Hashtags scanned from clip text (reconstructed from segments)
- ✅ **Language metadata included:** `transcript["language"]` = "spanish", "english", etc.

**Language Integration:**
```python
# In _extract_opening_words_node (copys_generator.py):
language = clip["transcript"].get("language", "es")
clip["language"] = language  # Add to state for prompt selection
```

Later in GENERATE_* nodes, use `clip["language"]` to load appropriate prompt file

---

## Next: Ready for Code Review

Once you confirm the questions above, I'll write the complete implementation with:
- ✓ Full function bodies (not TODOs)
- ✓ Error handling for all edge cases
- ✓ Detailed docstrings
- ✓ Logging statements for debugging
- ✓ Type hints for clarity

**Then we move to Step 02 (update prompts with opening words constraint)**
