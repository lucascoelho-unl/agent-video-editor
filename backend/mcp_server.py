import asyncio
import os
import sys
import traceback
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
from tools.tools import (
    delete_video_from_container,
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
        "delete_video_from_container": delete_video_from_container,
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
                description="Merges two videos that are already inside the container.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video1_filename": {
                            "type": "string",
                            "description": "The filename of the first video.",
                        },
                        "video2_filename": {
                            "type": "string",
                            "description": "The filename of the second video.",
                        },
                        "output_filename": {
                            "type": "string",
                            "description": "The filename for the merged video.",
                        },
                    },
                    "required": [
                        "video1_filename",
                        "video2_filename",
                        "output_filename",
                    ],
                },
            ),
            Tool(
                name="delete_video_from_container",
                description='Deletes a video from the container using a relative path (e.g., "videos/my_video.mp4", "results/output.mp4").',
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": 'The relative path of the video to delete (e.g., "videos/my_video.mp4").',
                        }
                    },
                    "required": ["file_path"],
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
