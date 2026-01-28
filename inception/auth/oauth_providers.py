"""
OAuth Providers for Inception.

Implements OAuth-based authentication for direct provider access,
using the krodotma-common browser session pattern from Pluribus:

Priority Order (Web Session Auth):
1. claude-web (Claude Max via claude.ai)
2. gemini-web (Gemini Ultra via aistudio.google.com)
3. chatgpt-web (ChatGPT via chat.openai.com)
4. grok-web (Grok via grok.com)

Fallback (API Keys):
5. OpenRouter
"""

from __future__ import annotations

import httpx
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from inception.auth.token_store import TokenStore, Token

# Import krodotma-common for shared browser session auth
KRODOTMA_COMMON = Path.home() / "krodotma-common"
PLURIBUS_ROOT = Path.home() / "pluribus_evolution"
if str(KRODOTMA_COMMON) not in sys.path:
    sys.path.insert(0, str(KRODOTMA_COMMON))
if str(PLURIBUS_ROOT) not in sys.path:
    sys.path.insert(0, str(PLURIBUS_ROOT))

try:
    from auth.browser_session_daemon import WEB_PROVIDERS
    WEB_PROVIDERS_AVAILABLE = True
except ImportError:
    WEB_PROVIDERS = {}
    WEB_PROVIDERS_AVAILABLE = False




@dataclass
class OAuthConfig:
    """Configuration for OAuth provider."""
    
    client_id: str
    auth_url: str
    token_url: str
    scopes: list[str]
    redirect_uri: str = "http://localhost:8000/auth/callback"


class OAuthProvider(ABC):
    """Abstract base class for OAuth-based LLM providers."""
    
    name: str
    config: OAuthConfig
    
    def __init__(self, token_store: TokenStore | None = None):
        self.token_store = token_store or TokenStore()
        self._client = httpx.Client(timeout=120.0)
    
    @abstractmethod
    def get_auth_url(self) -> str:
        """Get the authorization URL for OAuth flow."""
        pass
    
    @abstractmethod
    def exchange_code(self, code: str) -> Token:
        """Exchange authorization code for access token."""
        pass
    
    @abstractmethod
    def refresh_token(self, token: Token) -> Token:
        """Refresh an expired token."""
        pass
    
    def get_token(self) -> Token | None:
        """Get valid token, refreshing if needed."""
        token = self.token_store.load(self.name)
        if token is None:
            return None
        
        if token.is_expired and token.refresh_token:
            try:
                token = self.refresh_token(token)
                self.token_store.save(self.name, token)
            except Exception:
                return None
        
        return token if token.is_valid else None
    
    def is_available(self) -> bool:
        """Check if provider has valid authentication."""
        return self.get_token() is not None
    
    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Generate a completion using the provider."""
        pass


class ClawdBotProvider(OAuthProvider):
    """
    ClawdBot OAuth provider for Claude Max direct access.
    
    Uses subscription-based OAuth flow to avoid API key dependency.
    Priority 1 provider for Claude models.
    """
    
    name = "clawdbot"
    
    # Claude Max models available via ClawdBot
    MODELS = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3.5-haiku": "claude-3-5-haiku-20241022",
    }
    
    def __init__(
        self,
        model: str = "claude-3.5-sonnet",
        token_store: TokenStore | None = None,
    ):
        super().__init__(token_store)
        self.model = self.MODELS.get(model, model)
        self.config = OAuthConfig(
            client_id="inception-knowledge-system",
            auth_url="https://clawdbot.dev/oauth/authorize",
            token_url="https://clawdbot.dev/oauth/token",
            scopes=["completions", "streaming"],
        )
    
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL."""
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes),
            "response_type": "code",
            "state": f"inception_{int(time.time())}",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.auth_url}?{query}"
    
    def exchange_code(self, code: str) -> Token:
        """Exchange authorization code for token."""
        response = self._client.post(
            self.config.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.config.client_id,
                "redirect_uri": self.config.redirect_uri,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        expires_in = data.get("expires_in", 3600)
        token = Token(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            refresh_token=data.get("refresh_token"),
            scope=" ".join(self.config.scopes),
            provider=self.name,
        )
        self.token_store.save(self.name, token)
        return token
    
    def refresh_token(self, token: Token) -> Token:
        """Refresh an expired token."""
        if not token.refresh_token:
            raise ValueError("No refresh token available")
        
        response = self._client.post(
            self.config.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": self.config.client_id,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        expires_in = data.get("expires_in", 3600)
        new_token = Token(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            refresh_token=data.get("refresh_token", token.refresh_token),
            scope=token.scope,
            provider=self.name,
        )
        return new_token
    
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Generate completion via ClawdBot proxy to Claude."""
        token = self.get_token()
        if not token:
            raise RuntimeError("ClawdBot not authenticated. Run OAuth flow first.")
        
        response = self._client.post(
            "https://clawdbot.dev/v1/messages",
            headers={
                "Authorization": f"{token.token_type} {token.access_token}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system or "You are a helpful assistant.",
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json()


class MoltBotProvider(OAuthProvider):
    """
    MoltBot OAuth provider for Gemini Ultra direct access.
    
    Uses subscription-based OAuth flow to avoid API key dependency.
    Priority 2 provider for Gemini models.
    """
    
    name = "moltbot"
    
    # Gemini models available via MoltBot
    MODELS = {
        "gemini-ultra": "gemini-1.5-pro",
        "gemini-pro": "gemini-1.5-pro",
        "gemini-flash": "gemini-1.5-flash",
    }
    
    def __init__(
        self,
        model: str = "gemini-pro",
        token_store: TokenStore | None = None,
    ):
        super().__init__(token_store)
        self.model = self.MODELS.get(model, model)
        self.config = OAuthConfig(
            client_id="inception-knowledge-system",
            auth_url="https://moltbot.dev/oauth/authorize",
            token_url="https://moltbot.dev/oauth/token",
            scopes=["generate", "streaming"],
        )
    
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL."""
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes),
            "response_type": "code",
            "state": f"inception_{int(time.time())}",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.auth_url}?{query}"
    
    def exchange_code(self, code: str) -> Token:
        """Exchange authorization code for token."""
        response = self._client.post(
            self.config.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.config.client_id,
                "redirect_uri": self.config.redirect_uri,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        expires_in = data.get("expires_in", 3600)
        token = Token(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            refresh_token=data.get("refresh_token"),
            scope=" ".join(self.config.scopes),
            provider=self.name,
        )
        self.token_store.save(self.name, token)
        return token
    
    def refresh_token(self, token: Token) -> Token:
        """Refresh an expired token."""
        if not token.refresh_token:
            raise ValueError("No refresh token available")
        
        response = self._client.post(
            self.config.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": self.config.client_id,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        expires_in = data.get("expires_in", 3600)
        new_token = Token(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            refresh_token=data.get("refresh_token", token.refresh_token),
            scope=token.scope,
            provider=self.name,
        )
        return new_token
    
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Generate completion via MoltBot proxy to Gemini."""
        token = self.get_token()
        if not token:
            raise RuntimeError("MoltBot not authenticated. Run OAuth flow first.")
        
        # Gemini uses different format - combine system + user
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        response = self._client.post(
            f"https://moltbot.dev/v1/models/{self.model}:generateContent",
            headers={
                "Authorization": f"{token.token_type} {token.access_token}",
                "Content-Type": "application/json",
            },
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        response.raise_for_status()
        return response.json()


def get_oauth_provider(
    name: str = "auto",
    model: str | None = None,
) -> OAuthProvider:
    """
    Get an OAuth provider by name with automatic fallback.
    
    Priority order:
    1. ClawdBot (Claude Max)
    2. MoltBot (Gemini Ultra)
    
    Args:
        name: Provider name ("clawdbot", "moltbot", "auto")
        model: Optional model override
    
    Returns:
        An available OAuthProvider
    
    Raises:
        RuntimeError: If no provider is available
    """
    if name == "clawdbot":
        provider = ClawdBotProvider(model=model or "claude-3.5-sonnet")
        if provider.is_available():
            return provider
        raise RuntimeError(
            "ClawdBot not authenticated. "
            f"Visit: {provider.get_auth_url()}"
        )
    
    if name == "moltbot":
        provider = MoltBotProvider(model=model or "gemini-pro")
        if provider.is_available():
            return provider
        raise RuntimeError(
            "MoltBot not authenticated. "
            f"Visit: {provider.get_auth_url()}"
        )
    
    # Auto mode: try in priority order
    if name == "auto":
        # Priority 1: ClawdBot (Claude Max)
        clawdbot = ClawdBotProvider()
        if clawdbot.is_available():
            return clawdbot
        
        # Priority 2: MoltBot (Gemini Ultra)
        moltbot = MoltBotProvider()
        if moltbot.is_available():
            return moltbot
        
        raise RuntimeError(
            "No OAuth provider available. Authenticate with one of:\n"
            f"1. ClawdBot: {clawdbot.get_auth_url()}\n"
            f"2. MoltBot: {moltbot.get_auth_url()}"
        )
    
    raise ValueError(f"Unknown OAuth provider: {name}")
