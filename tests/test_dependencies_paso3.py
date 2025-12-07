#!/usr/bin/env python3
"""
Test: Verificar instalación de dependencias PASO3
Valida que OpenCV y MediaPipe estén correctamente instalados
"""

import sys

def test_opencv():
    try:
        import cv2
        print(f"✓ OpenCV installed: {cv2.__version__}")
        return True
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False

def test_mediapipe():
    try:
        import mediapipe as mp
        print(f"✓ MediaPipe installed: {mp.__version__}")

        # Test face detection model loading
        face_detection = mp.solutions.face_detection
        detector = face_detection.FaceDetection(min_detection_confidence=0.5)
        print("✓ MediaPipe face detection model loaded")
        detector.close()
        return True
    except ImportError as e:
        print(f"✗ MediaPipe import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ MediaPipe model loading failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing PASO3 dependencies...\n")

    opencv_ok = test_opencv()
    mediapipe_ok = test_mediapipe()

    print("\n" + "="*50)
    if opencv_ok and mediapipe_ok:
        print("✓ All dependencies working!")
        sys.exit(0)
    else:
        print("✗ Some dependencies failed")
        sys.exit(1)
