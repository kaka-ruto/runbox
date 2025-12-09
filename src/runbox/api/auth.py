"""Authentication for Runbox API."""

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from runbox.config import get_settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def verify_api_key(authorization: str | None = Security(api_key_header)) -> bool:
    """Verify the API key from the Authorization header."""
    settings = get_settings()

    if not settings.auth.enabled:
        return True

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    # Support "Bearer <token>" format
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization

    if token != settings.auth.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return True


def require_auth() -> bool:
    """Dependency for routes that require authentication."""
    return Depends(verify_api_key)
