"""
Main entry point for the video editor agent.
"""

import logging

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Configure logging as per ADK documentation
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

try:
    from .agent import root_agent
except ImportError:
    from agent import root_agent

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    session_service=session_service,
    app_name="agent",
)


# Dockerfile CMD to run the Agent API:
# CMD["adk", "api_server", "--host", "0.0.0.0", "--port", "8000", "agent"]

# Creating a user and session id:
# curl -X POST http://localhost:8000/apps/agent/users/user_123/sessions/session_123 \
# -H "Content-Type: application/json" \
# -d '{}'

# Making a call with the Session and User ID:
# curl -X POST http://localhost:8000/run \
# -H "Content-Type: application/json" \
# -d '{
#     "app_name": "agent",
#     "user_id": "user_123",
#     "session_id": "session_123",
#     "new_message": {
#         "role": "user",
#         "parts": [
#             {
#                 "text": "Please edit the videos at your disposal"
#             }
#         ]
#     }
# }'
