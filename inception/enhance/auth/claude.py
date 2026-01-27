"""
Claude OAuth Provider.

Implements browser-based OAuth authentication for Anthropic Claude,
mirroring the flow used by Claude Code with Pro/Max subscriptions.
"""

import asyncio
import logging
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode, parse_qs, urlparse

import httpx

from inception.enhance.auth.base import (
    OAuthConfig,
    OAuthToken,
    OAuthProvider,
    SubscriptionTier,
    AuthError,
    AuthCancelledError,
    TokenExpiredError,
    RefreshFailedError,
    generate_code_verifier,
    generate_code_challenge,
    generate_state,
)

logger = logging.getLogger(__name__)


@dataclass
class ClaudeOAuthConfig(OAuthConfig):
    """
    Claude-specific OAuth configuration.
    
    Based on the Claude Code OAuth flow:
    - Uses PKCE for security
    - Supports Pro/Max tier detection
    - Token stored in keychain
    """
    
    # Claude OAuth endpoints (beta backend)
    auth_url: str = "https://claude.ai/oauth/authorize"
    token_url: str = "https://claude.ai/oauth/token"
    userinfo_url: str = "https://claude.ai/api/account"
    revoke_url: str = "https://claude.ai/oauth/revoke"
    
    # API endpoint for authenticated requests
    api_base: str = "https://api.claude.ai/v1"
    
    # Client ID (public client, no secret)
    client_id: str = "inception-cli"
    
    # Default scopes
    scopes: list[str] = field(default_factory=lambda: [
        "model.access",
        "usage.read",
    ])
    
    # Callback configuration
    callback_port: int = 8042
    callback_path: str = "/callback/claude"
    
    # Timeouts
    auth_timeout_seconds: int = 120


class ClaudeOAuthProvider(OAuthProvider):
    """
    OAuth provider for Anthropic Claude.
    
    Implements the full OAuth 2.0 + PKCE flow:
    1. Generate PKCE verifier/challenge
    2. Open browser to authorization URL
    3. Start local callback server
    4. Exchange auth code for tokens
    5. Store tokens in keychain
    6. Auto-refresh when expired
    """
    
    def __init__(self, config: ClaudeOAuthConfig | None = None):
        super().__init__(config or ClaudeOAuthConfig())
        self.config: ClaudeOAuthConfig = self.config  # Type hint
        self._http_client: httpx.AsyncClient | None = None
    
    @property
    def name(self) -> str:
        return "claude"
    
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
        Perform full OAuth authentication flow.
        
        Opens browser for user authorization, waits for callback,
        then exchanges code for tokens.
        """
        logger.info("Starting Claude OAuth authentication flow")
        
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
        }
        auth_url = f"{self.config.auth_url}?{urlencode(auth_params)}"
        
        # Start callback server and open browser
        auth_code = await self._run_auth_flow(auth_url, state)
        
        # Exchange code for tokens
        token = await self._exchange_code(auth_code, code_verifier)
        
        # Get user info to determine tier
        user_info = await self.get_user_info(token)
        token.tier = self._parse_tier(user_info)
        token.provider = self.name
        
        logger.info(f"Claude OAuth complete: tier={token.tier.value}")
        return token
    
    async def _run_auth_flow(self, auth_url: str, expected_state: str) -> str:
        """
        Run the browser auth flow with local callback server.
        
        Returns authorization code on success.
        """
        from aiohttp import web
        
        auth_code: str | None = None
        auth_error: str | None = None
        
        async def callback_handler(request: web.Request) -> web.Response:
            nonlocal auth_code, auth_error
            
            # Check state
            state = request.query.get("state")
            if state != expected_state:
                auth_error = "State mismatch - possible CSRF attack"
                return web.Response(
                    text="Authentication failed: invalid state",
                    status=400
                )
            
            # Check for error
            if "error" in request.query:
                auth_error = request.query.get("error_description", request.query["error"])
                return web.Response(
                    text=f"Authentication failed: {auth_error}",
                    status=400
                )
            
            # Get code
            auth_code = request.query.get("code")
            if not auth_code:
                auth_error = "No authorization code received"
                return web.Response(
                    text="Authentication failed: no code",
                    status=400
                )
            
            # Success response
            return web.Response(
                text="""
                <html>
                <body style="font-family: system-ui; text-align: center; padding-top: 50px;">
                    <h1>✅ Authentication Successful</h1>
                    <p>You can close this window and return to Inception.</p>
                </body>
                </html>
                """,
                content_type="text/html"
            )
        
        # Create callback app
        app = web.Application()
        app.router.add_get(self.config.callback_path, callback_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(
            runner,
            self.config.callback_host,
            self.config.callback_port
        )
        
        try:
            await site.start()
            logger.info(f"Callback server started on {self.config.redirect_uri}")
            
            # Open browser
            logger.info(f"Opening browser for authentication...")
            webbrowser.open(auth_url)
            
            # Wait for callback
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
    
    async def _exchange_code(
        self,
        code: str,
        code_verifier: str
    ) -> OAuthToken:
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
            raise RefreshFailedError("No refresh token available")
        
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
            raise RefreshFailedError(f"Token refresh failed: {response.text}")
        
        data = response.json()
        
        expires_at = None
        if "expires_in" in data:
            expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])
        
        new_token = OAuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", token.refresh_token),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope", token.scope),
            provider=self.name,
            tier=token.tier,
        )
        
        logger.info("Claude token refreshed successfully")
        return new_token
    
    async def revoke(self, token: OAuthToken) -> None:
        """Revoke a token (logout)."""
        client = await self._get_client()
        
        await client.post(
            self.config.revoke_url,
            data={
                "token": token.access_token,
                "client_id": self.config.client_id,
            }
        )
        
        logger.info("Claude token revoked")
    
    async def get_user_info(self, token: OAuthToken) -> dict[str, Any]:
        """Get user info including subscription tier."""
        client = await self._get_client()
        
        response = await client.get(
            self.config.userinfo_url,
            headers={"Authorization": f"Bearer {token.access_token}"}
        )
        
        if response.status_code != 200:
            return {}
        
        return response.json()
    
    def _parse_tier(self, user_info: dict[str, Any]) -> SubscriptionTier:
        """Parse subscription tier from user info."""
        # Check subscription field
        subscription = user_info.get("subscription", {})
        plan = subscription.get("plan", "free").lower()
        
        if "max" in plan:
            return SubscriptionTier.MAX
        elif "pro" in plan:
            return SubscriptionTier.PRO
        elif "enterprise" in plan:
            return SubscriptionTier.ENTERPRISE
        
        return SubscriptionTier.FREE
    
    async def is_available(self) -> bool:
        """Check if Claude is reachable."""
        try:
            client = await self._get_client()
            response = await client.get("https://claude.ai", timeout=5.0)
            return response.status_code < 500
        except Exception:
            return False
