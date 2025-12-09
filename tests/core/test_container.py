"""Tests for container management - focusing on lifecycle behavior."""

import pytest


class TestContainerLifecycle:
    """Tests for container lifecycle behavior."""
    
    @pytest.mark.asyncio
    async def test_creates_container_on_first_request(self):
        """Container manager creates container on first request."""
        from runbox.core.container import ContainerManager
        import docker
        
        manager = ContainerManager()
        client = docker.from_env()
        
        try:
            container, cached = await manager.get_or_create(
                identifier="lifecycle-test-1",
                language="python",
            )
            
            assert cached is False
            assert container is not None
            assert container.status == "running"
        finally:
            await manager.cleanup_by_identifier("lifecycle-test-1")
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_reuses_existing_container(self):
        """Container manager reuses existing container."""
        from runbox.core.container import ContainerManager
        
        manager = ContainerManager()
        
        try:
            container1, cached1 = await manager.get_or_create(
                identifier="lifecycle-test-2",
                language="python",
            )
            
            container2, cached2 = await manager.get_or_create(
                identifier="lifecycle-test-2",
                language="python",
            )
            
            assert cached1 is False
            assert cached2 is True
            assert container1.id == container2.id
        finally:
            await manager.cleanup_by_identifier("lifecycle-test-2")
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_creates_separate_containers_per_language(self):
        """Container manager creates separate containers for different languages."""
        from runbox.core.container import ContainerManager
        
        manager = ContainerManager()
        
        try:
            python_container, _ = await manager.get_or_create(
                identifier="lifecycle-test-3",
                language="python",
            )
            
            ruby_container, _ = await manager.get_or_create(
                identifier="lifecycle-test-3",
                language="ruby",
            )
            
            assert python_container.id != ruby_container.id
            assert "python" in python_container.name
            assert "ruby" in ruby_container.name
        finally:
            await manager.cleanup_by_identifier("lifecycle-test-3")
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_cleanup_removes_containers(self):
        """Container manager removes containers on cleanup."""
        from runbox.core.container import ContainerManager
        import docker
        
        manager = ContainerManager()
        client = docker.from_env()
        
        try:
            container, _ = await manager.get_or_create(
                identifier="lifecycle-test-4",
                language="python",
            )
            container_name = container.name
            
            deleted = await manager.cleanup_by_identifier("lifecycle-test-4")
            
            assert container_name in deleted
            
            # Verify container is gone
            containers = client.containers.list(all=True)
            names = [c.name for c in containers]
            assert container_name not in names
        finally:
            await manager.shutdown()

