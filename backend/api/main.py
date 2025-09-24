#!/usr/bin/env python3
"""
Main entry point for the Video Upload API
Simple FastAPI server for uploading videos to Docker container
"""

import os

import docker
from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from video_service import delete_video, list_videos, save_video

app = FastAPI()

# Add CORS middleware for frontend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Video Upload API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


@app.get("/api/v1/videos")
async def list_videos_endpoint():
    """
    Endpoint to list all videos.
    """
    try:
        result = list_videos()
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/v1/upload")
async def upload_video_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to upload a video.
    """
    try:
        result = save_video(file)
        return JSONResponse(status_code=201, content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.delete("/api/v1/videos/{filename}")
async def delete_video_endpoint(filename: str, source: str = Query("videos")):
    """
    Endpoint to delete a video.
    """
    try:
        result = delete_video(filename, source)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/v1/container/status")
async def container_status_endpoint():
    """
    Endpoint to get container status.
    """
    try:
        # Check if the agent container is running by looking for a shared volume
        # Since both containers share the video_storage volume, we can check if
        # the agent has written any status files or if the shared storage is accessible

        shared_storage_path = "/app/storage"

        # Check if shared storage is accessible (indicates containers are running)
        if os.path.exists(shared_storage_path):
            # Try to create a simple test file to verify write access
            test_file = os.path.join(shared_storage_path, ".api_health_check")
            try:
                with open(test_file, "w") as f:
                    f.write("api_health_check")
                os.remove(test_file)

                return JSONResponse(
                    status_code=200,
                    content={
                        "container_running": True,
                        "container_id": "agent",
                        "message": "Agent container is running (shared storage accessible)",
                        "container_name": "agent",
                    },
                )
            except Exception:
                return JSONResponse(
                    status_code=200,
                    content={
                        "container_running": False,
                        "container_id": "agent",
                        "message": "Agent container may not be running (no write access to shared storage)",
                        "container_name": "agent",
                    },
                )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "container_running": False,
                    "container_id": "agent",
                    "message": "Agent container is not running (shared storage not accessible)",
                    "container_name": "agent",
                },
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "container_running": False,
                "container_id": None,
                "message": f"Error checking container status: {str(e)}",
            },
        )


@app.get("/api/v1/download/{filename}")
async def download_video_endpoint(filename: str, source: str = Query("results")):
    """
    Endpoint to download a video.
    """
    try:
        # Map source to directory
        source_map = {
            "videos": "/app/storage/videos",
            "results": "/app/storage/results",
            "temp": "/app/storage/temp",
        }

        if source not in source_map:
            return JSONResponse(status_code=400, content={"error": "Invalid source"})

        file_path = os.path.join(source_map[source], filename)

        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "File not found"})

        return FileResponse(file_path, filename=filename)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
