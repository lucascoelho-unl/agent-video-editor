#!/usr/bin/env python3
"""
Docker Manager for Video Processing Container
Handles all Docker operations with fallback methods
"""

import asyncio
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

    async def check_container_status(self) -> Tuple[bool, str]:
        """Check container status using subprocess (more reliable on macOS)"""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker",
                "ps",
                "--filter",
                f"name={self.container_name}",
                "--format",
                "{{.Status}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=TIMEOUT
            )

            if process.returncode == 0 and stdout:
                status = stdout.decode().strip()
                return ("Up" in status, status)
            else:
                return (False, "Container not found")
        except asyncio.TimeoutError:
            return (False, "Docker command timeout")
        except FileNotFoundError:
            return (False, "Docker not found in PATH")
        except Exception as e:
            return (False, f"Error: {str(e)}")

    async def exec_command(self, command: str) -> Tuple[bool, str]:
        """Execute command in container using asyncio subprocess"""
        try:
            full_command = ["docker", "exec", self.container_name, "sh", "-c", command]
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=TIMEOUT
            )
            output = stdout.decode().strip() or stderr.decode().strip()
            return (process.returncode == 0, output)
        except Exception as e:
            return (False, str(e))

    async def copy_file_to_container(self, file_path: str, container_path: str) -> bool:
        """Copy file to container using asyncio subprocess"""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker",
                "cp",
                file_path,
                f"{self.container_name}:{container_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=TIMEOUT)
            return process.returncode == 0
        except Exception as e:
            return False

    async def copy_file_from_container(
        self, container_path: str, local_path: str
    ) -> bool:
        """Copy file from container using asyncio subprocess"""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker",
                "cp",
                f"{self.container_name}:{container_path}",
                local_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=TIMEOUT)
            return process.returncode == 0
        except Exception as e:
            return False

    async def list_files(self, path: str) -> Tuple[bool, list]:
        """List files in container directory"""
        success, output = await self.exec_command(f"ls {path}")
        if success and output:
            files = [f.strip() for f in output.split("\n") if f.strip()]
            return (True, files)
        return (False, [])

    async def delete_file(self, file_path: str) -> bool:
        """Delete file in container"""
        success, _ = await self.exec_command(f"rm -f {file_path}")
        return success

    async def execute_script(
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
            if not await self.copy_file_to_container(
                temp_script_path, container_script_path
            ):
                return (False, "Failed to copy script to container.")

            # Execute the script in the container
            success, output = await self.exec_command(
                f"python3 {container_script_path}"
            )

            # Clean up the script from the container
            await self.delete_file(container_script_path)

            return (success, output)

        finally:
            # Clean up the local temporary file
            if temp_script_path and os.path.exists(temp_script_path):
                os.remove(temp_script_path)
