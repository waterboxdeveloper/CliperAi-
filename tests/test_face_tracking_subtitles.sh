#!/bin/bash
# Test para simular comando con face tracking (2 inputs + mapeo)

VIDEO_REFRAMED="output/Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream_LZlXASa8CZM/1_reframed_temp.mp4"
VIDEO_ORIGINAL="downloads/Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream_LZlXASa8CZM.mp4"
SRT_FILE="output/Storycraft in the Age of AI, Danny Headspace - AI CDMX Live Stream_LZlXASa8CZM/1.srt"
OUTPUT_TEST="output/test_face_tracking_subs.mp4"

# Primero necesitamos crear un video reframed temporal de prueba
# (sin face tracking, solo crop estático a 9:16)
echo "Paso 1: Crear video temporal 9:16 (simula reframed)..."
ffmpeg -y -ss 0.0 -i "$VIDEO_ORIGINAL" -t 10.0 \
  -vf "crop=ih*9/16:ih,scale=1080:1920" \
  -c:v libx264 -preset fast -crf 23 \
  -an \
  "output/temp_fake_reframed.mp4"

echo ""
echo "Paso 2: Aplicar MISMO comando que con face tracking..."
echo "  (2 inputs: video sin audio + video original con audio)"
echo ""

# COMANDO EXACTO que usa CLIPER con face tracking
ffmpeg -y \
  -i "output/temp_fake_reframed.mp4" \
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
  "$OUTPUT_TEST"

# Cleanup temporal
rm "output/temp_fake_reframed.mp4"

echo ""
echo "Video generado: $OUTPUT_TEST"
echo ""
echo "Ejecuta: ffplay \"$OUTPUT_TEST\""
echo ""
echo "¿Los subtítulos se duplican ahora?"
echo "Si SÍ: El problema está en el comando con 2 inputs + mapeo"
echo "Si NO: El problema está en el video reframed que genera FaceReframer"
