"""Tests for enhance/auth/openai.py (26%)"""
import pytest
from inception.enhance.auth.openai import OpenAIOAuthConfig, OpenAIOAuthProvider


class TestOpenAIOAuthConfig:
    def test_creation(self):
        config = OpenAIOAuthConfig()
        assert config is not None


class TestOpenAIOAuthProvider:
    def test_creation(self):
        provider = OpenAIOAuthProvider()
        assert provider is not None
    
    def test_name(self):
        provider = OpenAIOAuthProvider()
        assert provider.name == "openai"
    
    def test_has_authenticate(self):
        provider = OpenAIOAuthProvider()
        assert hasattr(provider, 'authenticate') or hasattr(provider, 'start_auth_flow')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
