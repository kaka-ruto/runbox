"""API routes for Runbox."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from runbox import __version__
from runbox.api.auth import verify_api_key
from runbox.api.schemas import (
    ContainerDeleteResponse,
    ErrorResponse,
    HealthResponse,
    RunRequest,
    RunResponse,
)
from runbox.config import get_settings
from runbox.core.executor import CodeExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")

# Executor instance (initialized on startup)
_executor: CodeExecutor | None = None


def get_executor() -> CodeExecutor:
    """Get the executor instance."""
    global _executor
    if _executor is None:
        _executor = CodeExecutor()
    return _executor


def init_executor() -> None:
    """Initialize the executor on startup."""
    global _executor
    _executor = CodeExecutor()


async def shutdown_executor() -> None:
    """Shutdown the executor gracefully."""
    global _executor
    if _executor:
        await _executor.shutdown()
        _executor = None


@router.post(
    "/run",
    response_model=RunResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Execute code",
    description="Execute code in an isolated container",
)
async def run_code(
    request: RunRequest,
    _: bool = Depends(verify_api_key),
    executor: CodeExecutor = Depends(get_executor),
) -> RunResponse:
    """Execute code in a sandboxed container."""
    settings = get_settings()
    
    # Validate language
    if request.language not in settings.languages:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {request.language}. "
                   f"Supported: {list(settings.languages.keys())}",
        )
    
    # Validate entrypoint exists in files
    file_paths = [f.path for f in request.files]
    if request.entrypoint not in file_paths:
        raise HTTPException(
            status_code=400,
            detail=f"Entrypoint '{request.entrypoint}' not found in files: {file_paths}",
        )
    
    try:
        result = await executor.execute(
            identifier=request.identifier,
            language=request.language,
            files=[(f.path, f.content) for f in request.files],
            entrypoint=request.entrypoint,
            env=request.env,
            timeout=request.timeout,
            memory=request.memory,
            network_allow=request.network_allow,
        )
        return RunResponse(**result)
    except Exception as e:
        logger.exception("Execution failed")
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {str(e)}",
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
    executor: CodeExecutor = Depends(get_executor),
) -> ContainerDeleteResponse:
    """Delete all containers for an identifier."""
    try:
        deleted = await executor.cleanup_containers(identifier)
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
