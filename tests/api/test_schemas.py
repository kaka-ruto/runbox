"""Tests for request/response schemas - focusing on validation behavior."""

import pytest
from pydantic import ValidationError

from runbox.api.schemas import (
    RunRequest,
    SetupRequest,
    SetupResponse,
    EnvironmentSnapshot,
    FileInput,
)


class TestSetupRequestValidation:
    """Tests for SetupRequest schema validation."""
    
    def test_valid_request(self):
        """Valid request passes validation."""
        request = SetupRequest(
            identifier="test-123",
            language="python",
        )
        
        assert request.identifier == "test-123"
        assert request.language == "python"
    
    def test_requires_identifier(self):
        """Request requires identifier."""
        with pytest.raises(ValidationError):
            SetupRequest(
                language="python",
            )
    
    def test_requires_language(self):
        """Request requires language."""
        with pytest.raises(ValidationError):
            SetupRequest(
                identifier="test",
            )
    
    def test_identifier_max_length(self):
        """Identifier has max length."""
        with pytest.raises(ValidationError):
            SetupRequest(
                identifier="x" * 200,
                language="python",
            )
    
    def test_optional_fields_have_defaults(self):
        """Optional fields have sensible defaults."""
        request = SetupRequest(
            identifier="test",
            language="python",
        )
        
        assert request.env == {}
        assert request.timeout is None
        assert request.memory is None
        assert request.network_allow is None


class TestRunRequestValidation:
    """Tests for RunRequest schema validation."""
    
    def test_valid_request(self):
        """Valid request passes validation."""
        request = RunRequest(
            container_id="runbox-test-python",
            files=[FileInput(path="main.py", content="print('hi')")],
            run_command="python main.py",
        )
        
        assert request.container_id == "runbox-test-python"
        assert len(request.files) == 1
    
    def test_requires_container_id(self):
        """Request requires container_id."""
        with pytest.raises(ValidationError):
            RunRequest(
                files=[FileInput(path="main.py", content="print('hi')")],
                run_command="python main.py",
            )
    
    def test_requires_files(self):
        """Request requires at least one file."""
        with pytest.raises(ValidationError):
            RunRequest(
                container_id="runbox-test-python",
                files=[],
                run_command="python main.py",
            )
    
    def test_timeout_must_be_positive(self):
        """Timeout must be positive."""
        with pytest.raises(ValidationError):
            RunRequest(
                container_id="runbox-test-python",
                files=[FileInput(path="main.py", content="print('hi')")],
                run_command="python main.py",
                timeout=-1,
            )
    
    def test_timeout_max_300_seconds(self):
        """Timeout cannot exceed 300 seconds."""
        with pytest.raises(ValidationError):
            RunRequest(
                container_id="runbox-test-python",
                files=[FileInput(path="main.py", content="print('hi')")],
                run_command="python main.py",
                timeout=500,
            )
    
    def test_optional_fields_have_defaults(self):
        """Optional fields have sensible defaults."""
        request = RunRequest(
            container_id="runbox-test-python",
            files=[FileInput(path="main.py", content="print('hi')")],
            run_command="python main.py",
        )
        
        assert request.env == {}
        assert request.timeout is None


class TestEnvironmentSnapshotValidation:
    """Tests for EnvironmentSnapshot schema."""
    
    def test_valid_snapshot(self):
        """Valid snapshot passes validation."""
        snapshot = EnvironmentSnapshot(
            os_name="debian",
            os_version="12",
            runtime_name="python",
            runtime_version="3.11.6",
            packages={"pip": "23.0.1", "requests": "2.31.0"},
        )
        
        assert snapshot.os_name == "debian"
        assert snapshot.runtime_version == "3.11.6"
        assert snapshot.packages["requests"] == "2.31.0"
    
    def test_packages_can_be_empty(self):
        """Packages dict can be empty."""
        snapshot = EnvironmentSnapshot(
            os_name="alpine",
            os_version="3.19",
            runtime_name="bash",
            runtime_version="5.2.21",
            packages={},
        )
        
        assert snapshot.packages == {}
