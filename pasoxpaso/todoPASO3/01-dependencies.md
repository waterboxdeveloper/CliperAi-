# Step 01: Dependencies Setup

**Goal:** Install and configure OpenCV and MediaPipe

---

## 📦 Dependencies to Add

We need two new libraries:

1. **`opencv-python`** - Video frame manipulation
2. **`mediapipe`** - Face detection AI models

---

## ✅ Tasks

### Task 1.1: Update `pyproject.toml`

**File:** `/pyproject.toml`

**Action:** Add to the `dependencies` array:

```toml
dependencies = [
    "clipsai",
    "whisperx @ git+https://github.com/m-bain/whisperx.git",
    "yt-dlp",
    "python-dotenv",
    "loguru",
    "typer",
    "tqdm",
    "pydantic",
    "ffmpeg-python",
    "rich>=14.2.0",
    "faster-whisper>=1.2.0",
    "langchain-google-genai>=2.1.12",
    "langgraph>=0.6.11",
    # NEW: Face reframing dependencies
    "opencv-python>=4.8.0",
    "mediapipe>=0.10.0",
]
```

- [ ] Added `opencv-python>=4.8.0`
- [ ] Added `mediapipe>=0.10.0`
- [ ] Added comment explaining their purpose

---

### Task 1.2: Install Dependencies Locally

**Command:**
```bash
uv sync
```

**Expected Output:**
```
Resolved X packages in Xms
Installed 2 packages in Xms
  + opencv-python==4.8.x
  + mediapipe==0.10.x
```

- [ ] Ran `uv sync` successfully
- [ ] Verified both packages installed
- [ ] No dependency conflicts reported

---

### Task 1.3: Verify Installation

**Create test file:** `test_deps.py` (temporary, will delete)

```python
#!/usr/bin/env python3
"""Quick test to verify dependencies are working"""

import sys

def test_opencv():
    try:
        import cv2
        print(f"✅ OpenCV installed: {cv2.__version__}")
        return True
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False

def test_mediapipe():
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe installed: {mp.__version__}")

        # Test face detection model loading
        face_detection = mp.solutions.face_detection
        detector = face_detection.FaceDetection(min_detection_confidence=0.5)
        print("✅ MediaPipe face detection model loaded")
        detector.close()
        return True
    except ImportError as e:
        print(f"❌ MediaPipe import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ MediaPipe model loading failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing dependencies...\n")

    opencv_ok = test_opencv()
    mediapipe_ok = test_mediapipe()

    print("\n" + "="*50)
    if opencv_ok and mediapipe_ok:
        print("✅ All dependencies working!")
        sys.exit(0)
    else:
        print("❌ Some dependencies failed")
        sys.exit(1)
```

**Run test:**
```bash
uv run test_deps.py
```

- [ ] OpenCV imports successfully
- [ ] MediaPipe imports successfully
- [ ] MediaPipe face detection model loads
- [ ] Deleted `test_deps.py` after verification

---

### Task 1.4: Update Dockerfile (for Docker deployment)

**File:** `/Dockerfile`

**Action:** Add system dependencies for OpenCV

**Find this section:**
```dockerfile
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*
```

**Update to:**
```dockerfile
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    # OpenCV system dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
```

**Why:** OpenCV needs these system libraries for video processing in Docker.

- [ ] Added `libgl1-mesa-glx` to Dockerfile
- [ ] Added `libglib2.0-0` to Dockerfile
- [ ] Removed apt cache to keep image small

---

## 🎯 Validation Checklist

Before moving to Step 02:

- [ ] `pyproject.toml` updated with both dependencies
- [ ] `uv sync` ran without errors
- [ ] Test script confirmed both libraries work
- [ ] MediaPipe face detection model loads successfully
- [ ] `Dockerfile` updated with OpenCV system deps
- [ ] Cleaned up temporary test file

---

## 📝 Notes

**OpenCV version:** We're using `opencv-python` (not `opencv-python-headless`) because it's the full version with all video codecs.

**MediaPipe models:** MediaPipe downloads AI models on first use (~6MB). This happens automatically when you first create a `FaceDetection()` object.

**Docker:** If you rebuild the Docker image, the Python dependencies will be installed via `uv sync` in the container.

---

## ❓ Troubleshooting

**Problem:** `ImportError: libGL.so.1: cannot open shared object file`
**Solution:** Missing system dependencies in Docker. Make sure you added `libgl1-mesa-glx` to Dockerfile.

**Problem:** MediaPipe model download fails
**Solution:** Check internet connection. MediaPipe needs to download models on first run.

**Problem:** `uv sync` conflicts
**Solution:** Try `uv sync --refresh` to rebuild dependency resolution.

---

**Next Step:** `02-spike-validation.md` →
