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


class TestSetupEndpoint:
    """Tests for /v1/setup endpoint."""
    
    def test_requires_authentication(self, client: TestClient):
        """Setup endpoint requires API key."""
        response = client.post(
            "/v1/setup",
            json={
                "identifier": "test-auth",
                "language": "python",
            },
        )
        
        assert response.status_code == 401
    
    def test_rejects_invalid_api_key(self, client: TestClient):
        """Setup endpoint rejects invalid API key."""
        response = client.post(
            "/v1/setup",
            headers={"Authorization": "Bearer wrong-key"},
            json={
                "identifier": "test-auth",
                "language": "python",
            },
        )
        
        assert response.status_code == 401
    
    def test_sets_up_python_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Setup endpoint creates Python container and returns environment snapshot."""
        response = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-setup-python",
                "language": "python",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check container_id
        assert data["container_id"].startswith("runbox-")
        assert "python" in data["container_id"]
        
        # Check environment_snapshot
        env = data["environment_snapshot"]
        assert env["os_name"] in ["debian", "ubuntu", "alpine"]
        assert env["os_version"] != "unknown"
        assert env["runtime_name"] == "python"
        assert env["runtime_version"].startswith("3.")
        
        # Check packages
        assert "pip" in env["packages"]
        assert "requests" in env["packages"]
        
        # Cleanup
        client.delete(
            "/v1/containers/test-setup-python",
            headers=auth_headers,
        )
    
    def test_sets_up_ruby_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Setup endpoint creates Ruby container and returns environment snapshot."""
        response = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-setup-ruby",
                "language": "ruby",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check container_id
        assert data["container_id"].startswith("runbox-")
        assert "ruby" in data["container_id"]
        
        # Check environment_snapshot
        env = data["environment_snapshot"]
        assert env["runtime_name"] == "ruby"
        assert env["runtime_version"].startswith("3.")
        
        # Check packages (gems)
        assert "faraday" in env["packages"]
        
        # Cleanup
        client.delete(
            "/v1/containers/test-setup-ruby",
            headers=auth_headers,
        )
    
    def test_sets_up_shell_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Setup endpoint creates Shell container and returns environment snapshot."""
        response = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-setup-shell",
                "language": "shell",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check container_id
        assert data["container_id"].startswith("runbox-")
        assert "shell" in data["container_id"]
        
        # Check environment_snapshot
        env = data["environment_snapshot"]
        assert env["os_name"] == "alpine"
        assert env["runtime_name"] == "bash"
        assert env["runtime_version"].startswith("5.")
        
        # Check tools
        assert "curl" in env["packages"] or "jq" in env["packages"]
        
        # Cleanup
        client.delete(
            "/v1/containers/test-setup-shell",
            headers=auth_headers,
        )
    
    def test_reuses_existing_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Setup endpoint reuses existing container and marks as cached."""
        # First setup
        response1 = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-reuse",
                "language": "python",
            },
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cached"] is False
        
        # Second setup with same identifier
        response2 = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-reuse",
                "language": "python",
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cached"] is True
        assert data2["container_id"] == data1["container_id"]
        
        # Cleanup
        client.delete(
            "/v1/containers/test-reuse",
            headers=auth_headers,
        )
    
    def test_rejects_unsupported_language(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Setup endpoint rejects unsupported languages."""
        response = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-unsupported",
                "language": "cobol",
            },
        )
        
        assert response.status_code == 400
        assert "Unsupported language" in response.json()["detail"]
    
    def test_validates_identifier_length(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Setup endpoint validates identifier length."""
        response = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "x" * 200,  # Too long
                "language": "python",
            },
        )
        
        assert response.status_code == 422  # Validation error


class TestRunEndpoint:
    """Tests for /v1/run endpoint (requires prior /setup)."""
    
    @pytest.fixture
    def python_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> str:
        """Create a Python container and return its ID."""
        response = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-run-python",
                "language": "python",
            },
        )
        container_id = response.json()["container_id"]
        yield container_id
        # Cleanup
        client.delete(
            "/v1/containers/test-run-python",
            headers=auth_headers,
        )
    
    def test_requires_authentication(
        self,
        client: TestClient,
        python_container: str,
        python_hello_files: list[dict],
    ):
        """Run endpoint requires API key."""
        response = client.post(
            "/v1/run",
            json={
                "container_id": python_container,
                "files": python_hello_files,
                "run_command": "python main.py",
            },
        )
        
        assert response.status_code == 401
    
    def test_executes_python_code(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_container: str,
        python_hello_files: list[dict],
    ):
        """Run endpoint executes Python code and returns output."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": python_container,
                "files": python_hello_files,
                "run_command": "python main.py",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "Hello, Runbox!" in data["stdout"]
    
    def test_executes_multiple_times_in_same_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_container: str,
    ):
        """Run endpoint can execute multiple times in the same container."""
        # First execution
        response1 = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": python_container,
                "files": [{"path": "main.py", "content": "print('Run 1')"}],
                "run_command": "python main.py",
            },
        )
        assert response1.status_code == 200
        assert "Run 1" in response1.json()["stdout"]
        
        # Second execution
        response2 = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": python_container,
                "files": [{"path": "main.py", "content": "print('Run 2')"}],
                "run_command": "python main.py",
            },
        )
        assert response2.status_code == 200
        assert "Run 2" in response2.json()["stdout"]
    
    def test_injects_environment_variables(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        python_container: str,
        python_with_env_files: list[dict],
    ):
        """Run endpoint injects environment variables."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": python_container,
                "files": python_with_env_files,
                "run_command": "python main.py",
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
        python_container: str,
        python_error_files: list[dict],
    ):
        """Run endpoint returns error output for syntax errors."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": python_container,
                "files": python_error_files,
                "run_command": "python main.py",
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
        python_container: str,
        python_timeout_files: list[dict],
    ):
        """Run endpoint respects timeout and terminates long-running code."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": python_container,
                "files": python_timeout_files,
                "run_command": "python main.py",
                "timeout": 2,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["timeout_exceeded"] is True
        assert data["execution_time_ms"] < 5000  # Should stop around 2s
    

    
    def test_returns_404_for_unknown_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ):
        """Run endpoint returns 404 for unknown container_id."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": "runbox-nonexistent-python",
                "files": [{"path": "main.py", "content": "print('hi')"}],
                "run_command": "python main.py",
            },
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRunEndpointRuby:
    """Tests for /v1/run endpoint with Ruby."""
    
    @pytest.fixture
    def ruby_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> str:
        """Create a Ruby container and return its ID."""
        response = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-run-ruby",
                "language": "ruby",
            },
        )
        container_id = response.json()["container_id"]
        yield container_id
        client.delete(
            "/v1/containers/test-run-ruby",
            headers=auth_headers,
        )
    
    def test_executes_ruby_code(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        ruby_container: str,
        ruby_hello_files: list[dict],
    ):
        """Run endpoint executes Ruby code and returns output."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": ruby_container,
                "files": ruby_hello_files,
                "run_command": "ruby main.rb",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Hello, Runbox!" in data["stdout"]


class TestRunEndpointShell:
    """Tests for /v1/run endpoint with Shell."""
    
    @pytest.fixture
    def shell_container(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> str:
        """Create a Shell container and return its ID."""
        response = client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-run-shell",
                "language": "shell",
            },
        )
        container_id = response.json()["container_id"]
        yield container_id
        client.delete(
            "/v1/containers/test-run-shell",
            headers=auth_headers,
        )
    
    def test_executes_shell_code(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        shell_container: str,
        shell_hello_files: list[dict],
    ):
        """Run endpoint executes shell code and returns output."""
        response = client.post(
            "/v1/run",
            headers=auth_headers,
            json={
                "container_id": shell_container,
                "files": shell_hello_files,
                "run_command": "sh main.sh",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Hello, Runbox!" in data["stdout"]


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
    ):
        """Delete endpoint removes containers for identifier."""
        # First create a container via setup
        client.post(
            "/v1/setup",
            headers=auth_headers,
            json={
                "identifier": "test-delete",
                "language": "python",
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
