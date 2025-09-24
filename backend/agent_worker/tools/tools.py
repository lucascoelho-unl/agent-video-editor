import asyncio
import json
import logging
import os
import tempfile
import time

import dotenv
import google.generativeai as genai
from moviepy import VideoFileClip, concatenate_videoclips

dotenv.load_dotenv(dotenv_path="agent/.env")
gemini_api_key = os.environ.get("GOOGLE_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=gemini_api_key)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def list_videos(directory: str = "videos") -> str:
    """
    Lists all videos in a specified directory within the /app/storage volume.
    """
    storage_path = f"/app/storage/{directory}"
    if not os.path.isdir(storage_path):
        return json.dumps({"error": f"Directory not found: {storage_path}"})

    videos = [
        f
        for f in os.listdir(storage_path)
        if os.path.isfile(os.path.join(storage_path, f))
    ]
    return json.dumps({"videos": videos})


async def delete_videos(video_filenames: list, directory: str = "videos") -> str:
    """
    Deletes one or more videos from a specified directory within the /app/storage volume.
    """
    storage_path = f"/app/storage/{directory}"
    deleted_files = []
    errors = []

    async def delete_file(filename):
        file_path = os.path.join(storage_path, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files.append(filename)
                logging.info(f"Successfully deleted {file_path}")
            except Exception as e:
                errors.append({"filename": filename, "error": str(e)})
                logging.error(f"Error deleting {file_path}: {e}")
        else:
            errors.append({"filename": filename, "error": "File not found"})
            logging.warning(f"File not found for deletion: {file_path}")

    await asyncio.gather(*[delete_file(filename) for filename in video_filenames])
    return json.dumps({"deleted": deleted_files, "errors": errors})


async def merge_videos(
    video_filenames: list, output_filename: str, directory: str = "videos"
) -> str:
    """
    Merges multiple videos from a specified directory into a single file.
    """
    storage_path = f"/app/storage/{directory}"
    video_paths = [os.path.join(storage_path, f) for f in video_filenames]
    output_path = os.path.join(storage_path, output_filename)

    try:
        loop = asyncio.get_running_loop()
        clips = await loop.run_in_executor(
            None, lambda: [VideoFileClip(path) for path in video_paths]
        )
        final_clip = concatenate_videoclips(clips)
        await loop.run_in_executor(None, final_clip.write_videofile, output_path)
        logging.info(f"Successfully merged videos into {output_filename}")
        return json.dumps(
            {
                "success": True,
                "message": f"Successfully merged videos into {output_filename}",
            }
        )
    except Exception as e:
        logging.error(f"Error merging videos: {e}")
        return json.dumps({"error": str(e)})


async def analyze_video_with_gemini(
    video_filename: str, prompt: str, source_directory: str = "videos"
) -> str:
    """
    Analyzes a video file with the Gemini API and returns a text-based analysis.
    """
    video_path = f"/app/storage/{source_directory}/{video_filename}"

    if not os.path.exists(video_path):
        logging.error(f"Video file not found at: {video_path}")
        return json.dumps({"error": f"Video file not found at: {video_path}"})

    video_file = None
    try:
        logging.info(f"Uploading {video_filename} to Gemini...")
        video_file = await asyncio.to_thread(genai.upload_file, path=video_path)

        processing_start_time = time.time()
        processing_timeout = 600
        while video_file.state.name == "PROCESSING":
            if time.time() - processing_start_time > processing_timeout:
                logging.error("Timeout: Video processing took too long.")
                return json.dumps({"error": "Timeout: Video processing took too long."})
            await asyncio.sleep(10)
            try:
                video_file = await asyncio.to_thread(genai.get_file, video_file.name)
            except Exception as e:
                logging.warning(f"Error checking video status: {e}")

        if video_file.state.name == "FAILED":
            logging.error(f"Video processing failed: {video_file.state.name}")
            return json.dumps(
                {"error": f"Video processing failed: {video_file.state.name}"}
            )

        logging.info("Generating content with Gemini...")
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")
        response = await asyncio.to_thread(
            model.generate_content,
            [video_file, prompt],
            request_options={"timeout": 1200},
        )

        logging.info("Successfully analyzed video with Gemini.")
        return json.dumps({"analysis": response.text})

    except Exception as e:
        logging.error(f"An error occurred during Gemini analysis: {e}")
        return json.dumps({"error": str(e)})
    finally:
        if video_file:
            try:
                await asyncio.to_thread(genai.delete_file, video_file.name)
                logging.info(f"Successfully deleted Gemini file {video_file.name}")
            except Exception as e:
                logging.error(f"Error deleting Gemini file {video_file.name}: {e}")
