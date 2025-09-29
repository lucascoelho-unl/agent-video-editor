#!/usr/bin/env python3
"""
Script to initialize MinIO with default scripts and bucket structure.
Run this after MinIO is up and running.
"""

import os
import sys
import time

from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "video-storage")


class MinioNotReadyError(Exception):
    """Custom exception for when MinIO is not ready."""


def wait_for_minio(max_retries=30, delay=2):
    """Wait for MinIO to be available."""
    print(f"Waiting for MinIO to be available at {MINIO_ENDPOINT}...")

    for attempt in range(max_retries):
        try:
            client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False,
            )
            client.list_buckets()
            print("MinIO is available!")
            return client
        except (S3Error, MaxRetryError) as e:
            print(f"Attempt {attempt + 1}/{max_retries}: MinIO not ready yet ({e})")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise MinioNotReadyError(f"MinIO not available after {max_retries} attempts") from e


def upload_default_scripts(client):
    """Upload default scripts to MinIO."""
    scripts_dir = "/app/storage"

    if not os.path.exists(scripts_dir):
        print(f"Scripts directory not found: {scripts_dir}")
        return

    script_files = ["edit.sh"]

    for script_file in script_files:
        script_path = os.path.join(scripts_dir, script_file)
        if os.path.exists(script_path):
            try:
                with open(script_path, "rb") as file_data:
                    client.put_object(
                        MINIO_BUCKET_NAME,
                        f"scripts/{script_file}",
                        file_data,
                        length=os.path.getsize(script_path),
                        content_type="text/plain",
                    )
                print(f"Uploaded {script_file} to MinIO")
            except (S3Error, OSError) as e:
                print(f"Failed to upload {script_file}: {e}")
        else:
            print(f"Script file not found: {script_path}")


def main():
    """Main initialization function."""
    try:
        # Wait for MinIO to be available
        client = wait_for_minio()

        # Ensure bucket exists
        if not client.bucket_exists(MINIO_BUCKET_NAME):
            client.make_bucket(MINIO_BUCKET_NAME)
            print(f"Created bucket: {MINIO_BUCKET_NAME}")
        else:
            print(f"Bucket already exists: {MINIO_BUCKET_NAME}")

        # Upload default scripts
        upload_default_scripts(client)

        print("MinIO initialization completed successfully!")

    except (S3Error, MinioNotReadyError) as e:
        print(f"MinIO initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
