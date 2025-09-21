import asyncio
import json

from tools.tools import list_videos_in_container, merge_videos_in_container


async def main():
    """
    Main function to test the video processing tools.
    """
    print("--- Testing list_videos_in_container Tool ---")
    print()

    try:
        result = await list_videos_in_container()
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
    print("--- Testing merge_videos_in_container Tool ---")
    print()

    try:
        # Get the list of videos in the container
        videos_json = await list_videos_in_container()
        videos = json.loads(videos_json)["videos"]

        # If there are at least 2 videos, merge them
        if len(videos) >= 2:
            video_filenames = videos  # Take all videos
            output_filename = "merged_test_video.mp4"
            result = await merge_videos_in_container(video_filenames, output_filename)
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


if __name__ == "__main__":
    asyncio.run(main())
