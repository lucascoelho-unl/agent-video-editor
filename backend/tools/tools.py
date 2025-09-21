import asyncio
import json
import os
import sys
from typing import Tuple

# Add project root to the Python path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.docker.factory import create_docker_manager, create_video_service
from backend.tools.scripts import batch_merge_videos_script
from backend.tools.video_utils import process_video, update_videos_data_after_delete


async def list_videos_in_container() -> str:
    """
    Lists all files in the 'videos', 'results', and 'temp' directories of the container.
    Returns a JSON string with structured data about all video files.
    """
    video_service = create_video_service()
    all_files = await video_service.list_videos()

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


async def get_videos_creation_timestamps() -> str:
    """
    Retrieves the creation timestamps for all videos from the videos_data.json file.
    """
    video_service = create_video_service()
    videos_data = await video_service.get_videos_data()

    # Extracting filename and creation_time from the data
    timestamps = [
        {"filename": data.get("filename"), "creation_time": data.get("creation_time")}
        for data in videos_data
    ]

    # Sort timestamps by creation_time in ascending order
    timestamps.sort(key=lambda x: x.get("creation_time") or "")

    return json.dumps(timestamps, indent=2)


async def get_video_transcript(video_filename: str) -> str:
    """
    Retrieves the transcript for a specific video.
    """
    video_service = create_video_service()
    videos_data = await video_service.get_videos_data()
    video_data = videos_data.get("videos", {}).get(video_filename, {})
    transcript = video_data.get("transcript", {})
    return transcript


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

    success, output = await docker_manager.execute_script(python_script)

    if success:
        # After a successful merge, process the new video to get its data
        try:
            await process_video(output_filename, video_dir=destination_directory)
            return f"Successfully merged {len(video_filenames)} videos: {', '.join(video_filenames)}\nOutput:\n{output}"
        except Exception as e:
            return f"Successfully merged videos, but failed to process the new video data: {str(e)}"
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

    delete_tasks = [video_service.delete_video(file_path) for file_path in file_paths]
    delete_results = await asyncio.gather(*delete_tasks, return_exceptions=True)

    for file_path, result in zip(file_paths, delete_results):
        if isinstance(result, Exception):
            errors.append(f"❌ {file_path}: {str(result)}")
        else:
            results.append(f"✅ {file_path}")

    # Next, update the JSON data file
    try:
        await update_videos_data_after_delete(file_paths)
        results.append("✅ `videos_data.txt` updated successfully.")
    except Exception as e:
        errors.append(f"❌ Error updating `videos_data.txt`: {str(e)}")

    # Format the response
    response_lines = [f"Batch delete completed: {len(file_paths)} files processed"]
    if results:
        response_lines.extend(results)
    if errors:
        response_lines.extend(errors)

    return "\n".join(response_lines)
