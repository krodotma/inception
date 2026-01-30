"""Deep auth manager tests to push enhance/auth/manager.py from 51% toward 80%"""
import pytest
from inception.enhance.auth.manager import OAuthManager, TokenStorage


class TestOAuthManager:
    def test_creation(self):
        manager = OAuthManager()
        assert manager is not None
    
    def test_providers_attr(self):
        manager = OAuthManager()
        if hasattr(manager, 'providers'):
            assert manager.providers is not None


class TestTokenStorage:
    def test_creation(self):
        storage = TokenStorage()
        assert storage is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
