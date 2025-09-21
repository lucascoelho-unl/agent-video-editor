#!/usr/bin/env python3
"""
Video Upload API Endpoints
Simple API for uploading videos to the Docker container
"""

import os

from docker.factory import create_services
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["video"])

# Initialize services
docker_manager, video_service = create_services()


@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {"message": "Video Upload API is running!", "status": "healthy"}


@router.get("/container/status")
async def check_container_status():
    """Check if the video processing container is running"""
    return video_service.get_container_status()


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file to the Docker container

    Supported formats: mp4, avi, mov, mkv, webm
    """
    return video_service.upload_video(file)


@router.get("/videos")
async def list_videos():
    """List all videos in the container"""
    return video_service.list_videos()


@router.get("/download/{filename}")
async def download_video(filename: str, source: str = "results"):
    """
    Download a video file from the container.
    The file is deleted from the server after being sent.

    Args:
        filename: Name of the video file
        source: Source directory - "videos", "results", or "temp" (default: "results")
    """
    temp_file_path = video_service.download_video(filename, source)

    async def cleanup():
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return FileResponse(
        path=temp_file_path,
        media_type="video/mp4",
        filename=filename,
        background=cleanup,
    )


@router.delete("/videos/{filename}")
async def delete_video(filename: str, source: str = "videos"):
    """
    Delete a video from the container.

    Args:
        filename: Name of the video file
        source: Source directory - "videos", "results", or "temp" (default: "videos")
    """
    file_path = f"{source}/{filename}"
    return video_service.delete_video(file_path)
