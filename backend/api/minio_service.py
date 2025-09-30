"""
MinIO service for handling video and audio file operations with S3-compatible storage.
"""

import io
import os

from fastapi import HTTPException, UploadFile
from minio import Minio
from minio.error import S3Error

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "video-storage")

# File type validation
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"}
ALLOWED_EXTENSIONS = ALLOWED_VIDEO_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,  # Set to True for HTTPS
)


def ensure_bucket_exists():
    """Ensure the bucket exists, create it if it doesn't."""
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
            minio_client.make_bucket(MINIO_BUCKET_NAME)
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bucket: {str(e)}") from e


def save_media_file(file: UploadFile) -> dict:
    """
    Saves an uploaded video or audio file to MinIO storage.
    """
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check if file already exists
    try:
        minio_client.stat_object(MINIO_BUCKET_NAME, f"videos/{file.filename}")
        raise HTTPException(status_code=409, detail="File with the same name already exists")
    except S3Error as e:
        if e.code != "NoSuchKey":
            raise HTTPException(
                status_code=500, detail=f"Error checking file existence: {str(e)}"
            ) from e

    # Ensure bucket exists
    ensure_bucket_exists()

    # Upload file to MinIO
    try:
        file_data = file.file.read()
        file.file.seek(0)  # Reset file pointer

        minio_client.put_object(
            MINIO_BUCKET_NAME,
            f"videos/{file.filename}",
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type or "application/octet-stream",
        )

        file_type = "video" if file_extension in ALLOWED_VIDEO_EXTENSIONS else "audio"
        return {"message": f"Successfully uploaded {file_type} file: {file.filename}"}

    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}") from e


def delete_media_file(filename: str, source: str = "videos") -> dict:
    """
    Deletes a video or audio file from MinIO storage.
    """
    # Map source to object prefix
    source_map = {
        "videos": "videos/",
        "results": "results/",
        "temp": "temp/",
    }

    if source not in source_map:
        raise HTTPException(status_code=400, detail="Invalid source")

    object_name = f"{source_map[source]}{filename}"

    try:
        minio_client.remove_object(MINIO_BUCKET_NAME, object_name)
        return {"message": f"Successfully deleted {filename}"}
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(status_code=404, detail="Media file not found") from e
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}") from e


def list_media_files() -> dict:
    """
    Lists all video and audio files in MinIO storage.
    """
    result = {"videos": [], "audio": [], "results": [], "temp": []}

    try:
        # List objects in the bucket
        objects = minio_client.list_objects(MINIO_BUCKET_NAME, recursive=True)

        for obj in objects:
            # Extract directory and filename
            path_parts = obj.object_name.split("/")
            if len(path_parts) < 2:
                continue

            directory = path_parts[0]
            filename = path_parts[-1]

            # Skip if it's a directory marker
            if not filename:
                continue

            file_extension = os.path.splitext(filename)[1].lower()

            if directory == "videos":
                if file_extension in ALLOWED_VIDEO_EXTENSIONS:
                    result["videos"].append(filename)
                elif file_extension in ALLOWED_AUDIO_EXTENSIONS:
                    result["audio"].append(filename)
            elif directory == "results":
                result["results"].append(filename)
            elif directory == "temp":
                result["temp"].append(filename)

    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}") from e

    return result


def get_media_file(filename: str, source: str = "videos") -> bytes:
    """
    Downloads a media file from MinIO storage.
    """
    # Map source to object prefix
    source_map = {
        "videos": "videos/",
        "results": "results/",
        "temp": "temp/",
    }

    if source not in source_map:
        raise HTTPException(status_code=400, detail="Invalid source")

    object_name = f"{source_map[source]}{filename}"

    try:
        response = minio_client.get_object(MINIO_BUCKET_NAME, object_name)
        return response.read()
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(status_code=404, detail="Media file not found") from e
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}") from e


def save_result_file(file_data: bytes, filename: str) -> dict:
    """
    Saves a result file to MinIO storage.
    """
    ensure_bucket_exists()

    try:
        minio_client.put_object(
            MINIO_BUCKET_NAME,
            f"results/{filename}",
            io.BytesIO(file_data),
            length=len(file_data),
            content_type="video/mp4",
        )
        return {"message": f"Successfully saved result file: {filename}"}
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to save result file: {str(e)}") from e


def get_file_url(filename: str, source: str = "videos", expires_in_seconds: int = 3600) -> str:
    """
    Generates a presigned URL for downloading a file from MinIO.
    """
    # Map source to object prefix
    source_map = {
        "videos": "videos/",
        "results": "results/",
        "temp": "temp/",
    }

    if source not in source_map:
        raise HTTPException(status_code=400, detail="Invalid source")

    object_name = f"{source_map[source]}{filename}"

    try:
        url = minio_client.presigned_get_object(
            MINIO_BUCKET_NAME, object_name, expires=expires_in_seconds
        )
        return url
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(status_code=404, detail="Media file not found") from e
        raise HTTPException(status_code=500, detail=f"Failed to generate URL: {str(e)}") from e
