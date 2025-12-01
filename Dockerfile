# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by FFmpeg, WhisperX, and OpenCV
# FFmpeg is crucial for video processing
# libmagic1 is needed by some Python packages (e.g., python-magic)
# libgl1-mesa-glx and libglib2.0-0 are required by OpenCV for video I/O
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libmagic1 \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first
COPY pyproject.toml ./

# Install Python dependencies using uv
# uv is recommended for its speed and lock file management
# Run uv sync inside the container to generate uv.lock and install dependencies
RUN pip install uv && \
    uv sync

# Copy the rest of your application code
COPY . .

# Expose any ports if your application had a web interface (not applicable for CLI)
# EXPOSE 8000

# Define the command to run your application
# This will be the default command when the container starts
CMD ["uv", "run", "cliper.py"]
