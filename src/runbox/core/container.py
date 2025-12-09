"""Container management for Runbox."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import docker
from docker.errors import NotFound, APIError
from docker.models.containers import Container

from runbox.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ContainerInfo:
    """Information about a managed container."""
    
    container_id: str
    identifier: str
    language: str
    created_at: datetime
    last_used_at: datetime


class ContainerManager:
    """Manages Docker containers for code execution."""
    
    def __init__(self) -> None:
        """Initialize the container manager."""
        self.client = docker.from_env()
        self.settings = get_settings()
        self._containers: dict[str, ContainerInfo] = {}
        self._locks: dict[str, asyncio.Lock] = {}
    
    def _container_name(self, identifier: str, language: str) -> str:
        """Generate container name from identifier and language."""
        # Sanitize identifier for Docker naming
        safe_id = "".join(c if c.isalnum() or c == "-" else "-" for c in identifier)
        return f"{self.settings.containers.prefix}-{safe_id}-{language}"
    
    def _get_lock(self, name: str) -> asyncio.Lock:
        """Get or create a lock for a container name."""
        if name not in self._locks:
            self._locks[name] = asyncio.Lock()
        return self._locks[name]
    
    async def get_or_create(
        self,
        identifier: str,
        language: str,
        memory: str | None = None,
        network_allow: list[str] | None = None,
    ) -> tuple[Container, bool]:
        """
        Get an existing container or create a new one.
        
        Returns:
            Tuple of (container, cached) where cached is True if container existed.
        """
        name = self._container_name(identifier, language)
        lock = self._get_lock(name)
        
        async with lock:
            # Try to get existing container
            try:
                container = self.client.containers.get(name)
                if container.status != "running":
                    container.start()
                
                # Update last used time
                if name in self._containers:
                    self._containers[name].last_used_at = datetime.now(timezone.utc)
                
                logger.debug(f"Reusing existing container: {name}")
                return container, True
            except NotFound:
                pass
            
            # Create new container
            language_config = self.settings.languages[language]
            
            container = await self._create_container(
                name=name,
                image=language_config.image,
                memory=memory or self.settings.limits.memory,
                network_allow=network_allow,
            )
            
            # Track container
            now = datetime.now(timezone.utc)
            self._containers[name] = ContainerInfo(
                container_id=container.id,
                identifier=identifier,
                language=language,
                created_at=now,
                last_used_at=now,
            )
            
            logger.info(f"Created new container: {name}")
            return container, False
    
    async def _create_container(
        self,
        name: str,
        image: str,
        memory: str,
        network_allow: list[str] | None = None,
    ) -> Container:
        """Create a new container."""
        settings = self.settings
        
        # Pull image if not present
        try:
            self.client.images.get(image)
        except NotFound:
            logger.info(f"Pulling image: {image}")
            self.client.images.pull(image)
        
        # Prepare container config
        container_config: dict[str, Any] = {
            "name": name,
            "image": image,
            "command": ["sleep", "infinity"],  # Keep container running
            "detach": True,
            "working_dir": settings.containers.work_dir,
            "mem_limit": memory,
            "cpu_period": 100000,
            "cpu_quota": int(settings.limits.cpu * 100000),
            "network_mode": "bridge",
            "security_opt": ["no-new-privileges"],
            "read_only": False,  # Need to write files
            "tmpfs": {"/tmp": "size=64M,mode=1777"},
        }
        
        # Create and start container
        loop = asyncio.get_event_loop()
        container = await loop.run_in_executor(
            None,
            lambda: self.client.containers.run(**container_config),
        )
        
        # Reload container to get current status
        container.reload()
        
        # Apply network restrictions if specified
        if network_allow is not None:
            await self._apply_network_policy(container, network_allow)
        
        return container
    
    async def _apply_network_policy(
        self,
        container: Container,
        allowed_domains: list[str],
    ) -> None:
        """Apply network allowlist to container using iptables."""
        if not allowed_domains:
            # Block all outgoing traffic
            await self._exec_as_root(
                container,
                ["iptables", "-A", "OUTPUT", "-j", "DROP"],
            )
            return
        
        # Default: drop all outgoing
        await self._exec_as_root(
            container,
            ["iptables", "-P", "OUTPUT", "DROP"],
        )
        
        # Allow loopback
        await self._exec_as_root(
            container,
            ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
        )
        
        # Allow established connections
        await self._exec_as_root(
            container,
            ["iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        )
        
        # Allow DNS
        await self._exec_as_root(
            container,
            ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "ACCEPT"],
        )
        
        # Allow specific domains (resolve to IPs)
        for domain in allowed_domains:
            # Allow by domain name - using string match for HTTP Host header
            # For HTTPS, we need to allow the IP
            try:
                result = await self._exec_in_container(
                    container,
                    ["getent", "hosts", domain],
                )
                if result["exit_code"] == 0:
                    ip = result["stdout"].split()[0]
                    await self._exec_as_root(
                        container,
                        ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "ACCEPT"],
                    )
            except Exception as e:
                logger.warning(f"Failed to resolve {domain}: {e}")
    
    async def _exec_as_root(
        self,
        container: Container,
        command: list[str],
    ) -> dict[str, Any]:
        """Execute command as root in container."""
        return await self._exec_in_container(container, command, user="root")
    
    async def _exec_in_container(
        self,
        container: Container,
        command: list[str],
        user: str = "root",
    ) -> dict[str, Any]:
        """Execute a command in the container."""
        loop = asyncio.get_event_loop()
        
        def _exec() -> tuple[int, bytes]:
            exec_result = container.exec_run(
                command,
                user=user,
                demux=True,
            )
            return exec_result.exit_code, exec_result.output
        
        exit_code, output = await loop.run_in_executor(None, _exec)
        stdout = output[0].decode() if output[0] else ""
        stderr = output[1].decode() if output[1] else ""
        
        return {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        }
    
    async def cleanup_idle(self) -> list[str]:
        """Remove containers that have been idle too long."""
        deleted: list[str] = []
        now = datetime.now(timezone.utc)
        idle_timeout = self.settings.containers.idle_timeout
        
        for name, info in list(self._containers.items()):
            idle_seconds = (now - info.last_used_at).total_seconds()
            if idle_seconds > idle_timeout:
                try:
                    container = self.client.containers.get(name)
                    container.stop(timeout=5)
                    container.remove(force=True)
                    deleted.append(name)
                    del self._containers[name]
                    logger.info(f"Cleaned up idle container: {name}")
                except NotFound:
                    del self._containers[name]
                except Exception as e:
                    logger.error(f"Failed to cleanup {name}: {e}")
        
        return deleted
    
    async def cleanup_by_identifier(self, identifier: str) -> list[str]:
        """Remove all containers for a given identifier."""
        deleted: list[str] = []
        prefix = f"{self.settings.containers.prefix}-{identifier}-"
        
        # Find matching containers
        try:
            containers = self.client.containers.list(all=True)
            for container in containers:
                if container.name.startswith(prefix):
                    try:
                        container.stop(timeout=5)
                        container.remove(force=True)
                        deleted.append(container.name)
                        if container.name in self._containers:
                            del self._containers[container.name]
                        logger.info(f"Deleted container: {container.name}")
                    except Exception as e:
                        logger.error(f"Failed to delete {container.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
        
        return deleted
    
    async def shutdown(self) -> None:
        """Shutdown and cleanup all managed containers."""
        logger.info("Shutting down container manager...")
        for name in list(self._containers.keys()):
            try:
                container = self.client.containers.get(name)
                container.stop(timeout=5)
                container.remove(force=True)
                logger.info(f"Stopped container: {name}")
            except Exception as e:
                logger.warning(f"Failed to stop {name}: {e}")
        
        self._containers.clear()
        self.client.close()

