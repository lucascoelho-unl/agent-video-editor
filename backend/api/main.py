"""
Main entry point for the Video Upload API
Simple FastAPI server for uploading videos to Docker container
"""

import io

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from minio.error import S3Error
from minio_service import (
    delete_media_file,
    get_file_url,
    get_media_file,
    list_media_files,
    minio_client,
    save_media_file,
)

app = FastAPI()

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


@app.get("/api/v1/medias")
async def list_media_endpoint():
    """
    Endpoint to list all media files (videos and audio).
    """
    result = list_media_files()
    return JSONResponse(status_code=200, content=result)


@app.post("/api/v1/upload")
async def upload_media_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to upload a video or audio file.
    """
    result = save_media_file(file)
    return JSONResponse(status_code=201, content=result)


@app.delete("/api/v1/media/{filename}")
async def delete_media_endpoint(filename: str, source: str = Query("medias")):
    """
    Endpoint to delete a video or audio file.
    """
    result = delete_media_file(filename, source)
    return JSONResponse(status_code=200, content=result)


@app.get("/api/v1/container/status")
async def container_status_endpoint():
    """
    Endpoint to get container status by checking MinIO connectivity.
    """
    try:
        # Try to list buckets to verify MinIO connectivity
        minio_client.list_buckets()

        return JSONResponse(
            status_code=200,
            content={
                "container_running": True,
                "container_id": "agent",
                "message": "Agent container is running (MinIO storage accessible)",
                "container_name": "agent",
                "storage_type": "MinIO",
            },
        )
    except S3Error as minio_error:
        return JSONResponse(
            status_code=200,
            content={
                "container_running": False,
                "container_id": "agent",
                "message": f"Agent container may not be running (MinIO not accessible: {str(minio_error)})",
                "container_name": "agent",
                "storage_type": "MinIO",
            },
        )


@app.get("/api/v1/download/{filename}")
async def download_video_endpoint(filename: str, source: str = Query("medias")):
    """
    Endpoint to download a video or audio file from MinIO storage.
    """
    file_data = get_media_file(filename, source)

    # Determine content type based on file extension
    file_extension = filename.lower().split(".")[-1]
    content_type_map = {
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "avi": "video/x-msvideo",
        "mkv": "video/x-matroska",
        "webm": "video/webm",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
    }
    content_type = content_type_map.get(file_extension, "application/octet-stream")

    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/v1/media/{filename}/url")
async def get_media_url_endpoint(
    filename: str, source: str = Query("results"), expires: int = Query(3600)
):
    """
    Endpoint to get a presigned URL for downloading a media file.
    """
    url = get_file_url(filename, source, expires)
    return JSONResponse(status_code=200, content={"url": url, "expires_in_seconds": expires})
