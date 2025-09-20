#!/usr/bin/env python3
"""
Docker Factory
Factory functions for creating Docker services
"""

from .manager import DockerManager
from .video_service import VideoService
from .config import CONTAINER_NAME


def create_docker_manager(container_name: str = None) -> DockerManager:
    """Create a DockerManager instance"""
    return DockerManager(container_name or CONTAINER_NAME)


def create_video_service(container_name: str = None) -> VideoService:
    """Create a VideoService instance"""
    docker_manager = create_docker_manager(container_name)
    return VideoService(docker_manager)


def create_services(container_name: str = None) -> tuple[DockerManager, VideoService]:
    """Create both DockerManager and VideoService instances"""
    docker_manager = create_docker_manager(container_name)
    video_service = VideoService(docker_manager)
    return docker_manager, video_service
