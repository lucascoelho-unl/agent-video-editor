#!/bin/bash

# Ensure we have exactly 4 arguments (3 inputs, 1 output)
if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <input1> <input2> <input3> <output>"
  exit 1
fi

INPUT1="$1"
INPUT2="$2"
INPUT3="$3"
OUTPUT="$4"

ffmpeg -i "$INPUT1" -i "$INPUT2" -i "$INPUT3" \
-filter_complex \
"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v0]; \
 [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v1]; \
 [2:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v2]; \
 [v0][0:a][v1][1:a][v2][2:a]concat=n=3:v=1:a=1[v][a]" \
-map "[v]" -map "[a]" \
-c:v libx264 -crf 23 -preset veryfast \
-c:a aac -b:a 192k \
"$OUTPUT"
