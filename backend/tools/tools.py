import asyncio
import json
import os
import sys
import tempfile
import time

import dotenv
import google.generativeai as genai

dotenv.load_dotenv(dotenv_path="agent/.env")
gemini_api_key = os.environ.get("GOOGLE_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=gemini_api_key)

# Add project root to the Python path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.docker.factory import create_docker_manager, create_video_service
from backend.tools.scripts import batch_merge_videos_script
from backend.tools.video_utils import (
    update_video_data_with_concatenated_transcript,
    update_videos_data_after_delete,
)


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


async def get_videos_creation_timestamps(
    video_filenames: list[str] | None = None,
) -> str:
    """
    Retrieves the creation timestamps for all videos or a specified list of videos
    from the videos_data.json file.
    """
    video_service = create_video_service()
    videos_data = await video_service.get_videos_data()

    videos = videos_data.get("videos", {})

    if video_filenames:
        videos_to_process = {
            filename: videos[filename]
            for filename in video_filenames
            if filename in videos
        }
    else:
        videos_to_process = videos

    timestamps = [
        {
            "filename": filename,
            "creation_time": data.get("metadata", {})
            .get("tags", {})
            .get("creation_time"),
        }
        for filename, data in videos_to_process.items()
    ]

    # Sort timestamps by creation_time in ascending order
    timestamps.sort(key=lambda x: x.get("creation_time") or "")

    return json.dumps(timestamps, indent=2)


async def get_video_transcript(video_filenames: list[str]) -> str:
    """
    Retrieves the transcript for a specific video or a list of videos.
    """
    video_service = create_video_service()
    videos_data = await video_service.get_videos_data()
    all_videos_data = videos_data.get("videos", {})

    transcripts = {}
    for video_filename in video_filenames:
        video_data = all_videos_data.get(video_filename)

        if not video_data:
            transcripts[video_filename] = f"Video data not found for: {video_filename}"
            continue

        transcript = video_data.get("transcript")

        if not transcript:
            transcripts[video_filename] = (
                f"No transcript found for video: {video_filename}"
            )
        else:
            transcripts[video_filename] = transcript

    return json.dumps(transcripts, indent=2)


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

    if not success:
        return f"Error merging videos: {output}"

    # After a successful merge, process the new video to get its data
    try:
        await update_video_data_with_concatenated_transcript(
            output_filename,
            destination_directory,
            video_filenames,
        )
        return f"Successfully merged {len(video_filenames)} videos: {', '.join(video_filenames)}\nOutput:\n{output}"
    except Exception as e:
        return f"Successfully merged videos, but failed to process the new video data: {str(e)}"


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


async def analyze_video_with_gemini(
    video_filename: str, prompt: str, source_directory: str = "videos"
) -> str:
    """
    Analyzes a video file with the Gemini API and returns a text-based analysis.
    """
    docker_manager = create_docker_manager()
    video_path_in_container = f"/app/{source_directory}/{video_filename}"

    # First, we need to get the video file out of the container to upload it to the Gemini API
    # This is a simplified approach; you might want to create a more robust file handling system
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(video_filename)[1]
    ) as temp_local_file:
        if not await docker_manager.copy_file_from_container(
            video_path_in_container, temp_local_file.name
        ):
            return json.dumps(
                {"error": f"Failed to copy {video_filename} from the container."}
            )

        video_file = None
        try:
            # Upload the file to the Gemini API
            video_file = genai.upload_file(path=temp_local_file.name)

            # Wait for the video to be processed, with a timeout
            processing_start_time = time.time()
            processing_timeout = 600  # 10 minutes
            while video_file.state.name == "PROCESSING":
                if time.time() - processing_start_time > processing_timeout:
                    return json.dumps(
                        {"error": "Timeout: Video processing took too long."}
                    )
                time.sleep(10)
                try:
                    video_file = genai.get_file(video_file.name)
                except Exception as e:
                    # Log the error and continue polling
                    print(f"Error checking video status: {e}")
                    pass

            if video_file.state.name == "FAILED":
                return json.dumps(
                    {"error": f"Video processing failed: {video_file.state.name}"}
                )

            # Make the LLM request with a longer timeout
            model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")
            response = model.generate_content(
                [video_file, prompt], request_options={"timeout": 1200}  # 20 minutes
            )

            return json.dumps({"analysis": response.text})

        except Exception as e:
            return json.dumps({"error": str(e)})
        finally:
            # Clean up the file from the Gemini API server
            if video_file:
                try:
                    genai.delete_file(video_file.name)
                except Exception as e:
                    print(f"Error deleting Gemini file {video_file.name}: {e}")
            # Clean up the local temporary file
            os.remove(temp_local_file.name)
