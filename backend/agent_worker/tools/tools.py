"""
Tools for media analysis and video editing.
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import List

from interfaces.llm_service_interface import LLMService
from interfaces.storage_service_interface import StorageService
from services.gemini_service import GeminiService
from services.minio_storage_service import MinioServiceError, MinioStorageService

from .utils import categorize_and_enrich_files, cleanup_temp_files, sort_media_files

# Using default logging module


class ServiceManager:
    """Manages service instances with lazy initialization."""

    def __init__(self):
        self._storage_service = MinioStorageService()
        self._llm_service = None

    @property
    def storage_service(self) -> StorageService:
        """Get the storage service instance."""
        return self._storage_service

    @property
    def llm_service(self) -> LLMService:
        """Get the LLM service instance, creating it if needed."""
        if self._llm_service is None:
            self._llm_service = GeminiService(self._storage_service)
        return self._llm_service


services = ServiceManager()


async def analyze_media_files(
    media_filenames: List[str], prompt: str, source_directory: str = "videos"
) -> str:
    """Analyzes media files with a given prompt."""
    logging.info(
        "Analyzing %d media files with prompt: '%s'",
        len(media_filenames),
        prompt,
    )
    return await services.llm_service.analyze_media_files(media_filenames, prompt, source_directory)


async def list_available_media_files(
    include_metadata: bool = False,
    sort_by: str = "creation_timestamp",
    sort_order: str = "desc",
) -> str:
    """Lists all available media files from storage."""
    try:
        logging.info(
            "Listing available media files with metadata: %s, sort_by: %s, sort_order: %s",
            include_metadata,
            sort_by,
            sort_order,
        )
        all_files = services.storage_service.list_all_files()
        logging.debug("Found %d total files in storage.", len(all_files))

        media_files = await categorize_and_enrich_files(
            services.storage_service, all_files, include_metadata
        )
        logging.debug(
            "Categorized files: %d videos, %d audios.",
            len(media_files["videos"]),
            len(media_files["audios"]),
        )

        if include_metadata:
            try:
                logging.debug("Sorting media files by '%s' in '%s' order.", sort_by, sort_order)
                media_files = sort_media_files(media_files, sort_by, sort_order)
            except ValueError as e:
                logging.error("Failed to sort media files: %s", e)
                return json.dumps({"error": str(e)})

        return json.dumps(
            {
                "videos": media_files["videos"],
                "audios": media_files["audios"],
                "total_video_count": len(media_files["videos"]),
                "total_audio_count": len(media_files["audios"]),
                "total_count": len(all_files),
            }
        )
    except MinioServiceError as e:
        logging.exception("Failed to list media files: %s", e)
        return json.dumps({"error": f"Failed to list media files: {str(e)}"})


async def read_edit_script(script_file_name: str = "edit.sh") -> str:
    """Reads the content of the edit script."""
    temp_path = None
    try:
        object_name = f"scripts/{script_file_name}"
        logging.info("Reading script: '%s'", object_name)
        temp_path = await asyncio.to_thread(
            services.storage_service.download_file_to_temp, object_name
        )
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()
        logging.debug("Successfully read %d bytes from '%s'", len(content), object_name)
        return json.dumps({"script_content": content})
    except (MinioServiceError, OSError) as e:
        logging.exception("Failed to read script '%s': %s", script_file_name, e)
        return json.dumps({"error": f"Failed to read script: {str(e)}"})
    finally:
        if temp_path:
            cleanup_temp_files([temp_path])


async def modify_edit_script(script_content: str, script_file_name: str = "edit.sh") -> str:
    """Modifies the content of the edit script."""
    try:
        object_name = f"scripts/{script_file_name}"
        logging.info("Modifying script: '%s'", object_name)
        await asyncio.to_thread(
            services.storage_service.upload_file_from_bytes,
            script_content.encode("utf-8"),
            object_name,
            "text/plain",
        )
        bytes_written = len(script_content.encode("utf-8"))
        logging.info(
            "Successfully wrote %d bytes to '%s'",
            bytes_written,
            script_file_name,
        )
        return json.dumps(
            {
                "success": True,
                "message": (
                    f"{script_file_name} script updated successfully "
                    f"({bytes_written} bytes written)"
                ),
            }
        )
    except MinioServiceError as e:
        logging.exception("Failed to update script '%s': %s", script_file_name, e)
        return json.dumps({"error": f"Failed to update {script_file_name} script: {str(e)}"})


async def execute_edit_script(
    input_file_names: List[str],
    output_file_name: str = "output.mp4",
    script_file_name: str = "edit.sh",
) -> str:
    """Executes the edit script with the given files."""
    temp_files = []
    try:
        script_object_name = f"scripts/{script_file_name}"
        logging.info(
            "Executing script '%s' with input files: %s", script_file_name, input_file_names
        )
        if not services.storage_service.file_exists(script_object_name):
            logging.error("Script '%s' not found in storage.", script_object_name)
            return json.dumps({"success": False, "error": f"{script_file_name} not found"})

        logging.debug("Downloading script '%s' to a temporary file...", script_object_name)
        temp_script_path = await asyncio.to_thread(
            services.storage_service.download_file_to_temp, script_object_name
        )
        os.chmod(temp_script_path, 0o755)
        temp_files.append(temp_script_path)

        # Download input files in parallel
        download_tasks = []
        for input_file_name in input_file_names:
            input_object_name = f"videos/{input_file_name}"
            logging.debug("Checking input file '%s'...", input_object_name)
            if not services.storage_service.file_exists(input_object_name):
                logging.error("Input file '%s' not found.", input_object_name)
                return json.dumps(
                    {"success": False, "error": f"Input file {input_file_name} not found"}
                )
            download_tasks.append(
                asyncio.to_thread(services.storage_service.download_file_to_temp, input_object_name)
            )

        temp_input_paths = await asyncio.gather(*download_tasks)
        temp_files.extend(temp_input_paths)

        with tempfile.NamedTemporaryFile(
            suffix=f"_{output_file_name}", delete=False
        ) as temp_output:
            temp_output_path = temp_output.name
        temp_files.append(temp_output_path)
        logging.debug("Created temporary output file at '%s'", temp_output_path)

        cmd = ["bash", temp_script_path] + temp_files[1:-1] + [temp_output_path]
        logging.debug("Executing command: %s", " ".join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        decoded_stdout = stdout.decode()
        decoded_stderr = stderr.decode()

        if process.returncode != 0:
            logging.error(
                "Script execution failed with return code %d: %s",
                process.returncode,
                decoded_stderr,
            )
            return json.dumps(
                {
                    "success": False,
                    "error": "Script execution failed with a non-zero exit code.",
                    "stdout": decoded_stdout,
                    "stderr": decoded_stderr,
                }
            )

        if not os.path.exists(temp_output_path) or os.path.getsize(temp_output_path) == 0:
            logging.error(
                "Script executed but output file was not created or is empty. stderr: %s",
                decoded_stderr,
            )
            return json.dumps(
                {
                    "success": False,
                    "error": "Script executed but output file was not created or is empty",
                    "stdout": decoded_stdout,
                    "stderr": decoded_stderr,
                }
            )

        result_object_name = f"videos/{output_file_name}"
        logging.debug("Uploading result to '%s'...", result_object_name)
        await asyncio.to_thread(
            services.storage_service.upload_file_from_path,
            temp_output_path,
            result_object_name,
            "video/mp4",
        )
        logging.info("Successfully executed script and uploaded result.")
        return json.dumps(
            {
                "success": True,
                "stdout": decoded_stdout,
                "stderr": decoded_stderr,
                "output_file": output_file_name,
                "output_object": result_object_name,
            }
        )

    except (MinioServiceError, OSError) as e:
        logging.exception("Failed to execute script '%s': %s", script_file_name, e)
        return json.dumps({"success": False, "error": f"Failed to execute script: {str(e)}"})

    finally:
        cleanup_temp_files(temp_files)
        logging.debug("Cleaned up %d temporary files.", len(temp_files))
