FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for videos and results
RUN mkdir -p /app/videos /app/results /app/temp

# Keep container running
CMD ["tail", "-f", "/dev/null"]