FROM python:3.13-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/storage/videos

COPY . .

CMD ["adk", "web", "--host", "0.0.0.0"]
