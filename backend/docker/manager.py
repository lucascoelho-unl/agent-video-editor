#!/usr/bin/env python3
"""
Docker Manager for Video Processing Container
Handles all Docker operations with fallback methods
"""

import os
import subprocess
import tempfile
from typing import Tuple

import docker

from .config import TIMEOUT


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
                timeout=TIMEOUT,
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
            # Use 'sh -c' to properly handle complex commands with quotes and pipes
            full_command = ["docker", "exec", self.container_name, "sh", "-c", command]
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,  # Increased timeout for video processing
            )
            output = result.stdout.strip() or result.stderr.strip()
            return (result.returncode == 0, output)
        except Exception as e:
            return (False, str(e))

    def copy_file_to_container(self, file_path: str, container_path: str) -> bool:
        """Copy file to container using subprocess"""
        try:
            result = subprocess.run(
                ["docker", "cp", file_path, f"{self.container_name}:{container_path}"],
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
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
                timeout=TIMEOUT,
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

    def execute_script(
        self, script_content: str, container_temp_path: str = "/app/temp"
    ) -> Tuple[bool, str]:
        """
        A helper function to execute a Python script inside the container.
        Handles creating, copying, executing, and cleaning up the script.
        """
        temp_script_path = None

        try:
            # Create a temporary file to hold the script
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as temp_script:
                temp_script.write(script_content)
                temp_script_path = temp_script.name

            # Define path for the script inside the container
            container_script_path = (
                f"{container_temp_path}/{os.path.basename(temp_script_path)}"
            )

            # Copy the script to the container
            if not self.copy_file_to_container(temp_script_path, container_script_path):
                return (False, "Failed to copy script to container.")

            # Execute the script in the container
            success, output = self.exec_command(f"python3 {container_script_path}")

            # Clean up the script from the container
            self.delete_file(container_script_path)

            return (success, output)

        finally:
            # Clean up the local temporary file
            if temp_script_path and os.path.exists(temp_script_path):
                os.remove(temp_script_path)
