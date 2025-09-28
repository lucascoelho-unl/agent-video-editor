"""
Main entry point for the video editor agent.
"""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from video_editor_agent import root_agent

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    session_service=session_service,
    app_name="video_editor_agent",
)


# Dockerfile CMD to run the Agent API:
# CMD["adk", "api_server", "--host", "0.0.0.0", "--port", "8000", "agent"]

# Creating a user and session id:
# curl -X POST http://localhost:8000/apps/video_editor_agent/users/user_123/sessions/session_123 \
# -H "Content-Type: application/json" \
# -d '{}'

# Making a call with the Session and User ID:
# curl -X POST http://localhost:8000/run \
# -H "Content-Type: application/json" \
# -d '{
#     "app_name": "video_editor_agent",
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
