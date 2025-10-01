"""Gemini service for handling language model operations."""

import asyncio
import base64
import json
import logging
import mimetypes  # Use the standard library for MIME types
import os

from google.api_core import exceptions
from interfaces.llm_service_interface import LLMService
from interfaces.storage_service_interface import StorageService
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiService(LLMService):
    """Implementation of the LLMService using Google's Gemini."""

    def __init__(self, storage_service: StorageService):
        """Initializes the GeminiService."""
        self.storage_service = storage_service

        # --- Environment Variable Setup ---
        self.model_name = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")

        if not self.model_name or not self.gemini_api_key:
            error_msg = "AGENT_MODEL or GOOGLE_API_KEY not found in environment variables."
            logging.critical(error_msg)
            raise ValueError(error_msg)

        # --- Initialize the LangChain LLM ---
        self.llm = ChatGoogleGenerativeAI(model=self.model_name, google_api_key=self.gemini_api_key)

        logging.info("GeminiService initialized with model: %s", self.model_name)

    async def analyze_media_files(
        self, media_filenames: list[str], prompt: str, source_directory: str = "videos"
    ) -> str:
        """Analyzes media files with a given prompt using the Gemini model via LangChain."""

        # --- Prepare the multimodal content for LangChain ---
        content = [{"type": "text", "text": prompt}]
        processed_files = 0
        not_found_files = []

        for filename in media_filenames:
            temp_path = None
            try:
                object_name = f"{source_directory}/{filename}"
                if not self.storage_service.file_exists(object_name):
                    logging.warning("Media file not found in storage: %s", object_name)
                    not_found_files.append(filename)
                    continue

                logging.info("Downloading '%s' from storage...", filename)
                temp_path = await asyncio.to_thread(
                    self.storage_service.download_file_to_temp, object_name
                )

                # --- Read file, encode, and add to content list ---
                with open(temp_path, "rb") as media_file:
                    encoded_data = base64.b64encode(media_file.read()).decode("utf-8")

                mime_type, _ = mimetypes.guess_type(temp_path)
                if not mime_type:
                    mime_type = "application/octet-stream"  # Default fallback

                logging.info("Adding '%s' to the request with MIME type '%s'", filename, mime_type)

                if mime_type.startswith("image/"):
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": f"data:{mime_type};base64,{encoded_data}",
                        }
                    )
                else:  # For video, audio, etc.
                    content.append(
                        {
                            "type": "media",
                            "data": encoded_data,
                            "mime_type": mime_type,
                        }
                    )
                processed_files += 1

            finally:
                # Clean up the temporary file immediately
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)

        # --- Handle cases where no files could be processed ---
        if processed_files == 0:
            error_msg = "Analysis could not be performed. "
            if not_found_files:
                error_msg += f"The following files were not found: {', '.join(not_found_files)}."
            else:
                error_msg += "No media files could be processed."
            logging.error(error_msg)
            return json.dumps({"error": error_msg})

        # --- Invoke the model with all content at once ---
        try:
            logging.info(
                "Generating content with LangChain Gemini using %d media file(s)...",
                processed_files,
            )
            message = HumanMessage(content=content)
            response = await self.llm.ainvoke([message], config={"request_timeout": 1200})

            logging.info("Successfully analyzed media files.")
            return json.dumps({"analysis": response.content})

        except exceptions.GoogleAPICallError as e:
            logging.exception("A Google API error occurred during analysis: %s", e)
            return json.dumps({"error": f"Google API Error: {e}"})
        except Exception as e:
            logging.exception("An unexpected error occurred: %s", e)
            return json.dumps({"error": str(e)})
