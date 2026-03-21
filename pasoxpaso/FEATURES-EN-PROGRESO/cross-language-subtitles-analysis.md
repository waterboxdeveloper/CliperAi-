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
- English video → Spanish subtitles (accessibility)
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

## Notes

**Related to PASO2 Enhancement:**
- Both features deal with multi-language support
- Both use language detection from transcripts
- Both could share translation infrastructure
- Consider bundling Phase 2 with PASO5 (publishing) for multi-market distribution

**File Organization:**
If Phase 2 is approved, create:
```
pasoxpaso/FEATURES-EN-PROGRESO/
├── cross-language-subtitles-analysis.md (this file)
└── todoCROSS-LANGUAGE-SUBTITLES/
    ├── 00-OVERVIEW.md
    ├── 01-translation-service.md
    ├── 02-timestamp-preservation.md
    ├── 03-cli-integration.md
    ├── 04-testing.md
    └── ARCHITECTURE-ALIGNMENT.md
```
