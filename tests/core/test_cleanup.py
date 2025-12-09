"""Tests for cleanup worker - focusing on cleanup behavior."""

import pytest
import asyncio


class TestCleanupWorker:
    """Tests for cleanup worker behavior."""
    
    @pytest.mark.asyncio
    async def test_removes_idle_containers(self):
        """Cleanup worker removes idle containers."""
        from runbox.core.container import ContainerManager
        from runbox.core.cleanup import CleanupWorker
        from runbox.config import get_settings
        from datetime import datetime, timezone, timedelta
        
        manager = ContainerManager()
        
        try:
            # Create a container
            container, _ = await manager.get_or_create(
                identifier="cleanup-test-1",
                language="python",
            )
            
            # Manually set last_used_at to past
            container_name = container.name
            if container_name in manager._containers:
                manager._containers[container_name].last_used_at = (
                    datetime.now(timezone.utc) - timedelta(hours=2)
                )
            
            # Run cleanup
            deleted = await manager.cleanup_idle()
            
            assert container_name in deleted
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_keeps_active_containers(self):
        """Cleanup worker keeps recently used containers."""
        from runbox.core.container import ContainerManager
        
        manager = ContainerManager()
        
        try:
            # Create a container (will have recent last_used_at)
            container, _ = await manager.get_or_create(
                identifier="cleanup-test-2",
                language="python",
            )
            container_name = container.name
            
            # Run cleanup
            deleted = await manager.cleanup_idle()
            
            # Container should not be deleted
            assert container_name not in deleted
        finally:
            await manager.cleanup_by_identifier("cleanup-test-2")
            await manager.shutdown()

