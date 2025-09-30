"""Abstract interface for a storage service."""

from abc import ABC, abstractmethod


class StorageService(ABC):
    """Abstract interface for a storage service."""

    @abstractmethod
    def download_file_to_temp(self, object_name: str) -> str:
        """Downloads a file to a temporary location."""

    @abstractmethod
    def upload_file_from_path(
        self, local_path: str, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Uploads a file from a local path."""

    @abstractmethod
    def upload_file_from_bytes(
        self, file_data: bytes, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Uploads file data from bytes."""

    @abstractmethod
    def list_all_files(self) -> list[str]:
        """Lists all files."""

    @abstractmethod
    def file_exists(self, object_name: str) -> bool:
        """Checks if a file exists."""

    @abstractmethod
    def delete_file(self, object_name: str) -> str:
        """Deletes a file."""

    @abstractmethod
    def get_file_info(self, object_name: str) -> dict:
        """Gets information about a file."""

    @abstractmethod
    def get_file_url(self, object_name: str, expires_in_seconds: int = 3600) -> str:
        """Gets a presigned URL for a file."""
