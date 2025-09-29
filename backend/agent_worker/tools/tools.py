"""
Tools for media analysis and video editing.
"""

import asyncio
import json
import logging
import os
import re
import tempfile
import uuid

import dotenv
import google.generativeai as genai
from google.api_core import exceptions

# Import MinIO service
from .minio_service import (
    MinioServiceError,
    download_file_to_temp,
    file_exists,
    get_file_info,
    list_files_in_directory,
    upload_file_from_bytes,
    upload_file_from_path,
)

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
    temp_files = []  # Track temporary files for cleanup
    not_found_files = []
    try:

        async def _upload_and_process(filename):
            object_name = f"{source_directory}/{filename}"

            # Check if file exists in MinIO
            if not file_exists(object_name):
                logging.warning("Media file not found in MinIO: %s", object_name)
                not_found_files.append(filename)
                return None

            logging.info("Downloading %s from MinIO...", filename)

            # Download file to temporary location
            temp_path = await asyncio.to_thread(download_file_to_temp, object_name)
            temp_files.append(temp_path)  # Track for cleanup

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

            # Sanitize the filename to create a valid resource name that consists of
            # only lowercase alphanumeric characters and dashes.
            base_filename, _ = os.path.splitext(filename)
            sanitized_base = re.sub(r"[^a-z0-9-]+", "-", base_filename.lower().strip()).strip("-")

            # If the sanitized base is empty (e.g., filename was only symbols), create a unique name.
            if not sanitized_base:
                sanitized_base = f"media-{uuid.uuid4()}"
                logging.warning(
                    "Sanitized base is empty, creating a unique name: %s", sanitized_base
                )

            media_file = await asyncio.to_thread(
                genai.upload_file,
                name=sanitized_base,
                display_name=filename,
                path=temp_path,
                mime_type=mime_type,
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
            if not_found_files:
                return json.dumps(
                    {
                        "analysis": f"Analysis could not be performed because the following files were not found: {', '.join(not_found_files)}."
                    }
                )
            return json.dumps(
                {"analysis": "Analysis could not be performed because no files could be processed."}
            )

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
        # Delete all uploaded files from Gemini
        if uploaded_files:
            logging.info("Deleting Gemini files...")
            delete_tasks = [asyncio.to_thread(genai.delete_file, f.name) for f in uploaded_files]
            await asyncio.gather(*delete_tasks)
            logging.info("Successfully deleted all Gemini files.")

        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass


async def list_available_media_files(
    include_metadata: bool = False,
    sort_by: str = "creation_timestamp",
    sort_order: str = "desc",
) -> str:
    """
    Lists all video and audio files available in MinIO storage.
    Optionally includes metadata and sorts by a specified field.
    """
    try:
        # Get all files from MinIO videos directory
        all_files = list_files_in_directory("videos")
        all_files.extend(list_files_in_directory("results"))
        all_files.extend(list_files_in_directory("temp"))

        video_files = []
        audio_files = []

        for filename in all_files:
            if filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv")):
                if include_metadata:
                    try:
                        # Get file info from MinIO
                        object_name = f"videos/{filename}"
                        file_info = await asyncio.to_thread(get_file_info, object_name)

                        metadata = {
                            "filename": filename,
                            "size_bytes": file_info["size"],
                            "size_mb": round(file_info["size"] / (1024 * 1024), 2),
                            "last_modified": file_info["last_modified"].isoformat(),
                            "content_type": file_info["content_type"],
                            "etag": file_info["etag"],
                        }
                        video_files.append(metadata)
                    except MinioServiceError as e:
                        logging.warning("Could not get metadata for %s: %s", filename, e)
                        video_files.append(filename)
                else:
                    # Simple filename only (no metadata)
                    video_files.append(filename)
            elif filename.lower().endswith(
                (".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma")
            ):
                if include_metadata:
                    try:
                        # Get file info from MinIO
                        object_name = f"videos/{filename}"
                        file_info = await asyncio.to_thread(get_file_info, object_name)

                        metadata = {
                            "filename": filename,
                            "size_bytes": file_info["size"],
                            "size_mb": round(file_info["size"] / (1024 * 1024), 2),
                            "last_modified": file_info["last_modified"].isoformat(),
                            "content_type": file_info["content_type"],
                            "etag": file_info["etag"],
                        }
                        audio_files.append(metadata)
                    except MinioServiceError as e:
                        logging.warning("Could not get metadata for %s: %s", filename, e)
                        audio_files.append(filename)
                else:
                    # Simple filename only (no metadata)
                    audio_files.append(filename)

        # Sort by a specified field if metadata is included
        if include_metadata and sort_by:
            valid_sort_fields = ["filename", "size_bytes", "last_modified"]
            if sort_by not in valid_sort_fields:
                return json.dumps(
                    {
                        "error": f"Invalid sort_by field: {sort_by}. Valid fields: {valid_sort_fields}"
                    }
                )

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
    except MinioServiceError as e:
        return json.dumps({"error": f"Failed to list media files: {str(e)}"})


async def read_edit_script(script_file_name: str = "edit.sh") -> str:
    """
    Reads the current content of the {script_file_name} script from MinIO.
    """
    try:
        object_name = f"scripts/{script_file_name}"

        # Download script to temporary file
        temp_path = await asyncio.to_thread(download_file_to_temp, object_name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()
            return json.dumps({"script_content": content})
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    except (MinioServiceError, OSError) as e:
        return json.dumps({"error": f"Failed to read script: {str(e)}"})


async def modify_edit_script(script_content: str, script_file_name: str = "edit.sh") -> str:
    """
    Replace the entire {script_file_name} script with new content in MinIO.
    """
    try:
        object_name = f"scripts/{script_file_name}"

        # Upload the new script content to MinIO
        await asyncio.to_thread(
            upload_file_from_bytes, script_content.encode("utf-8"), object_name, "text/plain"
        )

        bytes_written = len(script_content.encode("utf-8"))

        return json.dumps(
            {
                "success": True,
                "message": f"{script_file_name} script updated successfully ({bytes_written} bytes written)",
            }
        )

    except MinioServiceError as e:
        return json.dumps({"error": f"Failed to update {script_file_name} script: {str(e)}"})


async def execute_edit_script(
    input_files: list[str],
    output_filename: str = "output.mp4",
    script_file_name: str = "edit.sh",
) -> str:
    """
    Executes the {script_file_name} script asynchronously with the specified files.
    Downloads input files from MinIO, executes the script, and uploads the result back to MinIO.
    """
    temp_files = []
    temp_script_path = None

    try:
        # Download script from MinIO
        script_object_name = f"scripts/{script_file_name}"
        if not file_exists(script_object_name):
            return json.dumps({"success": False, "error": f"{script_file_name} not found in MinIO"})

        temp_script_path = await asyncio.to_thread(download_file_to_temp, script_object_name)

        # Make script executable
        os.chmod(temp_script_path, 0o755)

        # Download input files from MinIO to temporary files
        temp_input_files = []
        for input_file in input_files:
            input_object_name = f"videos/{input_file}"
            if not file_exists(input_object_name):
                return json.dumps(
                    {"success": False, "error": f"Input file {input_file} not found in MinIO"}
                )

            temp_input_path = await asyncio.to_thread(download_file_to_temp, input_object_name)
            temp_input_files.append(temp_input_path)
            temp_files.append(temp_input_path)

        # Create temporary output file
        temp_output_path = tempfile.mktemp(suffix=f"_{output_filename}")
        temp_files.append(temp_output_path)

        # Build the command to execute the script
        cmd = ["bash", temp_script_path] + temp_input_files + [temp_output_path]

        # Execute the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for the process to finish and capture the output
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            # Upload the result file to MinIO
            if os.path.exists(temp_output_path):
                result_object_name = f"results/{output_filename}"
                await asyncio.to_thread(
                    upload_file_from_path, temp_output_path, result_object_name, "video/mp4"
                )

                return json.dumps(
                    {
                        "success": True,
                        "output": stdout.decode(),
                        "output_file": output_filename,
                        "output_object": result_object_name,
                    }
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "error": "Script executed but output file was not created",
                        "stdout": stdout.decode(),
                    }
                )
        else:
            return json.dumps(
                {"success": False, "error": stderr.decode(), "stdout": stdout.decode()}
            )

    except (MinioServiceError, OSError) as e:
        return json.dumps({"success": False, "error": f"Failed to execute script: {str(e)}"})

    finally:
        # Clean up all temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except OSError:
                pass
