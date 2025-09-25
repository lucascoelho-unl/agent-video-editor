#!/bin/bash

# The script merges multiple video files into one.
# It takes all the input files as arguments, with the last argument being the output file.

# Get all arguments except the last one
inputs=("${@:1:$#-1}")
# The last argument is the output file
output_file="${!#}"

# Start building the ffmpeg command
ffmpeg_command="ffmpeg"
filter_complex=""
input_files_string=""

# Add input files to the command
for i in "${!inputs[@]}"; do
  input_files_string+=" -i ${inputs[$i]}"
  filter_complex+="[$i:v:0] [$i:a:0] "
done

# Complete the filter_complex string
filter_complex+="concat=n=${#inputs[@]}:v=1:a=1 [v] [a]"

# Construct the final command
# Use -vsync 2 to avoid timestamp issues
ffmpeg_command+="$input_files_string -filter_complex \"$filter_complex\" -map \"[v]\" -map \"[a]\" -vsync 2 $output_file"

# Execute the command
eval $ffmpeg_command
