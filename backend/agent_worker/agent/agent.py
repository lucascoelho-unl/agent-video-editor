# backend/agent_worker/agent/agent.py
"""Agent module for creating LangGraph agents with MCP tools."""

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

try:
    from .prompts import AGENT_INSTRUCTION
except ImportError:
    from prompts import AGENT_INSTRUCTION

MCP_SERVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server.py"))
AGENT_MODEL = os.getenv("AGENT_MODEL")


# Initialize MCP client with multiple servers
mcp_client = MultiServerMCPClient(
    {
        "mcp_server": {
            "command": "python",
            "args": [MCP_SERVER_PATH],
            "transport": "stdio",
        },
    }
)


async def create_agent():
    """
    Create and return the LangGraph agent with MCP tools.
    """
    tools = await mcp_client.get_tools()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-latest", google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    agent = create_react_agent(
        model=llm,
        tools=tools,
        # Using the original agent's instruction prompt
        prompt=AGENT_INSTRUCTION,
    )

    return agent
