"""Network policy management for Runbox."""

import asyncio
import logging
import socket
from typing import Any

logger = logging.getLogger(__name__)


async def resolve_domain(domain: str) -> list[str]:
    """Resolve a domain to IP addresses."""
    loop = asyncio.get_event_loop()
    
    try:
        result = await loop.run_in_executor(
            None,
            lambda: socket.getaddrinfo(domain, None, socket.AF_INET),
        )
        ips = list(set(addr[4][0] for addr in result))
        return ips
    except socket.gaierror as e:
        logger.warning(f"Failed to resolve {domain}: {e}")
        return []


def validate_domain(domain: str) -> bool:
    """Validate that a domain is safe to allow."""
    # Basic validation
    if not domain:
        return False
    
    # Prevent localhost/internal access
    blocked_patterns = [
        "localhost",
        "127.",
        "10.",
        "192.168.",
        "172.16.",
        "172.17.",
        "172.18.",
        "172.19.",
        "172.20.",
        "172.21.",
        "172.22.",
        "172.23.",
        "172.24.",
        "172.25.",
        "172.26.",
        "172.27.",
        "172.28.",
        "172.29.",
        "172.30.",
        "172.31.",
        "169.254.",
        "::1",
        "0.0.0.0",
        "metadata.google",
        "169.254.169.254",  # AWS metadata
    ]
    
    domain_lower = domain.lower()
    for pattern in blocked_patterns:
        if pattern in domain_lower:
            return False
    
    return True


def sanitize_network_allow(domains: list[str] | None) -> list[str]:
    """Sanitize and validate network allowlist."""
    if domains is None:
        return []
    
    return [d for d in domains if validate_domain(d)]

