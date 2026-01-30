"""More aggressive tests for auth/* providers"""
import pytest
from inception.enhance.auth.claude import ClaudeOAuthConfig, ClaudeOAuthProvider
from inception.enhance.auth.gemini import GeminiOAuthConfig, GeminiOAuthProvider
from inception.enhance.auth.openai import OpenAIOAuthConfig, OpenAIOAuthProvider


class TestClaudeProviderPaths:
    def test_provider_creation(self):
        provider = ClaudeOAuthProvider()
        assert provider is not None
    
    def test_provider_name(self):
        provider = ClaudeOAuthProvider()
        assert provider.name == "claude"
    
    def test_config_creation(self):
        config = ClaudeOAuthConfig()
        assert config is not None


class TestGeminiProviderPaths:
    def test_provider_creation(self):
        provider = GeminiOAuthProvider()
        assert provider is not None
    
    def test_provider_name(self):
        provider = GeminiOAuthProvider()
        assert provider.name == "gemini"
    
    def test_config_creation(self):
        config = GeminiOAuthConfig()
        assert config is not None


class TestOpenAIProviderPaths:
    def test_provider_creation(self):
        provider = OpenAIOAuthProvider()
        assert provider is not None
    
    def test_provider_name(self):
        provider = OpenAIOAuthProvider()
        assert provider.name == "openai"
    
    def test_config_creation(self):
        config = OpenAIOAuthConfig()
        assert config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
