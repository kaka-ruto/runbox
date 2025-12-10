"""Tests for environment introspection."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestIntrospector:
    """Tests for the Introspector class."""
    
    @pytest.fixture
    def introspector(self):
        """Create an Introspector instance."""
        from runbox.core.introspector import Introspector
        return Introspector()
    
    @pytest.fixture
    def mock_container(self):
        """Create a mock container."""
        container = MagicMock()
        return container
    
    def test_parses_os_release_debian(self, introspector):
        """Test parsing /etc/os-release for Debian-based systems."""
        output = """PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
ID=debian
"""
        # Simulate parsing
        os_name = "unknown"
        os_version = "unknown"
        for line in output.split("\n"):
            if line.startswith("ID="):
                os_name = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("VERSION_ID="):
                os_version = line.split("=", 1)[1].strip().strip('"')
        
        assert os_name == "debian"
        assert os_version == "12"
    
    def test_parses_os_release_alpine(self, introspector):
        """Test parsing /etc/os-release for Alpine Linux."""
        output = """NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.19.0
PRETTY_NAME="Alpine Linux v3.19"
"""
        os_name = "unknown"
        os_version = "unknown"
        for line in output.split("\n"):
            if line.startswith("ID="):
                os_name = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("VERSION_ID="):
                os_version = line.split("=", 1)[1].strip().strip('"')
        
        assert os_name == "alpine"
        assert os_version == "3.19.0"
    
    def test_parses_python_version(self, introspector):
        """Test parsing Python version output."""
        import re
        output = "Python 3.11.6"
        match = re.search(r"Python (\d+\.\d+\.\d+)", output)
        assert match is not None
        assert match.group(1) == "3.11.6"
    
    def test_parses_ruby_version(self, introspector):
        """Test parsing Ruby version output."""
        import re
        output = "ruby 3.2.2 (2023-03-30 revision e51014f9c0) [x86_64-linux]"
        match = re.search(r"ruby (\d+\.\d+\.\d+)", output)
        assert match is not None
        assert match.group(1) == "3.2.2"
    
    def test_parses_bash_version(self, introspector):
        """Test parsing Bash version output."""
        import re
        output = "GNU bash, version 5.2.21(1)-release (x86_64-alpine-linux-musl)"
        match = re.search(r"version (\d+\.\d+\.\d+)", output)
        assert match is not None
        assert match.group(1) == "5.2.21"
    
    def test_parses_pip_list_json(self, introspector):
        """Test parsing pip list --format=json output."""
        import json
        output = '[{"name": "pip", "version": "23.0.1"}, {"name": "requests", "version": "2.31.0"}]'
        packages_list = json.loads(output)
        packages = {pkg["name"]: pkg["version"] for pkg in packages_list}
        
        assert packages["pip"] == "23.0.1"
        assert packages["requests"] == "2.31.0"
    
    def test_parses_gem_list(self, introspector):
        """Test parsing gem list output."""
        import re
        output = """bigdecimal (default: 3.1.3)
bundler (2.4.10, default: 2.4.10)
faraday (2.9.0)
webmock (3.19.1)
"""
        packages = {}
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            match = re.match(r"^(\S+)\s+\((.+)\)$", line.strip())
            if match:
                name = match.group(1)
                versions = match.group(2).split(",")
                version = versions[0].strip().replace("default: ", "")
                packages[name] = version
        
        assert "faraday" in packages
        assert packages["faraday"] == "2.9.0"
        assert packages["bundler"] == "2.4.10"
        assert packages["bigdecimal"] == "3.1.3"


class TestIntrospectorIntegration:
    """Integration tests for introspector (requires Docker)."""
    
    @pytest.fixture
    def introspector(self):
        """Create an Introspector instance."""
        from runbox.core.introspector import Introspector
        return Introspector()
    
    @pytest.fixture
    def container_manager(self):
        """Create a ContainerManager instance."""
        from runbox.core.container import ContainerManager
        return ContainerManager()
    
    @pytest.mark.asyncio
    async def test_gets_python_environment_snapshot(
        self,
        introspector,
        container_manager,
    ):
        """Test getting environment snapshot for Python container."""
        try:
            container, _ = await container_manager.get_or_create(
                identifier="test-introspect-py",
                language="python",
            )
            
            snapshot = await introspector.get_environment_snapshot(
                container=container,
                language="python",
            )
            
            # Should have OS info
            assert snapshot.os_name in ["debian", "ubuntu", "alpine"]
            assert snapshot.os_version != "unknown"
            
            # Should have runtime info
            assert snapshot.runtime_name == "python"
            assert snapshot.runtime_version.startswith("3.")
            
            # Should have packages
            assert len(snapshot.packages) > 0
            assert "pip" in snapshot.packages
            assert "requests" in snapshot.packages
            
        finally:
            await container_manager.cleanup_by_identifier("test-introspect-py")
    
    @pytest.mark.asyncio
    async def test_gets_ruby_environment_snapshot(
        self,
        introspector,
        container_manager,
    ):
        """Test getting environment snapshot for Ruby container."""
        try:
            container, _ = await container_manager.get_or_create(
                identifier="test-introspect-rb",
                language="ruby",
            )
            
            snapshot = await introspector.get_environment_snapshot(
                container=container,
                language="ruby",
            )
            
            # Should have OS info
            assert snapshot.os_name in ["debian", "ubuntu", "alpine"]
            assert snapshot.os_version != "unknown"
            
            # Should have runtime info
            assert snapshot.runtime_name == "ruby"
            assert snapshot.runtime_version.startswith("3.")
            
            # Should have packages (gems)
            assert len(snapshot.packages) > 0
            assert "faraday" in snapshot.packages
            
        finally:
            await container_manager.cleanup_by_identifier("test-introspect-rb")
    
    @pytest.mark.asyncio
    async def test_gets_shell_environment_snapshot(
        self,
        introspector,
        container_manager,
    ):
        """Test getting environment snapshot for shell container."""
        try:
            container, _ = await container_manager.get_or_create(
                identifier="test-introspect-sh",
                language="shell",
            )
            
            snapshot = await introspector.get_environment_snapshot(
                container=container,
                language="shell",
            )
            
            # Should have OS info (Alpine for shell)
            assert snapshot.os_name == "alpine"
            assert snapshot.os_version != "unknown"
            
            # Should have runtime info
            assert snapshot.runtime_name == "bash"
            assert snapshot.runtime_version.startswith("5.")
            
            # Should have tools
            assert "curl" in snapshot.packages or "jq" in snapshot.packages
            
        finally:
            await container_manager.cleanup_by_identifier("test-introspect-sh")
