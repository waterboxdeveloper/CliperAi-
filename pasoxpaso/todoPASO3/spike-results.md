# Spike Validation Results

**Date:** November 26, 2024
**Video Tested:** Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream
**Duration Analyzed:** 10 seconds (300 frames)
**Hardware:** Apple M4 (Metal GPU acceleration)

---

## Performance Results

### Frame Sampling Rate: Every 1 Frame (Baseline)
- Detection time: 3.25ms average
- Effective FPS: 30.0 fps
- Face presence: 100.0%
- Avg movement: 4.3 px
- **Analysis:** Maximum quality, super stable tracking. Detection is instantaneous.

### Frame Sampling Rate: Every 3 Frames (Recommended)
- Detection time: 3.31ms average
- Effective FPS: 10.0 fps
- Face presence: 100.0%
- Avg movement: 11.0 px
- **Analysis:** 3x faster processing, still 100% detection. Movement acceptable with smoothing.

### Frame Sampling Rate: Every 5 Frames (Aggressive)
- Detection time: 3.28ms average
- Effective FPS: 6.0 fps
- Face presence: 100.0%
- Avg movement: 17.4 px
- **Analysis:** 5x faster but movement becomes noticeable. Too jittery for professional look.

---

## Conclusions

### 1. MediaPipe Accuracy: EXCELLENT
- 100% face detection rate across all sampling rates
- Never lost track of speaker
- Model confidence consistently high
- **Verdict:** Perfect choice for talking-head content

### 2. Recommended Sampling: Every 3 frames
- Validated Ben's recommendation with real data
- 3x performance improvement over baseline
- Movement (11px) is manageable with smoothing
- **Verdict:** Optimal balance of speed vs quality

### 3. Smoothing Needed: YES
- 11px average movement is perceptible without smoothing
- Will implement moving average filter in Step 07
- Predictive reframing will further improve smoothness
- **Verdict:** Critical for professional-looking output

### 4. Ready for Production: YES
- MediaPipe proven reliable on actual CLIPER content
- Performance exceeds requirements (3.3ms << 33ms budget at 30fps)
- Clear path forward with validated architecture
- **Verdict:** Proceed to Step 03 (production implementation)

---

## Architectural Insights

### Detection Speed Analysis
**DECISION:** Detection time (~3.3ms) is NOT the bottleneck
**IMPLICATION:** Frame sampling optimizes for total processing, not detection speed
**RESULT:** Can afford high-quality model (model_selection=1) without performance penalty

### Movement Pattern Analysis
**OBSERVATION:** Movement scales linearly with sampling rate (4.3 → 11.0 → 17.4 px)
**IMPLICATION:** Faces move gradually, not erratically
**RESULT:** Simple smoothing algorithms (moving average) will work well

### Face Presence Analysis
**OBSERVATION:** 100% detection on talking-head content
**IMPLICATION:** Fallback logic (center crop when no face) rarely needed
**RESULT:** Can optimize for happy path, simple fallback

---

## Hardware Notes

**Apple M4 Performance:**
- Metal GPU acceleration active
- TensorFlow Lite XNNPACK delegate enabled
- GL version: 2.1 Metal
- **Impact:** Face detection is essentially free (3.3ms)

**For Production:**
- Same performance expected on Apple Silicon
- Linux/Docker will be slower (CPU-only) but still acceptable
- May need to adjust frame_sample_rate on slower hardware

---

## Next Steps

1. **Step 03:** Implement `src/reframer.py` with validated architecture
2. **Step 04:** Integrate into `video_exporter.py`
3. **Step 07:** Add smoothing (moving average over 10 frames)
4. **Future:** Consider predictive reframing (2-second lookahead)

---

## Validation Checklist

- [x] Spike runs successfully
- [x] Tested with actual CLIPER video (talking-head livestream)
- [x] Face detection reliable (100% presence)
- [x] Frame sampling at 3x validated (optimal)
- [x] Results documented
- [x] Ready for production implementation

**Status:** VALIDATED - Proceed to Step 03
