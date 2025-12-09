"""Tests for authentication - focusing on behavior."""

import pytest
from fastapi.testclient import TestClient


class TestAuthentication:
    """Tests for API authentication."""
    
    def test_accepts_bearer_token(
        self,
        client: TestClient,
        api_key: str,
        python_hello_files: list[dict],
    ):
        """API accepts Bearer token format."""
        response = client.post(
            "/v1/run",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "identifier": "test",
                "language": "python",
                "files": python_hello_files,
                "entrypoint": "main.py",
            },
        )
        
        assert response.status_code == 200
    
    def test_accepts_raw_token(
        self,
        client: TestClient,
        api_key: str,
        python_hello_files: list[dict],
    ):
        """API accepts raw token without Bearer prefix."""
        response = client.post(
            "/v1/run",
            headers={"Authorization": api_key},
            json={
                "identifier": "test",
                "language": "python",
                "files": python_hello_files,
                "entrypoint": "main.py",
            },
        )
        
        assert response.status_code == 200
    
    def test_health_does_not_require_auth(self, client: TestClient):
        """Health endpoint does not require authentication."""
        response = client.get("/v1/health")
        
        assert response.status_code == 200

