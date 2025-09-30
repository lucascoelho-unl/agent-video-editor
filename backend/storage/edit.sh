#!/bin/bash

# Check if at least one input file and one output file are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input1> [input2...] <output>"
    exit 1
fi

# All arguments except the last one are inputs
inputs=("${@:1:$#-1}")
# The last argument is the output
output="${!#}"

# Build ffmpeg command
cmd="ffmpeg"
filter_complex=""
concat_inputs=""

for i in "${!inputs[@]}"; do
    cmd+=" -i \"${inputs[$i]}\""
    filter_complex+="[$i:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v$i]; "
    concat_inputs+="[v$i][${i}:a]"
done

# Check if there's more than one input to concatenate
if [ "${#inputs[@]}" -gt 1 ]; then
    filter_complex+="${concat_inputs}concat=n=${#inputs[@]}:v=1:a=1[v][a]"
    cmd+=" -filter_complex \"$filter_complex\" -map \"[v]\" -map \"[a]\""
else
    # If only one input, just map it directly without concat
    cmd+=" -map 0:v -map 0:a"
fi

cmd+=" -c:v libx264 -crf 23 -preset veryfast -c:a aac -b:a 192k \"$output\""

# Execute the command
eval $cmd
