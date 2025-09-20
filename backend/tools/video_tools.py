from moviepy import VideoFileClip, concatenate_videoclips


async def merge_videos(video_path1: str, video_path2: str, output_path: str):
    """
    Merges two videos together and saves the result to a file.

    Args:
        video_path1 (str): Path to the first video file.
        video_path2 (str): Path to the second video file.
        output_path (str): Path to save the merged video file.
    """
    try:
        # Load the video clips
        clip1 = VideoFileClip(video_path1)
        clip2 = VideoFileClip(video_path2)

        # Concatenate the clips
        final_clip = concatenate_videoclips([clip1, clip2])

        # Write the result to a file
        final_clip.write_videofile(output_path, codec="libx264")

        # Close the clips
        clip1.close()
        clip2.close()
        final_clip.close()

        print(f"Videos merged successfully! Output saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
