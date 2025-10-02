"""Utility functions for the agent tools."""

import asyncio
import logging
import os
from typing import Any, Dict, List

from interfaces.storage_service_interface import StorageService
from services.minio_storage_service import MinioServiceError

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv")
AUDIO_EXTENSIONS = (".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff")


async def get_file_metadata(storage_service: StorageService, object_name: str) -> Dict[str, Any]:
    """Fetches and formats metadata for a given file."""
    file_info = await asyncio.to_thread(storage_service.get_file_info, object_name)
    return {
        "filename": os.path.basename(object_name),
        "size_bytes": file_info["size"],
        "size_mb": round(file_info["size"] / (1024 * 1024), 2),
        "last_modified": file_info["last_modified"].isoformat(),
        "content_type": file_info["content_type"],
        "etag": file_info["etag"],
    }


async def categorize_and_enrich_files(
    storage_service: StorageService,
    files: List[str],
    include_metadata: bool,
) -> Dict[str, List[Any]]:
    """Categorizes files into videos, audios, and images, optionally fetching metadata."""
    categorized_files: Dict[str, List[Any]] = {"videos": [], "audios": [], "images": []}

    async def process_file(file_path: str):
        """Helper to process a single file."""
        base_filename = os.path.basename(file_path)
        file_ext = os.path.splitext(base_filename)[1].lower()

        media_info: Any
        if include_metadata:
            try:
                media_info = await get_file_metadata(storage_service, file_path)
            except MinioServiceError as e:
                logging.warning("Could not get metadata for %s: %s", base_filename, e)
                media_info = {"filename": base_filename, "error": str(e)}
        else:
            media_info = base_filename

        if file_ext in VIDEO_EXTENSIONS:
            categorized_files["videos"].append(media_info)
        elif file_ext in AUDIO_EXTENSIONS:
            categorized_files["audios"].append(media_info)
        elif file_ext in IMAGE_EXTENSIONS:
            categorized_files["images"].append(media_info)

    await asyncio.gather(*(process_file(file) for file in files))
    return categorized_files


def sort_media_files(
    media: Dict[str, List[Any]], sort_by: str, sort_order: str
) -> Dict[str, List[Any]]:
    """Sorts each category of media files by a given key."""
    if not sort_by:
        return media

    valid_sort_fields = ["filename", "size_bytes", "last_modified"]
    if sort_by not in valid_sort_fields:
        raise ValueError(f"Invalid sort_by field: {sort_by}. Valid fields: {valid_sort_fields}")

    reverse = sort_order.lower() == "desc"

    def sort_key(item: Any) -> Any:
        if isinstance(item, dict):
            return item.get(sort_by, 0)
        return item

    for category in ["videos", "audios", "images"]:
        if category in media:
            media[category].sort(key=sort_key, reverse=reverse)

    return media


def cleanup_temp_files(temp_files: List[str]):
    """Deletes a list of temporary files."""
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except OSError as e:
            logging.warning("Failed to delete temp file %s: %s", temp_file, e)
