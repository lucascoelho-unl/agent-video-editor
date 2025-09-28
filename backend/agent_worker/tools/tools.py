"""
Tools for media analysis and video editing.
"""

import asyncio
import json
import logging
import os
from datetime import datetime

import dotenv
import google.generativeai as genai
from google.api_core import exceptions

SCRIPTS_PATH = "/app/storage/scripts"
VIDEOS_PATH = "/app/storage/videos"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configure Gemini API
dotenv.load_dotenv(dotenv_path="agent/.env")
gemini_api_key = os.environ.get("GOOGLE_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=gemini_api_key)


async def analyze_media_files(
    media_filenames: list[str], prompt: str, source_directory: str = "videos"
) -> str:
    """
    Analyzes multiple video and audio files with the Gemini API in a single call
    and returns a text-based analysis.
    """

    # Upload and process media files concurrently
    uploaded_files = []
    try:

        async def _upload_and_process(filename):
            media_path = f"/app/storage/{source_directory}/{filename}"
            if not os.path.exists(media_path):
                logging.error("Media file not found: %s", media_path)
                return None

            logging.info("Uploading %s to Gemini...", filename)

            # Determine MIME type based on file extension
            file_extension = os.path.splitext(filename)[1].lower()
            mime_type_map = {
                ".mp4": "video/mp4",
                ".avi": "video/x-msvideo",
                ".mov": "video/quicktime",
                ".mkv": "video/x-matroska",
                ".webm": "video/webm",
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".aac": "audio/aac",
                ".flac": "audio/flac",
                ".ogg": "audio/ogg",
                ".m4a": "audio/mp4",
                ".wma": "audio/x-ms-wma",
            }
            mime_type = mime_type_map.get(file_extension, "application/octet-stream")

            media_file = await asyncio.to_thread(
                genai.upload_file, display_name=filename, path=media_path, mime_type=mime_type
            )

            # Wait for the media file to be processed
            while media_file.state.name == "PROCESSING":
                await asyncio.sleep(5)
                media_file = await asyncio.to_thread(genai.get_file, media_file.name)

            if media_file.state.name == "FAILED":
                logging.error("Processing failed for %s", filename)
                return None

            logging.info("Successfully processed %s", filename)
            return media_file

        # Create and run upload tasks in parallel
        tasks = [_upload_and_process(fname) for fname in media_filenames]
        results = await asyncio.gather(*tasks)

        # Filter out any files that failed to upload/process
        uploaded_files = [res for res in results if res is not None]
        if not uploaded_files:
            return json.dumps({"error": "All media file uploads failed or were not found."})

        # Generate content with Gemini using all media files
        logging.info("Generating content with Gemini using all media files...")
        model = genai.GenerativeModel(model_name="gemini-2.5-pro")

        # Combine the prompt and the list of uploaded media files
        content_to_send = [prompt] + uploaded_files

        response = await asyncio.to_thread(
            model.generate_content,
            content_to_send,
            request_options={"timeout": 1200},
        )

        logging.info("Successfully analyzed media files with Gemini.")
        return json.dumps({"analysis": response.text})

    except (OSError, ValueError, exceptions.GoogleAPICallError) as e:
        logging.error("An error occurred during Gemini analysis: %s", e)
        return json.dumps({"error": str(e)})

    finally:
        # Delete all uploaded files
        if uploaded_files:
            logging.info("Deleting Gemini files...")
            delete_tasks = [asyncio.to_thread(genai.delete_file, f.name) for f in uploaded_files]
            await asyncio.gather(*delete_tasks)
            logging.info("Successfully deleted all Gemini files.")


async def list_available_media_files(
    include_metadata: bool = False,
    sort_by: str = "creation_timestamp",
    sort_order: str = "desc",
) -> str:
    """
    Lists all video and audio files available in the storage directory.
    Optionally includes metadata and sorts by a specified field.
    """
    try:
        if not os.path.exists(VIDEOS_PATH):
            return json.dumps({"videos": [], "audio": []})

        video_files = []
        audio_files = []
        for file in os.listdir(VIDEOS_PATH):
            if file.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv")):
                if include_metadata:
                    file_path = os.path.join(VIDEOS_PATH, file)
                    stat = os.stat(file_path)

                    # Get file metadata (creation, modification, access times)
                    metadata = {
                        "filename": file,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "creation_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modification_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "access_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
                        "creation_timestamp": stat.st_ctime,
                        "modification_timestamp": stat.st_mtime,
                        "access_timestamp": stat.st_atime,
                    }
                    video_files.append(metadata)
                else:
                    # Simple filename only (no metadata)
                    video_files.append(file)
            elif file.lower().endswith((".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma")):
                if include_metadata:
                    file_path = os.path.join(VIDEOS_PATH, file)
                    stat = os.stat(file_path)

                    # Get file metadata (creation, modification, access times)
                    metadata = {
                        "filename": file,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "creation_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modification_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "access_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
                        "creation_timestamp": stat.st_ctime,
                        "modification_timestamp": stat.st_mtime,
                        "access_timestamp": stat.st_atime,
                    }
                    audio_files.append(metadata)
                else:
                    # Simple filename only (no metadata)
                    audio_files.append(file)

        # Sort by a specified field if metadata is included
        if include_metadata and sort_by:
            if sort_by not in [
                "filename",
                "size_bytes",
                "creation_timestamp",
                "modification_timestamp",
                "access_timestamp",
            ]:
                return json.dumps({"error": f"Invalid sort_by field: {sort_by}"})

            reverse = sort_order.lower() == "desc"
            video_files.sort(key=lambda x: x[sort_by], reverse=reverse)
            audio_files.sort(key=lambda x: x[sort_by], reverse=reverse)

        if include_metadata:
            return json.dumps(
                {
                    "videos": video_files,
                    "audio": audio_files,
                    "total_video_count": len(video_files),
                    "total_audio_count": len(audio_files),
                    "total_count": len(video_files) + len(audio_files),
                    "sorted_by": sort_by if sort_by else "None",
                    "sort_order": sort_order if sort_by else "None",
                }
            )
        else:
            return json.dumps({"videos": video_files, "audio": audio_files})
    except OSError as e:
        return json.dumps({"error": f"Failed to list media files: {str(e)}"})


async def read_edit_script(script_file_name: str = "edit.sh") -> str:
    """
    Reads the current content of the {script_file_name} script.
    """
    try:
        script_path = f"{SCRIPTS_PATH}/{script_file_name}"
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        return json.dumps({"script_content": content})
    except FileNotFoundError:
        return json.dumps({"error": f"{script_file_name} script not found"})
    except OSError as e:
        return json.dumps({"error": f"Failed to read script: {str(e)}"})


async def modify_edit_script(script_content: str, script_file_name: str = "edit.sh") -> str:
    """
    Replace the entire {script_file_name} script with new content.
    """
    try:
        script_path = f"{SCRIPTS_PATH}/{script_file_name}"

        # Write the new script content to the script file
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        bytes_written = len(script_content.encode("utf-8"))

        return json.dumps(
            {
                "success": True,
                "message": f"{script_file_name} script updated successfully ({bytes_written} bytes written)",
            }
        )

    except OSError as e:
        return json.dumps({"error": f"Failed to update {script_file_name} script: {str(e)}"})


async def execute_edit_script(
    input_files: list[str],
    output_file: str = "/app/storage/videos/results/output.mp4",
    script_file_name: str = "edit.sh",
) -> str:
    """
    Executes the {script_file_name} script asynchronously with the specified files.
    The script is expected to take input files as arguments, followed by the output file.
    """
    script_path = f"{SCRIPTS_PATH}/{script_file_name}"
    # Note: The script should be made executable during deployment, not here.
    # e.g., in a Dockerfile: RUN chmod +x /app/{script_file_name}

    if not os.path.exists(script_path):
        return json.dumps({"success": False, "error": f"{script_file_name} not found"})

    try:
        # Build the command to execute the script
        cmd = ["bash", script_path] + input_files + [output_file]

        # Execute the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=VIDEOS_PATH,
        )

        # Wait for the process to finish and capture the output
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return json.dumps(
                {"success": True, "output": stdout.decode(), "output_file": output_file}
            )
        else:
            return json.dumps(
                {"success": False, "error": stderr.decode(), "stdout": stdout.decode()}
            )
    except (OSError, ValueError) as e:
        return json.dumps({"success": False, "error": f"Failed to execute script: {str(e)}"})
