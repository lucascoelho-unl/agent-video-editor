#!/usr/bin/env python3
"""
Docker Configuration
Centralized configuration for Docker operations
"""
import os

# Container configuration
CONTAINER_NAME = "video-editor-tools"
CONTAINER_VIDEOS_PATH = "/app/videos"
CONTAINER_RESULTS_PATH = "/app/results"
CONTAINER_TEMP_PATH = "/app/temp"

# File upload configuration
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Docker command timeouts
DOCKER_COMMAND_TIMEOUT = 10
DOCKER_COPY_TIMEOUT = 30

TIMEOUT = 120

NUM_CORES = 4
