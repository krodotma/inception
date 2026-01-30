"""
Unit tests for auth/token_store.py

Tests for token storage:
- Token: Token dataclass
- TokenStore: Storage class
"""

import pytest
import tempfile
from pathlib import Path

try:
    from inception.auth.token_store import Token, TokenStore
    HAS_TOKEN_STORE = True
except ImportError:
    HAS_TOKEN_STORE = False


@pytest.mark.skipif(not HAS_TOKEN_STORE, reason="token_store module not available")
class TestToken:
    """Tests for Token dataclass."""
    
    def test_creation(self):
        """Test creating token."""
        token = Token(access_token="abc123")
        
        assert token.access_token == "abc123"
        assert token.token_type == "Bearer"
    
    def test_is_valid(self):
        """Test is_valid property."""
        token = Token(access_token="abc123")
        
        assert token.is_valid is True
    
    def test_is_expired_no_expiry(self):
        """Test is_expired with no expiry set."""
        token = Token(access_token="abc123")
        
        assert token.is_expired is False
    
    def test_is_expired_future(self):
        """Test is_expired with future expiry."""
        import time
        token = Token(
            access_token="abc123",
            expires_at=time.time() + 3600,  # 1 hour from now
        )
        
        assert token.is_expired is False
    
    def test_is_expired_past(self):
        """Test is_expired with past expiry."""
        import time
        token = Token(
            access_token="abc123",
            expires_at=time.time() - 3600,  # 1 hour ago
        )
        
        assert token.is_expired is True
    
    def test_to_dict(self):
        """Test to_dict serialization."""
        token = Token(access_token="abc123", provider="test")
        
        d = token.to_dict()
        
        assert d["access_token"] == "abc123"
        assert d["provider"] == "test"
    
    def test_from_dict(self):
        """Test from_dict deserialization."""
        data = {
            "access_token": "xyz789",
            "token_type": "Bearer",
            "provider": "clawdbot",
        }
        
        token = Token.from_dict(data)
        
        assert token.access_token == "xyz789"


@pytest.mark.skipif(not HAS_TOKEN_STORE, reason="token_store module not available")
class TestTokenStore:
    """Tests for TokenStore."""
    
    def test_creation(self):
        """Test creating store with temp dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TokenStore(base_dir=tmpdir)
            
            assert store.base_dir == Path(tmpdir)
    
    def test_save_and_load(self):
        """Test saving and loading token."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TokenStore(base_dir=tmpdir)
            token = Token(access_token="test123")
            
            store.save("testprovider", token)
            loaded = store.load("testprovider")
            
            assert loaded is not None
            assert loaded.access_token == "test123"
    
    def test_load_nonexistent(self):
        """Test loading nonexistent token."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TokenStore(base_dir=tmpdir)
            
            loaded = store.load("nonexistent")
            
            assert loaded is None
    
    def test_delete(self):
        """Test deleting token."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TokenStore(base_dir=tmpdir)
            token = Token(access_token="todelete")
            store.save("deleteme", token)
            
            result = store.delete("deleteme")
            
            assert result is True
            assert store.load("deleteme") is None
    
    def test_list_providers(self):
        """Test listing providers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TokenStore(base_dir=tmpdir)
            store.save("provider1", Token(access_token="a"))
            store.save("provider2", Token(access_token="b"))
            
            providers = store.list_providers()
            
            assert len(providers) == 2
    
    def test_has_valid_token(self):
        """Test has_valid_token check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TokenStore(base_dir=tmpdir)
            token = Token(access_token="valid")
            store.save("testprov", token)
            
            assert store.has_valid_token("testprov") is True
            assert store.has_valid_token("unknown") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
