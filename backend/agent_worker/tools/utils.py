"""Utility functions for the agent tools."""

import asyncio
import os
from typing import Any, Dict, List

from interfaces.storage_service_interface import StorageService
from logging_config import get_logger
from services.minio_storage_service import MinioServiceError

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv")
AUDIO_EXTENSIONS = (".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma")


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
    """Categorizes files into videos and audios, optionally fetching metadata."""
    video_files: List[Any] = []
    audio_files: List[Any] = []
    logger = get_logger(__name__)

    for file_path in files:
        base_filename = os.path.basename(file_path)

        if file_path.lower().endswith(VIDEO_EXTENSIONS):
            target_list = video_files
        elif file_path.lower().endswith(AUDIO_EXTENSIONS):
            target_list = audio_files
        else:
            continue

        if include_metadata:
            try:
                metadata = await get_file_metadata(storage_service, file_path)
                target_list.append(metadata)
            except MinioServiceError as e:
                logger.warning("Could not get metadata for %s: %s", base_filename, e)
                target_list.append({"filename": base_filename, "error": str(e)})
        else:
            target_list.append(base_filename)

    return {"videos": video_files, "audios": audio_files}


def sort_media_files(
    media: Dict[str, List[Any]], sort_by: str, sort_order: str
) -> Dict[str, List[Any]]:
    """Sorts video and audio files by a given key."""
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

    media["videos"].sort(key=sort_key, reverse=reverse)
    media["audios"].sort(key=sort_key, reverse=reverse)

    return media


def cleanup_temp_files(temp_files: List[str]):
    """Deletes a list of temporary files."""
    logger = get_logger(__name__)
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except OSError as e:
            logger.warning("Failed to delete temp file %s: %s", temp_file, e)
