import asyncio
import os
import sys
import traceback
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
from tools.tools import (
    delete_videos_from_container,
    get_video_transcript,
    get_videos_creation_timestamps,
    list_videos_in_container,
    merge_videos_in_container,
)


async def create_mcp_server():
    """Create and configure the MCP server instance."""

    server = Server(
        name="video-editor-mcp",
    )

    tool_logic_registry = {
        "list_videos_in_container": list_videos_in_container,
        "merge_videos_in_container": merge_videos_in_container,
        "delete_videos_from_container": delete_videos_from_container,
        "get_videos_creation_timestamps": get_videos_creation_timestamps,
        "get_video_transcript": get_video_transcript,
    }

    @server.list_tools()
    async def list_all_available_tools() -> list[Tool]:
        """
        Creates and returns a list of all tools available on the server.
        """
        return [
            Tool(
                name="list_videos_in_container",
                description="Lists all video files in the container organized by directory. Returns a JSON string with separate arrays for 'videos', 'results', and 'temp' directories, plus a total_count field.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="merge_videos_in_container",
                description="Merges one or more videos from the videos directory in the order provided. More efficient than merging pairs sequentially.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_filenames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of video filenames to merge in order (e.g., ['video1.mp4', 'video2.mp4', 'video3.mp4']).",
                        },
                        "output_filename": {
                            "type": "string",
                            "description": "The filename for the merged video.",
                        },
                        "source_directory": {
                            "type": "string",
                            "description": "The directory to get the videos from (default: 'videos').",
                        },
                        "destination_directory": {
                            "type": "string",
                            "description": "The directory to save the merged video to (default: 'results').",
                        },
                    },
                    "required": ["video_filenames", "output_filename"],
                },
            ),
            Tool(
                name="delete_videos_from_container",
                description="Deletes one or more videos from the container using a list of relative paths. More efficient than deleting files one by one.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": 'List of relative paths to delete (e.g., ["videos/video1.mp4", "results/output.mp4", "temp/temp_file.mp4"]).',
                        }
                    },
                    "required": ["file_paths"],
                },
            ),
            Tool(
                name="get_videos_creation_timestamps",
                description="Retrieves the creation timestamps for all videos or a specified list of videos.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_filenames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of video filenames to get timestamps for. If not provided, returns timestamps for all videos.",
                        }
                    },
                },
            ),
            Tool(
                name="get_video_transcript",
                description="Retrieves the transcript for a specific video or a list of videos.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_filenames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The filenames of the videos to get the transcript for.",
                        }
                    },
                    "required": ["video_filenames"],
                },
            ),
        ]

    @server.call_tool()
    async def execute_any_tool(name: str, arguments: dict) -> Dict[str, Any]:
        """
        Executes a tool by name with the given arguments.
        """
        if name in tool_logic_registry:
            tool_function = tool_logic_registry[name]
            # The result from the tool is a JSON string.
            result_str = await tool_function(**arguments)
            # We need to wrap this in the format the ADK expects.
            return {
                "content": [
                    {
                        "TextContent": {
                            "text": result_str,
                        }
                    }
                ]
            }
        else:
            raise Exception(f"Unknown tool called: {name}")

    return server


async def main():
    """Entry point that runs the MCP server over stdio."""
    try:
        server = await create_mcp_server()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )
    except Exception as e:
        print("Failed to start MCP server. The full error traceback is:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
