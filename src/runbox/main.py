"""Main entry point for Runbox server."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from runbox import __version__
from runbox.api.routes import router, init_runner, shutdown_runner, get_runner
from runbox.config import init_settings, get_settings
from runbox.core.cleanup import CleanupWorker
from runbox.utils.docker import check_docker_connection

# Load .env file if it exists (for local development)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Cleanup worker instance
_cleanup_worker: CleanupWorker | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global _cleanup_worker
    
    # Startup
    logger.info(f"Starting Runbox v{__version__}")
    
    # Check Docker connection
    if not check_docker_connection():
        logger.error("Docker is not available. Please ensure Docker is running.")
        raise RuntimeError("Docker not available")
    
    # Initialize runner
    init_runner()
    
    # Start cleanup worker
    runner = get_runner()
    _cleanup_worker = CleanupWorker(runner.container_manager)
    await _cleanup_worker.start()
    
    logger.info("Runbox started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Runbox...")
    
    if _cleanup_worker:
        await _cleanup_worker.stop()
    
    await shutdown_runner()
    
    logger.info("Runbox shutdown complete")


def create_app(config_path: str | None = None) -> FastAPI:
    """Create the FastAPI application."""
    # Initialize settings
    init_settings(config_path)
    settings = get_settings()
    
    app = FastAPI(
        title="Runbox",
        description="A fast, secure API for running code in isolated containers",
        version=__version__,
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(router)
    
    return app


def run() -> None:
    """Run the server."""
    config_path = os.environ.get("RUNBOX_CONFIG")
    init_settings(config_path)
    settings = get_settings()
    
    app = create_app(config_path)
    
    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
        log_level="info",
    )


# For running with `python -m runbox.main`
if __name__ == "__main__":
    run()

