"""
Unified OAuth Manager.

Orchestrates authentication across all providers with:
- Auto-selection based on availability
- Fallback chain for rate limits
- Health monitoring
- Token lifecycle management
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from inception.enhance.auth.base import (
    OAuthToken,
    OAuthProvider,
    SubscriptionTier,
    AuthError,
    TokenExpiredError,
    RefreshFailedError,
    ProviderUnavailableError,
    ModelInfo,
    PROVIDER_MODELS,
)
from inception.enhance.auth.storage import TokenStorage
from inception.enhance.auth.claude import ClaudeOAuthProvider, ClaudeOAuthConfig
from inception.enhance.auth.gemini import GeminiOAuthProvider, GeminiOAuthConfig
from inception.enhance.auth.openai import OpenAIOAuthProvider, OpenAIOAuthConfig

logger = logging.getLogger(__name__)


@dataclass
class OAuthManagerConfig:
    """Configuration for OAuth manager."""
    
    # Provider configs
    claude: ClaudeOAuthConfig = field(default_factory=ClaudeOAuthConfig)
    gemini: GeminiOAuthConfig = field(default_factory=GeminiOAuthConfig)
    openai: OpenAIOAuthConfig = field(default_factory=OpenAIOAuthConfig)
    
    # Fallback order (first = preferred)
    fallback_order: list[str] = field(default_factory=lambda: ["claude", "gemini", "openai"])
    
    # Auto-refresh threshold (refresh when this close to expiry)
    refresh_threshold_minutes: int = 5
    
    # Health check interval
    health_check_interval_seconds: int = 300


class OAuthManager:
    """
    Unified authentication manager across all LLM providers.
    
    Features:
    - Automatic provider selection based on availability
    - Token lifecycle management (store, refresh, revoke)
    - Fallback chain for rate limits
    - Health monitoring
    - Subscription tier detection
    
    Usage:
        manager = OAuthManager()
        
        # Setup authentication
        await manager.setup("claude")  # Opens browser
        
        # Get best available provider
        token = await manager.get_token()  # Auto-selects
        
        # Or specific provider
        token = await manager.get_token("gemini")
    """
    
    def __init__(self, config: OAuthManagerConfig | None = None):
        self.config = config or OAuthManagerConfig()
        self.storage = TokenStorage()
        
        # Initialize providers
        self.providers: dict[str, OAuthProvider] = {
            "claude": ClaudeOAuthProvider(self.config.claude),
            "gemini": GeminiOAuthProvider(self.config.gemini),
            "openai": OpenAIOAuthProvider(self.config.openai),
        }
        
        # Cache for token validity
        self._token_cache: dict[str, OAuthToken] = {}
        self._health_cache: dict[str, bool] = {}
        self._last_health_check: float = 0
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    async def setup(self, provider: str) -> OAuthToken:
        """
        Set up authentication for a provider.
        
        Opens browser for OAuth flow and stores token.
        
        Args:
            provider: Provider name (claude, gemini, openai)
            
        Returns:
            New OAuth token
        """
        if provider not in self.providers:
            raise AuthError(f"Unknown provider: {provider}")
        
        logger.info(f"Setting up authentication for {provider}")
        
        # Run OAuth flow
        token = await self.providers[provider].authenticate()
        
        # Store token
        self.storage.store(provider, token)
        self._token_cache[provider] = token
        
        logger.info(f"Authentication complete for {provider}: tier={token.tier.value}")
        return token
    
    async def get_token(self, provider: str | None = None) -> OAuthToken:
        """
        Get a valid token for a provider.
        
        If provider is None, selects best available.
        Automatically refreshes expired tokens.
        
        Args:
            provider: Specific provider or None for auto-select
            
        Returns:
            Valid OAuth token
            
        Raises:
            AuthError: No valid token available
        """
        if provider:
            return await self._get_provider_token(provider)
        
        # Auto-select from fallback chain
        for p in self.config.fallback_order:
            try:
                token = await self._get_provider_token(p)
                if token:
                    return token
            except AuthError:
                continue
        
        raise AuthError("No authenticated providers available. Run 'inception auth setup'")
    
    async def _get_provider_token(self, provider: str) -> OAuthToken:
        """Get or refresh token for specific provider."""
        # Check cache first
        if provider in self._token_cache:
            token = self._token_cache[provider]
            if not token.is_expired:
                return token
        
        # Try to load from storage
        token = self.storage.retrieve(provider)
        if token is None:
            raise AuthError(f"No token stored for {provider}")
        
        # Refresh if needed
        if token.is_expired:
            try:
                token = await self.providers[provider].refresh(token)
                self.storage.store(provider, token)
            except RefreshFailedError:
                # Need full re-auth
                raise AuthError(f"Token expired for {provider}, run 'inception auth setup {provider}'")
        
        self._token_cache[provider] = token
        return token
    
    async def logout(self, provider: str | None = None) -> None:
        """
        Logout from a provider or all providers.
        
        Args:
            provider: Specific provider or None for all
        """
        providers = [provider] if provider else list(self.providers.keys())
        
        for p in providers:
            token = self.storage.retrieve(p)
            if token:
                try:
                    await self.providers[p].revoke(token)
                except Exception as e:
                    logger.warning(f"Revoke failed for {p}: {e}")
                
                self.storage.delete(p)
                self._token_cache.pop(p, None)
                
            logger.info(f"Logged out from {p}")
    
    # =========================================================================
    # STATUS & HEALTH
    # =========================================================================
    
    async def status(self) -> dict[str, dict[str, Any]]:
        """
        Get authentication status for all providers.
        
        Returns:
            Dict of provider status info
        """
        result = {}
        
        for name, provider in self.providers.items():
            token = self.storage.retrieve(name)
            
            status = {
                "authenticated": token is not None,
                "tier": token.tier.value if token else None,
                "expires_at": token.expires_at.isoformat() if token and token.expires_at else None,
                "is_expired": token.is_expired if token else None,
                "available": await provider.is_available(),
            }
            
            if token and not token.is_expired:
                status["models"] = self._get_available_models(name, token.tier)
            
            result[name] = status
        
        return result
    
    def _get_available_models(self, provider: str, tier: SubscriptionTier) -> list[str]:
        """Get models available for provider/tier."""
        provider_models = PROVIDER_MODELS.get(provider, {})
        return provider_models.get(tier, [])
    
    async def health_check(self) -> dict[str, bool]:
        """
        Check health of all providers.
        
        Returns:
            Dict of provider name -> is_healthy
        """
        results = {}
        
        for name, provider in self.providers.items():
            results[name] = await provider.is_available()
        
        self._health_cache = results
        return results
    
    # =========================================================================
    # PROVIDER SELECTION
    # =========================================================================
    
    async def get_best_provider(
        self,
        model_preference: str | None = None,
        tier_required: SubscriptionTier | None = None,
    ) -> tuple[str, OAuthToken]:
        """
        Get the best available provider based on criteria.
        
        Args:
            model_preference: Preferred model name
            tier_required: Minimum tier required
            
        Returns:
            Tuple of (provider_name, token)
        """
        for provider_name in self.config.fallback_order:
            try:
                token = await self._get_provider_token(provider_name)
                
                # Check tier requirement
                if tier_required and token.tier.value < tier_required.value:
                    continue
                
                # Check model availability
                if model_preference:
                    models = self._get_available_models(provider_name, token.tier)
                    if model_preference not in models:
                        continue
                
                return (provider_name, token)
                
            except AuthError:
                continue
        
        raise AuthError("No suitable provider available")
    
    async def with_fallback(
        self,
        func: Callable[[str, OAuthToken], Any],
        max_retries: int = 3,
    ) -> Any:
        """
        Execute function with automatic provider fallback.
        
        If a provider fails (rate limit, etc), tries next.
        
        Args:
            func: Async function(provider_name, token) -> result
            max_retries: Max total attempts
            
        Returns:
            Function result
        """
        attempts = 0
        last_error = None
        
        for provider_name in self.config.fallback_order:
            if attempts >= max_retries:
                break
            
            try:
                token = await self._get_provider_token(provider_name)
                return await func(provider_name, token)
            except Exception as e:
                last_error = e
                attempts += 1
                logger.warning(f"{provider_name} failed: {e}, trying next...")
                continue
        
        raise AuthError(f"All providers failed: {last_error}")
    
    # =========================================================================
    # CONTEXT MANAGER
    # =========================================================================
    
    async def __aenter__(self) -> "OAuthManager":
        return self
    
    async def __aexit__(self, *args) -> None:
        # Cleanup HTTP clients
        for provider in self.providers.values():
            if hasattr(provider, "_http_client") and provider._http_client:
                await provider._http_client.aclose()
