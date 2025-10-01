"""Gemini service for handling language model operations."""

import asyncio
import json
import logging
import os
import re
import uuid

import google.generativeai as genai
from google.api_core import exceptions
from interfaces.llm_service_interface import LLMService
from interfaces.storage_service_interface import StorageService


class GeminiService(LLMService):
    """Implementation of the LLMService using Google's Gemini."""

    def __init__(self, storage_service: StorageService):
        """Initializes the GeminiService."""
        self.storage_service = storage_service

        self.model_name = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
        if not self.model_name:
            logging.critical("AGENT_MODEL not found in environment variables")
            raise ValueError("AGENT_MODEL not found in environment variables")

        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not self.gemini_api_key:
            logging.critical("GOOGLE_API_KEY not found in environment variables")
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        genai.configure(api_key=self.gemini_api_key)
        logging.info("GeminiService initialized with model: %s", self.model_name)

    async def analyze_media_files(
        self, media_filenames: list[str], prompt: str, source_directory: str = "videos"
    ) -> str:
        """Analyzes media files with a given prompt using the Gemini model."""
        uploaded_files = []
        temp_files = []
        not_found_files = []
        try:

            async def _upload_and_process(filename):
                object_name = f"{source_directory}/{filename}"
                if not self.storage_service.file_exists(object_name):
                    logging.warning("Media file not found in storage: %s", object_name)
                    not_found_files.append(filename)
                    return None

                logging.info("Downloading '%s' from storage...", filename)
                temp_path = await asyncio.to_thread(
                    self.storage_service.download_file_to_temp, object_name
                )
                temp_files.append(temp_path)

                logging.info("Uploading '%s' to Gemini...", filename)
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
                logging.debug("Determined MIME type for '%s' as '%s'", filename, mime_type)

                base_filename, _ = os.path.splitext(filename)
                sanitized_base = re.sub(r"[^a-z0-9-]+", "-", base_filename.lower().strip()).strip(
                    "-"
                )
                if not sanitized_base:
                    sanitized_base = f"media-{uuid.uuid4()}"
                    logging.warning(
                        "Sanitized base for '%s' is empty, creating a unique name: %s",
                        filename,
                        sanitized_base,
                    )

                media_file = await asyncio.to_thread(
                    genai.upload_file,
                    name=sanitized_base,
                    display_name=filename,
                    path=temp_path,
                    mime_type=mime_type,
                )
                logging.debug("File '%s' uploaded, waiting for processing...", filename)

                while media_file.state.name == "PROCESSING":
                    await asyncio.sleep(5)
                    media_file = await asyncio.to_thread(genai.get_file, media_file.name)
                    logging.debug("Checked status of '%s': %s", filename, media_file.state.name)

                if media_file.state.name == "FAILED":
                    logging.error("Processing failed for '%s'.", filename)
                    return None

                logging.info("Successfully processed '%s'", filename)
                return media_file

            tasks = [_upload_and_process(fname) for fname in media_filenames]
            results = await asyncio.gather(*tasks)
            uploaded_files = [res for res in results if res is not None]

            if not uploaded_files:
                if not_found_files:
                    logging.warning(
                        "Analysis could not be performed because the following files"
                        " were not found: %s",
                        ", ".join(not_found_files),
                    )
                    return json.dumps(
                        {
                            "analysis": "Analysis could not be performed because"
                            f" the following files were not found: {', '.join(not_found_files)}."
                        }
                    )
                logging.error(
                    "Analysis could not be performed because no files could be processed."
                )
                return json.dumps(
                    {
                        "analysis": "Analysis could not be performed because no files"
                        " could be processed."
                    }
                )

            logging.info("Generating content with Gemini using all media files...")
            model = genai.GenerativeModel(model_name=self.model_name)
            content_to_send = [prompt] + uploaded_files
            response = await asyncio.to_thread(
                model.generate_content,
                content_to_send,
                request_options={"timeout": 1200},
            )

            logging.info("Successfully analyzed media files with Gemini.")
            return json.dumps({"analysis": response.text})

        except (OSError, ValueError, exceptions.GoogleAPICallError) as e:
            logging.exception("An error occurred during Gemini analysis: %s", e)
            return json.dumps({"error": str(e)})

        finally:
            if uploaded_files:
                logging.debug("Deleting Gemini files...")
                delete_tasks = [
                    asyncio.to_thread(genai.delete_file, f.name) for f in uploaded_files
                ]
                await asyncio.gather(*delete_tasks)
                logging.info("Successfully deleted all Gemini files.")

            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
