#!/usr/bin/env python3
"""
Video Service for Docker Container
Handles video-specific operations in the container
"""

import asyncio
import json
import os
import shutil
import tempfile

import aiofiles
from fastapi import HTTPException, UploadFile

from .config import (
    ALLOWED_VIDEO_EXTENSIONS,
    CONTAINER_RESULTS_PATH,
    CONTAINER_TEMP_PATH,
    CONTAINER_VIDEOS_PATH,
)
from .manager import DockerManager


class VideoService:
    """Service for video operations in Docker container"""

    def __init__(self, docker_manager: DockerManager):
        self.docker = docker_manager

    def validate_video_file(self, filename: str) -> None:
        """Validate video file extension"""
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}",
            )

    async def ensure_container_running(self) -> None:
        """Ensure container is running, raise HTTPException if not"""
        is_running, status_msg = await self.docker.check_container_status()
        if not is_running:
            raise HTTPException(
                status_code=503,
                detail=f"Container is not running: {status_msg}. Please start it with: docker-compose up -d",
            )

    async def get_container_status(self) -> dict:
        """Get container status information"""
        is_running, status_msg = await self.docker.check_container_status()
        return {
            "container_running": is_running,
            "container_id": "unknown",
            "message": status_msg,
        }

    async def upload_video(self, file: UploadFile) -> dict:
        """Upload video file to container"""
        # Validate file type
        self.validate_video_file(file.filename)

        # Ensure container is running
        await self.ensure_container_running()

        # Create temporary file
        temp_file_path = None
        try:
            # Create temporary file
            file_extension = os.path.splitext(file.filename)[1].lower()
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_extension
            ) as temp_file:
                temp_file_path = temp_file.name

            async with aiofiles.open(temp_file_path, "wb") as out_file:
                while content := await file.read(1024 * 1024):  # Read in 1MB chunks
                    await out_file.write(content)

            # Get file size
            file_size = os.path.getsize(temp_file_path)

            # Copy file to container
            success = await self.docker.copy_file_to_container(
                temp_file_path, f"{CONTAINER_VIDEOS_PATH}/{file.filename}"
            )

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to upload file to container"
                )

            return {
                "success": True,
                "message": f"Video '{file.filename}' uploaded successfully to container",
                "filename": file.filename,
                "file_size": file_size,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error uploading video: {str(e)}"
            )
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    async def download_video(self, filename: str, source: str = "results") -> str:
        """
        Downloads a video from the container to a temporary local file.
        Returns the path to the temporary file.

        Args:
            filename: Name of the video file
            source: Source directory - "videos", "results", or "temp" (default: "results")
        """
        await self.ensure_container_running()

        # Determine the container path based on source
        if source == "videos":
            container_path = f"{CONTAINER_VIDEOS_PATH}/{filename}"
        elif source == "results":
            container_path = f"{CONTAINER_RESULTS_PATH}/{filename}"
        elif source == "temp":
            container_path = f"{CONTAINER_TEMP_PATH}/{filename}"
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid source. Must be 'videos', 'results', or 'temp'.",
            )

        # Create a temporary file to hold the video
        file_extension = os.path.splitext(filename)[1]
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension or ".mp4"
        )
        local_path = temp_file.name
        temp_file.close()

        # Copy the file from the container
        success = await self.docker.copy_file_from_container(container_path, local_path)

        if success:
            return local_path
        else:
            # Clean up the temporary file if the copy fails
            if os.path.exists(local_path):
                os.remove(local_path)
            raise HTTPException(
                status_code=404,
                detail=f"Video '{filename}' not found in container {source} or could not be downloaded.",
            )

    async def delete_video(self, file_path: str) -> dict:
        """Delete a video from a specified path in the container"""
        await self.ensure_container_running()

        # Sanitize and construct the full path
        if file_path.startswith("/"):
            file_path = file_path[1:]

        full_path = f"/app/{file_path}"

        # Delete video file
        success = await self.docker.delete_file(full_path)

        if success:
            return {
                "success": True,
                "message": f"Video '{file_path}' deleted successfully",
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Video at '{file_path}' not found or could not be deleted",
            )

    async def list_videos(self) -> dict:
        """List all videos in the container"""
        await self.ensure_container_running()

        # List videos, results, and temp files concurrently
        videos_task = self.docker.list_files(CONTAINER_VIDEOS_PATH)
        results_task = self.docker.list_files(CONTAINER_RESULTS_PATH)
        temp_task = self.docker.list_files(CONTAINER_TEMP_PATH)

        results = await asyncio.gather(videos_task, results_task, temp_task)

        videos_success, videos = results[0]
        results_success, results_files = results[1]
        temp_success, temp_files = results[2]

        return {
            "videos": videos if videos_success else [],
            "results": results_files if results_success else [],
            "temp": temp_files if temp_success else [],
        }

    async def get_videos_data(self) -> dict:
        """
        Retrieves video data from the JSON file in the container.
        """
        try:
            success, output = await self.docker.exec_command(
                "cat /app/videos_data.txt",
            )
            if success:
                return json.loads(output)
            return {}
        except Exception:
            return {}
