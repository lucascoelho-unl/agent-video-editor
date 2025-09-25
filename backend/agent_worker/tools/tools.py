import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime

import dotenv
import google.generativeai as genai

dotenv.load_dotenv(dotenv_path="agent/.env")
gemini_api_key = os.environ.get("GOOGLE_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=gemini_api_key)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def analyze_videos(
    video_filenames: list[str], prompt: str, source_directory: str = "videos"
) -> str:
    """
    Analyzes multiple video files with the Gemini API in a single call
    and returns a text-based analysis.
    """
    uploaded_files = []
    try:
        # --- UPLOAD AND PROCESS VIDEOS CONCURRENTLY ---
        async def _upload_and_process(filename):
            video_path = f"/app/storage/{source_directory}/{filename}"
            if not os.path.exists(video_path):
                logging.error(f"Video file not found: {video_path}")
                # Return None or raise an exception to signal failure
                return None

            logging.info(f"Uploading {filename} to Gemini...")
            video_file = await asyncio.to_thread(genai.upload_file, path=video_path)

            # Wait for the video to be processed
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(5)
                video_file = await asyncio.to_thread(genai.get_file, video_file.name)

            if video_file.state.name == "FAILED":
                logging.error(f"Processing failed for {filename}")
                return None

            logging.info(f"Successfully processed {filename}")
            return video_file

        # Create and run upload tasks in parallel
        tasks = [_upload_and_process(fname) for fname in video_filenames]
        results = await asyncio.gather(*tasks)

        # Filter out any files that failed to upload/process
        uploaded_files = [res for res in results if res is not None]
        if not uploaded_files:
            return json.dumps({"error": "All video uploads failed or were not found."})

        # --- GENERATE CONTENT WITH ALL VIDEOS ---
        logging.info("Generating content with Gemini using all videos...")
        model = genai.GenerativeModel(model_name="models/gemini-2.5-pro")

        # Combine the prompt and the list of uploaded video files
        content_to_send = [prompt] + uploaded_files

        response = await asyncio.to_thread(
            model.generate_content,
            content_to_send,
            request_options={"timeout": 1200},
        )

        logging.info("Successfully analyzed videos with Gemini.")
        return json.dumps({"analysis": response.text})

    except Exception as e:
        logging.error(f"An error occurred during Gemini analysis: {e}")
        return json.dumps({"error": str(e)})

    finally:
        # --- CLEANUP: DELETE ALL UPLOADED FILES ---
        if uploaded_files:
            logging.info("Deleting Gemini files...")
            delete_tasks = [
                asyncio.to_thread(genai.delete_file, f.name) for f in uploaded_files
            ]
            await asyncio.gather(*delete_tasks)
            logging.info("Successfully deleted all Gemini files.")


async def list_available_videos(
    include_metadata: bool = False,
    sort_by: str = "creation_timestamp",
    sort_order: str = "desc",
) -> str:
    """
    Lists all video files available in the storage directory.
    Optionally includes metadata and sorts by a specified field.
    """
    try:
        video_dir = "/app/storage/videos"
        if not os.path.exists(video_dir):
            return json.dumps({"videos": []})

        video_files = []
        for file in os.listdir(video_dir):
            if file.lower().endswith(
                (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv")
            ):
                if include_metadata:
                    file_path = os.path.join(video_dir, file)
                    stat = os.stat(file_path)

                    # Get file metadata
                    metadata = {
                        "filename": file,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "creation_time": datetime.fromtimestamp(
                            stat.st_ctime
                        ).isoformat(),
                        "modification_time": datetime.fromtimestamp(
                            stat.st_mtime
                        ).isoformat(),
                        "access_time": datetime.fromtimestamp(
                            stat.st_atime
                        ).isoformat(),
                        "creation_timestamp": stat.st_ctime,
                        "modification_timestamp": stat.st_mtime,
                        "access_timestamp": stat.st_atime,
                    }
                    video_files.append(metadata)
                else:
                    # Simple filename only
                    video_files.append(file)

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

        if include_metadata:
            return json.dumps(
                {
                    "videos": video_files,
                    "total_count": len(video_files),
                    "sorted_by": sort_by if sort_by else "None",
                    "sort_order": sort_order if sort_by else "None",
                }
            )
        else:
            return json.dumps({"videos": video_files})
    except Exception as e:
        return json.dumps({"error": f"Failed to list videos: {str(e)}"})


async def read_edit_script() -> str:
    """
    Reads the current content of the edit.sh script.
    """
    try:
        script_path = "/app/edit.sh"
        with open(script_path, "r") as f:
            content = f.read()
        return json.dumps({"script_content": content})
    except FileNotFoundError:
        return json.dumps({"error": "edit.sh script not found"})
    except Exception as e:
        return json.dumps({"error": f"Failed to read script: {str(e)}"})


async def modify_edit_script(script_content: str) -> str:
    """
    Replace the entire edit.sh script with new content.
    """
    try:
        script_path = "/app/edit.sh"

        # Write the new script content
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        bytes_written = len(script_content.encode("utf-8"))

        return json.dumps(
            {
                "success": True,
                "message": f"edit.sh script updated successfully ({bytes_written} bytes written)",
            }
        )

    except Exception as e:
        return json.dumps({"error": f"Failed to update edit.sh script: {str(e)}"})


async def execute_edit_script(
    input_files: list[str], output_file: str = "output.mp4"
) -> str:
    """
    Executes the edit.sh script asynchronously with the specified files.
    The script is expected to take input files as arguments, followed by the output file.
    """
    script_path = "/app/edit.sh"
    # Note: The script should be made executable during deployment, not here.
    # e.g., in a Dockerfile: RUN chmod +x /app/edit.sh

    if not os.path.exists(script_path):
        return json.dumps({"success": False, "error": "edit.sh not found"})

    try:
        # Build the command
        cmd = ["bash", script_path] + input_files + [output_file]

        # Execute the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/app/storage/videos",
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
    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"Failed to execute script: {str(e)}"}
        )
