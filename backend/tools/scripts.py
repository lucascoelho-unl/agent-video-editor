from backend.docker.config import NUM_CORES


def batch_merge_videos_script(video_paths, output_path):
    return f"""
import sys
from moviepy import VideoFileClip, concatenate_videoclips

try:
    # Load all video clips
    clips = [VideoFileClip(video_path) for video_path in {video_paths}]

    # Concatenate the clips
    # method="compose" handles clips of different sizes by creating a
    # background canvas and centering each clip.
    final_clip = concatenate_videoclips(clips, method="compose")

    # Write the result to a file
    final_clip.write_videofile("{output_path}", codec='libx264', fps=24, threads={NUM_CORES}, preset='superfast')
    
    # Close all clips
    for clip in clips:
        clip.close()
    final_clip.close()

    print(f"Successfully merged {{len(clips)}} videos into {output_path}")

except Exception as e:
    print(f"Error merging videos: {{str(e)}}")
    sys.exit(1)
"""
