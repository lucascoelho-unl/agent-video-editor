import asyncio
import sys
import traceback
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from backend.tools.docker_tools import get_video_by_filename, list_videos_in_container

# Import the actual tool logic
from backend.tools.video_tools import delete_video_from_working_dir, merge_videos


async def create_mcp_server():
    """Create and configure the MCP server instance."""

    server = Server(
        name="video-editor-mcp",
    )

    tool_logic_registry = {
        "merge_videos": merge_videos,
        "list_videos_in_container": list_videos_in_container,
        "get_video_by_filename": get_video_by_filename,
        "delete_video_from_working_dir": delete_video_from_working_dir,
    }

    @server.list_tools()
    async def list_all_available_tools() -> list[Tool]:
        """
        Creates and returns a list of all tools available on the server.
        """
        return [
            Tool(
                name="merge_videos",
                description="Merges two videos together and saves the result to a file.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_path1": {
                            "type": "string",
                            "description": "Path to the first video file",
                        },
                        "video_path2": {
                            "type": "string",
                            "description": "Path to the second video file",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path to save the merged video file",
                        },
                    },
                    "required": ["video_path1", "video_path2", "output_path"],
                },
            ),
            Tool(
                name="list_videos_in_container",
                description="Lists all video files in the /app/data directory of the container.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_video_by_filename",
                description="Downloads a video from the container to the local agent downloads directory.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The filename of the video to download.",
                        }
                    },
                    "required": ["filename"],
                },
            ),
            Tool(
                name="delete_video_from_working_dir",
                description="Deletes a video file from the agent's local working directory.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The name of the video file to delete.",
                        }
                    },
                    "required": ["filename"],
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
            return await tool_function(**arguments)
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
