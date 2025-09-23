import asyncio
import json
import time

from tools.tools import (
    analyze_video_with_gemini,
    delete_videos_from_container,
    get_video_transcript,
    get_videos_creation_timestamps,
    list_videos_in_container,
    merge_videos_in_container,
)
from tools.video_utils import process_video


async def main():
    """
    Main function to test the video processing tools.
    """
    print("--- Testing list_videos_in_container Tool ---")
    print()

    try:
        start_time = time.monotonic()
        result = await list_videos_in_container()
        end_time = time.monotonic()
        print(f"Execution time: {end_time - start_time:.4f} seconds")
        print("Tool Output:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        print()
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()

    print()
    print("--- Testing get_videos_creation_timestamps Tool ---")
    print()

    try:
        # Get the list of videos in the container
        start_time = time.monotonic()
        videos_json = await list_videos_in_container()
        videos = json.loads(videos_json)["videos"]

        # If there are videos, get their timestamps
        if videos:
            result = await get_videos_creation_timestamps(videos)
            end_time = time.monotonic()
            print(f"Execution time: {end_time - start_time:.4f} seconds")
            print("Tool Output:")
            print("-" * 40)
            print(result)
            print("-" * 40)
            print()
            print("✅ Test completed successfully!")
        else:
            print("No videos available to get timestamps. Skipping test.")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()

    print()
    print("--- Testing merge_videos_in_container Tool ---")
    print()

    try:
        # Get the list of videos in the container
        start_time = time.monotonic()
        videos_json = await list_videos_in_container()
        videos = json.loads(videos_json)["videos"]

        # If there are at least 2 videos, merge them
        if len(videos) >= 2:
            video_filenames = videos  # Take all videos
            output_filename = "merged_test_video.mp4"
            result = await merge_videos_in_container(video_filenames, output_filename)
            end_time = time.monotonic()
            print(f"Execution time: {end_time - start_time:.4f} seconds")
            print("Tool Output:")
            print("-" * 40)
            print(result)
            print("-" * 40)
            print()
            print("✅ Test completed successfully!")
        else:
            print("Not enough videos to merge. Skipping test.")
            print(f"Available videos: {videos}")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()

    print()
    print("--- Testing process_video Tool ---")
    print()

    try:
        # Get the list of videos in the container
        start_time = time.monotonic()
        videos_json = await list_videos_in_container()
        videos = json.loads(videos_json)["videos"]

        # If there is at least one video, process it
        if videos:
            await process_video("merged_test_video.mp4", "results")
            end_time = time.monotonic()
            print(f"Execution time: {end_time - start_time:.4f} seconds")
            print("Tool Output:")
            print("-" * 40)
            print(f"Successfully processed video: merged_test_video.mp4")
            print("-" * 40)
            print()
            print("✅ Test completed successfully!")
        else:
            print("No videos available to process. Skipping test.")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()

    print()
    print("--- Testing analyze_video_with_gemini Tool ---")
    print()

    try:
        # Get the list of videos in the container
        start_time = time.monotonic()
        videos_json = await list_videos_in_container()
        videos = json.loads(videos_json)["videos"]

        # If there is at least one video, analyze it
        if videos:
            prompt = "What is the main topic of this video?"
            result = await analyze_video_with_gemini(
                "merged_test_video.mp4", prompt, "results"
            )
            end_time = time.monotonic()
            print(f"Execution time: {end_time - start_time:.4f} seconds")
            print("Tool Output:")
            print("-" * 40)
            print(result)
            print("-" * 40)
            print()
            print("✅ Test completed successfully!")
        else:
            print("No videos available to analyze. Skipping test.")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()

    print()
    print("--- Testing get_video_transcript Tool ---")
    print()

    try:
        # Get the list of videos in the container
        start_time = time.monotonic()
        videos_json = await list_videos_in_container()
        videos = json.loads(videos_json)["videos"]

        # If there is at least one video, get its transcript
        if videos:
            result = await get_video_transcript(videos)
            end_time = time.monotonic()
            print(f"Execution time: {end_time - start_time:.4f} seconds")
            print("Tool Output:")
            print("-" * 40)
            print(result)
            print("-" * 40)
            print()
            print("✅ Test completed successfully!")
        else:
            print("No videos available to get transcript. Skipping test.")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()

    print()
    print("--- Testing delete_videos_from_container Tool ---")
    print()

    try:
        # List videos in the 'results' directory to find the merged video
        start_time = time.monotonic()
        videos_json = await list_videos_in_container()
        results_videos = json.loads(videos_json)["results"]
        videos_to_delete = []

        if "merged_test_video.mp4" in results_videos:
            videos_to_delete.append("results/merged_test_video.mp4")

        if videos_to_delete:
            result = await delete_videos_from_container(videos_to_delete)
            end_time = time.monotonic()
            print(f"Execution time: {end_time - start_time:.4f} seconds")
            print("Tool Output:")
            print("-" * 40)
            print(result)
            print("-" * 40)
            print()
            print("✅ Test completed successfully!")
        else:
            print("No videos to delete. Skipping test.")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
