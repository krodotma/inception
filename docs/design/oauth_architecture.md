# OAuth Authentication Architecture

## Overview

Inception implements **API-key-free authentication** using OAuth flows tied to subscription plans (Pro, Max, Ultra). This leverages the same authentication mechanisms used by Claude Code, Antigravity IDE, and OpenCode.

---

## Authentication Strategy

### Core Principle: NO API KEYS

Instead of API keys, we authenticate through:

1. **Browser-based OAuth flows** - User authorizes via provider's web UI
2. **Session tokens** - Short-lived tokens stored in OS keychain
3. **Refresh tokens** - Automatic token renewal without re-authentication
4. **Subscription detection** - Routes to appropriate tier (Pro/Max/Ultra)

---

## Provider Authentication Flows

### 1. Claude (Anthropic)

**Method**: OAuth 2.0 with PKCE via Claude Code flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Inception │────▶│ Local Server │────▶│ claude.ai/oauth │
│   (CLI/TUI) │     │  (callback)  │     │   (browser)     │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │                      │
                           │◀─────────────────────┘
                           │   (authorization code)
                           ▼
                    ┌──────────────┐
                    │    Keychain  │
                    │ (tokens)     │
                    └──────────────┘
```

**Implementation**:
```python
# inception/enhance/auth/claude.py
@dataclass
class ClaudeOAuthConfig:
    auth_url: str = "https://claude.ai/oauth/authorize"
    token_url: str = "https://claude.ai/oauth/token"
    callback_port: int = 8000
    scopes: list[str] = field(default_factory=lambda: ["model.access", "usage.read"])

class ClaudeOAuthProvider:
    def authenticate(self) -> OAuthToken:
        """Browser-based OAuth flow."""
        # 1. Start local callback server
        # 2. Open browser to auth URL with PKCE
        # 3. Wait for callback with auth code
        # 4. Exchange code for tokens
        # 5. Store in keychain
```

**Subscription Tiers**:
| Tier | Models | Rate Limits |
|------|--------|-------------|
| **Free** | Sonnet 3.5 | 50K tokens/month |
| **Pro** | Opus 4.5, Sonnet 4.5 | 5M tokens/month |
| **Max** | All models, priority | 20M tokens/month |

---

### 2. Gemini (Google)

**Method**: Google OAuth 2.0 with Vertex AI integration

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   Inception │────▶│ Local Server │────▶│ accounts.google.com │
│   (CLI/TUI) │     │  (callback)  │     │    (OAuth consent)  │
└─────────────┘     └──────────────┘     └─────────────────────┘
                           │                        │
                           │◀───────────────────────┘
                           │   (authorization code)
                           ▼
                    ┌──────────────┐     ┌───────────────┐
                    │    Keychain  │────▶│  Vertex AI    │
                    │ (tokens)     │     │   (API)       │
                    └──────────────┘     └───────────────┘
```

**Implementation**:
```python
# inception/enhance/auth/gemini.py
@dataclass
class GeminiOAuthConfig:
    client_id: str = "inception-cli.apps.googleusercontent.com"
    auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"
    scopes: list[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/generative-language",
        "https://www.googleapis.com/auth/cloud-platform",
    ])

class GeminiOAuthProvider:
    def authenticate(self) -> OAuthToken:
        """Google OAuth for Gemini access."""
```

**Subscription Tiers**:
| Tier | Models | Features |
|------|--------|----------|
| **Free** | Flash 2.0 | 15 req/min |
| **Pro** | Pro 3, Flash 3 | 60 req/min |
| **Ultra** | Ultra 3, Nano 2 | Priority, 2M context |

---

### 3. OpenAI

**Method**: Session token extraction from ChatGPT

> ⚠️ OpenAI doesn't offer official OAuth for third-party apps.
> We use session token approach similar to ChatGPT wrappers.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Inception │────▶│ Browser Automation│────▶│   chat.openai.com│
│   (CLI/TUI) │     │  (Playwright)     │     │   (login page)   │
└─────────────┘     └──────────────────────┘     └─────────────────┘
                            │                          │
                            │◀─────────────────────────┘
                            │   (session cookies)
                            ▼
                     ┌──────────────┐
                     │   Keychain   │
                     │ (session)    │
                     └──────────────┘
```

**Implementation**:
```python
# inception/enhance/auth/openai.py
@dataclass
class OpenAIOAuthConfig:
    login_url: str = "https://chat.openai.com/"
    api_base: str = "https://chat.openai.com/backend-api"
    session_refresh_interval: int = 3600  # 1 hour

class OpenAIOAuthProvider:
    def authenticate(self) -> SessionToken:
        """Extract session from browser login."""
```

**Subscription Tiers**:
| Tier | Models | Features |
|------|--------|----------|
| **Plus** | GPT-4o | 80 msg/3hr |
| **Pro** | GPT-4o, o1 | Unlimited |

---

## Unified OAuth Manager

```python
# inception/enhance/auth/manager.py
class OAuthManager:
    """Unified authentication across all providers."""
    
    def __init__(self, config: OAuthConfig):
        self.providers = {
            "claude": ClaudeOAuthProvider(config.claude),
            "gemini": GeminiOAuthProvider(config.gemini),
            "openai": OpenAIOAuthProvider(config.openai),
        }
        self.fallback_order = ["claude", "gemini", "openai"]
    
    async def ensure_authenticated(self, provider: str = "auto") -> OAuthToken:
        """Ensure we have valid auth for a provider."""
        if provider == "auto":
            for p in self.fallback_order:
                if await self.providers[p].is_ready():
                    return await self.providers[p].get_token()
        
        return await self.providers[provider].authenticate()
    
    async def get_available_models(self) -> list[ModelInfo]:
        """List models available through authenticated providers."""
```

---

## Token Storage

### Keychain Integration (Secure)

```python
# inception/enhance/auth/storage.py
class TokenStorage:
    """Secure token storage using OS keychain."""
    
    SERVICE_NAME = "com.inception.auth"
    
    def store(self, provider: str, token: OAuthToken) -> None:
        keyring.set_password(
            self.SERVICE_NAME,
            f"{provider}_access_token",
            token.access_token
        )
        keyring.set_password(
            self.SERVICE_NAME,
            f"{provider}_refresh_token",
            token.refresh_token
        )
    
    def retrieve(self, provider: str) -> OAuthToken | None:
        access = keyring.get_password(self.SERVICE_NAME, f"{provider}_access_token")
        refresh = keyring.get_password(self.SERVICE_NAME, f"{provider}_refresh_token")
        return OAuthToken(access, refresh) if access else None
```

---

## CLI Integration

```bash
# Initial setup - opens browser for each provider
inception auth setup

# Setup specific provider
inception auth setup claude
inception auth setup gemini

# Check authentication status
inception auth status

# Logout/clear tokens
inception auth logout claude

# Run with auto-provider selection
inception enhance extract video.mp4  # Uses best available provider
```

---

## Error Handling

### Token Expiration
```python
async def ensure_valid_token(self, provider: str) -> OAuthToken:
    token = self.storage.retrieve(provider)
    
    if token and token.is_expired:
        try:
            token = await self.providers[provider].refresh(token)
            self.storage.store(provider, token)
        except RefreshExpired:
            # Refresh token expired, need full re-auth
            token = await self.providers[provider].authenticate()
            self.storage.store(provider, token)
    
    return token
```

### Rate Limit Fallback
```python
async def complete_with_fallback(self, prompt: str) -> LLMResponse:
    for provider in self.fallback_order:
        try:
            return await self.complete(provider, prompt)
        except RateLimitError:
            logger.warning(f"{provider} rate limited, trying next...")
            continue
    raise AllProvidersExhausted()
```

---

## Security Considerations

1. **No secrets in code** - All tokens in OS keychain
2. **PKCE for OAuth** - Prevents authorization code interception
3. **Short-lived tokens** - Auto-refresh mechanism
4. **Scope minimization** - Request only needed permissions
5. **No token logging** - Redact in logs
6. **Encrypted storage** - OS keychain handles encryption
