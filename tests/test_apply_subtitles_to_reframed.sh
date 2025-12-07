#!/bin/bash
# Test para aplicar subtítulos al video reframed de prueba
# Replica exactamente el comando que usa video_exporter.py

SRT_FILE="output/Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream_LZlXASa8CZM/1.srt"
VIDEO_REFRAMED="output/debug_reframed_test.mp4"
VIDEO_ORIGINAL="downloads/Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream_LZlXASa8CZM.mp4"
OUTPUT="output/debug_with_subtitles.mp4"

echo "Aplicando subtítulos a video reframed de prueba..."
echo "Video reframed: $VIDEO_REFRAMED"
echo "SRT file: $SRT_FILE"
echo "Output: $OUTPUT"
echo ""

ffmpeg -y \
  -i "$VIDEO_REFRAMED" \
  -ss 0.0 \
  -i "$VIDEO_ORIGINAL" \
  -t 10.0 \
  -map 0:v \
  -map 1:a \
  -vf "subtitles='$SRT_FILE':force_style='FontName=Arial,FontSize=10,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,Outline=1,Shadow=1,Bold=0,Alignment=6,MarginV=100'" \
  -c:v libx264 \
  -c:a aac \
  -preset fast \
  -crf 23 \
  "$OUTPUT"

echo ""
echo "Video generado: $OUTPUT"
echo ""
echo "Para verificar duplicación:"
echo "  ffplay \"$OUTPUT\""
echo ""
echo "Para ver streams:"
echo "  ffprobe \"$OUTPUT\" -show_streams"
