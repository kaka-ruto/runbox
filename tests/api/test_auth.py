"""Tests for authentication - focusing on behavior."""

import pytest
from fastapi.testclient import TestClient


class TestAuthentication:
    """Tests for API authentication."""
    
    def test_accepts_bearer_token(
        self,
        client: TestClient,
        api_key: str,
    ):
        """API accepts Bearer token format."""
        response = client.post(
            "/v1/setup",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "identifier": "test-auth-bearer",
                "language": "python",
            },
        )
        
        assert response.status_code == 200
        
        # Cleanup
        client.delete(
            "/v1/containers/test-auth-bearer",
            headers={"Authorization": f"Bearer {api_key}"},
        )
    
    def test_accepts_raw_token(
        self,
        client: TestClient,
        api_key: str,
    ):
        """API accepts raw token without Bearer prefix."""
        response = client.post(
            "/v1/setup",
            headers={"Authorization": api_key},
            json={
                "identifier": "test-auth-raw",
                "language": "python",
            },
        )
        
        assert response.status_code == 200
        
        # Cleanup
        client.delete(
            "/v1/containers/test-auth-raw",
            headers={"Authorization": api_key},
        )
    
    def test_health_does_not_require_auth(self, client: TestClient):
        """Health endpoint does not require authentication."""
        response = client.get("/v1/health")
        
        assert response.status_code == 200
