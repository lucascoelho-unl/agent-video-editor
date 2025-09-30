"""MinIO storage service for handling file operations."""

import io
import logging
import os
import tempfile
import time
from typing import Dict, List

from interfaces.storage_service_interface import StorageService
from minio import Minio
from minio.error import S3Error

# Using default logging module


class MinioServiceError(Exception):
    """Custom exception for MinIO service errors."""


class MinioStorageService(StorageService):
    """Implementation of the StorageService for MinIO."""

    def __init__(self):
        """Initializes the MinioStorageService."""
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.minio_bucket_name = os.getenv("MINIO_BUCKET_NAME", "video-storage")

        self.minio_client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=False,
        )
        logging.info(
            "MinioStorageService initialized for bucket '%s' at '%s'",
            self.minio_bucket_name,
            self.minio_endpoint,
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensures the MinIO bucket exists, creating it if necessary."""
        try:
            if not self.minio_client.bucket_exists(self.minio_bucket_name):
                logging.info("Bucket '%s' not found. Creating it...", self.minio_bucket_name)
                self.minio_client.make_bucket(self.minio_bucket_name)
                logging.info("Bucket '%s' created successfully.", self.minio_bucket_name)
            else:
                logging.debug("Bucket '%s' already exists.", self.minio_bucket_name)
        except S3Error as e:
            logging.exception(
                "Failed to create or check bucket '%s': %s", self.minio_bucket_name, e
            )
            raise MinioServiceError(f"Failed to create bucket: {str(e)}") from e

    def download_file_to_temp(self, object_name: str, local_path: str | None = None) -> str:
        """Downloads a file from MinIO to a temporary location."""
        start_time = time.perf_counter()
        temp_path = None
        try:
            logging.debug("Downloading '%s' to a temporary file...", object_name)
            if local_path:
                temp_path = local_path
            else:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(object_name)[1]
                )
                temp_path = temp_file.name
                temp_file.close()

            self.minio_client.fget_object(self.minio_bucket_name, object_name, temp_path)
            duration = time.perf_counter() - start_time
            logging.info(
                "Successfully downloaded '%s' to '%s' in %.2f seconds",
                object_name,
                temp_path,
                duration,
            )
            return temp_path
        except S3Error as e:
            logging.exception("Failed to download '%s': %s", object_name, e)
            if e.code == "NoSuchKey":
                raise MinioServiceError(f"File not found: {object_name}") from e
            raise MinioServiceError(f"Failed to download file: {str(e)}") from e

    def upload_file_from_path(
        self, local_path: str, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Uploads a file to MinIO from a local path."""
        start_time = time.perf_counter()
        try:
            logging.debug("Uploading '%s' to '%s'...", local_path, object_name)
            self.minio_client.fput_object(
                self.minio_bucket_name, object_name, local_path, content_type=content_type
            )
            duration = time.perf_counter() - start_time
            logging.info(
                "Successfully uploaded '%s' to '%s' in %.2f seconds",
                local_path,
                object_name,
                duration,
            )
            return f"Successfully uploaded {object_name}"
        except S3Error as e:
            logging.exception("Failed to upload '%s': %s", local_path, e)
            raise MinioServiceError(f"Failed to upload file: {str(e)}") from e

    def upload_file_from_bytes(
        self, file_data: bytes, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Uploads file data to MinIO from bytes."""
        start_time = time.perf_counter()
        try:
            logging.debug("Uploading %d bytes to '%s'...", len(file_data), object_name)
            self.minio_client.put_object(
                self.minio_bucket_name,
                object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )
            duration = time.perf_counter() - start_time
            logging.info(
                "Successfully uploaded '%s' in %.2f seconds",
                object_name,
                duration,
            )
            return f"Successfully uploaded {object_name}"
        except S3Error as e:
            logging.exception("Failed to upload to '%s': %s", object_name, e)
            raise MinioServiceError(f"Failed to upload file: {str(e)}") from e

    def list_all_files(self) -> List[str]:
        """Lists all files in the bucket."""
        start_time = time.perf_counter()
        try:
            logging.debug("Listing all files in bucket '%s'...", self.minio_bucket_name)
            files = []
            objects = self.minio_client.list_objects(self.minio_bucket_name, recursive=True)
            for obj in objects:
                files.append(obj.object_name)
            duration = time.perf_counter() - start_time
            logging.info(
                "Found %d files in bucket '%s' in %.2f seconds.",
                len(files),
                self.minio_bucket_name,
                duration,
            )
            return files
        except S3Error as e:
            logging.exception("Failed to list files in bucket '%s': %s", self.minio_bucket_name, e)
            raise MinioServiceError(f"Failed to list files: {str(e)}") from e

    def file_exists(self, object_name: str) -> bool:
        """Checks if a file exists in MinIO."""
        try:
            logging.debug("Checking for existence of '%s'...", object_name)
            self.minio_client.stat_object(self.minio_bucket_name, object_name)
            logging.debug("'%s' exists.", object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                logging.debug("'%s' does not exist.", object_name)
                return False
            logging.exception("Error checking existence of '%s': %s", object_name, e)
            raise MinioServiceError(f"Error checking file existence: {str(e)}") from e

    def delete_file(self, object_name: str) -> str:
        """Deletes a file from MinIO."""
        try:
            logging.info("Deleting '%s'...", object_name)
            self.minio_client.remove_object(self.minio_bucket_name, object_name)
            logging.info("Successfully deleted '%s'", object_name)
            return f"Successfully deleted {object_name}"
        except S3Error as e:
            logging.exception("Failed to delete '%s': %s", object_name, e)
            if e.code == "NoSuchKey":
                raise MinioServiceError(f"File not found: {object_name}") from e
            raise MinioServiceError(f"Failed to delete file: {str(e)}") from e

    def get_file_info(self, object_name: str) -> Dict:
        """Gets information about a file from MinIO."""
        try:
            logging.debug("Getting file info for '%s'...", object_name)
            stat = self.minio_client.stat_object(self.minio_bucket_name, object_name)
            logging.debug("Successfully retrieved file info for '%s'", object_name)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
            }
        except S3Error as e:
            logging.exception("Failed to get file info for '%s': %s", object_name, e)
            if e.code == "NoSuchKey":
                raise MinioServiceError(f"File not found: {object_name}") from e
            raise MinioServiceError(f"Failed to get file info: {str(e)}") from e

    def get_file_url(self, object_name: str, expires_in_seconds: int = 3600) -> str:
        """Gets a presigned URL for a file from MinIO."""
        try:
            logging.debug(
                "Generating presigned URL for '%s' (expires in %d seconds)...",
                object_name,
                expires_in_seconds,
            )
            url = self.minio_client.presigned_get_object(
                self.minio_bucket_name, object_name, expires=expires_in_seconds
            )
            logging.info("Successfully generated presigned URL for '%s'", object_name)
            return url
        except S3Error as e:
            logging.exception("Failed to generate URL for '%s': %s", object_name, e)
            if e.code == "NoSuchKey":
                raise MinioServiceError(f"File not found: {object_name}") from e
            raise MinioServiceError(f"Failed to generate URL: {str(e)}") from e
