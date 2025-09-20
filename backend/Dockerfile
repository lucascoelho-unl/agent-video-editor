FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install only essential Python packages
RUN pip install --no-cache-dir \
    opencv-python \
    moviepy

# Create directories for videos and results
RUN mkdir -p /app/videos /app/results

# Keep container running
CMD ["tail", "-f", "/dev/null"]