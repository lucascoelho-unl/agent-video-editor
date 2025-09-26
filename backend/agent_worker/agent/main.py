from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import your agent from your agent.py file
from .agent import root_agent

# 1. Create instances of the services you need
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

# 2. Create the Runner instance and pass everything to it
runner = Runner(
    agent=root_agent,
    app_name="video_editor_agent",
    session_service=session_service,
    artifact_service=artifact_service,  # The service is now configured!
)
