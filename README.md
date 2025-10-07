# Agentistic Video Editor Interface 🎬

This project introduces an **agentic AI solution for video editing**, designed to streamline the creative workflow from raw media to polished video. It leverages multi-agent systems and advanced prompt engineering to offer an iterative and user-feedback-driven editing experience.

---

## Motivation

The primary motivation behind this project was to explore and understand:
* **Multi-agent solutions**: How autonomous AI agents can collaborate to achieve complex tasks.
* **Prompt engineering**: Crafting effective prompts to guide AI behavior.
* **Scalable agent development**: Building agents that can efficiently handle increasing complexity and data.

---

## Features

The system facilitates a unique video editing process through several specialized AI agents:

1.  **Interviewer Agent**: Engages with the user to comprehend the creative vision and goals for the video.
2.  **Video-Editing Agent**:
    * Receives structured prompts from the Interviewer.
    * Utilizes **Gemini Video Analysis tool** to understand video content.
    * Organizes video segments based on its understanding.
    * Generates an editing script using **FFmpeg** as the editing language.
3.  **Feedback Agent**:
    * "Watches" (analyzes using the Gemini Video Analysis tool) the newly edited video.
    * Provides constructive feedback on strengths and areas for improvement.
    * This agent drives an **iterative editing loop** until the video meets predefined quality standards.

The user then reviews the final result and can initiate further agentic iterations for refinement.

---

## Implementation Details

* **Frameworks**: Developed using **Google ADK** (Agent Development Kit) and **LangGraph tracing** for monitoring token usage and evaluating improvement metrics.
* **Language**: Python.
* **Libraries**:
    * **MCP library**: Likely for multi-agent coordination.
    * **FFmpeg**: For robust video editing capabilities.
    * **Gemini Video Analysis tool**: For understanding video content and providing feedback.
    * Example of a video that can be processed by the system: [https://www.youtube.com/watch?v=6OhqVQ0lO1g](https://www.youtube.com/watch?v=6OhqVQ0lO1g)
