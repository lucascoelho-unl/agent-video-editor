#!/bin/bash

# Ensure we have exactly 10 arguments (9 inputs, 1 output)
if [ "$#" -ne 10 ]; then
  echo "Usage: $0 <input1> <input2> <input3> <input4> <input5> <input6> <input7> <input8> <input9> <output>"
  exit 1
fi

INPUT1="$1"
INPUT2="$2"
INPUT3="$3"
INPUT4="$4"
INPUT5="$5"
INPUT6="$6"
INPUT7="$7"
INPUT8="$8"
INPUT9="$9"
OUTPUT="${10}"

ffmpeg -i "$INPUT1" -i "$INPUT2" -i "$INPUT3" -i "$INPUT4" -i "$INPUT5" -i "$INPUT6" -i "$INPUT7" -i "$INPUT8" -i "$INPUT9" \
-filter_complex \
"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v0]; \
 [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v1]; \
 [2:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v2]; \
 [3:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v3]; \
 [4:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v4]; \
 [5:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v5]; \
 [6:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v6]; \
 [7:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v7]; \
 [8:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v8]; \
 [v0][0:a][v1][1:a][v2][2:a][v3][3:a][v4][4:a][v5][5:a][v6][6:a][v7][7:a][v8][8:a]concat=n=9:v=1:a=1[v][a]" \
-map "[v]" -map "[a]" \
-c:v libx264 -crf 23 -preset veryfast \
-c:a aac -b:a 192k \
"$OUTPUT"
