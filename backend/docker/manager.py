#!/usr/bin/env python3
"""
Docker Manager for Video Processing Container
Handles all Docker operations with fallback methods
"""

import subprocess
from typing import Tuple

import docker


class DockerManager:
    """Handles all Docker operations with fallback methods"""

    def __init__(self, container_name: str = "video-editor-tools"):
        self.container_name = container_name

    def get_client(self):
        """Get Docker client with fallback methods"""
        try:
            return docker.from_env()
        except Exception:
            try:
                return docker.DockerClient(base_url="unix://var/run/docker.sock")
            except Exception:
                try:
                    return docker.DockerClient(
                        base_url="unix:///Users/lucascoelho/.docker/run/docker.sock"
                    )
                except Exception:
                    raise Exception(
                        "Cannot connect to Docker daemon. Make sure Docker is running."
                    )

    def check_container_status(self) -> Tuple[bool, str]:
        """Check container status using subprocess (more reliable on macOS)"""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={self.container_name}",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                status = result.stdout.strip()
                return ("Up" in status, status)
            else:
                return (False, "Container not found")
        except subprocess.TimeoutExpired:
            return (False, "Docker command timeout")
        except FileNotFoundError:
            return (False, "Docker not found in PATH")
        except Exception as e:
            return (False, f"Error: {str(e)}")

    def exec_command(self, command: str) -> Tuple[bool, str]:
        """Execute command in container using subprocess"""
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_name] + command.split(),
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (result.returncode == 0, result.stdout.strip())
        except Exception as e:
            return (False, str(e))

    def copy_file_to_container(self, file_path: str, container_path: str) -> bool:
        """Copy file to container using subprocess"""
        try:
            result = subprocess.run(
                ["docker", "cp", file_path, f"{self.container_name}:{container_path}"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception as e:
            return False

    def copy_file_from_container(self, container_path: str, local_path: str) -> bool:
        """Copy file from container using subprocess"""
        try:
            result = subprocess.run(
                ["docker", "cp", f"{self.container_name}:{container_path}", local_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception as e:
            return False

    def list_files(self, path: str) -> Tuple[bool, list]:
        """List files in container directory"""
        success, output = self.exec_command(f"ls {path}")
        if success and output:
            files = [f.strip() for f in output.split("\n") if f.strip()]
            return (True, files)
        return (False, [])

    def delete_file(self, file_path: str) -> bool:
        """Delete file in container"""
        success, _ = self.exec_command(f"rm -f {file_path}")
        return success

    def create_directory(self, path: str) -> bool:
        """Create directory in container"""
        success, _ = self.exec_command(f"mkdir -p {path}")
        return success

    def get_container_info(self) -> dict:
        """Get detailed container information"""
        is_running, status = self.check_container_status()
        return {"name": self.container_name, "running": is_running, "status": status}
