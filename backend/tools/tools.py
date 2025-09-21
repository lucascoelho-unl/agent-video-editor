import asyncio
import json
import os
import sys
from typing import Tuple

try:
    from .scripts import merge_videos_script
except ImportError:
    # Handle case when running script directly
    from scripts import merge_videos_script

# Add project root to the Python path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.docker.factory import create_docker_manager, create_video_service


async def list_videos_in_container() -> str:
    """
    Lists all files in the 'videos', 'results', and 'temp' directories of the container.
    Returns a JSON string with structured data about all video files.
    """
    video_service = create_video_service()
    all_files = video_service.list_videos()

    # Create structured data
    result = {
        "videos": all_files.get("videos", []),
        "results": all_files.get("results", []),
        "temp": all_files.get("temp", []),
        "total_count": len(all_files.get("videos", []))
        + len(all_files.get("results", []))
        + len(all_files.get("temp", [])),
    }

    return json.dumps(result, indent=2)


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

    python_script = merge_videos_script(video1_path, video2_path, output_path)
    success, output = docker_manager.execute_script(python_script)

    if success:
        return output
    else:
        return f"Error merging videos in container: {output}"


async def delete_video_from_container(file_path: str) -> str:
    """
    Deletes a video from a specified path in the container (e.g., "videos/my_video.mp4").
    """
    video_service = create_video_service()
    try:
        # The agent will provide a path like "videos/my_video.mp4".
        # The video_service expects the path relative to the /app/ directory.
        result = video_service.delete_video(file_path)
        return result.get("message", "Video deleted successfully.")
    except Exception as e:
        return f"Error deleting video from container: {str(e)}"


async def main():
    """
    Main function to test the list_videos_in_container tool.
    """
    print("--- Testing list_videos_in_container Tool ---")
    print()

    try:
        result = await list_videos_in_container()
        print("Tool Output:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        print()
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
