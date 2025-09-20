#!/usr/bin/env python3
"""
Video Service for Docker Container
Handles video-specific operations in the container
"""

import os
import tempfile
import shutil
from typing import List, Tuple
from fastapi import UploadFile, HTTPException
from .manager import DockerManager
from .config import (
    CONTAINER_VIDEOS_PATH,
    CONTAINER_RESULTS_PATH,
    ALLOWED_VIDEO_EXTENSIONS,
)


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

    def ensure_container_running(self) -> None:
        """Ensure container is running, raise HTTPException if not"""
        is_running, status_msg = self.docker.check_container_status()
        if not is_running:
            raise HTTPException(
                status_code=503,
                detail=f"Container is not running: {status_msg}. Please start it with: docker-compose up -d",
            )

    def upload_video(self, file: UploadFile) -> dict:
        """Upload video file to container"""
        # Validate file type
        self.validate_video_file(file.filename)

        # Ensure container is running
        self.ensure_container_running()

        # Create temporary file
        temp_file_path = None
        try:
            # Create temporary file
            file_extension = os.path.splitext(file.filename)[1].lower()
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_extension
            ) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_file_path = temp_file.name

            # Get file size
            file_size = os.path.getsize(temp_file_path)

            # Copy file to container
            success = self.docker.copy_file_to_container(
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

    def list_videos(self) -> dict:
        """List all videos in the container"""
        self.ensure_container_running()

        # List videos and results
        videos_success, videos = self.docker.list_files(CONTAINER_VIDEOS_PATH)
        results_success, results = self.docker.list_files(CONTAINER_RESULTS_PATH)

        return {
            "videos": videos if videos_success else [],
            "results": results if results_success else [],
        }

    def delete_video(self, filename: str) -> dict:
        """Delete a video from the container"""
        self.ensure_container_running()

        # Delete video file
        success = self.docker.delete_file(f"{CONTAINER_VIDEOS_PATH}/{filename}")

        if success:
            return {
                "success": True,
                "message": f"Video '{filename}' deleted successfully",
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Video '{filename}' not found or could not be deleted",
            )

    def get_container_status(self) -> dict:
        """Get container status information"""
        is_running, status_msg = self.docker.check_container_status()
        return {
            "container_running": is_running,
            "container_id": "unknown",
            "message": status_msg,
        }
