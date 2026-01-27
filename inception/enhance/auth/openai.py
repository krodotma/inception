"""
OpenAI OAuth Provider.

Implements session-based authentication for ChatGPT Plus/Pro,
extracting session tokens from browser login.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx

from inception.enhance.auth.base import (
    OAuthConfig,
    OAuthToken,
    OAuthProvider,
    SubscriptionTier,
    AuthError,
    AuthCancelledError,
    RefreshFailedError,
)

logger = logging.getLogger(__name__)


@dataclass
class OpenAIOAuthConfig(OAuthConfig):
    """
    OpenAI session-based configuration.
    
    OpenAI doesn't provide OAuth for third-party apps,
    so we use session token extraction from browser.
    """
    
    # OpenAI endpoints
    login_url: str = "https://chat.openai.com/"
    api_base: str = "https://chat.openai.com/backend-api"
    session_url: str = "https://chat.openai.com/api/auth/session"
    models_url: str = "https://chat.openai.com/backend-api/models"
    
    # Session refresh (ChatGPT sessions last ~7 days)
    session_refresh_hours: int = 24
    
    # Callback for browser-based auth
    callback_port: int = 8044
    callback_path: str = "/callback/openai"


class OpenAIOAuthProvider(OAuthProvider):
    """
    OAuth-like provider for OpenAI ChatGPT.
    
    Since OpenAI doesn't offer OAuth for third-party apps,
    this implements a session-based approach:
    
    1. Open browser to ChatGPT login
    2. User logs in manually
    3. Extract session token from browser
    4. Use session token for API access
    """
    
    def __init__(self, config: OpenAIOAuthConfig | None = None):
        super().__init__(config or OpenAIOAuthConfig())
        self.config: OpenAIOAuthConfig = self.config
        self._http_client: httpx.AsyncClient | None = None
    
    @property
    def name(self) -> str:
        return "openai"
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30),
                follow_redirects=True,
            )
        return self._http_client
    
    async def authenticate(self) -> OAuthToken:
        """
        Perform browser-based session authentication.
        
        Opens browser for manual login, then extracts session.
        """
        logger.info("Starting OpenAI session authentication")
        
        # Check if we can use Playwright for automated extraction
        try:
            session_token = await self._browser_auth_playwright()
        except ImportError:
            logger.warning("Playwright not available, using manual flow")
            session_token = await self._browser_auth_manual()
        
        # Create token from session
        token = OAuthToken(
            access_token=session_token,
            refresh_token=None,  # Sessions don't have refresh tokens
            token_type="Session",
            expires_at=datetime.utcnow() + timedelta(
                hours=self.config.session_refresh_hours
            ),
            scope="chat.completions",
            provider=self.name,
        )
        
        # Detect tier
        token.tier = await self._detect_tier(token)
        
        logger.info(f"OpenAI session auth complete: tier={token.tier.value}")
        return token
    
    async def _browser_auth_playwright(self) -> str:
        """
        Use Playwright to automate session extraction.
        
        Waits for user to complete login, then extracts cookies.
        """
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.goto(self.config.login_url)
            
            logger.info("Please log in to ChatGPT in the browser window...")
            
            # Wait for successful login (dashboard URL or specific element)
            try:
                await page.wait_for_url("**/chat.openai.com/**", timeout=120000)
                await page.wait_for_selector('[data-testid="chat-input"]', timeout=30000)
            except Exception:
                raise AuthCancelledError("Login timed out or was cancelled")
            
            # Extract session token from cookies
            cookies = await context.cookies()
            session_token = None
            
            for cookie in cookies:
                if cookie["name"] == "__Secure-next-auth.session-token":
                    session_token = cookie["value"]
                    break
            
            await browser.close()
            
            if not session_token:
                raise AuthError("Could not extract session token")
            
            return session_token
    
    async def _browser_auth_manual(self) -> str:
        """
        Manual session token input flow.
        
        Opens browser and prompts user to paste token.
        """
        import webbrowser
        from aiohttp import web
        
        session_token: str | None = None
        
        async def token_handler(request: web.Request) -> web.Response:
            nonlocal session_token
            
            if request.method == "POST":
                data = await request.post()
                session_token = data.get("token", "").strip()
                
                if session_token:
                    return web.Response(
                        text="""
                        <html>
                        <body style="font-family: system-ui; text-align: center; padding: 50px; background: #343541; color: white;">
                            <h1>✅ Session Token Received</h1>
                            <p>You can close this window.</p>
                        </body>
                        </html>
                        """,
                        content_type="text/html"
                    )
            
            # Show token input form
            return web.Response(
                text="""
                <html>
                <head>
                    <title>OpenAI Session Token</title>
                    <style>
                        body { font-family: system-ui; background: #343541; color: white; padding: 40px; }
                        .container { max-width: 600px; margin: 0 auto; }
                        h1 { color: #10a37f; }
                        .steps { background: #444654; padding: 20px; border-radius: 8px; margin: 20px 0; }
                        .steps li { margin: 10px 0; }
                        input[type="text"] { width: 100%; padding: 12px; border: none; border-radius: 4px; margin: 10px 0; }
                        button { background: #10a37f; color: white; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; }
                        button:hover { background: #0d8a6f; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>OpenAI Session Authentication</h1>
                        <div class="steps">
                            <p>To authenticate with ChatGPT:</p>
                            <ol>
                                <li>Log in to <a href="https://chat.openai.com" target="_blank" style="color: #10a37f;">chat.openai.com</a></li>
                                <li>Open Developer Tools (F12)</li>
                                <li>Go to Application → Cookies</li>
                                <li>Find <code>__Secure-next-auth.session-token</code></li>
                                <li>Copy and paste the value below</li>
                            </ol>
                        </div>
                        <form method="POST">
                            <input type="text" name="token" placeholder="Paste session token here..." required>
                            <button type="submit">Submit Token</button>
                        </form>
                    </div>
                </body>
                </html>
                """,
                content_type="text/html"
            )
        
        app = web.Application()
        app.router.add_get(self.config.callback_path, token_handler)
        app.router.add_post(self.config.callback_path, token_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.config.callback_host, self.config.callback_port)
        
        try:
            await site.start()
            
            # Open browser to our token input page
            token_url = f"http://{self.config.callback_host}:{self.config.callback_port}{self.config.callback_path}"
            webbrowser.open(token_url)
            
            # Wait for token
            timeout = self.config.auth_timeout_seconds
            start = asyncio.get_event_loop().time()
            
            while session_token is None:
                if asyncio.get_event_loop().time() - start > timeout:
                    raise AuthCancelledError("Session token input timed out")
                await asyncio.sleep(0.5)
            
            return session_token
            
        finally:
            await runner.cleanup()
    
    async def refresh(self, token: OAuthToken) -> OAuthToken:
        """
        Refresh session - requires re-authentication.
        
        ChatGPT sessions can't be programmatically refreshed.
        """
        # For sessions, we need to re-authenticate
        logger.info("Session refresh requested - initiating re-authentication")
        return await self.authenticate()
    
    async def revoke(self, token: OAuthToken) -> None:
        """Session revocation is a no-op (user must log out manually)."""
        logger.info("OpenAI session logout - please log out manually from chat.openai.com")
    
    async def get_user_info(self, token: OAuthToken) -> dict[str, Any]:
        """Get user info from session."""
        client = await self._get_client()
        
        try:
            response = await client.get(
                self.config.session_url,
                cookies={"__Secure-next-auth.session-token": token.access_token}
            )
            
            if response.status_code != 200:
                return {}
            
            return response.json()
        except Exception:
            return {}
    
    async def _detect_tier(self, token: OAuthToken) -> SubscriptionTier:
        """Detect subscription tier by checking available models."""
        client = await self._get_client()
        
        try:
            response = await client.get(
                self.config.models_url,
                cookies={"__Secure-next-auth.session-token": token.access_token}
            )
            
            if response.status_code != 200:
                return SubscriptionTier.FREE
            
            data = response.json()
            models = [m.get("slug", "") for m in data.get("models", [])]
            
            # Check for premium models
            if "o1" in models or "gpt-4o" in models:
                # Could be Plus or Pro
                if any(m for m in models if "extended" in m.lower()):
                    return SubscriptionTier.MAX  # Pro tier
                return SubscriptionTier.PRO  # Plus tier
            
            return SubscriptionTier.FREE
            
        except Exception as e:
            logger.warning(f"Tier detection failed: {e}")
            return SubscriptionTier.FREE
    
    async def is_available(self) -> bool:
        """Check if ChatGPT is reachable."""
        try:
            client = await self._get_client()
            response = await client.get("https://chat.openai.com", timeout=5.0)
            return response.status_code < 500
        except Exception:
            return False
