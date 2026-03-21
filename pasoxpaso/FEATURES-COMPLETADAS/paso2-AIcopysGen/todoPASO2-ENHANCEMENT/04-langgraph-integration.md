# Step 04: Integrate into LangGraph (Add Opening Words Node)

**Objective:** Add new node to 10-node LangGraph to extract opening words before copy generation

**File to modify:**
- `src/copys_generator.py`

**Time estimate:** 20 minutes

---

## Current LangGraph Flow (10 nodes)

```
START
  ↓
[1] CLASSIFY_CLIPS → Determine viral/educational/storytelling
  ↓
[2] GROUP_BY_STYLE → Partition by style
  ↓
[3] GENERATE_VIRAL → Generate for viral clips
[4] GENERATE_EDUCATIONAL → Generate for educational
[5] GENERATE_STORYTELLING → Generate for storytelling
  ↓
[6] MERGE_COPIES → Combine all results
  ↓
[7] VALIDATE_COPIES → Pydantic validation
  ↓
[8] ANALYZE_QUALITY → Check engagement scores
  ↓
[9] SAVE_COPIES → Save to file
  ↓
[10] HANDLE_RETRY → Retry on failure
  ↓
END
```

---

## New Flow (11 nodes)

```
START
  ↓
[1] CLASSIFY_CLIPS → Determine viral/educational/storytelling
  ↓
[2] GROUP_BY_STYLE → Partition by style
  ↓
[2.5] EXTRACT_OPENING_WORDS ← [NEW] Extract before generation
  ↓
[3] GENERATE_VIRAL → Generate (now has opening_words in state)
[4] GENERATE_EDUCATIONAL → Generate (now has opening_words in state)
[5] GENERATE_STORYTELLING → Generate (now has opening_words in state)
  ↓
[6] MERGE_COPIES → Combine all results
  ↓
[7] VALIDATE_COPIES → Pydantic validation (checks opening words!)
  ↓
[8] ANALYZE_QUALITY → Check engagement scores
  ↓
[9] SAVE_COPIES → Save to file
  ↓
[10] HANDLE_RETRY → Retry on failure
  ↓
END
```

**Why after GROUP_BY_STYLE?**
- All clips already classified by style
- Before generation nodes (they need opening_words)
- Can extract once for all clips at once

---

## New Node: `_extract_opening_words_node()`

**Location in copys_generator.py:**
```python
class CopysGenerator:
    def __init__(self, ...):
        self.subtitle_generator = SubtitleGenerator(...)  # Existing
        # ...

    def generate_copies(self, ...):
        """Main entry point"""
        graph = StateGraph(CopysGeneratorState)

        # Add all nodes...
        graph.add_node("classify_clips", self._classify_clips_node)
        graph.add_node("group_by_style", self._group_by_style_node)
        graph.add_node("extract_opening_words", self._extract_opening_words_node)  # [NEW]
        graph.add_node("generate_viral", self._generate_viral_node)
        # ... rest of nodes ...

        # Connect nodes...
        graph.add_edge("classify_clips", "group_by_style")
        graph.add_edge("group_by_style", "extract_opening_words")  # [NEW]
        graph.add_edge("extract_opening_words", "generate_viral")  # [NEW]
        # ... rest of edges ...

    def _extract_opening_words_node(self, state):
        """
        Extract speaker's opening words from each clip before generation.

        This node:
        1. Takes classified + grouped clips
        2. For each clip, extracts first 5-10 seconds of speaker's words
        3. Also extracts any hashtags speaker mentioned
        4. Adds to each clip: opening_words, speaker_hashtags
        5. Passes updated state to generation nodes
        """
        # TODO: Implement
        pass
```

---

## Node Implementation Pattern

**What the node does:**

```python
def _extract_opening_words_node(self, state):
    """Extract opening words for all clips"""

    clips = state["clips"]
    extraction_results = []

    for clip in clips:
        try:
            # 1. Extract opening words from transcript
            opening_info = self.subtitle_generator.extract_opening_words_from_clip(
                transcript=clip["transcript"],
                clip_start=clip["start"],
                clip_end=clip["end"],
                opening_duration=10.0  # First 10 seconds
            )

            # 2. Extract hashtags from clip text
            speaker_hashtags = self.subtitle_generator.extract_speaker_hashtags(
                clip_text=clip["full_text"]  # Or reconstruct from transcript
            )

            # 3. Add to clip object
            clip["opening_words"] = opening_info["opening_words"]
            clip["opening_words_duration"] = opening_info["opening_duration_actual"]
            clip["speaker_hashtags"] = speaker_hashtags

            extraction_results.append({
                "clip_id": clip["id"],
                "opening_words": opening_info["opening_words"],
                "hashtags": speaker_hashtags,
                "success": opening_info.get("success", True)
            })

            logger.info(
                f"Extracted opening words for clip {clip['id']}: "
                f"'{opening_info['opening_words']}'"
            )

        except Exception as e:
            logger.warning(
                f"Failed to extract opening words for clip {clip['id']}: {e}"
            )
            # Fallback: empty opening words (generation will still work)
            clip["opening_words"] = ""
            clip["speaker_hashtags"] = []

    # 4. Update state with extraction results
    state["clips"] = clips
    state["extraction_results"] = extraction_results

    logger.info(
        f"Extracted opening words for {len(clips)} clips. "
        f"Success: {sum(1 for r in extraction_results if r['success'])}/{len(clips)}"
    )

    return state
```

---

## State Updates

**Before node (state structure):**
```python
state = {
    "clips": [
        {
            "id": 0,
            "transcript": {...},  # WhisperX output
            "full_text": "La IA es revolucionaria...",
            "start": 15.0,
            "end": 80.0,
            "style": "viral"
        }
    ],
    "viral_clips": [0, 5, 12, ...],
    "educational_clips": [2, 8, 15, ...],
    # ...
}
```

**After node (state structure):**
```python
state = {
    "clips": [
        {
            "id": 0,
            "transcript": {...},
            "full_text": "La IA es revolucionaria...",
            "start": 15.0,
            "end": 80.0,
            "style": "viral",
            # [NEW] Added by extraction node:
            "opening_words": "La IA es revolucionaria",
            "opening_words_duration": 2.34,
            "speaker_hashtags": ["#AICDMX", "#Future"]
        }
    ],
    "viral_clips": [0, 5, 12, ...],
    # ... rest unchanged ...
    "extraction_results": [  # [NEW]
        {
            "clip_id": 0,
            "opening_words": "La IA es revolucionaria",
            "hashtags": ["#AICDMX", "#Future"],
            "success": True
        }
    ]
}
```

---

## Generation Nodes (Modified Usage with Language Support)

**Helper method - Load Language-Specific Prompt:**

```python
def _load_language_specific_prompt(self, style: str, language: str = "es") -> str:
    """
    Load language-specific prompt template

    Args:
        style: "viral", "educational", or "storytelling"
        language: "es" (Spanish) or "en" (English)

    Returns:
        Prompt template text
    """
    language_code = "ES" if language.lower().startswith("es") else "EN"
    prompt_file = Path(f"src/prompts/{style}_prompt_{language_code}.txt")

    if not prompt_file.exists():
        self.logger.warning(f"Prompt not found: {prompt_file}, using Spanish default")
        prompt_file = Path(f"src/prompts/{style}_prompt_ES.txt")

    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()
```

---

**Current generation node (before):**
```python
def _generate_viral_node(self, state):
    """Generate viral copies"""
    viral_clips = [state["clips"][i] for i in state["viral_clips"]]

    # Generate copy without opening words knowledge
    for clip in viral_clips:
        copy = self.llm.invoke(
            f"Generate viral copy for: {clip['full_text']}"
        )
        # ...
```

**After enhancement (with language support):**
```python
def _generate_viral_node(self, state):
    """Generate viral copies with language awareness"""
    viral_clips = [state["clips"][i] for i in state["viral_clips"]]

    # Load base prompt (language-specific)
    for clip in viral_clips:
        language = clip.get("language", "es")
        base_prompt = self._load_language_specific_prompt("viral", language)

        # Fill in dynamic values
        prompt = base_prompt.format(
            opening_words=clip.get("opening_words", ""),
            hashtags=" ".join(clip.get("speaker_hashtags", []))
        )

        # Add context
        full_prompt = f"{prompt}\n\nClip content:\n{clip['full_text']}"

        copy = self.llm.invoke(full_prompt)
        # ... rest of logic
```

**Key difference:** Language-specific prompt loaded based on `clip["language"]`

---

## Edge Cases Handled

| Case | Behavior |
|------|----------|
| Extraction fails | opening_words = "" (empty) |
| No hashtags found | speaker_hashtags = [] (empty list) |
| Clip < 10 seconds | Extract full clip duration |
| No transcript | Skip clip, log warning |

---

## Logging Strategy

**Info level (normal operation):**
```
✓ Extracted opening words for clip 0: 'La IA es revolucionaria'
✓ Extracted opening words for 30 clips. Success: 29/30
```

**Warning level (recoverable errors):**
```
⚠ Failed to extract opening words for clip 5: No words in opening window
⚠ No hashtags found in clip 12 - will use LLM-generated hashtags
```

**Error level (unrecoverable):**
```
✗ Critical error in extraction node: transcript missing for clip 8
```

---

## Integration Checklist

- [ ] Add `_extract_opening_words_node()` method to CopysGenerator class
- [ ] Add node to graph: `graph.add_node("extract_opening_words", self._extract_opening_words_node)`
- [ ] Add edge from GROUP_BY_STYLE: `graph.add_edge("group_by_style", "extract_opening_words")`
- [ ] Add edge to GENERATE_VIRAL: `graph.add_edge("extract_opening_words", "generate_viral")`
- [ ] Update GENERATE_* nodes to use `clip["opening_words"]` in prompt
- [ ] Update VALIDATE_COPIES to check opening_words_used
- [ ] Test with sample data (see Step 05)

---

## Next Steps

Once integration is complete:
→ Move to Step 05 (Testing)
