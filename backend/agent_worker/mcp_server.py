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
            logging.debug("Running tool '%s' with arguments: %s", name, kwargs)
            if asyncio.iscoroutinefunction(tool_logic_registry[name]):
                result = await tool_logic_registry[name](**kwargs)
            else:
                result = tool_logic_registry[name](**kwargs)
            logging.info("Tool '%s' executed successfully", name)
            return result
        except (KeyError, TypeError) as e:
            logging.exception("Error running tool '%s': %s", name, e)
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
                    "Analyzes video, audio, or image content using a multimodal AI to provide "
                    "insights. Use this to understand what's in the media files before "
                    "deciding on an editing strategy. The tool downloads files from "
                    "storage, analyzes them, and returns a text description."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "media_filenames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "A list of media filenames to analyze (e.g., "
                                "['video1.mp4', 'audio1.mp3', 'image1.png'])."
                            ),
                        },
                        "prompt": {
                            "type": "string",
                            "description": (
                                "The guiding question or instruction for the analysis "
                                "(e.g., 'Identify the main speaker in the audio.' or "
                                "'Summarize the key events in the video.')."
                            ),
                        },
                        "source_directory": {
                            "type": "string",
                            "description": (
                                "The source prefix in the object storage for the media "
                                "files (e.g., 'medias', 'results', 'temp'). Defaults to 'medias'."
                            ),
                        },
                    },
                    "required": ["media_filenames", "prompt"],
                },
            ),
            Tool(
                name="list_available_media_files",
                description=(
                    "Lists all video, audio, and image files in object storage, with optional "
                    "metadata and sorting. Essential for discovering what media is "
                    "available to work with."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_metadata": {
                            "type": "boolean",
                            "description": (
                                "Set to true to include detailed metadata such as file "
                                "size and last modified date. Defaults to False."
                            ),
                        },
                        "sort_by": {
                            "type": "string",
                            "description": (
                                "The field to sort by when metadata is included. "
                                "Options: 'filename', 'size_bytes', 'last_modified'. "
                                "Defaults to 'last_modified'."
                            ),
                            "enum": [
                                "filename",
                                "size_bytes",
                                "last_modified",
                            ],
                        },
                        "sort_order": {
                            "type": "string",
                            "description": (
                                "The sort order ('asc' or 'desc'). Defaults to 'desc'."
                            ),
                            "enum": ["asc", "desc"],
                        },
                    },
                },
            ),
            Tool(
                name="read_edit_script",
                description=(
                    "Reads the content of an FFmpeg script from storage. Always use "
                    "this to retrieve the current script before making changes."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "script_file_name": {
                            "type": "string",
                            "description": ("The name of the script to read (default: 'edit.sh')."),
                        },
                    },
                },
            ),
            Tool(
                name="modify_edit_script",
                description=(
                    "Overwrites an FFmpeg script in storage with new content. Use this "
                    "to update a script with your desired editing commands."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "script_content": {
                            "type": "string",
                            "description": "The full content to write to the script file.",
                        },
                        "script_file_name": {
                            "type": "string",
                            "description": (
                                "The name of the script to modify (default: 'edit.sh')."
                            ),
                        },
                    },
                    "required": ["script_content"],
                },
            ),
            Tool(
                name="execute_edit_script",
                description=(
                    "Executes an editing script on video files from storage. This tool "
                    "orchestrates a complete editing job by: 1. Downloading the "
                    "specified input video files from the 'medias/' prefix in storage. "
                    "2. Downloading the specified script from the 'scripts/' prefix. "
                    "3. Executing the script with the inputs. 4. Uploading the "
                    "resulting video to the path specified in the output_filepath. "
                    "The script receives input filenames as arguments, "
                    "followed by the output filename."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "input_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "A list of input video filenames to be processed from the "
                                "'medias' prefix in storage."
                            ),
                        },
                        "output_filepath": {
                            "type": "string",
                            "description": (
                                "The desired filepath for the output video, which will be "
                                "stored in object storage (e.g., 'results/my_video.mp4')."
                            ),
                        },
                        "script_file_name": {
                            "type": "string",
                            "description": (
                                "The name of the script file to execute (default: " "'edit.sh')."
                            ),
                        },
                    },
                    "required": ["input_files", "output_filepath"],
                },
            ),
        ]

    @server.call_tool()
    async def execute_any_tool(name: str, arguments: dict) -> Dict[str, Any]:
        """
        Executes a tool by name with the given arguments.
        """
        logging.info("Received request to execute tool '%s'", name)
        if name in tool_logic_registry:
            result_str = await run_tool(name, **arguments)
            logging.debug("Tool '%s' returned: %s", name, result_str)
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

    logging.info("MCP server created successfully")
    return server


async def main():
    """Entry point that runs the MCP server over stdio."""
    try:
        logging.info("Starting MCP server...")
        server = await create_mcp_server()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
        logging.info("MCP server stopped gracefully")
    except (asyncio.CancelledError, ConnectionError) as e:
        logging.error("MCP server failed to start or unexpectedly stopped: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
