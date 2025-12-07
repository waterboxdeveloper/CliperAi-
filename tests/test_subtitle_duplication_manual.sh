#!/bin/bash
# Test manual para reproducir duplicación de subtítulos

# Archivos
VIDEO_ORIGINAL="downloads/Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream_LZlXASa8CZM.mp4"
SRT_FILE="output/Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream_LZlXASa8CZM/1.srt"
OUTPUT_TEST="output/test_subtitle_duplication.mp4"

echo "Generando video de prueba con MISMO comando que usa CLIPER..."
echo ""

# COMANDO EXACTO que genera CLIPER (según debug log)
ffmpeg -y \
  -ss 0.0 \
  -i "$VIDEO_ORIGINAL" \
  -t 10.0 \
  -vf "crop=ih*9/16:ih,scale=1080:1920,subtitles='$SRT_FILE':force_style='FontName=Arial,FontSize=10,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,Outline=1,Shadow=1,Bold=0,Alignment=6,MarginV=100'" \
  -c:v libx264 \
  -c:a aac \
  -preset fast \
  -crf 23 \
  "$OUTPUT_TEST"

echo ""
echo "Video generado: $OUTPUT_TEST"
echo "Ahora ejecuta: ffplay \"$OUTPUT_TEST\""
echo ""
echo "¿Los subtítulos se duplican en este video también?"
echo "Si SÍ se duplican: El problema está en el filtro FFmpeg"
echo "Si NO se duplican: El problema está en el código Python"
