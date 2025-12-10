"""API routes for Runbox."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from runbox import __version__
from runbox.api.auth import verify_api_key
from runbox.api.schemas import (
    ContainerDeleteResponse,
    EnvironmentSnapshot,
    ErrorResponse,
    HealthResponse,
    RunRequest,
    RunResponse,
    SetupRequest,
    SetupResponse,
)
from runbox.config import get_settings
from runbox.core.runner import CodeRunner
from runbox.core.introspector import Introspector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")

# Runner and introspector instances (initialized on startup)
_runner: CodeRunner | None = None
_introspector: Introspector | None = None


def get_runner() -> CodeRunner:
    """Get the runner instance."""
    global _runner
    if _runner is None:
        _runner = CodeRunner()
    return _runner


def get_introspector() -> Introspector:
    """Get the introspector instance."""
    global _introspector
    if _introspector is None:
        _introspector = Introspector()
    return _introspector


def init_runner() -> None:
    """Initialize the runner on startup."""
    global _runner, _introspector
    _runner = CodeRunner()
    _introspector = Introspector()


async def shutdown_runner() -> None:
    """Shutdown the runner gracefully."""
    global _runner, _introspector
    if _runner:
        await _runner.shutdown()
        _runner = None
    _introspector = None


@router.post(
    "/setup",
    response_model=SetupResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Set up container",
    description="Create or reuse a container and return environment information",
)
async def setup_container(
    request: SetupRequest,
    _: bool = Depends(verify_api_key),
    runner: CodeRunner = Depends(get_runner),
    introspector: Introspector = Depends(get_introspector),
) -> SetupResponse:
    """Set up a container and return environment snapshot."""
    settings = get_settings()
    
    # Validate language
    if request.language not in settings.languages:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {request.language}. "
                   f"Supported: {list(settings.languages.keys())}",
        )
    
    try:
        # Get or create container
        container, cached = await runner.container_manager.get_or_create(
            identifier=request.identifier,
            language=request.language,
            memory=request.memory,
            network_allow=request.network_allow,
        )
        
        # Get environment snapshot
        env_snapshot = await introspector.get_environment_snapshot(
            container=container,
            language=request.language,
        )
        
        return SetupResponse(
            container_id=container.name,
            cached=cached,
            environment_snapshot=EnvironmentSnapshot(
                os_name=env_snapshot.os_name,
                os_version=env_snapshot.os_version,
                runtime_name=env_snapshot.runtime_name,
                runtime_version=env_snapshot.runtime_version,
                packages=env_snapshot.packages,
            ),
        )
    except Exception as e:
        logger.exception("Setup failed")
        raise HTTPException(
            status_code=500,
            detail=f"Setup failed: {str(e)}",
        )


@router.post(
    "/run",
    response_model=RunResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Run code",
    description="Run code in a pre-setup container",
)
async def run_code(
    request: RunRequest,
    _: bool = Depends(verify_api_key),
    runner: CodeRunner = Depends(get_runner),
) -> RunResponse:
    """Run code in a container that was set up via /setup."""
    # Validate entrypoint exists in files
    file_paths = [f.path for f in request.files]
    if request.entrypoint not in file_paths:
        raise HTTPException(
            status_code=400,
            detail=f"Entrypoint '{request.entrypoint}' not found in files: {file_paths}",
        )
    
    try:
        result = await runner.run_in_container(
            container_id=request.container_id,
            files=[(f.path, f.content) for f in request.files],
            entrypoint=request.entrypoint,
            env=request.env,
            timeout=request.timeout,
            new_dependencies=request.new_dependencies,
        )
        return RunResponse(**result)
    except ValueError as e:
        # Container not found
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Run failed")
        raise HTTPException(
            status_code=500,
            detail=f"Run failed: {str(e)}",
        )


@router.delete(
    "/containers/{identifier}",
    response_model=ContainerDeleteResponse,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Delete containers",
    description="Force cleanup all containers for an identifier",
)
async def delete_containers(
    identifier: str,
    _: bool = Depends(verify_api_key),
    runner: CodeRunner = Depends(get_runner),
) -> ContainerDeleteResponse:
    """Delete all containers for an identifier."""
    try:
        deleted = await runner.cleanup_containers(identifier)
        return ContainerDeleteResponse(deleted=deleted)
    except Exception as e:
        logger.exception("Failed to delete containers")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete containers: {str(e)}",
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check service health",
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__,
    )

