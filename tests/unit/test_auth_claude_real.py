"""
REAL tests for enhance/auth/claude.py
"""
import pytest
from inception.enhance.auth.claude import ClaudeOAuthConfig, ClaudeOAuthProvider
from inception.enhance.auth.base import SubscriptionTier


class TestClaudeOAuthConfig:
    def test_defaults(self):
        config = ClaudeOAuthConfig()
        assert config.auth_url == "https://claude.ai/oauth/authorize"
        assert config.token_url == "https://claude.ai/oauth/token"
        assert config.client_id == "inception-cli"
        assert config.callback_port == 8042
    
    def test_scopes(self):
        config = ClaudeOAuthConfig()
        assert "model.access" in config.scopes


class TestClaudeOAuthProvider:
    def test_creation(self):
        provider = ClaudeOAuthProvider()
        assert provider is not None
    
    def test_name(self):
        provider = ClaudeOAuthProvider()
        assert provider.name == "claude"
    
    def test_creation_custom_config(self):
        config = ClaudeOAuthConfig(callback_port=9000)
        provider = ClaudeOAuthProvider(config=config)
        assert provider.config.callback_port == 9000
    
    def test_parse_tier_free(self):
        provider = ClaudeOAuthProvider()
        tier = provider._parse_tier({})
        assert tier == SubscriptionTier.FREE
    
    def test_parse_tier_pro(self):
        provider = ClaudeOAuthProvider()
        tier = provider._parse_tier({"subscription": {"plan": "pro"}})
        assert tier == SubscriptionTier.PRO
    
    def test_parse_tier_max(self):
        provider = ClaudeOAuthProvider()
        tier = provider._parse_tier({"subscription": {"plan": "max"}})
        assert tier == SubscriptionTier.MAX
    
    def test_parse_tier_enterprise(self):
        provider = ClaudeOAuthProvider()
        tier = provider._parse_tier({"subscription": {"plan": "enterprise"}})
        assert tier == SubscriptionTier.ENTERPRISE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
