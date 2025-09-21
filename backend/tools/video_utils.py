import json

from docker.factory import create_docker_manager
from tools.scripts import (
    extract_transcript_script,
    extract_video_data_script,
    read_video_data_script,
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


async def process_video(filename: str, video_dir: str = "videos") -> None:
    """
    Processes a video to extract metadata and transcript, then saves it to a JSON file.
    """
    docker_manager = create_docker_manager()

    # Define paths
    video_path = f"/app/{video_dir}/{filename}"
    output_path = "/app/videos_data.txt"

    metadata_script = extract_video_data_script(video_path)
    metadata_success, metadata_output = docker_manager.execute_script(metadata_script)

    if not metadata_success:
        raise Exception(f"Error extracting metadata: {metadata_output}")

    # Extract transcript
    transcript_script = extract_transcript_script(video_path)
    transcript_success, transcript_output = docker_manager.execute_script(
        transcript_script
    )

    if not transcript_success:
        raise Exception(f"Error extracting transcript: {transcript_output}")

    # Prepare data
    if metadata_success:
        raw_metadata = json.loads(metadata_output)
        metadata_content = _process_metadata(raw_metadata)
    else:
        metadata_content = {"error": metadata_output}

    if transcript_success:
        raw_transcript = json.loads(transcript_output)
        transcript_content = _process_transcript(raw_transcript)
    else:
        transcript_content = {"error": transcript_output}

    video_data = {
        filename: {
            "metadata": metadata_content,
            "transcript": transcript_content,
        }
    }

    # Read existing data, append new data, and write back
    read_script = read_video_data_script(output_path)
    read_success, existing_data_str = docker_manager.execute_script(read_script)
    if not read_success:
        raise Exception(f"Error reading existing data: {existing_data_str}")

    existing_data = {}
    if existing_data_str.strip():
        existing_data = json.loads(existing_data_str)

    if "videos" not in existing_data:
        existing_data["videos"] = {}

    existing_data["videos"].update(video_data)

    # Safely encode the JSON data to a string
    json_data_string = json.dumps(existing_data, indent=2, ensure_ascii=False)

    # Write the data to the file using UTF-8 encoding
    write_script = write_video_data_script(output_path, json_data_string)
    write_success, write_output = docker_manager.execute_script(write_script)
    if not write_success:
        raise Exception(f"Error writing video data: {write_output}")
