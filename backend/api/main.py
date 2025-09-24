#!/usr/bin/env python3
"""
Main entry point for the Video Upload API
Simple FastAPI server for uploading videos to Docker container
"""

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from video_service import delete_video, list_videos, save_video

app = FastAPI()


@app.get("/videos")
async def list_videos_endpoint():
    """
    Endpoint to list all videos.
    """
    try:
        result = list_videos()
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/upload")
async def upload_video_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to upload a video.
    """
    try:
        result = save_video(file)
        return JSONResponse(status_code=201, content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.delete("/delete/{filename}")
async def delete_video_endpoint(filename: str):
    """
    Endpoint to delete a video.
    """
    try:
        result = delete_video(filename)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
