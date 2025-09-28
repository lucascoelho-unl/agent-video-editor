"""
MCP server for the video editor agent.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
from tools.tools import (
    analyze_media_files,
    execute_edit_script,
    list_available_media_files,
    modify_edit_script,
    read_edit_script,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def create_mcp_server():
    """Create and configure the MCP server instance."""

    server = Server(
        name="video-editor-mcp",
    )

    tool_logic_registry = {
        "analyze_media_files": analyze_media_files,
        "read_edit_script": read_edit_script,
        "modify_edit_script": modify_edit_script,
        "execute_edit_script": execute_edit_script,
        "list_available_media_files": list_available_media_files,
    }

    async def run_tool(name: str, **kwargs):
        try:
            if asyncio.iscoroutinefunction(tool_logic_registry[name]):
                return await tool_logic_registry[name](**kwargs)
            else:
                return tool_logic_registry[name](**kwargs)
        except (KeyError, TypeError) as e:
            logging.error("Error running tool %s: %s", name, e)
            return json.dumps({"error": str(e)})

    @server.list_tools()
    async def list_all_available_tools() -> list[Tool]:
        """
        Creates and returns a list of all tools available on the server.
        """
        return [
            Tool(
                name="analyze_media_files",
                description=(
                    "Analyzes multiple video and audio files (or one if only one is "
                    "provided) with a multimodal AI model to understand their content. "
                    "Provide a list of media filenames and a text prompt."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "media_filenames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "A list of filenames of the media files to analyze "
                                "(e.g., ['video1.mp4', 'audio1.mp3'])."
                            ),
                        },
                        "prompt": {
                            "type": "string",
                            "description": (
                                "The text prompt for the analysis (e.g., 'Describe "
                                "what is happening in these media files.')."
                            ),
                        },
                        "source_directory": {
                            "type": "string",
                            "description": (
                                "The directory to get the media files from (default: "
                                "'videos'). Media files are stored in "
                                "/app/storage/videos/."
                            ),
                        },
                    },
                    "required": ["media_filenames", "prompt"],
                },
            ),
            Tool(
                name="read_edit_script",
                description=(
                    "Reads the current content of a script file that can be "
                    "modified for video editing. Defaults to edit.sh but can "
                    "specify any script filename."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "script_file_name": {
                            "type": "string",
                            "description": (
                                "The name of the script file to read (default: " "'edit.sh')."
                            ),
                        },
                    },
                },
            ),
            Tool(
                name="modify_edit_script",
                description=(
                    "Replace the entire content of a script file with new content. "
                    "Use this to modify scripts for different video editing tasks. "
                    "Defaults to edit.sh but can specify any script filename."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "script_content": {
                            "type": "string",
                            "description": "The complete script content to write to the file.",
                        },
                        "script_file_name": {
                            "type": "string",
                            "description": (
                                "The name of the script file to modify (default: " "'edit.sh')."
                            ),
                        },
                    },
                    "required": ["script_content"],
                },
            ),
            Tool(
                name="execute_edit_script",
                description=(
                    "Executes a script file with specified input video files and "
                    "output file. Defaults to edit.sh but can specify any script "
                    "filename."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "input_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of input video file paths to process.",
                        },
                        "output_file": {
                            "type": "string",
                            "description": (
                                "Output file path (default: "
                                "'/app/storage/videos/results/output.mp4')."
                            ),
                        },
                        "script_file_name": {
                            "type": "string",
                            "description": (
                                "The name of the script file to execute (default: " "'edit.sh')."
                            ),
                        },
                    },
                    "required": ["input_files"],
                },
            ),
            Tool(
                name="list_available_media_files",
                description=(
                    "Lists all video and audio files available in the storage "
                    "directory. Optionally includes metadata and sorts by a "
                    "specified field."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_metadata": {
                            "type": "boolean",
                            "description": (
                                "Whether to include detailed metadata (creation time, "
                                "file size, etc.). Defaults to False."
                            ),
                        },
                        "sort_by": {
                            "type": "string",
                            "description": (
                                "The metadata field to sort by. Valid fields are "
                                "'filename', 'size_bytes', 'creation_timestamp', "
                                "'modification_timestamp', 'access_timestamp'. "
                                "Defaults to 'creation_timestamp'. Only applies when "
                                "include_metadata is True."
                            ),
                            "enum": [
                                "filename",
                                "size_bytes",
                                "creation_timestamp",
                                "modification_timestamp",
                                "access_timestamp",
                            ],
                        },
                        "sort_order": {
                            "type": "string",
                            "description": (
                                "The sort order. Valid values are 'asc' (ascending) "
                                "and 'desc' (descending). Defaults to 'desc'. Only "
                                "applies when include_metadata is True."
                            ),
                            "enum": ["asc", "desc"],
                        },
                    },
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
            logging.error("Unknown tool called: %s", name)
            raise ValueError(f"Unknown tool called: {name}")

    return server


async def main():
    """Entry point that runs the MCP server over stdio."""
    try:
        server = await create_mcp_server()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    except (asyncio.CancelledError, ConnectionError) as e:
        logging.error("Failed to start MCP server: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
