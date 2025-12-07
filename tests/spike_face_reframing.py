#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPIKE: Face Reframing Validation
Validates MediaPipe + frame sampling before production implementation

TEMPORAL - Este archivo se borrará después de validar resultados
"""

import cv2
import mediapipe as mp
import time
from pathlib import Path
from typing import Optional, Dict, List

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

        print(f"\nVideo: {Path(video_path).name}")
        print(f"Resolution: {width}x{height}, FPS: {fps:.1f}")
        print(f"Sampling: every {self.frame_sample_rate} frame(s)\n")

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
                    print(f"Progress: {progress:.1f}%", end='\r')

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
        print("ANALYSIS REPORT")
        print("="*60)
        for key, value in report.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        print("="*60 + "\n")

def main():
    # Find sample video
    downloads_dir = Path("downloads")
    videos = list(downloads_dir.glob("*.mp4"))

    if not videos:
        print("ERROR: No video found in downloads/ folder")
        print("Please add a video to test with")
        return

    video_path = videos[0]

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
