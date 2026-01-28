"""
Token Store for OAuth credentials.

Stores tokens securely with expiration tracking. Tokens are stored in:
~/.config/inception/tokens/{provider}.json

Security model:
- No API keys in code or config
- OAuth tokens with expiration
- Automatic refresh when possible
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class Token:
    """OAuth token with metadata."""
    
    access_token: str
    token_type: str = "Bearer"
    expires_at: float | None = None  # Unix timestamp
    refresh_token: str | None = None
    scope: str | None = None
    provider: str = ""
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5min buffer)."""
        if self.expires_at is None:
            return False
        return time.time() > (self.expires_at - 300)
    
    @property
    def is_valid(self) -> bool:
        """Check if token appears valid."""
        return bool(self.access_token) and not self.is_expired
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Token":
        """Create from dictionary."""
        return cls(**data)


class TokenStore:
    """
    Secure token storage for OAuth providers.
    
    Usage:
        store = TokenStore()
        store.save("clawdbot", token)
        token = store.load("clawdbot")
    """
    
    def __init__(self, base_dir: str | Path | None = None):
        """Initialize token store.
        
        Args:
            base_dir: Base directory for token storage.
                     Defaults to ~/.config/inception/tokens
        """
        if base_dir is None:
            base_dir = Path.home() / ".config" / "inception" / "tokens"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions on directory
        os.chmod(self.base_dir, 0o700)
    
    def _path(self, provider: str) -> Path:
        """Get token file path for provider."""
        return self.base_dir / f"{provider}.json"
    
    def save(self, provider: str, token: Token) -> None:
        """Save token for provider.
        
        Args:
            provider: Provider name (e.g., "clawdbot", "moltbot")
            token: Token to save
        """
        token.provider = provider
        path = self._path(provider)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(token.to_dict(), f, indent=2)
        
        # Set restrictive permissions on file
        os.chmod(path, 0o600)
    
    def load(self, provider: str) -> Token | None:
        """Load token for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Token if found and valid, None otherwise
        """
        path = self._path(provider)
        if not path.exists():
            return None
        
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            token = Token.from_dict(data)
            
            if token.is_valid:
                return token
            return None
        except (json.JSONDecodeError, TypeError, KeyError):
            return None
    
    def delete(self, provider: str) -> bool:
        """Delete token for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if deleted, False if not found
        """
        path = self._path(provider)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def list_providers(self) -> list[str]:
        """List all providers with stored tokens."""
        return [p.stem for p in self.base_dir.glob("*.json")]
    
    def has_valid_token(self, provider: str) -> bool:
        """Check if provider has a valid (non-expired) token."""
        token = self.load(provider)
        return token is not None and token.is_valid
