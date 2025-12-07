# Step 07: Optimization & Polish

**Goal:** Performance tuning, predictive reframing, and production hardening

---

## 📋 Optimization Areas

Based on testing results from Step 06, we'll optimize:

1. ✅ **Smoothing:** Reduce jitter with moving average filter
2. ✅ **Predictive Reframing:** Implement 2-second lookahead (Ben's recommendation)
3. ✅ **Performance:** Optimize frame processing
4. ✅ **Configuration:** Fine-tune default parameters
5. ✅ **Polish:** Better logging, error messages, user feedback

---

## ✅ Tasks

### Task 7.1: Implement Position Smoothing

**Problem:** Even with "keep in frame" strategy, crop position can jump when reframing

**Solution:** Apply moving average filter to smooth crop positions over time

**File:** `/src/reframer.py`

**Add to `__init__` method:**

```python
def __init__(self, ...):
    # ... existing code ...

    # Smoothing window for crop positions
    self.smoothing_window_size = 10  # Average over last 10 position updates
    self.crop_position_history = deque(maxlen=self.smoothing_window_size)
```

**Create new method:**

```python
def _smooth_crop_position(self, new_crop_x: int) -> int:
    """
    Apply moving average smoothing to crop position

    Args:
        new_crop_x: Newly calculated crop X position

    Returns:
        Smoothed crop X position
    """
    self.crop_position_history.append(new_crop_x)

    # Return average of recent positions
    smoothed = int(sum(self.crop_position_history) / len(self.crop_position_history))
    return smoothed
```

**Update `_calculate_crop_keep_in_frame()` to use smoothing:**

```python
# At the end of the method, before returning:
crop_x = self._smooth_crop_position(crop_x)
return (crop_x, 0, crop_width, crop_height)
```

- [ ] Added position history deque to `__init__`
- [ ] Implemented `_smooth_crop_position()` method
- [ ] Integrated smoothing into crop calculation
- [ ] Tested: smoother camera movements

---

### Task 7.2: Implement Predictive Reframing (Advanced)

**This is Ben's 2-second lookahead recommendation!**

**Add to `__init__`:**

```python
def __init__(self, ...):
    # ... existing code ...

    # Predictive reframing
    self.enable_prediction = True  # Can be made configurable
    self.prediction_window_seconds = 2.0
    self.face_center_history = deque(maxlen=60)  # 2 seconds at 30fps
```

**Create prediction method:**

```python
def _predict_face_position(self, current_face_x: int, fps: float) -> Optional[int]:
    """
    Predict where the face will be in N seconds based on velocity

    Args:
        current_face_x: Current face center X position
        fps: Video frame rate

    Returns:
        Predicted X position, or None if not enough history
    """
    self.face_center_history.append(current_face_x)

    # Need at least 2 seconds of history for prediction
    required_samples = int(fps * self.prediction_window_seconds)

    if len(self.face_center_history) < required_samples:
        return None  # Not enough data yet

    # Calculate velocity (pixels per second)
    oldest_x = self.face_center_history[0]
    time_elapsed = self.prediction_window_seconds
    velocity = (current_face_x - oldest_x) / time_elapsed

    # Predict future position
    predicted_x = current_face_x + int(velocity * self.prediction_window_seconds)

    return predicted_x
```

**Update `_calculate_crop_keep_in_frame()` to use prediction:**

```python
def _calculate_crop_keep_in_frame(self, face, frame_width, frame_height, current_crop_x, fps=30):
    # ... existing code to calculate safe zones ...

    face_x = face['center_x']

    # Predictive reframing: check if face will exit safe zone soon
    if self.enable_prediction and current_crop_x is not None:
        predicted_x = self._predict_face_position(face_x, fps)

        if predicted_x is not None:
            # Check if predicted position will exit safe zone
            safe_left = current_crop_x + safe_margin
            safe_right = current_crop_x + crop_width - safe_margin

            if not (safe_left <= predicted_x <= safe_right):
                # Face WILL exit safe zone - start reframing NOW
                logger.debug(f"Predictive reframe triggered: predicted position {predicted_x}")

                # Calculate new position based on prediction
                if predicted_x < safe_left:
                    crop_x = predicted_x - safe_margin
                else:
                    crop_x = predicted_x - crop_width + safe_margin

                crop_x = max(0, min(crop_x, frame_width - crop_width))
                crop_x = self._smooth_crop_position(crop_x)
                return (crop_x, 0, crop_width, crop_height)

    # ... rest of existing logic for reactive reframing ...
```

**Note:** You'll need to pass `fps` parameter through the call chain.

- [ ] Added prediction history tracking
- [ ] Implemented velocity calculation
- [ ] Implemented predictive position calculation
- [ ] Integrated prediction into keep_in_frame logic
- [ ] Tested: camera anticipates movement smoothly

---

### Task 7.3: Add Maximum Pan Speed Limit

**Problem:** Large jumps in crop position can be jarring

**Solution:** Limit how fast the crop can move per frame

**Add to `__init__`:**

```python
def __init__(self, ...):
    # ... existing code ...

    # Movement speed limits (pixels per second)
    self.max_pan_speed_px_per_sec = 300  # Configurable
```

**Create method:**

```python
def _apply_pan_speed_limit(
    self,
    new_crop_x: int,
    previous_crop_x: int,
    fps: float
) -> int:
    """
    Limit crop movement speed to prevent jarring jumps

    Args:
        new_crop_x: Target crop position
        previous_crop_x: Current crop position
        fps: Video frame rate

    Returns:
        Crop position adjusted for speed limit
    """
    max_movement_per_frame = self.max_pan_speed_px_per_sec / fps

    delta = new_crop_x - previous_crop_x

    if abs(delta) > max_movement_per_frame:
        # Clamp movement to max speed
        if delta > 0:
            return previous_crop_x + int(max_movement_per_frame)
        else:
            return previous_crop_x - int(max_movement_per_frame)

    return new_crop_x
```

**Apply before smoothing:**

```python
crop_x = self._apply_pan_speed_limit(crop_x, current_crop_x, fps)
crop_x = self._smooth_crop_position(crop_x)
```

- [ ] Added max pan speed configuration
- [ ] Implemented speed limiting logic
- [ ] Integrated into crop calculation
- [ ] Tested: no jarring jumps

---

### Task 7.4: Optimize Frame Processing

**Current:** Every frame is read, even if not processed

**Optimization:** Skip reading frames we won't process

**File:** `/src/reframer.py` in `reframe_video()` method

**Current code:**
```python
while cap.isOpened() and frame_number < end_frame:
    ret, frame = cap.read()
    if not ret:
        break

    if frame_number % self.frame_sample_rate == 0:
        # Process frame
        ...
```

**Optimized:**
```python
while cap.isOpened() and frame_number < end_frame:
    # Skip frames we won't process (for detection)
    if frame_number % self.frame_sample_rate != 0:
        # Still need to read for output, but skip detection
        ret, frame = cap.read()
        if not ret:
            break
    else:
        ret, frame = cap.read()
        if not ret:
            break

        # Process this frame
        face = self._detect_largest_face(frame)
        ...
```

**Note:** This optimization is minor since we need to read all frames for output anyway. Main benefit is skipping face detection.

- [ ] Reviewed frame processing logic
- [ ] Verified frame sampling is working correctly
- [ ] Profiled if needed (consider using `cProfile`)

---

### Task 7.5: Fine-Tune Default Parameters

**Based on test results, adjust defaults:**

**File:** `/src/reframer.py`

**Review and adjust these values:**

```python
def __init__(
    self,
    frame_sample_rate: int = 3,        # Test showed 3 is optimal
    safe_zone_margin: float = 0.15,    # May need adjustment (0.10-0.20)
    detection_confidence: float = 0.5,  # Lower = more detections, higher = fewer false positives
    strategy: str = "keep_in_frame",
    max_pan_speed_px_per_sec: int = 300,  # Adjust based on testing
    smoothing_window_size: int = 10,       # Larger = smoother but less responsive
):
```

**Document recommendations in code:**

```python
"""
Default Parameters (Recommended):
- frame_sample_rate: 3 (good balance of speed/quality)
- safe_zone_margin: 0.15 (15% breathing room)
- detection_confidence: 0.5 (works for most videos)
- max_pan_speed: 300 px/sec (smooth but responsive)
- smoothing_window: 10 frames (eliminates jitter)

Adjust based on content type:
- Static interview: Increase safe_zone_margin to 0.20
- Energetic presentation: Reduce safe_zone_margin to 0.10
- Performance critical: Increase frame_sample_rate to 5
- Highest quality: Decrease frame_sample_rate to 1
"""
```

- [ ] Reviewed all default parameters
- [ ] Adjusted based on test results
- [ ] Documented parameter tuning guidelines
- [ ] Tested with new defaults

---

### Task 7.6: Improve Logging and Debug Info

**Add detailed logging for debugging:**

```python
def reframe_video(self, ...):
    # ... existing code ...

    logger.info(f"Reframing configuration:")
    logger.info(f"  Strategy: {self.strategy}")
    logger.info(f"  Frame sampling: 1/{self.frame_sample_rate}")
    logger.info(f"  Safe zone margin: {self.safe_zone_margin*100:.0f}%")
    logger.info(f"  Prediction: {'enabled' if self.enable_prediction else 'disabled'}")

    # ... during processing ...

    if face:
        logger.debug(f"Frame {frame_number}: Face at ({face['center_x']}, {face['center_y']}), crop_x={current_crop_x}")
    else:
        logger.debug(f"Frame {frame_number}: No face detected, using fallback")
```

**Add statistics at the end:**

```python
# After processing loop
face_detection_rate = (frames_with_faces / frames_processed) * 100
logger.info(f"Processing complete:")
logger.info(f"  Frames processed: {frames_processed}")
logger.info(f"  Face detection rate: {face_detection_rate:.1f}%")
logger.info(f"  Average crop position: {avg_crop_x:.0f}px")
```

- [ ] Added configuration logging
- [ ] Added debug logging during processing
- [ ] Added summary statistics
- [ ] Logs are helpful for troubleshooting

---

### Task 7.7: Add Progress Callback (Optional)

**For better UX, show face tracking progress:**

**Add callback support:**

```python
def reframe_video(
    self,
    ...,
    progress_callback: Optional[callable] = None
):
    """
    Args:
        progress_callback: Function(current, total) called with progress
    """

    # During processing:
    if progress_callback and frame_number % 10 == 0:
        progress_callback(frame_number - start_frame, end_frame - start_frame)
```

**Use in `video_exporter.py`:**

```python
def progress_update(current, total):
    pct = (current / total) * 100
    logger.info(f"Face tracking progress: {pct:.1f}%")

success = reframer.reframe_video(
    ...,
    progress_callback=progress_update
)
```

- [ ] Added progress callback support (optional)
- [ ] Integrated with video_exporter if implemented

---

## 🎯 Final Validation

### Performance Targets
- [ ] Processing speed: < 3x slower than static crop
- [ ] Face detection rate: > 80% for talking-head videos
- [ ] No memory leaks during long video processing
- [ ] Handles 1080p video smoothly

### Quality Targets
- [ ] Smooth camera movements (no jitter)
- [ ] Face stays in frame 99%+ of time
- [ ] Anticipatory movement looks natural
- [ ] Better results than static crop

### Production Readiness
- [ ] Error handling covers all edge cases
- [ ] Logging provides actionable debugging info
- [ ] Configuration parameters are well-documented
- [ ] Code follows project style guidelines
- [ ] Ready to merge into main branch

---

## 📊 Benchmark Results

**Document final performance:**

```markdown
# Optimization Results

## Before Optimization
- Processing speed: ___x slower than static
- Face stays in frame: ___%
- Jitter/jumpiness: [High/Medium/Low]

## After Optimization
- Processing speed: ___x slower than static
- Face stays in frame: ___%
- Jitter/jumpiness: [High/Medium/Low]
- Predictive reframing: [Enabled/Disabled]

## Improvements
- Speed improvement: ___%
- Quality improvement: [Subjective assessment]
- Ready for production: YES/NO
```

- [ ] Created optimization benchmark document

---

## 🎉 Completion Checklist

- [ ] All 7 steps completed
- [ ] Face tracking feature fully integrated
- [ ] Tested with real videos
- [ ] Performance is acceptable
- [ ] Quality is better than static crop
- [ ] Code is production-ready
- [ ] Documentation is complete

---

## 🚀 Future Enhancements

**Ideas for future iterations:**

1. **Multi-face tracking:** Track multiple faces, switch between speakers
2. **Scene detection:** Detect scene changes, reset tracking
3. **GPU acceleration:** Use GPU for MediaPipe for faster processing
4. **Pose estimation:** Track full body, not just face
5. **Custom training:** Train MediaPipe on specific face types
6. **Real-time preview:** Show tracking visualization
7. **Auto-tuning:** Automatically adjust parameters based on video analysis

---

**Congratulations! 🎉**

You've successfully implemented intelligent face reframing for CLIPER!

The feature is now ready for production use.
