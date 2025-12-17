"""Environment introspection for containers."""

import asyncio
import json
import logging
import re
from dataclasses import dataclass

from docker.models.containers import Container

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentSnapshot:
    """Snapshot of the container environment."""
    
    os_name: str
    os_version: str
    runtime_name: str
    runtime_version: str
    packages: dict[str, str]  # package_name -> version


class Introspector:
    """Introspects container environments to gather runtime information."""
    
    # Commands for getting OS info (works on both Alpine and Debian)
    OS_INFO_COMMAND = ["sh", "-c", "cat /etc/os-release 2>/dev/null || echo 'ID=unknown\nVERSION_ID=unknown'"]
    
    # Language-specific version and package commands
    LANGUAGE_COMMANDS = {
        "python": {
            "version": ["python", "--version"],
            "packages": ["pip", "list", "--format=json"],
        },
        "ruby": {
            "version": ["ruby", "--version"],
            "packages": ["gem", "list", "--local", "--no-versions"],  # We'll parse with versions separately
        },
        "shell": {
            "version": ["bash", "--version"],
            "packages": None,  # Shell doesn't have packages in the same way
        },
    }
    
    async def get_environment_snapshot(
        self,
        container: Container,
        language: str,
    ) -> EnvironmentSnapshot:
        """
        Get a snapshot of the container's environment.
        
        Args:
            container: Docker container to introspect
            language: Programming language of the container
            
        Returns:
            EnvironmentSnapshot with OS, runtime, and package information
        """
        # Get OS info
        os_name, os_version = await self._get_os_info(container)
        
        # Get runtime info
        runtime_name, runtime_version = await self._get_runtime_info(container, language)
        
        # Get installed packages
        packages = await self._get_packages(container, language)
        
        return EnvironmentSnapshot(
            os_name=os_name,
            os_version=os_version,
            runtime_name=runtime_name,
            runtime_version=runtime_version,
            packages=packages,
        )
    
    async def _get_os_info(self, container: Container) -> tuple[str, str]:
        """Get OS name and version from /etc/os-release."""
        result = await self._exec_in_container(container, self.OS_INFO_COMMAND)
        
        if result["exit_code"] != 0:
            return "unknown", "unknown"
        
        output = result["stdout"]
        os_name = "unknown"
        os_version = "unknown"
        
        for line in output.split("\n"):
            if line.startswith("ID="):
                os_name = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("VERSION_ID="):
                os_version = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("PRETTY_NAME=") and os_name == "unknown":
                # Fallback to PRETTY_NAME if ID is not available
                os_name = line.split("=", 1)[1].strip().strip('"')
        
        return os_name, os_version
    
    async def _get_runtime_info(
        self,
        container: Container,
        language: str,
    ) -> tuple[str, str]:
        """Get runtime name and version."""
        commands = self.LANGUAGE_COMMANDS.get(language)
        if not commands:
            return language, "unknown"
        
        result = await self._exec_in_container(container, commands["version"])
        
        if result["exit_code"] != 0:
            return language, "unknown"
        
        output = result["stdout"].strip()
        
        # Parse version based on language
        if language == "python":
            # Output: "Python 3.11.6"
            match = re.search(r"Python (\d+\.\d+\.\d+)", output)
            version = match.group(1) if match else "unknown"
            return "python", version
            
        elif language == "ruby":
            # Output: "ruby 3.2.2 (2023-03-30 revision e51014f9c0) [x86_64-linux]"
            match = re.search(r"ruby (\d+\.\d+\.\d+)", output)
            version = match.group(1) if match else "unknown"
            return "ruby", version
            
        elif language == "shell":
            # Output: "GNU bash, version 5.2.21(1)-release (x86_64-alpine-linux-musl)"
            match = re.search(r"version (\d+\.\d+\.\d+)", output)
            version = match.group(1) if match else "unknown"
            return "bash", version
        
        return language, "unknown"
    
    async def _get_packages(
        self,
        container: Container,
        language: str,
    ) -> dict[str, str]:
        """Get installed packages for the language."""
        commands = self.LANGUAGE_COMMANDS.get(language)
        if not commands or commands.get("packages") is None:
            # For shell, return common tools
            if language == "shell":
                return await self._get_shell_tools(container)
            return {}
        
        if language == "python":
            return await self._get_python_packages(container)
        elif language == "ruby":
            return await self._get_ruby_packages(container)
        
        return {}
    
    async def _get_python_packages(self, container: Container) -> dict[str, str]:
        """Get installed Python packages via pip."""
        result = await self._exec_in_container(
            container,
            ["pip", "list", "--format=json"],
        )
        
        if result["exit_code"] != 0:
            logger.warning(f"Failed to get Python packages: {result['stderr']}")
            return {}
        
        try:
            packages_list = json.loads(result["stdout"])
            return {pkg["name"]: pkg["version"] for pkg in packages_list}
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse pip list output: {e}")
            return {}
    
    async def _get_ruby_packages(self, container: Container) -> dict[str, str]:
        """Get installed Ruby gems."""
        # Use gem list with versions
        result = await self._exec_in_container(
            container,
            ["gem", "list", "--local"],
        )
        
        if result["exit_code"] != 0:
            logger.warning(f"Failed to get Ruby gems: {result['stderr']}")
            return {}
        
        packages = {}
        # Parse output like: "bundler (2.4.10, default: 2.4.10)"
        for line in result["stdout"].strip().split("\n"):
            if not line.strip():
                continue
            match = re.match(r"^(\S+)\s+\((.+)\)$", line.strip())
            if match:
                name = match.group(1)
                # Take first version (may have multiple)
                versions = match.group(2).split(",")
                version = versions[0].strip().replace("default: ", "")
                packages[name] = version
        
        return packages
    
    # Alpine system packages to exclude (these come pre-installed and aren't useful to report)
    ALPINE_SYSTEM_PACKAGES = {
        # Core Alpine packages
        "alpine-baselayout", "alpine-baselayout-data", "alpine-keys", "apk-tools",
        "busybox", "busybox-binsh", "libc-utils", "musl", "musl-utils",
        # SSL/crypto libraries
        "ca-certificates", "ca-certificates-bundle", "libcrypto3", "libssl3", 
        "ssl_client", "openssl",
        # System utilities  
        "scanelf", "zlib", "libgcc", "libstdc++",
        # Network infrastructure (dependencies, not tools)
        "libidn2", "libunistring", "nghttp2-libs", "libpsl", "libcurl",
        "c-ares", "brotli-libs",
        # iptables infrastructure
        "iptables", "libmnl", "libnftnl", "libnetfilter_conntrack", "libnl3",
        # DNS tools dependencies
        "bind-libs", "bind-tools", "fstrm", "json-c", "krb5-libs", 
        "libcom_err", "libverto", "protobuf-c", "keyutils-libs",
        # Other system libs
        "libedit", "ncurses-libs", "ncurses-terminfo-base", "readline",
        "oniguruma",  # jq dependency
    }

    async def _get_shell_tools(self, container: Container) -> dict[str, str]:
        """
        Get installed packages via apk (Alpine).
        
        This returns only user-installed tools (curl, jq, bats, etc.),
        filtering out system dependencies. The list updates dynamically
        when new packages are installed via apk.
        """
        result = await self._exec_in_container(
            container, 
            ["sh", "-c", "apk list --installed 2>/dev/null"]
        )
        
        if result["exit_code"] == 0 and result["stdout"].strip():
            packages = {}
            # Parse apk output: "curl-8.5.0-r0 x86_64 {curl} (MIT)"
            for line in result["stdout"].strip().split("\n"):
                if not line.strip():
                    continue
                # Extract package name and version
                match = re.match(r"^([a-zA-Z0-9_-]+)-(\d+\.\d+(?:\.\d+)?)", line.strip())
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    # Only include packages NOT in the system exclusion list
                    if name not in self.ALPINE_SYSTEM_PACKAGES:
                        packages[name] = version
            return packages
        
        # Fallback: check individual tools (for non-Alpine systems like Debian)
        tools = {
            "curl": ["curl", "--version"],
            "jq": ["jq", "--version"],
            "bats": ["bats", "--version"],
        }
        
        packages = {}
        for tool, cmd in tools.items():
            result = await self._exec_in_container(container, cmd)
            if result["exit_code"] == 0:
                output = result["stdout"].strip()
                first_line = output.split("\n")[0]
                match = re.search(r"(\d+\.\d+(?:\.\d+)?)", first_line)
                if match:
                    packages[tool] = match.group(1)
        
        return packages
    
    async def _exec_in_container(
        self,
        container: Container,
        command: list[str],
    ) -> dict[str, str]:
        """Execute a command in the container."""
        loop = asyncio.get_event_loop()
        
        def _exec() -> tuple[int, bytes, bytes]:
            exec_result = container.exec_run(
                command,
                user="root",
                demux=True,
            )
            output = exec_result.output
            stdout = output[0] if output and output[0] else b""
            stderr = output[1] if output and output[1] else b""
            return exec_result.exit_code, stdout, stderr
        
        exit_code, stdout_bytes, stderr_bytes = await loop.run_in_executor(None, _exec)
        
        return {
            "exit_code": exit_code,
            "stdout": stdout_bytes.decode("utf-8", errors="replace"),
            "stderr": stderr_bytes.decode("utf-8", errors="replace"),
        }
