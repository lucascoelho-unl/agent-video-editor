"""
Main entry point for the video editor agent.
"""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from .agent import root_agent

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    session_service=session_service,
    app_name="video_editor_agent",
)
