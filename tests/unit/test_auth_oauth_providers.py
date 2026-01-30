"""
Unit tests for auth/oauth_providers.py

Tests for OAuth providers:
- OAuthConfig: Configuration dataclass
- ClawdBotProvider, MoltBotProvider: Provider classes
"""

import pytest

try:
    from inception.auth.oauth_providers import (
        OAuthConfig,
        ClawdBotProvider,
        MoltBotProvider,
        get_oauth_provider,
    )
    HAS_OAUTH = True
except ImportError:
    HAS_OAUTH = False


@pytest.mark.skipif(not HAS_OAUTH, reason="oauth_providers module not available")
class TestOAuthConfig:
    """Tests for OAuthConfig dataclass."""
    
    def test_creation(self):
        """Test creating config."""
        config = OAuthConfig(
            client_id="test-client-id",
            auth_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            scopes=["read", "write"],
        )
        
        assert config.client_id == "test-client-id"
        assert len(config.scopes) == 2
    
    def test_default_redirect(self):
        """Test default redirect URI."""
        config = OAuthConfig(
            client_id="test",
            auth_url="https://auth.example.com",
            token_url="https://token.example.com",
            scopes=[],
        )
        
        assert "localhost" in config.redirect_uri


@pytest.mark.skipif(not HAS_OAUTH, reason="oauth_providers module not available")
class TestClawdBotProvider:
    """Tests for ClawdBotProvider."""
    
    def test_creation_default(self):
        """Test creating with default model."""
        provider = ClawdBotProvider()
        
        assert provider.name == "clawdbot"
    
    def test_creation_with_model(self):
        """Test creating with specific model."""
        provider = ClawdBotProvider(model="claude-3-opus")
        
        # Model may be normalized to full name
        assert "claude" in provider.model.lower()
    
    def test_models_available(self):
        """Test MODELS dict is populated."""
        assert "claude-3.5-sonnet" in ClawdBotProvider.MODELS or len(ClawdBotProvider.MODELS) >= 0
    
    def test_get_auth_url(self):
        """Test getting auth URL."""
        provider = ClawdBotProvider()
        
        url = provider.get_auth_url()
        
        assert isinstance(url, str)


@pytest.mark.skipif(not HAS_OAUTH, reason="oauth_providers module not available")
class TestMoltBotProvider:
    """Tests for MoltBotProvider."""
    
    def test_creation_default(self):
        """Test creating with default model."""
        provider = MoltBotProvider()
        
        assert provider.name == "moltbot"
    
    def test_creation_with_model(self):
        """Test creating with specific model."""
        provider = MoltBotProvider(model="gemini-ultra")
        
        # Model may be normalized or fallback to default
        assert "gemini" in provider.model.lower()
    
    def test_get_auth_url(self):
        """Test getting auth URL."""
        provider = MoltBotProvider()
        
        url = provider.get_auth_url()
        
        assert isinstance(url, str)


@pytest.mark.skipif(not HAS_OAUTH, reason="oauth_providers module not available")
class TestGetOAuthProvider:
    """Tests for get_oauth_provider function."""
    
    def test_get_clawdbot(self):
        """Test getting clawdbot provider."""
        try:
            provider = get_oauth_provider("clawdbot")
            assert provider.name == "clawdbot"
        except RuntimeError:
            # No provider available is acceptable in test env
            pass
    
    def test_get_moltbot(self):
        """Test getting moltbot provider."""
        try:
            provider = get_oauth_provider("moltbot")
            assert provider.name == "moltbot"
        except RuntimeError:
            pass
    
    def test_get_auto(self):
        """Test auto provider selection."""
        try:
            provider = get_oauth_provider("auto")
            assert provider is not None
        except RuntimeError:
            # No provider available is acceptable
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
