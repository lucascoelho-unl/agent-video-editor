from google.adk.runners import Runner

from .agent import root_agent

runner = Runner(
    agent=root_agent,
    app_name="video_editor_agent",
)
