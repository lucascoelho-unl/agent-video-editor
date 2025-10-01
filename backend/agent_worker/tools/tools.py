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
    sort_by: str = "last_modified",
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
    input_files: list[str],
    output_file: str,
    script_file_name: str = "edit.sh",
) -> str:
    """
    Executes a script asynchronously with specified files from storage.
    Downloads inputs and the script, runs the script, and uploads the output.
    """
    logging.info(
        "Executing edit script '%s' with inputs %s to output '%s'",
        script_file_name,
        input_files,
        output_file,
    )
    temp_dir = tempfile.mkdtemp()
    logging.debug("Created temporary directory: %s", temp_dir)
    local_input_paths = []
    local_script_path = None
    local_output_path = os.path.join(temp_dir, output_file)

    try:
        # Download input files
        logging.info("Downloading input files...")
        for file_name in input_files:
            object_name = f"videos/{file_name}"
            local_path = os.path.join(temp_dir, file_name)
            logging.debug("Downloading '%s' to '%s'", object_name, local_path)
            await asyncio.to_thread(
                services.storage_service.download_file_to_temp, object_name, local_path
            )
            local_input_paths.append(local_path)
        logging.info("Downloaded %d input files.", len(local_input_paths))

        # Download and prepare the script
        logging.info("Downloading script '%s'...", script_file_name)
        script_object_name = f"scripts/{script_file_name}"
        local_script_path = os.path.join(temp_dir, script_file_name)
        await asyncio.to_thread(
            services.storage_service.download_file_to_temp,
            script_object_name,
            local_script_path,
        )
        logging.debug("Downloaded script to '%s'", local_script_path)
        os.chmod(local_script_path, 0o755)  # Make script executable
        logging.debug("Made script '%s' executable.", local_script_path)

        # Execute the script
        cmd = (
            ["bash", local_script_path]
            + [os.path.basename(p) for p in local_input_paths]
            + [os.path.basename(local_output_path)]
        )
        logging.info("Executing command: %s", " ".join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logging.info("Script executed successfully. Uploading output file...")
            # Upload the output file
            output_object_name = f"videos/{output_file}"
            await asyncio.to_thread(
                services.storage_service.upload_file_from_path,
                local_output_path,
                output_object_name,
                "video/mp4",
            )
            logging.info("Successfully uploaded '%s'", output_object_name)
            return json.dumps(
                {"success": True, "output": stdout.decode(), "output_file": output_object_name}
            )
        else:
            logging.error("Script execution failed with return code %d.", process.returncode)
            logging.error("Stderr: %s", stderr.decode())
            logging.error("Stdout: %s", stdout.decode())
            return json.dumps(
                {"success": False, "error": stderr.decode(), "stdout": stdout.decode()}
            )
    except (MinioServiceError, OSError) as e:
        logging.exception("Failed to execute script due to an exception.")
        return json.dumps({"success": False, "error": f"Failed to execute script: {str(e)}"})
    finally:
        # Cleanup all temporary files
        logging.info("Cleaning up temporary files...")
        all_temp_files = (
            local_input_paths
            + ([local_script_path] if local_script_path else [])
            + [local_output_path]
        )
        cleanup_temp_files(all_temp_files)
        if os.path.exists(temp_dir):
            logging.debug("Removing temporary directory: %s", temp_dir)
            os.rmdir(temp_dir)
        logging.info("Cleanup complete.")
