cd backend\
python main.py

cd frontend\
npm start

cd backend\
adk web

cd backend:\
-docker-compose down\
-docker-compose up -d\
-docker-compose logs -f\
-docker-compose build --no-cache

- TODO: Log all parts of the merging videos function to spot what is taking longer and improve eficiency.
- TODO: Create video processing to store information in the container. Video processing whenever it is uploaded with transctips, time stamps, metadata etc
- TODO: Add following agent specialized in analizing transcript context and organizing the merging order
- TODO: Move video processing to when user clicks edit button.
- TODO: Make sure merged videos have the same proportions for quality sake

---

TODO HIGHEST PRIORITY: Organize building blocks for major future upcomings (have building blocks ready) Code organization and simplicity is top priority right now.

---

TODO BIIIG REFACTORING: Scalability Roadmap

Phase 1 (Refactor Locally):

- Separate your current backend into two parts: the API server (FastAPI) and the worker logic.
- Introduce Redis and Celery into your docker-compose.yml file.
- Change the API to add jobs to the queue instead of doing the work itself.
- Modify your video processing code to run as a Celery worker that listens to the queue.

Phase 2 (Initial Deployment):

- Deploy your docker-compose stack to a single VM on a cloud provider (e.g., DigitalOcean, AWS EC2).
- Use managed services for your database (e.g., AWS RDS) and file storage (AWS S3) from the start.

Phase 3 (True Scaling):

- When you need more power than one VM can provide, migrate your containers from the VM to a container orchestration service like AWS ECS or Google Cloud Run.
- Set up auto-scaling rules for your workers based on the length of the job queue.
- This architecture is the standard for building scalable, resilient applications and will provide the excellent building blocks you're looking for.

---

TODO: Add following agent specialized in analizing transcript context and organizing the merging order
TODO: Move video processing to when user clicks edit button. (need to have an edit button)
TODO: Make sure merged videos have the same proportions for quality sake
TODO: Make cuts inside the video for simplicity and pacing. Remove buzzwords per say, and repetitive video parts overall (I think this gemini tool will be extremelly helpful for this. https://www.youtube.com/watch?v=6OhqVQ0lO1g)
TODO: Make tool communication by HTTP Stremable Manager (just like creevo)

---

Ideally, I would open a moviepy "server" and have the docker call tools that "change" the videos inside the "server" per say. This way we can have the output be processed only once.

What can we do?

1. Decide what method to use for the transcripts
2. Create a "server" that runs in the container, and tools that call "endpoints" in this server and do stuff.
3. On startup, videos are processed into the container, and into the server. Agent then do its thing for editing, and at the end, process the video back up.
   3.1 While the server is running in the docker container, the agent needs to be able to understand the context of the videos, for this, the video processing will occur using gemini's video processing tools
   3.2 After that, the agent delegates another agent to contextualize and organize the videos and return a list of merging order (maybe gemini video editor can do this!)
   3.3 The editing agent then goes to the video folder and merges the videos given the list that was returned to him

---

---

---

---

---

---

---

Intelligent Clip Extraction (Smart B-Roll):
Concept: The agent could automatically identify and extract interesting or relevant clips from a longer video.
User Flow: A user could ask the agent, "Create a highlight reel of all the funny moments from this video," and the agent would use Gemini to identify those moments and merge them into a new clip.

Transcript-Based Editing:
Concept: Since you're already extracting transcripts, you can take this a step further. The agent could use Gemini to understand the context of the transcript and perform edits based on it.
User Flow: A user could say, "Merge all the clips where the speaker is talking about 'AI'," and the agent would use the transcript and Gemini's understanding to find and merge the relevant video segments.

Automated Video Chaptering:
Concept: For longer videos, the agent could automatically identify different topics or scenes and create video chapters.
User Flow: A user uploads a long video, and the agent uses Gemini to analyze the content and generate a list of chapters with timestamps and descriptions, which could be displayed in the video player.
