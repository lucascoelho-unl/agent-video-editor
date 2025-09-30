"""
Defines the video editor agent.
"""

import logging
import os

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

try:
    from .prompts import AGENT_DESCRIPTION, AGENT_INSTRUCTION
except ImportError:
    from prompts import AGENT_DESCRIPTION, AGENT_INSTRUCTION

# Configure logging as per ADK documentation
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server.py"))

logging.debug("MCP server path: %s", mcp_server_path)

mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python3",
            args=[mcp_server_path],
        ),
        timeout=100000,
    ),
)

logging.debug("MCP toolset initialized successfully")

root_agent = Agent(
    name="agent",
    model="gemini-2.5-pro",
    description=(AGENT_DESCRIPTION),
    instruction=(AGENT_INSTRUCTION),
    tools=[mcp_toolset],
)
logging.info("Agent initialized successfully")
