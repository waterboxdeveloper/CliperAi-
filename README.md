# CLIPER 🎬

**Transform long videos into viral clips automatically**



---

## 🚀 What is CLIPER?

CLIPER is a CLI tool that automatically converts long YouTube videos into short, engaging clips perfect for TikTok, Instagram Reels, and YouTube Shorts. It uses AI to intelligently detect the best moments to cut.

###  Features

- ** Smart Download**: Download videos from YouTube with quality options
- *+ AI Transcription**: Convert audio to text with precise timestamps using WhisperX
- ** Intelligent Clipping**: Detect optimal cut points using ClipsAI's TextTiling algorithm
- ** Social Media Ready**: Export clips in 9:16 format with subtitles
- ** Fast & Efficient**: Optimized for Apple Silicon (M1/M2/M3/M4)
- ** Resume Capability**: Continue where you left off if interrupted
- ** Beautiful CLI**: Professional interface with Rich library

---

## 🛠️ Installation

### Prerequisites

- **Python 3.9+** (required by WhisperX)
- **FFmpeg** (for video processing)
- **macOS/Linux** (tested on macOS, should work on Linux)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/opino-tech/cliper.git
cd cliper

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### System Dependencies

```bash
# macOS (with Homebrew)
brew install ffmpeg libmagic

# Ubuntu/Debian
sudo apt-get install ffmpeg libmagic1
```

---

## 🎯 Quick Start

```bash
# Run CLIPER
uv run cliper.py

# Or activate virtual environment first
source .venv/bin/activate
python cliper.py
```

### Basic Workflow

1. **Download**: Provide a YouTube URL
2. **Transcribe**: AI converts audio to text with timestamps
3. **Generate Clips**: AI detects optimal cut points
4. **Export**: Create final clips in 9:16 format with subtitles

---

##  Usage Examples

### Download and Process a Video

```bash
# Start CLIPER
uv run cliper.py

# Choose option 1: Download new video
# Enter YouTube URL when prompted
# Select transcription settings (model size, language)
# Choose clip generation method (AI detection or fixed time)
# Export clips with subtitles
```

### Process Existing Video

```bash
# If you already have a video in downloads/
# Choose option 1: Process a video
# Select from available videos
# Continue from where you left off
```

---

##  Configuration

### Content Presets

CLIPER includes smart presets for different content types:

- **Livestream**: Optimized for long-form content with minimal topic changes
- **Podcast**: Perfect for multi-speaker content with topic transitions
- **Tutorial**: Ideal for structured educational content

### Environment Variables

Create a `.env` file for advanced configuration:

```env
# Optional: HuggingFace token for future features
HUGGINGFACE_TOKEN=hf_xxxxx

# Output directory
OUTPUT_DIR=./output

# Whisper model size
WHISPER_MODEL=base

# Clip duration limits
MIN_CLIP_DURATION=30
MAX_CLIP_DURATION=90
```

---

##  Architecture

```
URL → Download → Transcribe → Detect Clips → Export → Output
```

### Core Modules

- **`downloader.py`**: YouTube video download with yt-dlp
- **`transcriber.py`**: Audio-to-text conversion with WhisperX
- **`clips_generator.py`**: AI-powered clip detection with ClipsAI
- **`video_exporter.py`**: Video cutting and resizing
- **`subtitle_generator.py`**: Subtitle generation and embedding

### Data Flow

```
downloads/           # Original videos
├── video.mp4

temp/                # Intermediate files
├── video_transcript.json
├── video_clips.json
└── video_audio.wav

output/              # Final clips
└── video/
    ├── clip_001_9x16_subs.mp4
    ├── clip_001.srt
    └── ...
```

---

##  How It Works

### 1. Transcription (WhisperX)
- Extracts audio from video
- Converts speech to text with word-level timestamps
- Supports multiple languages with auto-detection
- Optimized for Apple Silicon performance

### 2. Clip Detection (ClipsAI)
- Analyzes transcript using TextTiling algorithm
- Detects topic changes using BERT embeddings
- Falls back to fixed-time cuts for homogeneous content
- Configurable duration limits (30-90 seconds)

### 3. Export (FFmpeg)
- Cuts video segments at detected timestamps
- Resizes to 9:16 aspect ratio for social media
- Generates and embeds subtitles
- Maintains high quality with optimized encoding

---

##  Performance

**Tested on:** MacBook Pro M4, 99-minute livestream

```
Download:     3 minutes
Transcription: 25 minutes (medium model, CPU)
Clip Detection: 4 seconds
Export:       8 minutes (14 clips)
Total:        ~36 minutes

Output:
- 1,083 transcribed segments
- 52,691 characters
- 14 clips of 90s each
- Complete coverage of 99 minutes
```

**Bottleneck:** Transcription (70% of total time)

---

##  Advanced Usage

### Custom Clip Generation

```python
from src.clips_generator import ClipsGenerator

generator = ClipsGenerator(
    min_clip_duration=60,
    max_clip_duration=120
)

clips = generator.generate_clips(
    transcript_path="temp/video_transcript.json",
    min_clips=5,
    max_clips=20
)
```

### Direct Transcription

```python
from src.transcriber import Transcriber

transcriber = Transcriber(model_size="base")
transcript_path = transcriber.transcribe(
    video_path="downloads/video.mp4",
    language="es"
)
```

---

##  Troubleshooting

### Common Issues

**"No clips found"**
- Video may be too short or have no topic changes
- Try increasing `max_clip_duration`
- Use "fixed time" method as fallback

**"Transcription failed"**
- Check if FFmpeg is installed
- Verify video has audio track
- Try smaller Whisper model (`tiny`)

**"Import error"**
- Run from project root: `uv run cliper.py`
- Ensure virtual environment is activated
- Check all dependencies are installed

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uv run cliper.py
```
### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black src/
uv run isort src/
```

---

##  License

This project is licensed under the MIT License - 

---

## 🙏 Acknowledgments

- **WhisperX**: For precise audio transcription
- **ClipsAI**: For intelligent clip detection
- **Rich**: For beautiful CLI interface
- **yt-dlp**: For robust YouTube downloading
- **FFmpeg**: For video processing

---
</div>
