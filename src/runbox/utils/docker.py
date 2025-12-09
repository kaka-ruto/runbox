"""Docker utility functions."""

import docker
from docker.errors import DockerException


def check_docker_connection() -> bool:
    """Check if Docker is available and running."""
    try:
        client = docker.from_env()
        client.ping()
        client.close()
        return True
    except DockerException:
        return False


def get_docker_version() -> str | None:
    """Get Docker version."""
    try:
        client = docker.from_env()
        version = client.version()
        client.close()
        return version.get("Version")
    except DockerException:
        return None

