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
                    "content": "Edit the videos at your disposal to make a short highlight video about the topic of the videos.",
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
