"""Background cleanup worker for Runbox."""

import asyncio
import logging

from runbox.config import get_settings
from runbox.core.container import ContainerManager

logger = logging.getLogger(__name__)


class CleanupWorker:
    """Background worker that cleans up idle containers."""
    
    def __init__(self, container_manager: ContainerManager) -> None:
        """Initialize the cleanup worker."""
        self.container_manager = container_manager
        self.settings = get_settings()
        self._running = False
        self._task: asyncio.Task | None = None
    
    async def start(self) -> None:
        """Start the cleanup worker."""
        if not self.settings.cleanup.enabled:
            logger.info("Cleanup worker disabled")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Cleanup worker started")
    
    async def stop(self) -> None:
        """Stop the cleanup worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Cleanup worker stopped")
    
    async def _run(self) -> None:
        """Main cleanup loop."""
        interval = self.settings.cleanup.interval
        
        while self._running:
            try:
                await asyncio.sleep(interval)
                
                if not self._running:
                    break
                
                deleted = await self.container_manager.cleanup_idle()
                if deleted:
                    logger.info(f"Cleaned up {len(deleted)} idle containers")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Cleanup worker error: {e}")
                await asyncio.sleep(60)  # Wait before retry

