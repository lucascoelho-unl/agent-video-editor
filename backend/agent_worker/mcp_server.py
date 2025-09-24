import asyncio
import json
import logging
import sys
import traceback
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
from tools.tools import analyze_videos, list_videos

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def create_mcp_server():
    """Create and configure the MCP server instance."""

    server = Server(
        name="video-editor-mcp",
    )

    tool_logic_registry = {
        "list_videos": list_videos,
        "analyze_videos": analyze_videos,
    }

    async def run_tool(name: str, **kwargs):
        try:
            if asyncio.iscoroutinefunction(tool_logic_registry[name]):
                return await tool_logic_registry[name](**kwargs)
            else:
                return tool_logic_registry[name](**kwargs)
        except Exception as e:
            logging.error(f"Error running tool {name}: {e}")
            return json.dumps({"error": str(e)})

    @server.list_tools()
    async def list_all_available_tools() -> list[Tool]:
        """
        Creates and returns a list of all tools available on the server.
        """
        return [
            Tool(
                name="list_videos",
                description="Lists all videos in a specified directory.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "The directory to list videos from (default: 'videos').",
                        }
                    },
                },
            ),
            Tool(
                name="analyze_videos",
                description="Analyzes multiple video files (or one if only one is provided) with a multimodal AI model to understand their content. Provide a list of video filenames and a text prompt.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_filenames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A list of filenames of the videos to analyze (e.g., ['video1.mp4', 'video2.mp4']).",
                        },
                        "prompt": {
                            "type": "string",
                            "description": "The text prompt for the analysis (e.g., 'Describe what is happening in these videos.').",
                        },
                        "source_directory": {
                            "type": "string",
                            "description": "The directory to get the videos from (default: 'videos').",
                        },
                    },
                    "required": ["video_filenames", "prompt"],
                },
            ),
        ]

    @server.call_tool()
    async def execute_any_tool(name: str, arguments: dict) -> Dict[str, Any]:
        """
        Executes a tool by name with the given arguments.
        """
        if name in tool_logic_registry:
            result_str = await run_tool(name, **arguments)
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
            logging.error(f"Unknown tool called: {name}")
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
        logging.error("Failed to start MCP server.", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
