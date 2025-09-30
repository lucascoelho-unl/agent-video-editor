FROM python:3.13-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make test script executable
RUN chmod +x test_timing.py

# Ensure Python output is unbuffered for real-time logging
ENV PYTHONUNBUFFERED=1

# CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8000", "agent"]
CMD ["adk", "web", "--host", "0.0.0.0", "--log_level", "INFO"]
