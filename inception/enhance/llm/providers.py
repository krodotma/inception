"""
LLM providers for extraction enhancement.

Supports:
- Ollama (local, offline-capable)
- OpenRouter (cost-effective, diverse models)
- Cloud (Claude/GPT-4 direct API)
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    raw_response: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    name: str
    
    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate a completion."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass
    
    def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Generate a completion and parse as JSON."""
        response = self.complete(prompt, system, temperature, max_tokens)
        
        # Extract JSON from response (handle markdown code blocks)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        return json.loads(content.strip())


class OllamaProvider(LLMProvider):
    """Local Ollama provider for offline extraction."""
    
    name = "ollama"
    
    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url
        self._client = httpx.Client(timeout=120.0)
    
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            return self.model.split(":")[0] in model_names
        except Exception:
            return False
    
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate completion using Ollama."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=self.model,
            provider=self.name,
            tokens_used=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
            cost_usd=0.0,  # Local is free
            raw_response=data,
        )


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider for cost-effective cloud access."""
    
    name = "openrouter"
    
    # Pricing per 1M tokens (approximate)
    PRICING = {
        "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        "anthropic/claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "openai/gpt-4o": {"input": 2.5, "output": 10.0},
        "meta-llama/llama-3.1-70b-instruct": {"input": 0.52, "output": 0.75},
    }
    
    def __init__(
        self,
        model: str = "anthropic/claude-3-haiku",
        api_key: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self._client = httpx.Client(
            base_url="https://openrouter.ai/api/v1",
            timeout=120.0,
        )
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate completion using OpenRouter."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.post(
            "/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/inception",
                "X-Title": "Inception",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        # Calculate cost
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        pricing = self.PRICING.get(self.model, {"input": 1.0, "output": 2.0})
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.model,
            provider=self.name,
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            raw_response=data,
        )


class CloudProvider(LLMProvider):
    """Direct cloud provider (Claude or OpenAI)."""
    
    name = "cloud"
    
    def __init__(
        self,
        provider: Literal["anthropic", "openai"] = "anthropic",
        model: str | None = None,
        api_key: str | None = None,
    ):
        self.provider_type = provider
        
        if provider == "anthropic":
            self.model = model or "claude-3-5-sonnet-20241022"
            self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            self._base_url = "https://api.anthropic.com/v1"
        else:
            self.model = model or "gpt-4o"
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            self._base_url = "https://api.openai.com/v1"
        
        self._client = httpx.Client(timeout=120.0)
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate completion using direct API."""
        if self.provider_type == "anthropic":
            return self._complete_anthropic(prompt, system, temperature, max_tokens)
        else:
            return self._complete_openai(prompt, system, temperature, max_tokens)
    
    def _complete_anthropic(
        self,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Complete using Anthropic API."""
        response = self._client.post(
            f"{self._base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
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
        data = response.json()
        
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        # Claude pricing (Sonnet)
        cost = (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000
        
        return LLMResponse(
            content=data["content"][0]["text"],
            model=self.model,
            provider=f"cloud/{self.provider_type}",
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            raw_response=data,
        )
    
    def _complete_openai(
        self,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Complete using OpenAI API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # GPT-4o pricing
        cost = (input_tokens * 2.5 + output_tokens * 10.0) / 1_000_000
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.model,
            provider=f"cloud/{self.provider_type}",
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            raw_response=data,
        )


def get_provider(
    name: str = "auto",
    offline: bool = False,
    model: str | None = None,
) -> LLMProvider:
    """
    Get an LLM provider by name with automatic fallback.
    
    Priority Order (per OAuth-first strategy):
    1. OAuth providers (ClawdBot/MoltBot) - subscription-based, no API keys
    2. Ollama (local, free)
    3. OpenRouter (API key fallback)
    4. Direct Cloud (API key fallback)
    
    Args:
        name: Provider name ("ollama", "openrouter", "cloud", "clawdbot", "moltbot", "auto")
        offline: If True, only use local providers
        model: Optional model override
    
    Returns:
        An available LLMProvider
    
    Raises:
        RuntimeError: If no provider is available
    """
    # Import OAuth providers (lazy to avoid circular imports)
    try:
        from inception.auth.oauth_providers import (
            ClawdBotProvider, MoltBotProvider, get_oauth_provider
        )
        oauth_available = True
    except ImportError:
        oauth_available = False
    
    # Explicit OAuth provider requests
    if name == "clawdbot" and oauth_available:
        return get_oauth_provider("clawdbot", model=model)
    
    if name == "moltbot" and oauth_available:
        return get_oauth_provider("moltbot", model=model)
    
    # Offline mode - Ollama only
    if name == "ollama" or (name == "auto" and offline):
        provider = OllamaProvider(model=model or "llama3.2")
        if provider.is_available():
            return provider
        if name == "ollama":
            raise RuntimeError("Ollama not available. Run: ollama pull llama3.2")
    
    if offline:
        raise RuntimeError("No offline provider available. Install Ollama.")
    
    if name == "openrouter":
        provider = OpenRouterProvider(model=model or "anthropic/claude-3-haiku")
        if provider.is_available():
            return provider
        raise RuntimeError("OpenRouter API key not configured.")
    
    if name == "cloud":
        provider = CloudProvider(model=model)
        if provider.is_available():
            return provider
        raise RuntimeError("Cloud API key not configured.")
    
    # Auto mode: OAuth-first priority order
    if name == "auto":
        # Priority 1: OAuth providers (ClawdBot/MoltBot)
        if oauth_available:
            try:
                return get_oauth_provider("auto", model=model)
            except RuntimeError:
                pass  # Fall through to other providers
        
        # Priority 2: Ollama (free, local, private)
        ollama = OllamaProvider()
        if ollama.is_available():
            return ollama
        
        # Priority 3: OpenRouter (cost-effective fallback)
        openrouter = OpenRouterProvider()
        if openrouter.is_available():
            return openrouter
        
        # Priority 4: Direct cloud APIs
        cloud = CloudProvider()
        if cloud.is_available():
            return cloud
        
        raise RuntimeError(
            "No LLM provider available. Options:\n"
            "1. Authenticate with ClawdBot: OAuth flow for Claude Max\n"
            "2. Authenticate with MoltBot: OAuth flow for Gemini Ultra\n"
            "3. Install Ollama: brew install ollama && ollama pull llama3.2\n"
            "4. Set OPENROUTER_API_KEY environment variable\n"
            "5. Set ANTHROPIC_API_KEY or OPENAI_API_KEY"
        )
    
    raise ValueError(f"Unknown provider: {name}")

