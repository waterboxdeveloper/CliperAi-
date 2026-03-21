# Paso 3 Implementation Overview

**Feature:** Intelligent Face Reframing with Detection
**Goal:** Dynamic vertical video framing that keeps the speaker in view professionally

---

## 📚 Implementation Steps

This folder contains detailed instructions for each implementation phase:

1. **`01-dependencies.md`** - Install and configure MediaPipe + OpenCV
2. **`02-spike-validation.md`** - Build proof-of-concept to validate approach
3. **`03-reframer-module.md`** - Create `src/reframer.py` with core logic
4. **`04-integration.md`** - Integrate reframer into `video_exporter.py`
5. **`05-cli-flags.md`** - Add CLI flags to `cliper.py`
6. **`06-testing.md`** - Test with real videos and validate quality
7. **`07-optimization.md`** - Performance tuning and polish

---

## 🎯 Key Design Decisions

Based on expert review (`ben-coments.md`), we're implementing:

✅ **Frame Sampling:** Process every 3rd frame (configurable)
✅ **Keep in Frame:** Minimal movement, only when needed (NOT constant centering)
✅ **Predictive Reframing:** 2-second lookahead for smooth anticipatory panning
✅ **Configurable Speed:** User control over movement speed and safe zones

---

## 📋 Implementation Phases

### Phase 1: Foundation (Steps 01-03)
- Set up dependencies
- Validate MediaPipe accuracy with spike
- Build core `reframer.py` module

### Phase 2: Integration (Steps 04-05)
- Connect reframer to video export pipeline
- Add CLI flags for user control

### Phase 3: Validation (Step 06)
- Test with multiple video types
- Compare quality vs static crop

### Phase 4: Optimization (Step 07)
- Performance benchmarks
- Fine-tune parameters
- Production hardening

---

## 🚦 Getting Started

**Read in order:**
1. Start with this overview
2. Follow steps 01 → 07 sequentially
3. Each file has detailed instructions and code examples
4. Mark checkboxes as you complete tasks

**Prerequisites:**
- CLIPER project setup and working
- Python 3.9+ environment with `uv`
- Sample video in `downloads/` folder

---

## 📖 Reference Documents

- `../paso3.md` - Original feature specification
- `../ben-coments.md` - Expert technical recommendations
- `../contextofull.md` - Project architecture and philosophy

---

**Ready?** Start with `01-dependencies.md` →
