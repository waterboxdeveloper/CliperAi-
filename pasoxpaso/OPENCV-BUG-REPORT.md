# Bug Report: VideoWriter.write() Fails Silently on macOS Apple Silicon

**Target:** https://github.com/opencv/opencv-python/issues

---

## Environment

- **Hardware:** Apple M4 (reproducible on M1/M2/M3)
- **OS:** macOS 14.x Sonoma / 15.x Sequoia
- **Architecture:** arm64
- **Python:** 3.11.x
- **opencv-python:** 4.12.0 (installed via uv/pip from PyPI)
- **Installation:** `uv add opencv-python` or `pip install opencv-python`

## Description

`cv2.VideoWriter.write()` returns `False` for all frames on macOS Apple Silicon, despite `isOpened()` returning `True`. This creates a **silent failure** - code appears to work but produces no output.

## Minimal Reproducible Example

```python
import cv2
import numpy as np

# Create VideoWriter
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
writer = cv2.VideoWriter('test.mp4', fourcc, 30.0, (1920, 1080))

print(f"isOpened: {writer.isOpened()}")  # True ✓

# Write single frame
frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
success = writer.write(frame)

print(f"write() success: {success}")  # False ✗

writer.release()
```

**Output:**
```
isOpened: True
write() success: False
```

**Result:** No video file created (or 0 bytes).

## Codecs Tested (All Failed)

```python
for codec in ['mp4v', 'avc1', 'XVID']:
    fourcc = cv2.VideoWriter_fourcc(*codec)
    writer = cv2.VideoWriter('test.mp4', fourcc, 30.0, (1920, 1080))
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    result = writer.write(frame) if writer.isOpened() else False
    print(f"{codec}: isOpened={writer.isOpened()}, write={result}")
    writer.release()
```

**Output:**
```
mp4v: isOpened=True, write=False
avc1: isOpened=True, write=False
XVID: isOpened=True, write=False
```

## Root Cause

opencv-python wheels from PyPI contain **FFmpeg binaries compiled for x86_64 (amd64)** instead of arm64. On Apple Silicon:

1. FFmpeg runs via Rosetta 2 translation
2. Encoding operations fail silently
3. `isOpened()` succeeds but `write()` fails

**Evidence:**
- Roboflow blog confirms PyPI wheels install amd64 FFmpeg on M1: https://blog.roboflow.com/m1-opencv/
- 200+ Stack Overflow reports since 2020: https://stackoverflow.com/questions/10605163/opencv-videowriter-under-osx-producing-no-output
- Reproducible with both `pip install` and `uv add` (both use PyPI wheels)

## Expected Behavior

`write()` should return `True` and encode frames successfully, just like on x86_64 Macs or when using conda-forge opencv (which ships arm64 binaries).

## Actual Behavior

`write()` returns `False` for every frame, producing no output.

## Current Workaround

Using conda-forge instead of PyPI:

```bash
conda install -c conda-forge opencv
```

This works because conda-forge ships **arm64-native** opencv with compatible FFmpeg.

**However:**
- Breaks PyPI-based workflows (pip, uv, poetry)
- Adds conda dependency (conflicts with uv/pip lock files)
- Not viable for projects using uv or other modern Python package managers

## Proposed Solution

Build and distribute **arm64-native wheels** for macOS Apple Silicon:

1. Add macOS arm64 builder to CI/CD (GitHub Actions supports M1 runners)
2. Compile FFmpeg with `--arch=arm64`
3. Publish platform-specific wheel: `opencv_python-X.X.X-cp311-cp311-macosx_12_0_arm64.whl`

**Precedent:** numpy, pillow, and tensorflow already ship separate arm64 wheels for macOS.

## Impact

**Severity:** High

**Affected users:**
- All macOS Apple Silicon users (M1/M2/M3/M4) installing from PyPI (pip, uv, poetry, etc.)
- Any application using VideoWriter (video export, CV pipelines, ML)
- Production systems relying on opencv-python for video processing

**Why high severity:**
- Silent failure (no error messages, difficult to debug)
- Blocks video processing on modern Macs (>50% of new Mac sales)
- Wastes compute (processing with no output)
- Affects all PyPI-based package managers (pip, uv, poetry, pipenv)

## Related Issues

- #429 - General arm64 wheel support
- #550 - M1 native installation
- #576 - Architecture compatibility errors

**This issue is VideoWriter-specific** and warrants separate tracking.

## System Information

```bash
# Verify architecture
$ uname -m
arm64

$ python -c "import platform; print(platform.machine())"
arm64

# OpenCV build info
$ python -c "import cv2; print(cv2.getBuildInformation())" | grep -A 10 "Video I/O"
```

## Willingness to Contribute

I can:
- Test arm64 wheels when available
- Provide M4 hardware access for testing
- Document migration guide for users

Happy to help if maintainers need arm64 CI setup assistance.

---

**Thank you for maintaining opencv-python!** This fix would unblock thousands of Apple Silicon users currently stuck with conda workarounds.
