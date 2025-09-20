import asyncio
import sys
import traceback
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# Import the actual tool logic
from tools.video_tools import merge_videos


async def create_mcp_server():
    """Create and configure the MCP server instance."""

    server = Server(
        name="video-editor-mcp",
    )

    tool_logic_registry = {
        "merge_videos": merge_videos,
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
            )
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
