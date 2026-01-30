"""Tests for enhance/auth/claude.py (40%)"""
import pytest
from inception.enhance.auth.claude import ClaudeOAuthConfig, ClaudeOAuthProvider


class TestClaudeOAuthConfig:
    def test_creation(self):
        config = ClaudeOAuthConfig()
        assert config is not None
    
    def test_has_auth_url(self):
        config = ClaudeOAuthConfig()
        assert hasattr(config, 'auth_url') or hasattr(config, 'authorization_endpoint')


class TestClaudeOAuthProvider:
    def test_creation(self):
        provider = ClaudeOAuthProvider()
        assert provider is not None
    
    def test_name(self):
        provider = ClaudeOAuthProvider()
        assert provider.name == "claude"
    
    def test_has_methods(self):
        provider = ClaudeOAuthProvider()
        assert hasattr(provider, 'authenticate') or hasattr(provider, 'start_auth_flow')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
