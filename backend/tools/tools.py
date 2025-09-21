import asyncio
import os
import sys
import tempfile
from typing import List, Literal, Tuple

# Add project root to the Python path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.docker.factory import create_docker_manager, create_video_service


async def list_videos_in_container() -> List[Tuple[str, List[str]]]:
    """
    Lists all files in the 'videos', 'results', and 'temp' directories of the container.
    Returns a list of tuples, where each tuple is (directory_name, file_list).
    """
    video_service = create_video_service()
    all_files = video_service.list_videos()

    # Format the output as a list of tuples
    return [(folder, files) for folder, files in all_files.items()]


async def merge_videos_in_container(
    video1_filename: str, video2_filename: str, output_filename: str
) -> str:
    """
    Merges two videos that are already inside the container.
    The result is saved to the /app/results directory in the container.
    """
    docker_manager = create_docker_manager()

    # Construct the python script to execute inside the container
    video1_path = f"/app/videos/{video1_filename}"
    video2_path = f"/app/videos/{video2_filename}"
    output_path = f"/app/results/{output_filename}"

    python_script = f"""
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

    # Execute the script
    success, output = docker_manager.execute_script(python_script)

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


async def main():
    """
    Main function to test the docker tools.
    """
    print("--- Testing Video Tools ---")

    print("\n1. Listing videos in container...")
    dir_contents = await list_videos_in_container()

    if not dir_contents:
        print("Error listing videos or no directories found. Aborting test.")
        return

    videos = []
    for folder, files in dir_contents:
        print(f"   Contents of /{folder}:")
        if files:
            for file in files:
                print(f"     - {file}")
            if folder == "videos":
                videos.extend(files)
        else:
            print("     (empty)")

    if len(videos) < 2:
        print("\nNot enough videos to test merging. Need at least 2.")
        return

    video1 = videos[0]
    video2 = videos[1]
    output_filename = "merged_test_video.mp4"

    print(f"\n2. Merging '{video1}' and '{video2}' into '{output_filename}'...")

    merge_result = await merge_videos_in_container(video1, video2, output_filename)

    print(f"   Merge result: {merge_result}")

    print("\n--- Test Complete ---")


if __name__ == "__main__":
    asyncio.run(main())
