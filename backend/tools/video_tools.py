import os

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


async def delete_video_from_working_dir(filename: str) -> str:
    """
    Deletes a video file from the agent's local working directory.

    Args:
        filename (str): The name of the video file to delete.
    """
    try:
        # Define the path to the agent's downloads directory
        agent_downloads_path = os.path.join(
            os.path.dirname(__file__), "..", "agent", "downloads"
        )
        file_path = os.path.join(agent_downloads_path, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            return f"Successfully deleted {filename} from the working directory."
        else:
            return f"Error: {filename} not found in the working directory."

    except Exception as e:
        return f"An error occurred: {str(e)}"
