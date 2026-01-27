"""
OAuth Authentication Module for Inception.

Provides API-key-free authentication using browser-based OAuth flows
tied to subscription plans (Pro, Max, Ultra) for Claude, Gemini, and OpenAI.
"""

from inception.enhance.auth.base import (
    OAuthConfig,
    OAuthToken,
    OAuthProvider,
    AuthError,
    TokenExpiredError,
    RefreshFailedError,
)
from inception.enhance.auth.storage import TokenStorage
from inception.enhance.auth.manager import OAuthManager
from inception.enhance.auth.claude import ClaudeOAuthProvider, ClaudeOAuthConfig
from inception.enhance.auth.gemini import GeminiOAuthProvider, GeminiOAuthConfig
from inception.enhance.auth.openai import OpenAIOAuthProvider, OpenAIOAuthConfig

__all__ = [
    # Base
    "OAuthConfig",
    "OAuthToken",
    "OAuthProvider",
    "AuthError",
    "TokenExpiredError",
    "RefreshFailedError",
    # Storage
    "TokenStorage",
    # Manager
    "OAuthManager",
    # Providers
    "ClaudeOAuthProvider",
    "ClaudeOAuthConfig",
    "GeminiOAuthProvider",
    "GeminiOAuthConfig",
    "OpenAIOAuthProvider",
    "OpenAIOAuthConfig",
]
