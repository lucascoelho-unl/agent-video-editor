import asyncio
import os
import sys
from typing import List, Tuple

# Add project root to the Python path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.docker.factory import create_services


async def list_videos_in_container() -> List[str]:
    """
    Lists all video files in the /app/data directory of the container.
    """
    docker_manager, video_service = create_services()
    return video_service.list_videos()


async def get_video_by_filename(filename: str) -> str:
    """
    Gets a video by filename from the /app/data directory of the container.
    """
    docker_manager, video_service = create_services()
    return video_service.get_video_by_filename(filename)


async def main():
    """
    Main function to test the docker tools.
    """
    print("Listing videos in container...")
    videos = await list_videos_in_container()

    if videos:
        print("Found videos:")
        for video in videos["videos"]:
            print(f"- {video}")

        # Test getting the first video
        first_video = videos["videos"][0]
        print(f"Attempting to download '{first_video}'...")
        local_path = await get_video_by_filename(first_video)
        if "Error" in local_path:
            print(local_path)
        else:
            print(f"Successfully downloaded to: {local_path}")
    else:
        print("No videos found to test download.")


if __name__ == "__main__":
    asyncio.run(main())
