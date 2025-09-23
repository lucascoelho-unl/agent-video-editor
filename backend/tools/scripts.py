import base64
import json


def batch_merge_videos_script(video_paths, output_path):
    return f"""
import sys
import time
from moviepy import VideoFileClip, concatenate_videoclips

try:
    print("Starting video merge process.")
    
    # Load all video clips
    start_time = time.time()
    print("Loading video clips...")
    clips = [VideoFileClip(video_path) for video_path in {video_paths}]
    load_time = time.time() - start_time
    print(f"Clips loaded in {{load_time:.2f}} seconds.")

    # Concatenate the clips
    start_time = time.time()
    print("Concatenating video clips...")
    # method="compose" handles clips of different sizes by creating a
    # background canvas and centering each clip.
    final_clip = concatenate_videoclips(clips, method="compose")
    concat_time = time.time() - start_time
    print(f"Clips concatenated in {{concat_time:.2f}} seconds.")

    # Write the result to a file
    start_time = time.time()
    print("Writing final video file...")
    final_clip.write_videofile("{output_path}", codec='libx264', fps=24, threads=4, preset='superfast')
    write_time = time.time() - start_time
    print(f"Final video written in {{write_time:.2f}} seconds.")
    
    # Close all clips
    print("Closing video clips...")
    for clip in clips:
        clip.close()
    final_clip.close()
    print("All clips closed.")

    print(f"Successfully merged {{len(clips)}} videos into {output_path}")

except Exception as e:
    print(f"Error merging videos: {{str(e)}}")
    sys.exit(1)
"""


def append_to_videos_data_script(video_data: dict) -> str:
    """
    Creates a script to append new video data to the videos_data.txt file.
    """
    video_data_str = json.dumps(video_data)
    return f"""
import json
import os

output_path = "/app/videos_data.txt"
new_data = json.loads('{video_data_str}')

if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
    existing_data = {{"videos": {{}} }}
else:
    with open(output_path, "r") as f:
        try:
            existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = {{"videos": {{}} }}

if "videos" not in existing_data:
    existing_data["videos"] = {{}}

existing_data["videos"].update(new_data)

with open(output_path, "w") as f:
    json.dump(existing_data, f, indent=4)
"""


def extract_video_data_script(video_path: str) -> str:
    """
    Creates a script to extract video metadata using ffprobe.
    """
    return f"""
import json
import subprocess

try:
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', '{video_path}'],
        capture_output=True,
        text=True,
        check=True
    )
    metadata = json.loads(result.stdout)
    print(json.dumps(metadata, indent=2))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""


def extract_transcript_script(video_path):
    return f"""
import whisper
import json

try:
    model = whisper.load_model('tiny')
    result = model.transcribe('{video_path}')
    print(json.dumps(result, indent=2))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""


def read_video_data_script(file_path: str) -> str:
    """
    Returns a Python script to read the content of a file.
    """
    return f"""
import json
try:
    with open('{file_path}', 'r', encoding='utf-8') as f:
        print(f.read())
except FileNotFoundError:
    print('')
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""


def write_video_data_script(data: dict) -> str:
    """
    Returns a Python script to write data to a JSON file.
    """
    json_data_string = json.dumps(data, indent=2)
    encoded_data = base64.b64encode(json_data_string.encode("utf-8")).decode("utf-8")
    return f"""
import json
import base64
try:
    decoded_data = base64.b64decode('{encoded_data}').decode('utf-8')
    with open('/app/videos_data.txt', 'w') as f:
        f.write(decoded_data)
    print("Successfully wrote to videos_data.txt")
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""
