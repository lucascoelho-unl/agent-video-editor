import os
import shutil

from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile

load_dotenv()

STORAGE_PATH = os.getenv("STORAGE_PATH", "/app/storage/videos")
RESULTS_PATH = os.path.join(STORAGE_PATH, "results")
TEMP_PATH = os.path.join(STORAGE_PATH, "temp")
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
        "results": RESULTS_PATH,
        "temp": TEMP_PATH,
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

    # List videos (excluding subdirectories)
    if os.path.exists(STORAGE_PATH):
        result["videos"] = [
            f
            for f in os.listdir(STORAGE_PATH)
            if os.path.isfile(os.path.join(STORAGE_PATH, f))
        ]

    # List results from videos/results directory
    if os.path.exists(RESULTS_PATH):
        result["results"] = [
            f
            for f in os.listdir(RESULTS_PATH)
            if os.path.isfile(os.path.join(RESULTS_PATH, f))
        ]

    # List temp files from videos/temp directory
    if os.path.exists(TEMP_PATH):
        result["temp"] = [
            f
            for f in os.listdir(TEMP_PATH)
            if os.path.isfile(os.path.join(TEMP_PATH, f))
        ]

    return result
