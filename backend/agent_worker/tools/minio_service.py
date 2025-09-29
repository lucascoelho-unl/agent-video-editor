"""
MinIO service for the agent worker to handle video and audio file operations with S3-compatible storage.
"""

import io
import os
import tempfile

import dotenv
from minio import Minio
from minio.error import S3Error

# Load environment variables
dotenv.load_dotenv(dotenv_path="agent/.env")

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "video-storage")


class MinioServiceError(Exception):
    """Custom exception for MinIO service errors."""


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
        raise MinioServiceError(f"Failed to create bucket: {str(e)}") from e


def download_file_to_temp(object_name: str) -> str:
    """
    Downloads a file from MinIO to a temporary file and returns the path.
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(object_name)[1]
        )
        temp_path = temp_file.name
        temp_file.close()

        # Download the file from MinIO
        minio_client.fget_object(MINIO_BUCKET_NAME, object_name, temp_path)

        return temp_path
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise MinioServiceError(f"File not found: {object_name}") from e
        raise MinioServiceError(f"Failed to download file: {str(e)}") from e


def upload_file_from_path(
    local_path: str, object_name: str, content_type: str = "application/octet-stream"
) -> str:
    """
    Uploads a local file to MinIO storage.
    """
    try:
        ensure_bucket_exists()

        minio_client.fput_object(
            MINIO_BUCKET_NAME, object_name, local_path, content_type=content_type
        )

        return f"Successfully uploaded {object_name}"
    except S3Error as e:
        raise MinioServiceError(f"Failed to upload file: {str(e)}") from e


def upload_file_from_bytes(
    file_data: bytes, object_name: str, content_type: str = "application/octet-stream"
) -> str:
    """
    Uploads file data from bytes to MinIO storage.
    """
    try:
        ensure_bucket_exists()

        minio_client.put_object(
            MINIO_BUCKET_NAME,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type,
        )

        return f"Successfully uploaded {object_name}"
    except S3Error as e:
        raise MinioServiceError(f"Failed to upload file: {str(e)}") from e


def list_files_in_directory(directory: str = "videos") -> list[str]:
    """
    Lists all files in a specific directory/prefix in MinIO.
    """
    try:
        files = []
        objects = minio_client.list_objects(
            MINIO_BUCKET_NAME, prefix=f"{directory}/", recursive=True
        )

        for obj in objects:
            # Extract just the filename from the object path
            filename = obj.object_name.split("/")[-1]
            if filename:  # Skip empty filenames (directory markers)
                files.append(filename)

        return files
    except S3Error as e:
        raise MinioServiceError(f"Failed to list files: {str(e)}") from e


def file_exists(object_name: str) -> bool:
    """
    Checks if a file exists in MinIO storage.
    """
    try:
        minio_client.stat_object(MINIO_BUCKET_NAME, object_name)
        return True
    except S3Error as e:
        if e.code == "NoSuchKey":
            return False
        raise MinioServiceError(f"Error checking file existence: {str(e)}") from e


def delete_file(object_name: str) -> str:
    """
    Deletes a file from MinIO storage.
    """
    try:
        minio_client.remove_object(MINIO_BUCKET_NAME, object_name)
        return f"Successfully deleted {object_name}"
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise MinioServiceError(f"File not found: {object_name}") from e
        raise MinioServiceError(f"Failed to delete file: {str(e)}") from e


def get_file_info(object_name: str) -> dict:
    """
    Gets file information from MinIO storage.
    """
    try:
        stat = minio_client.stat_object(MINIO_BUCKET_NAME, object_name)
        return {
            "size": stat.size,
            "last_modified": stat.last_modified,
            "etag": stat.etag,
            "content_type": stat.content_type,
        }
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise MinioServiceError(f"File not found: {object_name}") from e
        raise MinioServiceError(f"Failed to get file info: {str(e)}") from e


def get_file_url(object_name: str, expires_in_seconds: int = 3600) -> str:
    """
    Generates a presigned URL for downloading a file from MinIO.
    """
    try:
        url = minio_client.presigned_get_object(
            MINIO_BUCKET_NAME, object_name, expires=expires_in_seconds
        )
        return url
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise MinioServiceError(f"File not found: {object_name}") from e
        raise MinioServiceError(f"Failed to generate URL: {str(e)}") from e
