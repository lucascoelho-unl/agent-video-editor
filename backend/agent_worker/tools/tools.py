"""
Tools for media analysis and video editing.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime
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
    input_file_names: List[str],
    output_file_name: str = "output.mp4",
    script_file_name: str = "edit.sh",
    timeout_seconds: int = 300,  # 5 minutes default timeout
) -> str:
    """Executes the edit script with the given files."""
    temp_files = []
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    try:
        script_object_name = f"scripts/{script_file_name}"
        logging.info(
            "[%s] Executing script '%s' with input files: %s (timeout: %ds)",
            timestamp,
            script_file_name,
            input_file_names,
            timeout_seconds,
        )

        # Check if script exists with timeout
        try:
            script_exists = await asyncio.wait_for(
                asyncio.to_thread(services.storage_service.file_exists, script_object_name),
                timeout=30.0,  # 30 second timeout for file existence check
            )
        except asyncio.TimeoutError:
            logging.error("Timeout checking if script '%s' exists", script_object_name)
            return json.dumps({"success": False, "error": "Timeout checking script existence"})

        if not script_exists:
            logging.error("Script '%s' not found in storage.", script_object_name)
            return json.dumps({"success": False, "error": f"{script_file_name} not found"})

        # Download script with timeout
        logging.debug("Downloading script '%s' to a temporary file...", script_object_name)
        script_download_start = time.time()
        try:
            temp_script_path = await asyncio.wait_for(
                asyncio.to_thread(
                    services.storage_service.download_file_to_temp, script_object_name
                ),
                timeout=60.0,  # 60 second timeout for script download
            )
        except asyncio.TimeoutError:
            logging.error("Timeout downloading script '%s'", script_object_name)
            return json.dumps({"success": False, "error": "Timeout downloading script"})

        os.chmod(temp_script_path, 0o755)
        temp_files.append(temp_script_path)
        script_download_duration = time.time() - script_download_start
        logging.info(
            "[%s] Script download completed in %.3f seconds",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            script_download_duration,
        )

        # Download input files in parallel with timeout
        download_tasks = []
        for input_file_name in input_file_names:
            input_object_name = f"videos/{input_file_name}"
            logging.debug("Checking input file '%s'...", input_object_name)

            # Check file existence with timeout
            try:
                file_exists = await asyncio.wait_for(
                    asyncio.to_thread(services.storage_service.file_exists, input_object_name),
                    timeout=30.0,
                )
            except asyncio.TimeoutError:
                logging.error("Timeout checking if input file '%s' exists", input_object_name)
                return json.dumps(
                    {"success": False, "error": f"Timeout checking input file {input_file_name}"}
                )

            if not file_exists:
                logging.error("Input file '%s' not found.", input_object_name)
                return json.dumps(
                    {"success": False, "error": f"Input file {input_file_name} not found"}
                )

            # Create download task with timeout
            download_task = asyncio.wait_for(
                asyncio.to_thread(
                    services.storage_service.download_file_to_temp, input_object_name
                ),
                timeout=120.0,  # 2 minutes per file download
            )
            download_tasks.append(download_task)

        input_download_start = time.time()
        try:
            temp_input_paths = await asyncio.gather(*download_tasks)
        except asyncio.TimeoutError:
            logging.error("Timeout downloading input files")
            return json.dumps({"success": False, "error": "Timeout downloading input files"})

        temp_files.extend(temp_input_paths)
        input_download_duration = time.time() - input_download_start
        logging.info(
            "[%s] Input files download completed in %.3f seconds",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            input_download_duration,
        )

        with tempfile.NamedTemporaryFile(
            suffix=f"_{output_file_name}", delete=False
        ) as temp_output:
            temp_output_path = temp_output.name
        temp_files.append(temp_output_path)
        logging.debug("Created temporary output file at '%s'", temp_output_path)

        cmd = ["bash", temp_script_path] + temp_files[1:-1] + [temp_output_path]
        logging.debug("Executing command: %s", " ".join(cmd))

        script_exec_start = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,  # Use the main timeout for script execution
            )
        except asyncio.TimeoutError:
            logging.error("Script execution timed out after %d seconds", timeout_seconds)
            # Try to kill the process if it's still running
            if process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except (OSError, ProcessLookupError) as e:
                    logging.warning("Failed to kill timed out process: %s", e)
            return json.dumps(
                {
                    "success": False,
                    "error": f"Script execution timed out after {timeout_seconds} seconds",
                }
            )

        script_exec_duration = time.time() - script_exec_start
        logging.info(
            "[%s] Script execution completed in %.3f seconds",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            script_exec_duration,
        )

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

        upload_start = time.time()
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    services.storage_service.upload_file_from_path,
                    temp_output_path,
                    result_object_name,
                    "video/mp4",
                ),
                timeout=120.0,  # 2 minutes for upload
            )
        except asyncio.TimeoutError:
            logging.error("Timeout uploading result file")
            return json.dumps({"success": False, "error": "Timeout uploading result file"})

        upload_duration = time.time() - upload_start
        logging.info(
            "[%s] Result upload completed in %.3f seconds",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            upload_duration,
        )

        total_duration = time.time() - start_time
        logging.info(
            "[%s] Total execute_edit_script completed in %.3f seconds",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            total_duration,
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
