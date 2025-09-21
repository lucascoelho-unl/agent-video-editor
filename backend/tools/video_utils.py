import asyncio
import json
import os

from docker.factory import create_docker_manager, create_video_service

from .scripts import (
    extract_transcript_script,
    extract_video_data_script,
    write_video_data_script,
)


def _process_metadata(raw_metadata: dict) -> dict:
    """Processes raw ffprobe metadata to extract specific fields."""
    format_data = raw_metadata.get("format", {})
    tags = format_data.get("tags", {})

    return {
        "filename": format_data.get("filename"),
        "format_name": format_data.get("format_name"),
        "start_time": format_data.get("start_time"),
        "duration": format_data.get("duration"),
        "size": format_data.get("size"),
        "tags": {"creation_time": tags.get("creation_time")},
    }


def _process_transcript(raw_transcript: dict) -> dict:
    """Processes raw whisper transcript to extract specific fields."""
    processed_segments = [
        {
            "id": segment.get("id"),
            "seek": segment.get("seek"),
            "start": segment.get("start"),
            "end": segment.get("end"),
            "text": segment.get("text"),
        }
        for segment in raw_transcript.get("segments", [])
    ]

    return {
        "text": raw_transcript.get("text"),
        "segments": processed_segments,
        "language": raw_transcript.get("language"),
    }


async def get_transcript(video_path: str) -> str:
    """
    Retrieves the transcript for a specific video by executing a script in the container.
    """
    script = extract_transcript_script(video_path)
    success, output = await create_docker_manager().execute_script(script)

    if success:
        try:
            # Attempt to parse the JSON output from the script
            transcript_data = json.loads(output)
            # Return the transcript text, or the full JSON if 'text' is not available
            return transcript_data.get("text", json.dumps(transcript_data))
        except json.JSONDecodeError:
            # If output is not JSON, return it as is
            return output
    else:
        return f"Error retrieving transcript: {output}"


async def update_videos_data_after_delete(file_paths: list) -> None:
    """
    Updates the videos_data.txt file after deleting videos.
    """
    videos_data = await create_video_service().get_videos_data()
    if "videos" not in videos_data:
        return  # No video data to update

    # Create a set of filenames to be deleted for efficient lookup
    filenames_to_delete = {os.path.basename(path) for path in file_paths}

    # Filter out the deleted videos
    videos_data["videos"] = {
        filename: data
        for filename, data in videos_data["videos"].items()
        if filename not in filenames_to_delete
    }

    # Write the updated data back to the file
    script = write_video_data_script(videos_data)
    success, output = await create_docker_manager().execute_script(script)
    if not success:
        raise Exception(f"Error updating videos_data.txt: {output}")


async def process_video(filename: str, video_dir: str = "videos") -> None:
    """
    Processes a video to extract metadata and transcript, then saves it to a JSON file.
    """
    video_path = f"/app/{video_dir}/{filename}"
    output_path = "/app/videos_data.txt"

    video_service = create_video_service()
    docker_manager = create_docker_manager()

    # Extract metadata and transcript concurrently
    metadata_script = extract_video_data_script(video_path)
    transcript_script = extract_transcript_script(video_path)

    results = await asyncio.gather(
        docker_manager.execute_script(metadata_script),
        docker_manager.execute_script(transcript_script),
    )

    metadata_success, metadata_output = results[0]
    transcript_success, transcript_output = results[1]

    if not metadata_success:
        raise Exception(f"Error extracting metadata: {metadata_output}")
    if not transcript_success:
        raise Exception(f"Error extracting transcript: {transcript_output}")

    # Process and combine data
    raw_metadata = json.loads(metadata_output)
    raw_transcript = json.loads(transcript_output)
    video_data = {
        filename: {
            "metadata": _process_metadata(raw_metadata),
            "transcript": _process_transcript(raw_transcript),
        }
    }

    # Update the JSON file
    existing_data = await video_service.get_videos_data()
    if "videos" not in existing_data:
        existing_data["videos"] = {}
    existing_data["videos"].update(video_data)

    # Write the updated data back to the file
    script = write_video_data_script(existing_data)
    success, output = await docker_manager.execute_script(script)
    if not success:
        raise Exception(f"Error updating videos_data.txt: {output}")
