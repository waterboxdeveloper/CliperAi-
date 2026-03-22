# Cross-Language Subtitles Feature Analysis

**Status:** 🚧 PROPOSED (no implementation yet)
**Date:** 2026-03-21
**Context:** CLI currently shows `[cyan]Add burned-in subtitles (English)?[/cyan]` which is misleading

---

## Problem Statement

### Current Behavior (cliper.py)
```python
"[cyan]Add burned-in subtitles (English)?[/cyan]",
```

### Issues
1. **Misleading prompt:** Assumes subtitles will be in English
2. **Wrong assumption:** Subtitles are generated from transcript in VIDEO's language, not English
3. **No flexibility:** User cannot choose subtitle language different from video language
4. **Hard-coded:** English is hard-coded in the question

---

## Desired Behavior

### Phase 1: Fix Current Behavior (Quick Win)
```
Question: "Add burned-in subtitles?"  [y/n]
Behavior: Auto-generate subtitles in VIDEO's language
```

**Why:**
- Subtitles should match video language (user expectation)
- No choice needed for Phase 1
- Language is already detected by WhisperX

### Phase 2: Cross-Language Subtitles (Advanced Feature)
```
Question: "Add burned-in subtitles?"  [y/n]
If yes:
  "Subtitle language: [1] Same as video (Spanish) [2] English [3] Other"
```

**Use Cases:**
- Spanish video → English subtitles (for bilingual distribution)
- English video → Spanish subtitlesper (accessibility)
- Any video → Multiple language versions

---

## Architecture: Phase 2 (Future Implementation)

### Pipeline Impact

```
Current Flow:
Video → Transcribe (WhisperX) → Detect Language → Generate Subtitles (same lang)

New Flow (Phase 2):
Video → Transcribe (WhisperX) → Detect Language
    ├─ Option 1: Generate Subtitles (same language)
    ├─ Option 2: Translate → Generate Subtitles (different language)
    └─ Option 3: Generate Subtitles (multiple languages)
```

### Proposed Implementation Path

**Step 1: Add subtitle language parameter**
```python
# subtitle_generator.py
def generate_srt_from_transcript(
    self,
    transcript_path: str,
    output_path: Optional[str] = None,
    target_language: str = "auto"  # "auto" = same as video
) -> Optional[str]:
```

**Step 2: Translation layer (if target_language != video_language)**
```python
# translation_service.py (NEW FILE)
class TranslationService:
    def translate_transcript(
        self,
        transcript: Dict,
        source_language: str,
        target_language: str,
        provider: str = "gemini"  # or anthropic, deepl, etc
    ) -> Dict:
        """Translate transcript while preserving timestamps"""
```

**Step 3: CLI integration**
```python
# cliper.py
subtitle_language = prompt.ask(
    "[cyan]Subtitle language:[/cyan]",
    choices=[
        "same",      # Same as video (default)
        "english",   # English
        "spanish",   # Spanish
        "french",    # etc
        "custom"     # User specifies
    ],
    default="same"
)
```

### Files That Need Changes

| File | Change | Type | Effort |
|------|--------|------|--------|
| `subtitle_generator.py` | Add `target_language` param | Modification | Low |
| `translation_service.py` | NEW - Translation logic | New File | High |
| `video_exporter.py` | Accept multiple subtitle tracks | Modification | Medium |
| `cliper.py` | Fix prompt, add language choice | Modification | Low |
| `models/subtitle_schemas.py` | Add language metadata | New File | Low |

---

## Critical Decisions (To Be Made)

### 1. Translation Provider
**Options:**
- A: **Gemini API** (using existing infrastructure)
  - ✅ Already in use for copy generation
  - ✅ Bilingual support proven (PASO2)
  - ❌ Cost per translation

- B: **DeepL API** (specialized translation)
  - ✅ Superior translation quality
  - ✅ Cost-effective for volume
  - ❌ New dependency

- C: **Google Translate API** (simple, standard)
  - ✅ Wide language support
  - ✅ Reliable
  - ❌ Rate limits, cost

**Recommendation:** Start with Gemini (reuse infrastructure), consider DeepL for production.

### 2. Timestamp Preservation
**Challenge:** Translation can change word count → timestamps may shift

**Solution Options:**
- A: **Align to original timestamps** (may break sync)
- B: **Re-calculate timestamps** (requires word-level timing from translation)
- C: **Keep original language subtitles** (don't translate, only use for reference)

**Recommendation:** Option B - preserve sync quality

### 3. Multiple Language Output
**Question:** Generate subtitles in multiple languages simultaneously?

**Options:**
- Sequential: English → Spanish → French (one at a time)
- Batch: All languages in one call (faster)

**Recommendation:** Sequential first, batch later if performance needed.

---

## Architectural Alignment

### PASO Structure
```
PASO1: Download + Transcribe + Detect Clips ✅
PASO2: AI Copy Generation (with language support) ✅
PASO3: Face Tracking & Reframing ✅
PASO4: Branding (Logo + Outro) 🚧
PASO5: Publishing (Postiz) ⏳
PASO6: Cross-Language Subtitles ⏳ (PROPOSED)
```

### Bilingual Infrastructure Already Exists
From PASO2 enhancement:
- ✅ Language detection (WhisperX)
- ✅ Language-aware prompt loading (`get_prompt_for_style(style, language)`)
- ✅ Bilingual validation (Pydantic schemas)
- ✅ Multi-language testing framework

**Impact:** Cross-language subtitles can reuse this infrastructure.

---

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Translation quality** | Wrong meaning in subtitles | Use quality provider (DeepL), human review option |
| **Timestamp drift** | Out-of-sync subtitles | Re-calculate timestamps algorithmically |
| **API costs** | Budget impact | Implement caching, batch processing |
| **Language support gaps** | Unsupported languages fail | Start with top 10 languages, graceful fallback |
| **User confusion** | Wrong subtitle selection | Clear CLI labeling, sensible defaults |

---

## Quick Win: Fix Phase 1 (Now)

Before implementing Phase 2, fix the current misleading prompt:

**Change in cliper.py:**
```python
# BEFORE:
"[cyan]Add burned-in subtitles (English)?[/cyan]",

# AFTER:
"[cyan]Add burned-in subtitles?[/cyan]",  # Subtitles will be in video language
```

**Why now:**
- 5-minute fix
- Removes confusion
- No code impact
- Users get correct behavior

---

## Timeline Estimate (Phase 2)

| Step | Time | Notes |
|------|------|-------|
| Decide translation provider | 1 hour | DeepL vs Gemini vs Google Translate |
| Implement translation service | 8 hours | Handle timestamp preservation |
| Update subtitle_generator.py | 2 hours | Add language parameter |
| CLI integration | 2 hours | Language selection UI |
| Testing | 4 hours | Unit + integration tests |
| Documentation | 2 hours | Usage guide + architecture |
| **TOTAL** | **~19 hours** | ~2-3 days of work |

---

## Success Criteria (Phase 2)

✅ User can select subtitle language different from video language
✅ Subtitles remain in perfect sync with video
✅ All major languages supported (ES, EN, FR, DE, PT, etc)
✅ Translation quality is high (manual review not needed)
✅ Cost per video < $0.50 for multi-language subtitles
✅ Graceful fallback if translation fails

---

## Next Steps

1. ✅ **Approve Phase 1 fix** (5 min change)
2. ⏳ **Decide on translation provider** (when ready for Phase 2)
3. ⏳ **Plan Phase 2 implementation** (create implementation steps)
4. ⏳ **Execute Phase 2** (19 hours estimated)

---

## Subtitle Styling & Positioning (Phase 3: UX Critical)

### Problem Statement

Current subtitle styling is inconsistent and limited:
- ❌ Only one or two style options
- ❌ Fixed positioning cannot adapt to different scenes
- ❌ Monochrome - no way to emphasize key words
- ❌ Font size varies - inconsistent look

### Desired Behavior

**3 Positions, All Extra-Tiny (8px), All Yellow, FFmpeg Native**

Using ffmpeg's `subtitles` filter with ASS/SSA styles:

```
Position 1: BOTTOM (Default - waist level)
- Alignment: 2 (bottom-center)
- MarginV: 20 (20px from bottom)
- Font: 8px, Bold: 0
- Color: Yellow (#FFFF00)
- Purpose: Primary position, maximum visibility

Position 2: MIDDLE (Mid-frame)
- Alignment: 5 (middle-center)
- MarginV: 0 (centered)
- Font: 8px, Bold: 0
- Color: Yellow (#FFFF00)
- Purpose: Alternative when bottom crowded

Position 3: VERY HIGH (Top of frame)
- Alignment: 8 (top-center)
- MarginV: 10 (10px from top)
- Font: 8px, Bold: 0
- Color: Yellow (#FFFF00)
- Purpose: Alternative for extreme cases
```

### NEW: Multicolor Subtitles (Word-Level Emphasis)

**Capability:** Change subtitle color per word using ASS override tags

```
Instead of: "La inteligencia artificial es fascinante"
           [all yellow]

We can have: "La inteligencia {artificial} es fascinante"
            [yellow] [yellow] [magenta] [yellow] [yellow]

Implementation: SRT → ASS conversion with inline color tags
```

**Use Case:** Emphasize keywords (product names, hashtags, calls-to-action)
- Default color: Yellow (#FFFF00)
- Emphasis color: Magenta (#FF00FF) or other
- Keyword list: Pass from clip metadata to subtitle_generator

**Technical Implementation:**
- ASS/SSA format supports `{\c&H0000FF&}color text{\c}` syntax
- Can be added when generating SRT → ASS conversion
- No ffmpeg changes needed - native ASS feature

### Why Stay with FFmpeg Native?

**Decision:** Use ffmpeg `subtitles` filter instead of PIL rendering
- ✅ Already integrated and tested
- ✅ No new dependencies
- ✅ Fast and reliable
- ✅ ASS format natively supports multicolor
- ✅ Simplifies deployment (no PIL overhead)

**Trade-off:** Can't do dynamic face-aware positioning, but:
- 3 fixed positions cover 95% of use cases
- Keep in frame strategy (PASO3) already handles face safety
- Subtitle positioning secondary to face clarity

### Implementation Impact

**Files affected:**
- `src/video_exporter.py` → Simplify to 3 styles (bottom, middle, very_high)
- `src/subtitle_generator.py` → Support multicolor via ASS tags
- `cliper.py` → CLI: Ask user for position (bottom/middle/very_high)
- `tests/test_subtitle_styles.py` → NEW - validate all 3 positions

**CLI Integration:**
```python
subtitle_position = prompt.ask(
    "Subtitle position?",
    choices=["bottom", "middle", "very_high"],
    default="bottom"
)
```

---

## Multicolor Implementation: SRT → ASS Conversion (Phase 3b)

### Decision: Option B - Generate ASS Directly in subtitle_generator.py

**Why B instead of A (runtime conversion)?**

| Aspect | A: Runtime Conversion | B: Direct ASS Generation |
|--------|----------------------|--------------------------|
| **When conversion happens** | During export (per clip) | During transcription (once) |
| **Performance impact** | Per-clip overhead | Zero overhead at export |
| **File storage** | SRT only (smaller) | ASS only (slightly larger) |
| **Complexity** | Simpler initial code | Better architecture |
| **Flexibility** | Dynamic (can change per export) | Static (baked into file) |

**Why "greater initial complexity" is misleading:**
- B is NOT more complex, just different
- A requires regex parsing + tag insertion per export (repeated work)
- B requires understanding ASS format upfront, but clean afterwards
- Example: 30 clips × 10 exports = 300 conversions (A) vs 30 conversions (B)

### ASS Format vs SRT: What Changes?

**SRT Format (Current):**
```
1
00:00:00,000 --> 00:00:02,500
La inteligencia artificial es fascinante
```

**ASS Format (Proposed):**
```
[Script Info]
Title: Clip Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, ...
Style: Default,Arial,8,&H0000FFFF,&H00000000,...

[Events]
Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.50,Default,,0,0,0,,La inteligencia {\c&HFF00FF&}artificial{\c} es fascinante
```

**Key Differences:**
1. **Header metadata** - Styling info baked in (fonts, colors, positions)
2. **Override tags** - `{\c&HBBGGRR&}text{\c}` for per-word color changes
3. **Larger file size** - ~2-3KB per clip (negligible for video export)
4. **One-time generation** - All styling decided at subtitle creation

### Zero Export Overhead Explanation

**Current flow (SRT):**
```
Export: Read SRT → Pass to ffmpeg
        ffmpeg applies style via -vf filter (fontsize, color, positioning)
        Result: Styled video
```

**New flow (ASS):**
```
Export: Read ASS → Pass to ffmpeg
        ffmpeg applies style via ASS metadata (fontsize, color, positioning)
        Result: Styled video
```

**Why no overhead?**
- FFmpeg does styling work EITHER WAY
- Whether style info comes from `-vf filter` or ASS file = same CPU
- ASS actually slightly FASTER (no filter parsing needed)
- Difference: Negligible (<1% export time)

### Implementation: What subtitle_generator.py Must Do

**Current (SRT generation):**
```python
def generate_srt_from_transcript(self, transcript, output_path):
    srt_lines = []
    for segment in transcript['segments']:
        srt_lines.append(f"{sequence}\n{timestamp}\n{text}\n")

    with open(output_path, 'w') as f:
        f.write("\n".join(srt_lines))
    return output_path
```

**New (ASS generation):**
```python
def generate_ass_from_transcript(
    self,
    transcript,
    output_path,
    subtitle_position: str = "bottom",  # bottom, middle, very_high
    emphasis_keywords: Optional[List[str]] = None  # Words to highlight
):
    """
    Generate ASS file with:
    1. Header with style metadata (font, size, color, position)
    2. Events with word-level coloring (keyword emphasis)

    Args:
        transcript: WhisperX output with word timestamps
        output_path: Path to .ass file
        subtitle_position: Position of subtitles on screen
        emphasis_keywords: Words to highlight in different color

    Returns:
        Path to generated ASS file
    """

    # Build ASS header with positioning info
    header = f"""[Script Info]
Title: Clip Subtitles
...

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, ...
Style: {subtitle_position},Arial,8,&H0000FFFF,&H00000000,0,0,{margin_v},,
"""

    # Build events with word-level coloring
    events = []
    for segment in transcript['segments']:
        # Split by words, apply color to emphasis_keywords
        colored_text = apply_keyword_highlighting(
            segment['text'],
            emphasis_keywords,
            color_default="&H0000FFFF",  # Yellow
            color_emphasis="&HFF00FF"     # Magenta
        )

        dialogue = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{colored_text}"
        events.append(dialogue)

    # Write complete ASS file
    with open(output_path, 'w') as f:
        f.write(header)
        f.write("[Events]\n")
        for event in events:
            f.write(event + "\n")

    return output_path
```

### Per-Word Coloring: How It Works

**Input:**
```python
text = "La inteligencia artificial es fascinante"
keywords = ["artificial"]
```

**Processing:**
```python
def apply_keyword_highlighting(text, keywords, color_default, color_emphasis):
    words = text.split()
    colored_words = []

    for word in words:
        if word.lower() in keywords:
            # Wrap in color override tag
            colored = f"{{\\c&H{color_emphasis}&}}{word}{{\\c}}"
        else:
            colored = word
        colored_words.append(colored)

    return " ".join(colored_words)

# Output:
"La inteligencia {\c&HFF00FF&}artificial{\c} es fascinante"
```

**FFmpeg rendering:**
```
"La inteligencia" → Yellow
"artificial" → Magenta (emphasis)
"es fascinante" → Yellow (back to default)
```

### Files to Modify

| File | Change | Effort | Notes |
|------|--------|--------|-------|
| `src/subtitle_generator.py` | Add `generate_ass_from_transcript()` method | Medium | New method, keep SRT for backward compat |
| `src/subtitle_generator.py` | Add `apply_keyword_highlighting()` helper | Low | Pure string manipulation |
| `src/video_exporter.py` | Accept `.ass` files in addition to `.srt` | Low | Just pass filename to ffmpeg |
| `cliper.py` | Add keyword input for emphasis (optional) | Low | Future: `--emphasis-keywords "word1,word2"` |
| `models/subtitle_schemas.py` | Add `SubtitleConfig` with position + keywords | Low | Pydantic validation |
| `tests/test_ass_generation.py` | NEW - Validate ASS format, color tags | Medium | Comprehensive testing |

### Migration Path (Non-Breaking)

**Phase 1 (Now):**
- Add `generate_ass_from_transcript()` as new method
- Keep SRT generation (backward compatible)
- CLI can choose: "SRT only" vs "ASS with multicolor"

**Phase 2 (Future):**
- Make ASS default for all new clips
- Automatically convert old SRT files to ASS
- Deprecate SRT-only workflow

**Phase 3 (Later):**
- Remove SRT generation (if no users need it)

### Coloring Options: Flexibility Example

```python
# Basic: Single emphasis color (magenta for keywords)
generate_ass_from_transcript(
    transcript,
    output_path="clip.ass",
    subtitle_position="bottom",
    emphasis_keywords=["AICDMX", "inteligencia"]
)

# Advanced: Custom colors per keyword (future)
generate_ass_from_transcript(
    transcript,
    output_path="clip.ass",
    subtitle_position="middle",
    keyword_colors={
        "AICDMX": "&H00FF00",      # Green (hashtag)
        "inteligencia": "&HFF00FF",  # Magenta (key concept)
        "fascinante": "&H0000FF"     # Red (emotion)
    }
)
```

### Success Criteria (Phase 3b)

✅ ASS files generated correctly with ASS header + styling metadata
✅ Subtitle position baked into ASS (no ffmpeg filter needed)
✅ Per-word color highlighting works (keywords in different color)
✅ File size impact negligible (~2-3KB per clip)
✅ Export performance identical to SRT (zero overhead)
✅ Backward compatible: Old clips still work
✅ Tests validate ASS format syntax + color tag parsing

---

## Notes

**Related to PASO2 Enhancement:**
- Both features deal with multi-language support
- Both use language detection from transcripts
- Both could share translation infrastructure
- Consider bundling Phase 2 with PASO5 (publishing) for multi-market distribution

**Subtitle Improvements Summary:**
- Phase 1: Fix misleading English prompt (QUICK WIN)
- Phase 2: Cross-language subtitle translation (ADVANCED)
- Phase 3: Positioning redesign (CRITICAL for UX) ← NEW

**File Organization:**
If features are approved, create:
```
pasoxpaso/FEATURES-EN-PROGRESO/
├── subtitles-fix.md (this file - consolidated)
├── todoPHASE1/
│   └── 01-fix-prompt.md
├── todoPHASE2/
│   ├── 00-OVERVIEW.md
│   ├── 01-translation-service.md
│   ├── 02-timestamp-preservation.md
│   ├── 03-cli-integration.md
│   ├── 04-testing.md
│   └── ARCHITECTURE-ALIGNMENT.md
└── todoPHASE3/
    ├── 00-OVERVIEW.md
    ├── 01-positioning-logic.md
    ├── 02-font-sizing.md
    ├── 03-safe-zone-integration.md
    └── ARCHITECTURE-ALIGNMENT.md
```
