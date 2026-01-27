"""
Gemini OAuth Provider.

Implements Google OAuth 2.0 authentication for Gemini/Vertex AI,
using subscription tier detection for Pro/Ultra access.
"""

import asyncio
import logging
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from inception.enhance.auth.base import (
    OAuthConfig,
    OAuthToken,
    OAuthProvider,
    SubscriptionTier,
    AuthError,
    AuthCancelledError,
    RefreshFailedError,
    generate_code_verifier,
    generate_code_challenge,
    generate_state,
)

logger = logging.getLogger(__name__)


@dataclass
class GeminiOAuthConfig(OAuthConfig):
    """
    Gemini-specific OAuth configuration.
    
    Uses Google OAuth 2.0 with Generative AI scopes.
    """
    
    # Google OAuth endpoints
    auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"
    userinfo_url: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    revoke_url: str = "https://oauth2.googleapis.com/revoke"
    subscription_url: str = "https://generativelanguage.googleapis.com/v1/models"
    
    # API endpoint
    api_base: str = "https://generativelanguage.googleapis.com/v1"
    
    # Client configuration (public client for CLI)
    client_id: str = "inception-cli.apps.googleusercontent.com"
    
    # Scopes for Generative AI access
    scopes: list[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/generative-language",
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/userinfo.email",
    ])
    
    # Callback configuration
    callback_port: int = 8043
    callback_path: str = "/callback/gemini"
    
    # Additional auth parameters
    access_type: str = "offline"  # For refresh token
    prompt: str = "consent"  # Always show consent for refresh token


class GeminiOAuthProvider(OAuthProvider):
    """
    OAuth provider for Google Gemini.
    
    Implements Google OAuth 2.0 with:
    - PKCE support
    - Offline access for refresh tokens
    - Subscription tier detection
    """
    
    def __init__(self, config: GeminiOAuthConfig | None = None):
        super().__init__(config or GeminiOAuthConfig())
        self.config: GeminiOAuthConfig = self.config
        self._http_client: httpx.AsyncClient | None = None
    
    @property
    def name(self) -> str:
        return "gemini"
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.token_timeout_seconds),
                follow_redirects=True,
            )
        return self._http_client
    
    async def authenticate(self) -> OAuthToken:
        """
        Perform Google OAuth authentication flow.
        """
        logger.info("Starting Gemini/Google OAuth authentication flow")
        
        # Generate PKCE values
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = generate_state()
        
        # Build authorization URL
        auth_params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": self.config.access_type,
            "prompt": self.config.prompt,
        }
        auth_url = f"{self.config.auth_url}?{urlencode(auth_params)}"
        
        # Run auth flow
        auth_code = await self._run_auth_flow(auth_url, state)
        
        # Exchange for tokens
        token = await self._exchange_code(auth_code, code_verifier)
        
        # Detect subscription tier
        token.tier = await self._detect_tier(token)
        token.provider = self.name
        
        logger.info(f"Gemini OAuth complete: tier={token.tier.value}")
        return token
    
    async def _run_auth_flow(self, auth_url: str, expected_state: str) -> str:
        """Run browser auth flow with callback server."""
        from aiohttp import web
        
        auth_code: str | None = None
        auth_error: str | None = None
        
        async def callback_handler(request: web.Request) -> web.Response:
            nonlocal auth_code, auth_error
            
            state = request.query.get("state")
            if state != expected_state:
                auth_error = "State mismatch"
                return web.Response(text="Authentication failed", status=400)
            
            if "error" in request.query:
                auth_error = request.query.get("error_description", request.query["error"])
                return web.Response(text=f"Error: {auth_error}", status=400)
            
            auth_code = request.query.get("code")
            if not auth_code:
                auth_error = "No authorization code"
                return web.Response(text="No code received", status=400)
            
            return web.Response(
                text="""
                <html>
                <body style="font-family: system-ui; text-align: center; padding-top: 50px; background: linear-gradient(135deg, #4285f4, #34a853);">
                    <div style="background: white; padding: 40px; border-radius: 12px; display: inline-block; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
                        <h1 style="color: #202124;">✅ Gemini Connected</h1>
                        <p style="color: #5f6368;">You can close this window and return to Inception.</p>
                    </div>
                </body>
                </html>
                """,
                content_type="text/html"
            )
        
        app = web.Application()
        app.router.add_get(self.config.callback_path, callback_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.config.callback_host, self.config.callback_port)
        
        try:
            await site.start()
            logger.info(f"Callback server on {self.config.redirect_uri}")
            
            webbrowser.open(auth_url)
            
            timeout = self.config.auth_timeout_seconds
            start = asyncio.get_event_loop().time()
            
            while auth_code is None and auth_error is None:
                if asyncio.get_event_loop().time() - start > timeout:
                    raise AuthCancelledError("Authentication timed out")
                await asyncio.sleep(0.5)
            
            if auth_error:
                raise AuthError(f"Authentication failed: {auth_error}")
            
            return auth_code
            
        finally:
            await runner.cleanup()
    
    async def _exchange_code(self, code: str, code_verifier: str) -> OAuthToken:
        """Exchange authorization code for tokens."""
        client = await self._get_client()
        
        response = await client.post(
            self.config.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.config.redirect_uri,
                "client_id": self.config.client_id,
                "code_verifier": code_verifier,
            }
        )
        
        if response.status_code != 200:
            raise AuthError(f"Token exchange failed: {response.text}")
        
        data = response.json()
        
        expires_at = None
        if "expires_in" in data:
            expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])
        
        return OAuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope", ""),
            provider=self.name,
        )
    
    async def refresh(self, token: OAuthToken) -> OAuthToken:
        """Refresh an expired token."""
        if not token.refresh_token:
            raise RefreshFailedError("No refresh token")
        
        client = await self._get_client()
        
        response = await client.post(
            self.config.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": self.config.client_id,
            }
        )
        
        if response.status_code != 200:
            raise RefreshFailedError(f"Refresh failed: {response.text}")
        
        data = response.json()
        
        expires_at = None
        if "expires_in" in data:
            expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])
        
        return OAuthToken(
            access_token=data["access_token"],
            refresh_token=token.refresh_token,  # Google doesn't always return new refresh token
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope", token.scope),
            provider=self.name,
            tier=token.tier,
        )
    
    async def revoke(self, token: OAuthToken) -> None:
        """Revoke a token."""
        client = await self._get_client()
        await client.post(
            self.config.revoke_url,
            params={"token": token.access_token}
        )
        logger.info("Gemini token revoked")
    
    async def get_user_info(self, token: OAuthToken) -> dict[str, Any]:
        """Get user info from Google."""
        client = await self._get_client()
        
        response = await client.get(
            self.config.userinfo_url,
            headers={"Authorization": f"Bearer {token.access_token}"}
        )
        
        if response.status_code != 200:
            return {}
        
        return response.json()
    
    async def _detect_tier(self, token: OAuthToken) -> SubscriptionTier:
        """Detect subscription tier by checking available models."""
        client = await self._get_client()
        
        try:
            response = await client.get(
                self.config.subscription_url,
                headers={"Authorization": f"Bearer {token.access_token}"}
            )
            
            if response.status_code != 200:
                return SubscriptionTier.FREE
            
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            
            # Check for premium models
            if any("ultra" in m.lower() for m in models):
                return SubscriptionTier.ULTRA
            elif any("pro" in m.lower() for m in models):
                return SubscriptionTier.PRO
            
            return SubscriptionTier.FREE
            
        except Exception as e:
            logger.warning(f"Tier detection failed: {e}")
            return SubscriptionTier.FREE
    
    async def is_available(self) -> bool:
        """Check if Gemini API is reachable."""
        try:
            client = await self._get_client()
            response = await client.get(
                "https://generativelanguage.googleapis.com/",
                timeout=5.0
            )
            return response.status_code < 500
        except Exception:
            return False
