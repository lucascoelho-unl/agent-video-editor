"""Main entry point for the video editor agent."""

import asyncio

try:
    from .agent import create_agent
except ImportError:
    from agent import create_agent


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
                {
                    "role": "user",
                    "content": "Analyse all the media files you have and tell me what is in them.",
                }
            ],
        },
        config={"recursion_limit": 100},
    )

    print("\n--- Agent Result ---")
    print(result)
    print("--------------------")


if __name__ == "__main__":
    asyncio.run(main())
