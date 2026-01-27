"""
Unit tests for OAuth authentication module.

Tests cover:
- Token serialization/deserialization
- PKCE generation
- Storage operations
- Manager provider selection
- Individual provider configs
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile

from inception.enhance.auth.base import (
    OAuthToken,
    OAuthConfig,
    SubscriptionTier,
    AuthError,
    TokenExpiredError,
    RefreshFailedError,
    generate_code_verifier,
    generate_code_challenge,
    generate_state,
    PROVIDER_MODELS,
)
from inception.enhance.auth.storage import TokenStorage
from inception.enhance.auth.claude import ClaudeOAuthConfig, ClaudeOAuthProvider
from inception.enhance.auth.gemini import GeminiOAuthConfig, GeminiOAuthProvider
from inception.enhance.auth.openai import OpenAIOAuthConfig, OpenAIOAuthProvider
from inception.enhance.auth.manager import OAuthManager, OAuthManagerConfig


# =============================================================================
# TOKEN TESTS
# =============================================================================

class TestOAuthToken:
    """Tests for OAuthToken dataclass."""
    
    def test_token_creation(self):
        """Test basic token creation."""
        token = OAuthToken(
            access_token="test_access_123",
            refresh_token="test_refresh_456",
            provider="claude",
        )
        
        assert token.access_token == "test_access_123"
        assert token.refresh_token == "test_refresh_456"
        assert token.provider == "claude"
        assert token.tier == SubscriptionTier.FREE
    
    def test_token_not_expired(self):
        """Test token expiration check for valid token."""
        token = OAuthToken(
            access_token="test",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        assert not token.is_expired
    
    def test_token_expired(self):
        """Test token expiration check for expired token."""
        token = OAuthToken(
            access_token="test",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        
        assert token.is_expired
    
    def test_token_no_expiry(self):
        """Test token without expiration."""
        token = OAuthToken(access_token="test")
        
        assert not token.is_expired
        assert token.time_until_expiry is None
    
    def test_token_serialization(self):
        """Test token to/from dict."""
        original = OAuthToken(
            access_token="access_123",
            refresh_token="refresh_456",
            token_type="Bearer",
            expires_at=datetime(2026, 12, 31, 23, 59, 59),
            scope="model.access",
            provider="claude",
            tier=SubscriptionTier.PRO,
        )
        
        # Serialize
        data = original.to_dict()
        assert data["access_token"] == "access_123"
        assert data["tier"] == "pro"
        
        # Deserialize
        restored = OAuthToken.from_dict(data)
        assert restored.access_token == original.access_token
        assert restored.refresh_token == original.refresh_token
        assert restored.tier == original.tier
        assert restored.provider == original.provider


# =============================================================================
# PKCE TESTS
# =============================================================================

class TestPKCE:
    """Tests for PKCE helpers."""
    
    def test_code_verifier_length(self):
        """Test code verifier has correct length."""
        verifier = generate_code_verifier(64)
        assert len(verifier) == 64
    
    def test_code_verifier_characters(self):
        """Test code verifier uses valid characters."""
        verifier = generate_code_verifier()
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
        assert all(c in valid_chars for c in verifier)
    
    def test_code_challenge_generation(self):
        """Test code challenge from verifier."""
        verifier = "test_verifier_12345678901234567890123456789012345678901234"
        challenge = generate_code_challenge(verifier)
        
        # Challenge should be base64url encoded
        assert isinstance(challenge, str)
        assert len(challenge) > 0
        # No padding characters
        assert "=" not in challenge
    
    def test_state_uniqueness(self):
        """Test state generation produces unique values."""
        states = [generate_state() for _ in range(100)]
        assert len(set(states)) == 100


# =============================================================================
# STORAGE TESTS
# =============================================================================

class TestTokenStorage:
    """Tests for token storage."""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create storage with temp file path."""
        return TokenStorage(fallback_path=tmp_path / "tokens.json")
    
    def test_store_and_retrieve(self, temp_storage):
        """Test storing and retrieving tokens."""
        token = OAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            provider="claude",
            tier=SubscriptionTier.PRO,
        )
        
        temp_storage.store("claude", token)
        retrieved = temp_storage.retrieve("claude")
        
        assert retrieved is not None
        assert retrieved.access_token == "test_access"
        assert retrieved.tier == SubscriptionTier.PRO
    
    def test_retrieve_nonexistent(self, temp_storage):
        """Test retrieving non-existent token."""
        result = temp_storage.retrieve("nonexistent")
        assert result is None
    
    def test_delete_token(self, temp_storage):
        """Test deleting a token."""
        token = OAuthToken(access_token="test")
        temp_storage.store("claude", token)
        
        temp_storage.delete("claude")
        
        assert temp_storage.retrieve("claude") is None
    
    def test_list_providers(self, temp_storage):
        """Test listing providers with tokens."""
        temp_storage.store("claude", OAuthToken(access_token="c"))
        temp_storage.store("gemini", OAuthToken(access_token="g"))
        
        providers = temp_storage.list_providers()
        
        assert "claude" in providers
        assert "gemini" in providers
    
    def test_clear_all(self, temp_storage):
        """Test clearing all tokens."""
        temp_storage.store("claude", OAuthToken(access_token="c"))
        temp_storage.store("gemini", OAuthToken(access_token="g"))
        
        temp_storage.clear_all()
        
        assert temp_storage.retrieve("claude") is None
        assert temp_storage.retrieve("gemini") is None


# =============================================================================
# PROVIDER CONFIG TESTS
# =============================================================================

class TestProviderConfigs:
    """Tests for provider configurations."""
    
    def test_claude_config_defaults(self):
        """Test Claude config has correct defaults."""
        config = ClaudeOAuthConfig()
        
        assert "claude.ai" in config.auth_url
        assert config.use_pkce is True
        assert config.callback_port == 8042
        assert "model.access" in config.scopes
    
    def test_gemini_config_defaults(self):
        """Test Gemini config has correct defaults."""
        config = GeminiOAuthConfig()
        
        assert "accounts.google.com" in config.auth_url
        assert "generative-language" in config.scopes[0]
        assert config.access_type == "offline"
    
    def test_openai_config_defaults(self):
        """Test OpenAI config has correct defaults."""
        config = OpenAIOAuthConfig()
        
        assert "chat.openai.com" in config.login_url
        assert config.callback_port == 8044
    
    def test_redirect_uri_construction(self):
        """Test redirect URI is correctly constructed."""
        config = OAuthConfig(
            callback_host="127.0.0.1",
            callback_port=8000,
            callback_path="/callback",
        )
        
        assert config.redirect_uri == "http://127.0.0.1:8000/callback"


# =============================================================================
# MANAGER TESTS
# =============================================================================

class TestOAuthManager:
    """Tests for OAuth manager."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager with temp storage."""
        manager = OAuthManager()
        manager.storage = TokenStorage(fallback_path=tmp_path / "tokens.json")
        return manager
    
    def test_manager_has_all_providers(self, manager):
        """Test manager has all three providers."""
        assert "claude" in manager.providers
        assert "gemini" in manager.providers
        assert "openai" in manager.providers
    
    def test_get_available_models_pro(self, manager):
        """Test getting models for Pro tier."""
        models = manager._get_available_models("claude", SubscriptionTier.PRO)
        
        assert len(models) > 0
        assert any("opus" in m.lower() or "sonnet" in m.lower() for m in models)
    
    def test_get_available_models_free(self, manager):
        """Test getting models for Free tier."""
        models = manager._get_available_models("gemini", SubscriptionTier.FREE)
        
        assert len(models) > 0
        assert any("flash" in m.lower() for m in models)
    
    @pytest.mark.asyncio
    async def test_get_token_no_auth(self, manager):
        """Test getting token when not authenticated."""
        with pytest.raises(AuthError, match="No authenticated"):
            await manager.get_token()
    
    @pytest.mark.asyncio
    async def test_get_token_cached(self, manager):
        """Test getting token from cache."""
        token = OAuthToken(
            access_token="cached_token",
            provider="claude",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        manager._token_cache["claude"] = token
        
        result = await manager._get_provider_token("claude")
        
        assert result.access_token == "cached_token"
    
    @pytest.mark.asyncio
    async def test_status_no_auth(self, manager):
        """Test status when not authenticated."""
        # Mock is_available to avoid network calls
        for provider in manager.providers.values():
            provider.is_available = AsyncMock(return_value=True)
        
        status = await manager.status()
        
        assert "claude" in status
        assert "gemini" in status
        assert "openai" in status
        assert not status["claude"]["authenticated"]
    
    @pytest.mark.asyncio
    async def test_health_check(self, manager):
        """Test health check caches results."""
        for provider in manager.providers.values():
            provider.is_available = AsyncMock(return_value=True)
        
        health = await manager.health_check()
        
        assert health["claude"] is True
        assert health["gemini"] is True
        assert manager._health_cache == health


# =============================================================================
# PROVIDER MODEL MAPPING TESTS
# =============================================================================

class TestProviderModels:
    """Tests for provider model mappings."""
    
    def test_claude_models_exist(self):
        """Test Claude models are defined."""
        assert "claude" in PROVIDER_MODELS
        assert SubscriptionTier.FREE in PROVIDER_MODELS["claude"]
        assert SubscriptionTier.PRO in PROVIDER_MODELS["claude"]
        assert SubscriptionTier.MAX in PROVIDER_MODELS["claude"]
    
    def test_gemini_models_exist(self):
        """Test Gemini models are defined."""
        assert "gemini" in PROVIDER_MODELS
        assert SubscriptionTier.ULTRA in PROVIDER_MODELS["gemini"]
    
    def test_openai_models_exist(self):
        """Test OpenAI models are defined."""
        assert "openai" in PROVIDER_MODELS
        assert SubscriptionTier.MAX in PROVIDER_MODELS["openai"]
    
    def test_higher_tiers_have_more_models(self):
        """Test higher tiers generally have more/better models."""
        claude_free = len(PROVIDER_MODELS["claude"][SubscriptionTier.FREE])
        claude_max = len(PROVIDER_MODELS["claude"][SubscriptionTier.MAX])
        
        assert claude_max >= claude_free


# =============================================================================
# SUBSCRIPTION TIER TESTS
# =============================================================================

class TestSubscriptionTier:
    """Tests for subscription tier enum."""
    
    def test_tier_values(self):
        """Test tier enum values."""
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.PRO.value == "pro"
        assert SubscriptionTier.MAX.value == "max"
        assert SubscriptionTier.ULTRA.value == "ultra"
    
    def test_tier_from_string(self):
        """Test creating tier from string."""
        tier = SubscriptionTier("pro")
        assert tier == SubscriptionTier.PRO
