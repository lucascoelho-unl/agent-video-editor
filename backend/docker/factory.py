#!/usr/bin/env python3
"""
Docker Factory
Factory functions for creating Docker services
"""

from .manager import DockerManager
from .video_service import VideoService


def create_docker_manager() -> DockerManager:
    """Create and return a DockerManager instance"""
    return DockerManager()


def create_video_service() -> VideoService:
    """Create and return a VideoService instance"""
    docker_manager = create_docker_manager()
    return VideoService(docker_manager)


def create_services() -> tuple[DockerManager, VideoService]:
    """Create and return a tuple of services"""
    docker_manager = create_docker_manager()
    video_service = VideoService(docker_manager)
    return docker_manager, video_service
