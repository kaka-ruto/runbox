"""Tests for API routes - focusing on behavior, not implementation."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for /v1/health endpoint."""
    
    def test_returns_healthy_status(self, client: TestClient):
        """Health endpoint returns healthy status."""
        response = client.get("/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestRunEndpoint:
    """Tests for /v1/run endpoint."""
    
    def test_requires_authentication(self, client: TestClient, python_hello_files: list[dict]):
        """Run endpoint requires API key."""
        response = client.post(
            "/v1/run",
            json={
                "identifier": "test-auth",
                "language": "python",
                "files": python_hello_files,
                "entrypoint": "main.py",
            },
        )
        
        assert response.status_code == 401
    
    def test_rejects_invalid_api_key(
        self,
        client: TestClient,
        python_hello_files: list[dict],
    ):
        """Run endpoint rejects invalid API key."""
        response = client.post(
            "/v1/run",
            headers={"Authorization": "Bearer wrong-key"},
            json={
                "identifier": "test-auth",
                "language": "python",
                "files": python_hello_files,
                "entrypoint": "main.py",
            },
        )
        
        assert response.status_code == 401
    
    def test_executes_python_code(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_hello_files: list[dict],
    ):
        """Run endpoint executes Python code and returns output."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-python",
                "language": "python",
                "files": python_hello_files,
                "entrypoint": "main.py",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "Hello, Runbox!" in data["stdout"]
        assert data["container_id"].startswith("runbox-")
    
    def test_executes_ruby_code(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        ruby_hello_files: list[dict],
    ):
        """Run endpoint executes Ruby code and returns output."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-ruby",
                "language": "ruby",
                "files": ruby_hello_files,
                "entrypoint": "main.rb",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Hello, Runbox!" in data["stdout"]
    
    def test_executes_shell_code(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        shell_hello_files: list[dict],
    ):
        """Run endpoint executes shell code and returns output."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-shell",
                "language": "shell",
                "files": shell_hello_files,
                "entrypoint": "main.sh",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Hello, Runbox!" in data["stdout"]
    
    def test_injects_environment_variables(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_with_env_files: list[dict],
    ):
        """Run endpoint injects environment variables."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-env",
                "language": "python",
                "files": python_with_env_files,
                "entrypoint": "main.py",
                "env": {"TEST_VAR": "secret_value"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "secret_value" in data["stdout"]
    
    def test_handles_syntax_errors(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_error_files: list[dict],
    ):
        """Run endpoint returns error output for syntax errors."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-error",
                "language": "python",
                "files": python_error_files,
                "entrypoint": "main.py",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["exit_code"] != 0
        assert "SyntaxError" in data["stderr"]
    
    def test_respects_timeout(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_timeout_files: list[dict],
    ):
        """Run endpoint respects timeout and terminates long-running code."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-timeout",
                "language": "python",
                "files": python_timeout_files,
                "entrypoint": "main.py",
                "timeout": 2,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["timeout_exceeded"] is True
        assert data["execution_time_ms"] < 5000  # Should stop around 2s
    
    def test_rejects_unsupported_language(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Run endpoint rejects unsupported languages."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-unsupported",
                "language": "cobol",
                "files": [{"path": "main.cob", "content": "HELLO"}],
                "entrypoint": "main.cob",
            },
        )
        
        assert response.status_code == 400
        assert "Unsupported language" in response.json()["detail"]
    
    def test_rejects_missing_entrypoint(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Run endpoint rejects when entrypoint not in files."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-entrypoint",
                "language": "python",
                "files": [{"path": "other.py", "content": "print('hi')"}],
                "entrypoint": "main.py",
            },
        )
        
        assert response.status_code == 400
        assert "not found in files" in response.json()["detail"]
    
    def test_validates_identifier_length(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_hello_files: list[dict],
    ):
        """Run endpoint validates identifier length."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "x" * 200,  # Too long
                "language": "python",
                "files": python_hello_files,
                "entrypoint": "main.py",
            },
        )
        
        assert response.status_code == 422  # Validation error


class TestContainerDeleteEndpoint:
    """Tests for /v1/containers/{identifier} DELETE endpoint."""
    
    def test_requires_authentication(self, client: TestClient):
        """Delete endpoint requires API key."""
        response = client.delete("/v1/containers/test-id")
        
        assert response.status_code == 401
    
    def test_deletes_containers(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_hello_files: list[dict],
    ):
        """Delete endpoint removes containers for identifier."""
        # First create a container
        client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "identifier": "test-delete",
                "language": "python",
                "files": python_hello_files,
                "entrypoint": "main.py",
            },
        )
        
        # Then delete it
        response = client.delete(
            "/v1/containers/test-delete",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
        assert isinstance(data["deleted"], list)

