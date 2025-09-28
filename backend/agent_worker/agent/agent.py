"""
Defines the video editor agent.
"""

import os

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

try:
    from .prompts import AGENT_DESCRIPTION, AGENT_INSTRUCTION
except ImportError:
    from prompts import AGENT_DESCRIPTION, AGENT_INSTRUCTION

mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server.py"))

mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python3",
            args=[mcp_server_path],
        ),
        timeout=100000,
    ),
)

root_agent = Agent(
    name="agent",
    model="gemini-2.5-pro",
    description=(AGENT_DESCRIPTION),
    instruction=(AGENT_INSTRUCTION),
    tools=[mcp_toolset],
)
