# agent-video-editor

Agent that is able to edit videos given a prompt

# Spin up the API server

cd backend
python main.py

# Stop containers

docker-compose down

# Start containers

docker-compose up -d

# View logs

docker-compose logs -f

# Rebuild if you change Dockerfile

docker-compose build --no-cache

TODO: Move video processing to when user clicks edit button.
TODO: Make sure merged videos have the same proportions for quality sake
