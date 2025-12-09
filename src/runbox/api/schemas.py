"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field


class FileInput(BaseModel):
    """A file to be written to the container."""

    path: str = Field(..., description="File path relative to working directory")
    content: str = Field(..., description="File content")


class RunRequest(BaseModel):
    """Request to execute code."""

    identifier: str = Field(
        ...,
        description="Unique identifier for container reuse (e.g., project ID, session ID)",
        min_length=1,
        max_length=128,
    )
    language: str = Field(
        ...,
        description="Programming language (python, ruby, shell)",
    )
    files: list[FileInput] = Field(
        ...,
        description="Files to write before execution",
        min_length=1,
    )
    entrypoint: str = Field(
        ...,
        description="File to execute",
    )
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables to set",
    )
    timeout: int | None = Field(
        default=None,
        description="Execution timeout in seconds (default: 30)",
        ge=1,
        le=300,
    )
    memory: str | None = Field(
        default=None,
        description="Memory limit (e.g., '256m', '1g')",
    )
    network_allow: list[str] | None = Field(
        default=None,
        description="Allowed network destinations (domains/IPs)",
    )


class RunResponse(BaseModel):
    """Response from code execution."""

    success: bool = Field(..., description="Whether execution completed successfully (exit code 0)")
    exit_code: int = Field(..., description="Process exit code")
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    container_id: str = Field(..., description="Container identifier")
    cached: bool = Field(..., description="Whether container was reused")
    timeout_exceeded: bool = Field(default=False, description="Whether execution timed out")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict | None = Field(default=None, description="Additional error details")


class ContainerDeleteResponse(BaseModel):
    """Response from container deletion."""

    deleted: list[str] = Field(..., description="List of deleted container IDs")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
