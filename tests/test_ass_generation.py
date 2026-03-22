# -*- coding: utf-8 -*-
"""
Test ASS Subtitle Generation (Phase 3b)

Validates:
1. ASS file structure (header, styles, events)
2. Subtitle positioning (bottom, middle, very_high)
3. Keyword highlighting with color tags
4. Time format conversion (seconds → ASS format)
"""

import json
import tempfile
from pathlib import Path

from src.subtitle_generator import SubtitleGenerator


class TestASSGeneration:
    """Test ASS subtitle generation functionality."""

    @staticmethod
    def create_mock_transcript(clip_start=0.0, clip_end=5.0):
        """Create a simple mock WhisperX transcript for testing."""
        return {
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "La inteligencia artificial",
                    "words": [
                        {"word": "La", "start": 0.0, "end": 0.5},
                        {"word": "inteligencia", "start": 0.5, "end": 1.5},
                        {"word": "artificial", "start": 1.5, "end": 2.5}
                    ]
                },
                {
                    "start": 2.5,
                    "end": 5.0,
                    "text": "es fascinante #AICDMX",
                    "words": [
                        {"word": "es", "start": 2.5, "end": 3.0},
                        {"word": "fascinante", "start": 3.0, "end": 4.0},
                        {"word": "#AICDMX", "start": 4.0, "end": 5.0}
                    ]
                }
            ]
        }

    def test_ass_file_structure(self):
        """Test that ASS file has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock transcript
            transcript_path = Path(tmpdir) / "transcript.json"
            transcript = self.create_mock_transcript()

            with open(transcript_path, 'w') as f:
                json.dump(transcript, f)

            # Generate ASS
            generator = SubtitleGenerator()
            output_path = Path(tmpdir) / "test.ass"

            result = generator.generate_ass_for_clip(
                transcript_path=str(transcript_path),
                clip_start=0.0,
                clip_end=5.0,
                output_path=str(output_path),
                subtitle_position="bottom"
            )

            # Verify file was created
            assert result is not None
            assert output_path.exists()

            # Verify ASS structure
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check required sections
            assert "[Script Info]" in content, "Missing [Script Info] section"
            assert "[V4+ Styles]" in content, "Missing [V4+ Styles] section"
            assert "[Events]" in content, "Missing [Events] section"
            assert "Style: bottom" in content, "Missing bottom style definition"

            print("✓ ASS file structure is correct")

    def test_subtitle_positioning(self):
        """Test positioning for bottom, middle, very_high."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript_path = Path(tmpdir) / "transcript.json"
            transcript = self.create_mock_transcript()

            with open(transcript_path, 'w') as f:
                json.dump(transcript, f)

            generator = SubtitleGenerator()

            for position in ["bottom", "middle", "very_high"]:
                output_path = Path(tmpdir) / f"test_{position}.ass"

                result = generator.generate_ass_for_clip(
                    transcript_path=str(transcript_path),
                    clip_start=0.0,
                    clip_end=5.0,
                    output_path=str(output_path),
                    subtitle_position=position
                )

                assert result is not None
                assert output_path.exists()

                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                assert f"Style: {position}" in content, f"Missing {position} style"

            print("✓ All 3 positioning options generate correctly")

    def test_keyword_highlighting(self):
        """Test keyword highlighting with color override tags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript_path = Path(tmpdir) / "transcript.json"
            transcript = self.create_mock_transcript()

            with open(transcript_path, 'w') as f:
                json.dump(transcript, f)

            generator = SubtitleGenerator()
            output_path = Path(tmpdir) / "test_keywords.ass"

            # Generate with keyword emphasis
            result = generator.generate_ass_for_clip(
                transcript_path=str(transcript_path),
                clip_start=0.0,
                clip_end=5.0,
                output_path=str(output_path),
                subtitle_position="bottom",
                emphasis_keywords=["artificial", "AICDMX"]
            )

            assert result is not None

            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for color override tags
            # Format: {\c&HBBGGRR&}text{\c}
            assert r"{\c&HFF00FF&}" in content, "Missing color override tag for emphasized word"

            print("✓ Keyword highlighting with color tags works")

    def test_ass_time_format(self):
        """Test seconds to ASS time format conversion."""
        generator = SubtitleGenerator()

        test_cases = [
            (0.0, "0:00:00.00"),
            (1.5, "0:00:01.50"),
            (61.25, "0:01:01.25"),
            (3665.99, "1:01:05.99"),
        ]

        for seconds, expected_time in test_cases:
            result = generator._seconds_to_ass_time(seconds)
            assert result == expected_time, f"Time format mismatch: {result} != {expected_time}"

        print("✓ ASS time format conversion is correct")

    def test_dialogue_event_format(self):
        """Test ASS Dialogue event formatting."""
        generator = SubtitleGenerator()

        event = generator._format_ass_event(
            index=1,
            start_time=0.0,
            end_time=2.5,
            style_name="bottom",
            text=r"La {\c&HFF00FF&}inteligencia{\c} artificial"
        )

        # Verify format
        assert "Dialogue:" in event
        assert "0:00:00.00" in event
        assert "0:00:02.50" in event
        assert "bottom" in event
        assert r"{\c&HFF00FF&}inteligencia{\c}" in event

        print("✓ Dialogue event format is correct")


if __name__ == "__main__":
    test = TestASSGeneration()

    print("\nRunning ASS Generation Tests\n" + "=" * 50)

    test.test_ass_file_structure()
    test.test_subtitle_positioning()
    test.test_keyword_highlighting()
    test.test_ass_time_format()
    test.test_dialogue_event_format()

    print("\n" + "=" * 50)
    print("✅ All ASS generation tests passed!")
