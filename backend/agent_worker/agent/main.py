# backend/agent_worker/agent/main.py
import asyncio
import os

from dotenv import load_dotenv

try:
    from .agent import create_agent
except ImportError:
    from agent import create_agent

# Load environment variables from .env file
load_dotenv()


async def main():
    """
    Create and run the video editor agent with a sample task.
    """
    print("Creating LangGraph agent...")
    agent = await create_agent()
    print("Agent created. Invoking with a sample task...")

    # Example task for the video agent
    result = await agent.ainvoke(
        {
            "messages": [
                {"role": "user", "content": "First, list all the available media files for me."}
            ],
        },
        config={"recursion_limit": 100},
    )

    print("\n--- Agent Result ---")
    print(result)
    print("--------------------")


if __name__ == "__main__":
    # This will run the agent once when the script is executed.
    # Traces will be sent to LangSmith automatically due to the environment variables.
    asyncio.run(main())
