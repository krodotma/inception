"""
Base classes and types for OAuth authentication.

Provides abstract base classes and common data structures for
browser-based OAuth flows across all providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
import hashlib
import secrets
import base64
import logging

logger = logging.getLogger(__name__)


# ==============================================================================
# EXCEPTIONS
# ==============================================================================

class AuthError(Exception):
    """Base authentication error."""
    pass


class TokenExpiredError(AuthError):
    """Token has expired and needs refresh."""
    pass


class RefreshFailedError(AuthError):
    """Token refresh failed, need full re-auth."""
    pass


class AuthCancelledError(AuthError):
    """User cancelled authentication flow."""
    pass


class ProviderUnavailableError(AuthError):
    """Provider is not available or reachable."""
    pass


# ==============================================================================
# SUBSCRIPTION TIERS
# ==============================================================================

class SubscriptionTier(Enum):
    """Subscription tier levels across providers."""
    FREE = "free"
    PRO = "pro"           # Claude Pro, Gemini Pro, ChatGPT Plus
    MAX = "max"           # Claude Max
    ULTRA = "ultra"       # Gemini Ultra
    ENTERPRISE = "enterprise"


# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class OAuthToken:
    """OAuth token with metadata."""
    
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: str = ""
    provider: str = ""
    tier: SubscriptionTier = SubscriptionTier.FREE
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 min buffer)."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=5))
    
    @property
    def time_until_expiry(self) -> timedelta | None:
        """Time remaining until token expires."""
        if self.expires_at is None:
            return None
        return self.expires_at - datetime.utcnow()
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
            "provider": self.provider,
            "tier": self.tier.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OAuthToken":
        """Deserialize from dictionary."""
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope", ""),
            provider=data.get("provider", ""),
            tier=SubscriptionTier(data.get("tier", "free")),
        )


@dataclass
class OAuthConfig:
    """Base OAuth configuration."""
    
    # OAuth endpoints
    auth_url: str = ""
    token_url: str = ""
    
    # Client configuration
    client_id: str = ""
    client_secret: str = ""  # Empty for public clients
    
    # Local callback
    callback_host: str = "127.0.0.1"
    callback_port: int = 8000
    callback_path: str = "/callback"
    
    # Scopes
    scopes: list[str] = field(default_factory=list)
    
    # Security
    use_pkce: bool = True
    
    # Timeouts
    auth_timeout_seconds: int = 120
    token_timeout_seconds: int = 30
    
    @property
    def redirect_uri(self) -> str:
        """Construct redirect URI."""
        return f"http://{self.callback_host}:{self.callback_port}{self.callback_path}"


# ==============================================================================
# PKCE HELPERS
# ==============================================================================

def generate_code_verifier(length: int = 64) -> str:
    """Generate a PKCE code verifier."""
    # Use URL-safe characters
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_code_challenge(verifier: str) -> str:
    """Generate a PKCE code challenge from verifier (S256)."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def generate_state() -> str:
    """Generate a random state parameter."""
    return secrets.token_urlsafe(32)


# ==============================================================================
# ABSTRACT PROVIDER
# ==============================================================================

class OAuthProvider(ABC):
    """Abstract base class for OAuth providers."""
    
    def __init__(self, config: OAuthConfig):
        self.config = config
        self._token: OAuthToken | None = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'claude', 'gemini')."""
        pass
    
    @abstractmethod
    async def authenticate(self) -> OAuthToken:
        """
        Perform full OAuth authentication flow.
        
        Opens browser for user authorization and waits for callback.
        Returns new token on success.
        """
        pass
    
    @abstractmethod
    async def refresh(self, token: OAuthToken) -> OAuthToken:
        """
        Refresh an expired token.
        
        Raises RefreshFailedError if refresh token is invalid.
        """
        pass
    
    @abstractmethod
    async def revoke(self, token: OAuthToken) -> None:
        """Revoke a token (logout)."""
        pass
    
    @abstractmethod
    async def get_user_info(self, token: OAuthToken) -> dict[str, Any]:
        """Get user info including subscription tier."""
        pass
    
    async def is_available(self) -> bool:
        """Check if provider is available."""
        # Default implementation - can be overridden
        return True
    
    async def ensure_valid_token(self, token: OAuthToken) -> OAuthToken:
        """
        Ensure token is valid, refreshing if needed.
        
        Returns valid token or raises AuthError.
        """
        if not token.is_expired:
            return token
        
        if not token.refresh_token:
            raise TokenExpiredError(f"{self.name}: Token expired and no refresh token")
        
        try:
            return await self.refresh(token)
        except Exception as e:
            raise RefreshFailedError(f"{self.name}: Refresh failed: {e}")


# ==============================================================================
# MODEL INFO
# ==============================================================================

@dataclass
class ModelInfo:
    """Information about an available model."""
    
    id: str
    name: str
    provider: str
    tier_required: SubscriptionTier
    context_window: int = 0
    supports_vision: bool = False
    supports_tools: bool = False


# Default models per provider/tier
PROVIDER_MODELS: dict[str, dict[SubscriptionTier, list[str]]] = {
    "claude": {
        SubscriptionTier.FREE: ["claude-3-5-sonnet"],
        SubscriptionTier.PRO: ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
        SubscriptionTier.MAX: ["claude-4-opus", "claude-4-sonnet", "claude-3-5-sonnet"],
    },
    "gemini": {
        SubscriptionTier.FREE: ["gemini-2.0-flash"],
        SubscriptionTier.PRO: ["gemini-pro-3", "gemini-flash-3", "gemini-2.0-flash"],
        SubscriptionTier.ULTRA: ["gemini-ultra-3", "gemini-pro-3", "gemini-nano-2"],
    },
    "openai": {
        SubscriptionTier.FREE: ["gpt-3.5-turbo"],
        SubscriptionTier.PRO: ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        SubscriptionTier.MAX: ["gpt-4o", "o1", "o1-mini", "gpt-4-turbo"],
    },
}
