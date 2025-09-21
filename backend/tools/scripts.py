def merge_videos_script(video1_path, video2_path, output_path):
    return f"""
from moviepy import VideoFileClip, concatenate_videoclips

try:
    clip1 = VideoFileClip('{video1_path}')
    clip2 = VideoFileClip('{video2_path}')
    final_clip = concatenate_videoclips([clip1, clip2])
    final_clip.write_videofile('{output_path}', codec='libx264')
    clip1.close()
    clip2.close()
    final_clip.close()
    print(f'Successfully merged videos into {output_path}')
except Exception as e:
    print(f'Error merging videos: {{str(e)}}')
"""
