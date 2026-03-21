# Step 02: Spike Validation

**Goal:** Build a proof-of-concept to validate MediaPipe accuracy and frame sampling performance

---

## 📋 What is a Spike?

A **spike** is a quick experiment to validate technical assumptions **before** building production code.

**We're testing:**
1. ✅ MediaPipe face detection accuracy on our video content
2. ✅ Frame sampling performance (every 1 vs 3 vs 5 frames)
3. ✅ "Keep in frame" logic feasibility
4. ✅ Tracking quality over time

**This is NOT production code** - it's a learning tool!

---

## ✅ Tasks

### Task 2.1: Create Spike Script

**File:** `/spike_face_reframing.py` (root of project)

**Purpose:** Standalone script to test face detection without touching CLIPER code.

**Key Features:**
- Test MediaPipe face detection on real video
- Compare different frame sampling rates (1, 3, 5)
- Measure performance (detection time, FPS)
- Generate analysis report

**Instructions:**
See the full spike script code in the appendix below.

- [ ] Created `spike_face_reframing.py` in project root
- [ ] Script includes frame sampling logic
- [ ] Script includes performance measurement
- [ ] Script generates analysis report

---

### Task 2.2: Run Spike with Sample Video

**Command:**
```bash
uv run spike_face_reframing.py
```

**Expected behavior:**
- Finds video in `downloads/` folder
- Tests 3 different frame sampling rates
- Shows progress during processing
- Prints detailed analysis report for each test

**Watch for:**
- Face detection rate (should be >80% for talking-head videos)
- Average detection time (should be <33ms for real-time at 30fps)
- Crop movement stability (smoother = better)

- [ ] Ran spike successfully
- [ ] Reviewed performance metrics
- [ ] Face detection accuracy acceptable (>70%)
- [ ] Frame sampling at 3x shows good performance

---

### Task 2.3: Analyze Results

**Questions to answer:**

1. **Is MediaPipe accurate enough?**
   - Does it detect the speaker's face consistently?
   - How often does it fail (no detection)?
   - Does it handle multiple people correctly (picks largest face)?

2. **What's the optimal frame sampling rate?**
   - Every 1 frame: Best quality, slowest
   - Every 3 frames: Recommended balance
   - Every 5 frames: Fastest, but jittery?

3. **How much does the crop move?**
   - Large movements = need smoothing
   - Small movements = tracking is stable

**Record your findings:**

```
Face Detection Accuracy: ____%
Recommended Frame Sample Rate: ___
Average Crop Movement: ___ pixels
Performance: ___ fps at recommended sampling
```

- [ ] Analyzed face detection accuracy
- [ ] Chose optimal frame sampling rate
- [ ] Noted crop movement patterns
- [ ] Recorded performance metrics

---

### Task 2.4: Document Findings

**File:** `/pasoxpaso/todoPASO3/spike-results.md` (create new file)

**Template:**
```markdown
# Spike Validation Results

**Date:** [Date]
**Video Tested:** [Video filename]
**Duration Analyzed:** 10 seconds

## Performance Results

### Frame Sampling Rate: Every 1 Frame
- Detection FPS: ___ fps
- Face presence: ___%
- Avg movement: ___ px

### Frame Sampling Rate: Every 3 Frames (Recommended)
- Detection FPS: ___ fps
- Face presence: ___%
- Avg movement: ___ px

### Frame Sampling Rate: Every 5 Frames
- Detection FPS: ___ fps
- Face presence: ___%
- Avg movement: ___ px

## Conclusions

1. **MediaPipe Accuracy:** [Good/Needs improvement]
2. **Recommended Sampling:** Every ___ frames
3. **Smoothing Needed:** [Yes/No - based on movement]
4. **Ready for Production:** [Yes/No]

## Observations

[Any notable findings, edge cases, or issues discovered]
```

- [ ] Created `spike-results.md`
- [ ] Filled in performance data
- [ ] Documented conclusions
- [ ] Noted any issues or edge cases

---

## 🎯 Validation Checklist

Before moving to Step 03:

- [ ] Spike script runs successfully
- [ ] Tested with actual CLIPER video content
- [ ] Face detection works reliably (>70% presence)
- [ ] Frame sampling at 3x provides good performance
- [ ] Results documented in `spike-results.md`
- [ ] Ready to proceed with production implementation

---

## 📝 Spike Script Code

<details>
<summary>Click to expand full spike code</summary>

**File:** `spike_face_reframing.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPIKE: Face Reframing Validation
Validates MediaPipe + frame sampling before production implementation
"""

import cv2
import mediapipe as mp
import time
from pathlib import Path
from typing import Optional, Dict, List
from collections import deque

class FaceReframingSpike:
    def __init__(self, frame_sample_rate: int = 3):
        self.frame_sample_rate = frame_sample_rate

        # MediaPipe face detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=1,  # Full-range model
            min_detection_confidence=0.5
        )

        self.stats = {
            'frames_processed': 0,
            'frames_with_faces': 0,
            'detection_time_ms': [],
        }

    def detect_largest_face(self, frame) -> Optional[Dict]:
        """Detect largest face using MediaPipe"""
        start_time = time.time()

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(frame_rgb)

        detection_time = (time.time() - start_time) * 1000
        self.stats['detection_time_ms'].append(detection_time)

        if not results.detections:
            return None

        # Find largest face
        h, w, _ = frame.shape
        largest_face = None
        max_area = 0

        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            area = width * height

            if area > max_area:
                max_area = area
                largest_face = {
                    'x': x, 'y': y, 'width': width, 'height': height,
                    'center_x': x + width // 2,
                    'center_y': y + height // 2,
                }

        return largest_face

    def analyze_video(self, video_path: str, max_frames: int = 300):
        """Analyze video and collect stats"""
        cap = cv2.VideoCapture(str(video_path))

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"\n📹 Video: {Path(video_path).name}")
        print(f"   Resolution: {width}x{height}, FPS: {fps:.1f}")
        print(f"   Sampling: every {self.frame_sample_rate} frame(s)\n")

        frame_number = 0
        detections = []

        while cap.isOpened() and frame_number < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % self.frame_sample_rate == 0:
                self.stats['frames_processed'] += 1
                face = self.detect_largest_face(frame)

                if face:
                    self.stats['frames_with_faces'] += 1
                    detections.append(face)

                if self.stats['frames_processed'] % 30 == 0:
                    progress = (frame_number / max_frames) * 100
                    print(f"   Progress: {progress:.1f}%", end='\r')

            frame_number += 1

        cap.release()
        print("\n")
        return self._generate_report(detections, fps)

    def _generate_report(self, detections: List[Dict], fps: float):
        """Generate performance report"""
        if not self.stats['detection_time_ms']:
            return {'error': 'No frames processed'}

        avg_time = sum(self.stats['detection_time_ms']) / len(self.stats['detection_time_ms'])
        frames_processed = self.stats['frames_processed']
        frames_with_faces = self.stats['frames_with_faces']
        face_rate = (frames_with_faces / frames_processed * 100) if frames_processed > 0 else 0

        # Movement analysis
        if len(detections) > 1:
            movements = [abs(detections[i+1]['center_x'] - detections[i]['center_x'])
                        for i in range(len(detections)-1)]
            avg_movement = sum(movements) / len(movements)
        else:
            avg_movement = 0

        return {
            'avg_detection_ms': round(avg_time, 2),
            'effective_fps': round(fps / self.frame_sample_rate, 2),
            'frames_processed': frames_processed,
            'face_presence_rate': f"{face_rate:.1f}%",
            'avg_movement_px': round(avg_movement, 1),
        }

    def print_report(self, report: Dict):
        """Print analysis report"""
        print("="*60)
        print("📊 ANALYSIS REPORT")
        print("="*60)
        for key, value in report.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        print("="*60 + "\n")

def main():
    # Find sample video
    video_path = list(Path("downloads").glob("*.mp4"))[0]

    print("SPIKE: MediaPipe Face Detection Validation")
    print("="*60)

    for sample_rate in [1, 3, 5]:
        print(f"\nTesting: Every {sample_rate} frame(s)")
        spike = FaceReframingSpike(frame_sample_rate=sample_rate)
        report = spike.analyze_video(str(video_path), max_frames=300)
        spike.print_report(report)
        time.sleep(1)

if __name__ == "__main__":
    main()
```
</details>

---

## ❓ Troubleshooting

**Problem:** Spike script crashes with import errors
**Solution:** Make sure you completed Step 01 (dependencies)

**Problem:** No video found
**Solution:** Ensure a `.mp4` file exists in `downloads/` folder

**Problem:** Very low face detection rate (<50%)
**Solution:** Check video content - is there a visible face? Try adjusting `min_detection_confidence`

---

**Next Step:** `03-reframer-module.md` →
