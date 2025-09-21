import asyncio
import json
import os
import sys
from typing import Tuple

# Add project root to the Python path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.docker.factory import create_docker_manager, create_video_service
from backend.tools.scripts import batch_merge_videos_script, merge_videos_script


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
    video_filenames: list,
    output_filename: str,
    source_directory: str = "videos",
    destination_directory: str = "results",
) -> str:
    """
    Merges one or more videos from a specified source directory and saves the result to a destination directory.
    """
    if len(video_filenames) < 2:
        return "Error: At least 2 videos are required for merging."

    docker_manager = create_docker_manager()

    # Construct video paths
    video_paths = [
        f"/app/{source_directory}/{filename}" for filename in video_filenames
    ]
    output_path = f"/app/{destination_directory}/{output_filename}"

    python_script = batch_merge_videos_script(video_paths, output_path)

    success, output = docker_manager.execute_script(python_script)

    if success:
        return f"Successfully merged {len(video_filenames)} videos: {', '.join(video_filenames)}"
    else:
        return f"Error merging videos: {output}"


async def delete_videos_from_container(file_paths: list) -> str:
    """
    Deletes one or more videos from the container using a list of relative paths.
    """
    if not file_paths:
        return "Error: No file paths provided for deletion."

    video_service = create_video_service()
    results = []
    errors = []

    for file_path in file_paths:
        try:
            result = video_service.delete_video(file_path)
            results.append(f"✅ {file_path}")
        except Exception as e:
            errors.append(f"❌ {file_path}: {str(e)}")

    # Format the response
    response_lines = [f"Batch delete completed: {len(file_paths)} files processed"]
    if results:
        response_lines.extend(results)
    if errors:
        response_lines.extend(errors)

    return "\n".join(response_lines)


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
