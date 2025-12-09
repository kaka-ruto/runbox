"""Tests for network policy - focusing on allowlist behavior."""

import pytest

from runbox.core.network import validate_domain, sanitize_network_allow


class TestDomainValidation:
    """Tests for domain validation."""
    
    def test_allows_valid_domains(self):
        """Validator allows valid domains."""
        assert validate_domain("api.stripe.com") is True
        assert validate_domain("example.com") is True
        assert validate_domain("sub.domain.example.com") is True
    
    def test_blocks_localhost(self):
        """Validator blocks localhost."""
        assert validate_domain("localhost") is False
        assert validate_domain("localhost:3000") is False
    
    def test_blocks_private_ips(self):
        """Validator blocks private IP ranges."""
        assert validate_domain("127.0.0.1") is False
        assert validate_domain("10.0.0.1") is False
        assert validate_domain("192.168.1.1") is False
        assert validate_domain("172.16.0.1") is False
    
    def test_blocks_metadata_endpoints(self):
        """Validator blocks cloud metadata endpoints."""
        assert validate_domain("169.254.169.254") is False
        assert validate_domain("metadata.google.internal") is False
    
    def test_blocks_empty_domain(self):
        """Validator blocks empty domain."""
        assert validate_domain("") is False


class TestNetworkAllowSanitization:
    """Tests for network allowlist sanitization."""
    
    def test_filters_invalid_domains(self):
        """Sanitizer filters out invalid domains."""
        domains = ["api.stripe.com", "localhost", "api.twilio.com", "127.0.0.1"]
        result = sanitize_network_allow(domains)
        
        assert "api.stripe.com" in result
        assert "api.twilio.com" in result
        assert "localhost" not in result
        assert "127.0.0.1" not in result
    
    def test_handles_none(self):
        """Sanitizer handles None input."""
        result = sanitize_network_allow(None)
        assert result == []
    
    def test_handles_empty_list(self):
        """Sanitizer handles empty list."""
        result = sanitize_network_allow([])
        assert result == []

