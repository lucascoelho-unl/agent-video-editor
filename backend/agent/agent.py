import os

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

from .prompts import agent_description, agent_instruction

mcp_server_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "mcp_server.py")
)

mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python3",
            args=[mcp_server_path],
        ),
    ),
)

root_agent = Agent(
    name="video_editor_agent",
    model="gemini-2.5-pro",
    description=(agent_description),
    instruction=(agent_instruction),
    tools=[mcp_toolset],
)
