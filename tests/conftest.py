"""Pytest configuration and fixtures for Runbox tests."""

import os
import pytest
from fastapi.testclient import TestClient

# Set test API key before importing app
os.environ["RUNBOX_API_KEY"] = "test-api-key"


@pytest.fixture(scope="session")
def api_key() -> str:
    """Return the test API key."""
    return "test-api-key"


@pytest.fixture(scope="session")
def auth_headers(api_key: str) -> dict[str, str]:
    """Return authentication headers."""
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture(scope="module")
def app():
    """Create test application."""
    from runbox.main import create_app
    return create_app()


@pytest.fixture(scope="module")
def client(app) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def python_hello_files() -> list[dict]:
    """Return simple Python hello world files."""
    return [
        {"path": "main.py", "content": "print('Hello, Runbox!')"}
    ]


@pytest.fixture
def python_with_env_files() -> list[dict]:
    """Return Python files that read environment variables."""
    return [
        {
            "path": "main.py",
            "content": "import os; print(os.environ.get('TEST_VAR', 'not set'))"
        }
    ]


@pytest.fixture
def python_timeout_files() -> list[dict]:
    """Return Python files that will timeout."""
    return [
        {
            "path": "main.py",
            "content": "import time; time.sleep(60)"
        }
    ]


@pytest.fixture
def python_error_files() -> list[dict]:
    """Return Python files with syntax error."""
    return [
        {"path": "main.py", "content": "print('hello'"}  # Missing closing paren
    ]


@pytest.fixture
def python_network_files() -> list[dict]:
    """Return Python files that make network requests."""
    return [
        {
            "path": "main.py",
            "content": """
import urllib.request
import sys

try:
    response = urllib.request.urlopen('https://api.stripe.com', timeout=5)
    print(f'SUCCESS: {response.status}')
except Exception as e:
    print(f'BLOCKED: {e}', file=sys.stderr)
    sys.exit(1)
"""
        }
    ]


@pytest.fixture
def ruby_hello_files() -> list[dict]:
    """Return simple Ruby hello world files."""
    return [
        {"path": "main.rb", "content": "puts 'Hello, Runbox!'"}
    ]


@pytest.fixture
def shell_hello_files() -> list[dict]:
    """Return simple shell hello world files."""
    return [
        {"path": "main.sh", "content": "#!/bin/bash\necho 'Hello, Runbox!'"}
    ]

