"""Tests for request/response schemas - focusing on validation behavior."""

import pytest
from pydantic import ValidationError

from runbox.api.schemas import RunRequest, FileInput


class TestRunRequestValidation:
    """Tests for RunRequest schema validation."""
    
    def test_valid_request(self):
        """Valid request passes validation."""
        request = RunRequest(
            identifier="test-123",
            language="python",
            files=[FileInput(path="main.py", content="print('hi')")],
            entrypoint="main.py",
        )
        
        assert request.identifier == "test-123"
        assert request.language == "python"
        assert len(request.files) == 1
    
    def test_requires_identifier(self):
        """Request requires identifier."""
        with pytest.raises(ValidationError):
            RunRequest(
                language="python",
                files=[FileInput(path="main.py", content="print('hi')")],
                entrypoint="main.py",
            )
    
    def test_requires_files(self):
        """Request requires at least one file."""
        with pytest.raises(ValidationError):
            RunRequest(
                identifier="test",
                language="python",
                files=[],
                entrypoint="main.py",
            )
    
    def test_timeout_must_be_positive(self):
        """Timeout must be positive."""
        with pytest.raises(ValidationError):
            RunRequest(
                identifier="test",
                language="python",
                files=[FileInput(path="main.py", content="print('hi')")],
                entrypoint="main.py",
                timeout=-1,
            )
    
    def test_timeout_max_300_seconds(self):
        """Timeout cannot exceed 300 seconds."""
        with pytest.raises(ValidationError):
            RunRequest(
                identifier="test",
                language="python",
                files=[FileInput(path="main.py", content="print('hi')")],
                entrypoint="main.py",
                timeout=500,
            )
    
    def test_optional_fields_have_defaults(self):
        """Optional fields have sensible defaults."""
        request = RunRequest(
            identifier="test",
            language="python",
            files=[FileInput(path="main.py", content="print('hi')")],
            entrypoint="main.py",
        )
        
        assert request.env == {}
        assert request.timeout is None
        assert request.memory is None
        assert request.network_allow is None

