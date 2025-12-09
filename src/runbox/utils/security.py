"""Security utilities for Runbox."""

import re
from typing import Any


def sanitize_identifier(identifier: str) -> str:
    """Sanitize identifier for use in container names."""
    # Allow alphanumeric, hyphens, and underscores
    sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "-", identifier)
    # Remove consecutive hyphens
    sanitized = re.sub(r"-+", "-", sanitized)
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip("-")
    # Limit length
    return sanitized[:64]


def sanitize_env_vars(env: dict[str, str]) -> dict[str, str]:
    """Sanitize environment variables."""
    sanitized = {}
    
    for key, value in env.items():
        # Validate key format
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            continue
        
        # Limit value length
        if len(value) > 32768:  # 32KB max
            value = value[:32768]
        
        sanitized[key] = value
    
    return sanitized


def validate_file_path(path: str) -> bool:
    """Validate that a file path is safe."""
    # Prevent directory traversal
    if ".." in path:
        return False
    
    # Prevent absolute paths
    if path.startswith("/"):
        return False
    
    # Prevent hidden files at root
    if path.startswith("."):
        return False
    
    # Check for valid characters
    if not re.match(r"^[a-zA-Z0-9_\-./]+$", path):
        return False
    
    return True

