import asyncio
import os
import sys
from typing import List, Tuple

# Add project root to the Python path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.docker.factory import create_docker_manager, create_video_service


async def list_videos_in_container() -> List[str]:
    """
    Lists all video files in the /app/videos directory of the container.
    """
    docker_manager = create_docker_manager()
    # List files in the directory
    success, files = docker_manager.list_files("/app/videos")
    if not success:
        return ["Error: Could not list files in the container."]

    # Filter for video files (you can customize the extensions)
    video_extensions = [".mp4", ".mov", ".avi", ".mkv"]
    video_files = [f for f in files if any(f.endswith(ext) for ext in video_extensions)]

    return video_files


async def merge_videos_in_container(
    video1_filename: str, video2_filename: str, output_filename: str
) -> str:
    """
    Merges two videos that are already inside the container.
    The result is saved to the /app/results directory in the container.
    """
    docker_manager = create_docker_manager()

    # Construct the python command to execute inside the container
    video1_path = f"/app/videos/{video1_filename}"
    video2_path = f"/app/videos/{video2_filename}"
    output_path = f"/app/results/{output_filename}"

    python_script = (
        f"from moviepy.editor import VideoFileClip, concatenate_videoclips; "
        f"clip1 = VideoFileClip('{video1_path}'); "
        f"clip2 = VideoFileClip('{video2_path}'); "
        f"final_clip = concatenate_videoclips([clip1, clip2]); "
        f"final_clip.write_videofile('{output_path}', codec='libx264'); "
        f"clip1.close(); clip2.close(); final_clip.close(); "
        f"print(f'Successfully merged videos into {output_path}')"
    )

    command_to_run = f"python3 -c {python_script}"

    # Execute the command
    success, output = docker_manager.exec_command(command_to_run)

    if success:
        return output
    else:
        return f"Error merging videos in container: {output}"


async def delete_video_from_container(filename: str) -> str:
    """
    Deletes a video from the /app/videos directory in the container.
    """
    video_service = create_video_service()
    try:
        result = video_service.delete_video(filename)
        return result.get("message", "Video deleted successfully.")
    except Exception as e:
        return f"Error deleting video from container: {str(e)}"


async def get_video_by_filename(filename: str) -> str:
    """
    Gets a video by filename from the /app/data directory of the container.
    """
    video_service = create_video_service()
    return video_service.get_video_by_filename(filename)
