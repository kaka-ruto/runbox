"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field, model_validator


class FileInput(BaseModel):
    """A file to be written to the container."""

    path: str = Field(..., description="File path relative to working directory")
    content: str = Field(..., description="File content")


# =============================================================================
# Setup Endpoint Schemas
# =============================================================================


class SetupRequest(BaseModel):
    """Request to set up a container environment."""

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
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables to set in the container",
    )
    timeout: int | None = Field(
        default=None,
        description="Default execution timeout in seconds",
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


class EnvironmentSnapshot(BaseModel):
    """Snapshot of the container environment."""

    os_name: str = Field(..., description="Operating system name (e.g., 'debian', 'alpine')")
    os_version: str = Field(..., description="Operating system version")
    runtime_name: str = Field(..., description="Runtime name (e.g., 'python', 'ruby', 'bash')")
    runtime_version: str = Field(..., description="Runtime version (e.g., '3.11.6')")
    packages: dict[str, str] = Field(
        ...,
        description="Installed packages with versions (e.g., {'requests': '2.31.0'})",
    )


class SetupResponse(BaseModel):
    """Response from container setup."""

    container_id: str = Field(..., description="Container identifier for use in /run")
    cached: bool = Field(..., description="Whether an existing container was reused")
    environment_snapshot: EnvironmentSnapshot = Field(
        ...,
        description="Snapshot of the container's environment",
    )


# =============================================================================
# Run Endpoint Schemas
# =============================================================================


class RunRequest(BaseModel):
    """Request to execute code in a pre-setup container."""

    container_id: str = Field(
        ...,
        description="Container ID from /setup response",
        min_length=1,
        max_length=256,
    )
    files: list[FileInput] = Field(
        ...,
        description="Files to write before execution",
        min_length=1,
    )
    run_command: str = Field(
        ...,
        description="Command to execute (e.g., 'python app.py', 'pytest test.py')",
    )
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Runtime environment variables (merged with setup env)",
    )
    timeout: int | None = Field(
        default=None,
        description="Execution timeout in seconds (overrides setup timeout)",
        ge=1,
        le=300,
    )
    new_dependencies: list[str] | None = Field(
        default=None,
        description=(
            "Optional: New dependencies to install before running. "
            "Python: ['requests==2.31.0', 'pytest']. "
            "Ruby: ['rails', 'rspec']. "
            "Shell: ['curl', 'jq', 'git'] (uses apk)"
        ),
    )


class RunResponse(BaseModel):
    """Response from code execution."""

    success: bool = Field(..., description="Whether execution completed successfully (exit code 0)")
    exit_code: int = Field(..., description="Process exit code")
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    timeout_exceeded: bool = Field(default=False, description="Whether execution timed out")
    packages: dict[str, str] | None = Field(
        default=None,
        description="Updated package list (only included if new_dependencies were installed)",
    )


# =============================================================================
# Common Schemas
# =============================================================================


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
