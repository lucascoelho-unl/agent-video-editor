import asyncio
import json
import logging
import os
import time

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


async def list_videos(directory: str = "videos") -> str:
    """
    Lists all videos in a specified directory.
    """
    return json.dumps({"videos": os.listdir(f"/app/storage/{directory}")})


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
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

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
