#!/usr/bin/env python3
"""
Video Upload API Endpoints
Simple API for uploading videos to the Docker container
"""

from docker.factory import create_services
from fastapi import APIRouter, File, UploadFile

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


@router.delete("/videos/{filename}")
async def delete_video(filename: str):
    """Delete a video from the container"""
    return video_service.delete_video(filename)
