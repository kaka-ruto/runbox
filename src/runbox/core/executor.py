"""Code execution logic for Runbox."""

import asyncio
import logging
import time
from typing import Any

from docker.models.containers import Container

from runbox.config import get_settings
from runbox.core.container import ContainerManager

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Error during code execution."""
    pass


class TimeoutError(ExecutionError):
    """Execution timed out."""
    pass


class CodeExecutor:
    """Executes code in sandboxed containers."""
    
    def __init__(self) -> None:
        """Initialize the executor."""
        self.settings = get_settings()
        self.container_manager = ContainerManager()
    
    async def execute(
        self,
        identifier: str,
        language: str,
        files: list[tuple[str, str]],
        entrypoint: str,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
        memory: str | None = None,
        network_allow: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute code in a sandboxed container.
        
        Args:
            identifier: Unique identifier for container reuse
            language: Programming language
            files: List of (path, content) tuples
            entrypoint: File to execute
            env: Environment variables
            timeout: Execution timeout in seconds
            memory: Memory limit
            network_allow: Allowed network destinations
        
        Returns:
            Execution result dictionary
        """
        timeout = timeout or self.settings.limits.timeout
        env = env or {}
        
        # Get or create container
        container, cached = await self.container_manager.get_or_create(
            identifier=identifier,
            language=language,
            memory=memory,
            network_allow=network_allow,
        )
        
        container_name = container.name
        
        try:
            # Clean working directory
            await self._clean_workdir(container)
            
            # Write files to container
            await self._write_files(container, files)
            
            # Execute code
            start_time = time.monotonic()
            result = await self._run_code(
                container=container,
                language=language,
                entrypoint=entrypoint,
                env=env,
                timeout=timeout,
            )
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            
            return {
                "success": result["exit_code"] == 0 and not result.get("timeout", False),
                "exit_code": result["exit_code"],
                "stdout": self._truncate_output(result["stdout"]),
                "stderr": self._truncate_output(result["stderr"]),
                "execution_time_ms": execution_time_ms,
                "container_id": container_name,
                "cached": cached,
                "timeout_exceeded": result.get("timeout", False),
            }
            
        except Exception as e:
            logger.exception(f"Execution failed in {container_name}")
            raise ExecutionError(f"Execution failed: {str(e)}")
    
    async def _clean_workdir(self, container: Container) -> None:
        """Clean the working directory in the container."""
        workdir = self.settings.containers.work_dir
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: container.exec_run(
                ["sh", "-c", f"rm -rf {workdir}/* {workdir}/.*"],
                user="root",
            ),
        )
    
    async def _write_files(
        self,
        container: Container,
        files: list[tuple[str, str]],
    ) -> None:
        """Write files to the container."""
        import io
        import tarfile
        
        workdir = self.settings.containers.work_dir
        
        # Create tar archive in memory
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            for path, content in files:
                # Create file info
                file_data = content.encode("utf-8")
                file_info = tarfile.TarInfo(name=path)
                file_info.size = len(file_data)
                file_info.mode = 0o644
                
                # Add to archive
                tar.addfile(file_info, io.BytesIO(file_data))
        
        tar_buffer.seek(0)
        
        # Copy to container
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: container.put_archive(workdir, tar_buffer),
        )
    
    async def _run_code(
        self,
        container: Container,
        language: str,
        entrypoint: str,
        env: dict[str, str],
        timeout: int,
    ) -> dict[str, Any]:
        """Run code in the container with timeout."""
        language_config = self.settings.languages[language]
        workdir = self.settings.containers.work_dir
        
        # Build command
        cmd = [language_config.entrypoint_cmd, f"{workdir}/{entrypoint}"]
        
        loop = asyncio.get_event_loop()
        
        # Create exec instance
        def create_exec() -> Any:
            return container.client.api.exec_create(
                container.id,
                cmd,
                environment=env,
                workdir=workdir,
                user="nobody",  # Run as unprivileged user
            )
        
        exec_instance = await loop.run_in_executor(None, create_exec)
        exec_id = exec_instance["Id"]
        
        # Start exec and get output with timeout
        def start_exec() -> tuple[bytes, bytes]:
            output = container.client.api.exec_start(
                exec_id,
                demux=True,
            )
            return output if output else (b"", b"")
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                loop.run_in_executor(None, start_exec),
                timeout=timeout,
            )
            
            # Get exit code
            def get_exit_code() -> int:
                inspect = container.client.api.exec_inspect(exec_id)
                return inspect.get("ExitCode", -1)
            
            exit_code = await loop.run_in_executor(None, get_exit_code)
            
            return {
                "exit_code": exit_code,
                "stdout": stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else "",
                "stderr": stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else "",
                "timeout": False,
            }
            
        except asyncio.TimeoutError:
            # Kill the process
            logger.warning(f"Execution timed out after {timeout}s")
            
            # Try to kill any running processes
            try:
                await loop.run_in_executor(
                    None,
                    lambda: container.exec_run(
                        ["pkill", "-9", "-f", entrypoint],
                        user="root",
                    ),
                )
            except Exception:
                pass
            
            return {
                "exit_code": 124,  # Standard timeout exit code
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds",
                "timeout": True,
            }
    
    def _truncate_output(self, output: str) -> str:
        """Truncate output to max size."""
        max_size = self.settings.limits.output_max
        if len(output) > max_size:
            return output[:max_size] + f"\n... (truncated, exceeded {max_size} bytes)"
        return output
    
    async def cleanup_containers(self, identifier: str) -> list[str]:
        """Cleanup all containers for an identifier."""
        return await self.container_manager.cleanup_by_identifier(identifier)
    
    async def shutdown(self) -> None:
        """Shutdown the executor."""
        await self.container_manager.shutdown()

