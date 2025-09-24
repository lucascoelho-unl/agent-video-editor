import os
import shutil

from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile

load_dotenv()

STORAGE_PATH = os.getenv("STORAGE_PATH", "/app/storage/videos")
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


def save_video(file: UploadFile):
    """
    Saves an uploaded video to the storage volume.
    """
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_path = os.path.join(STORAGE_PATH, file.filename)
    if os.path.exists(file_path):
        raise HTTPException(
            status_code=409, detail="File with the same name already exists"
        )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": f"Successfully uploaded {file.filename}"}


def delete_video(filename: str, source: str = "videos"):
    """
    Deletes a video from the storage volume.
    """
    # Map source to directory
    source_map = {
        "videos": STORAGE_PATH,
        "results": "/app/storage/results",
        "temp": "/app/storage/temp",
    }

    if source not in source_map:
        raise HTTPException(status_code=400, detail="Invalid source")

    file_path = os.path.join(source_map[source], filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")

    os.remove(file_path)
    return {"message": f"Successfully deleted {filename}"}


def list_videos():
    """
    Lists all videos in the storage volume.
    """
    result = {"videos": [], "results": [], "temp": []}

    # List videos
    if os.path.exists(STORAGE_PATH):
        result["videos"] = [
            f
            for f in os.listdir(STORAGE_PATH)
            if os.path.isfile(os.path.join(STORAGE_PATH, f))
        ]

    # List results
    results_path = "/app/storage/results"
    if os.path.exists(results_path):
        result["results"] = [
            f
            for f in os.listdir(results_path)
            if os.path.isfile(os.path.join(results_path, f))
        ]

    # List temp files
    temp_path = "/app/storage/temp"
    if os.path.exists(temp_path):
        result["temp"] = [
            f
            for f in os.listdir(temp_path)
            if os.path.isfile(os.path.join(temp_path, f))
        ]

    return result
