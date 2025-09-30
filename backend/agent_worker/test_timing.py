#!/usr/bin/env python3
"""
Simple test script to list all videos and run exec command with timing logs.
"""

import asyncio
import json
import logging
import time
from datetime import datetime

from tools.tools import execute_edit_script, list_available_media_files

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def log_with_timestamp(message: str, level: str = "INFO"):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {level}: {message}")


async def test_video_processing():
    """Test function that lists videos and runs exec command with timing."""

    log_with_timestamp("Starting video processing test")
    start_time = time.time()

    try:
        # Step 1: List all available media files
        log_with_timestamp("Step 1: Listing all available media files")
        step1_start = time.time()

        media_result = await list_available_media_files(include_metadata=True)
        media_data = json.loads(media_result)

        step1_duration = time.time() - step1_start
        log_with_timestamp(f"Step 1 completed in {step1_duration:.3f} seconds")

        if "error" in media_data:
            log_with_timestamp(f"Error listing media files: {media_data['error']}", "ERROR")
            return

        videos = media_data.get("videos", [])
        log_with_timestamp(f"Found {len(videos)} video files")

        if not videos:
            log_with_timestamp("No videos found to process", "WARNING")
            return

        # Display video information
        log_with_timestamp("Video files found:")
        for i, video in enumerate(videos[:5]):  # Show first 5 videos
            if isinstance(video, dict):
                filename = video.get("filename", "unknown")
                size_mb = video.get("size_mb", 0)
                log_with_timestamp(f"  {i+1}. {filename} ({size_mb} MB)")
            else:
                log_with_timestamp(f"  {i+1}. {video}")

        if len(videos) > 5:
            log_with_timestamp(f"  ... and {len(videos) - 5} more videos")

        # Step 2: Execute edit script with first few videos
        log_with_timestamp("Step 2: Executing edit script")
        step2_start = time.time()

        # Use first 2 videos for testing (or all if less than 2)
        test_videos = videos[:2] if len(videos) >= 2 else videos

        # Extract filenames
        input_filenames = []
        for video in test_videos:
            if isinstance(video, dict):
                input_filenames.append(video["filename"])
            else:
                input_filenames.append(video)

        log_with_timestamp(f"Processing videos: {input_filenames}")

        # Execute the edit script with a shorter timeout for testing
        exec_result = await execute_edit_script(
            input_file_names=input_filenames,
            output_file_name="test_output.mp4",
            script_file_name="edit.sh",
            timeout_seconds=60,  # 1 minute timeout for testing
        )

        step2_duration = time.time() - step2_start
        log_with_timestamp(f"Step 2 completed in {step2_duration:.3f} seconds")

        # Parse and display results
        exec_data = json.loads(exec_result)
        if exec_data.get("success"):
            log_with_timestamp(
                f"Script execution successful! Output: {exec_data.get('output_file')}"
            )
            if exec_data.get("stdout"):
                log_with_timestamp(f"Script stdout: {exec_data['stdout']}")
        else:
            log_with_timestamp(f"Script execution failed: {exec_data.get('error')}", "ERROR")
            if exec_data.get("stderr"):
                log_with_timestamp(f"Script stderr: {exec_data['stderr']}", "ERROR")

        # Total timing
        total_duration = time.time() - start_time
        log_with_timestamp(f"Total test completed in {total_duration:.3f} seconds")
        log_with_timestamp("Test summary:")
        log_with_timestamp(f"  - List files: {step1_duration:.3f}s")
        log_with_timestamp(f"  - Execute script: {step2_duration:.3f}s")
        log_with_timestamp(f"  - Total time: {total_duration:.3f}s")

    except (ValueError, KeyError, json.JSONDecodeError, OSError, RuntimeError) as e:
        log_with_timestamp(f"Test failed with exception: {str(e)}", "ERROR")
        logger.exception("Full exception details:")


async def main():
    """Main entry point."""
    log_with_timestamp("=== Video Processing Timing Test ===")
    await test_video_processing()
    log_with_timestamp("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
