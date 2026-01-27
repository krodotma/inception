"""
Vision Language Model providers.

Supports:
- LLaVA via Ollama (local, offline-capable)
- GPT-4V via OpenAI (high quality)
- Claude Vision via Anthropic (alternative)
"""

from __future__ import annotations

import base64
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class VLMResponse:
    """Response from a VLM provider."""
    
    description: str
    model: str
    provider: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    raw_response: dict[str, Any] = field(default_factory=dict)


class VLMProvider(ABC):
    """Abstract base class for VLM providers."""
    
    name: str
    
    @abstractmethod
    def analyze_image(
        self,
        image_path: Path | str,
        prompt: str = "Describe this image in detail.",
        max_tokens: int = 1024,
    ) -> VLMResponse:
        """Analyze an image."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass
    
    def _load_image_base64(self, image_path: Path | str) -> str:
        """Load an image as base64."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_mime_type(self, image_path: Path | str) -> str:
        """Get MIME type for an image."""
        suffix = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_types.get(suffix, "image/png")


class LLaVAProvider(VLMProvider):
    """LLaVA provider via Ollama."""
    
    name = "llava"
    
    def __init__(
        self,
        model: str = "llava:7b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url
        self._client = httpx.Client(timeout=180.0)  # Vision can be slow
    
    def is_available(self) -> bool:
        """Check if LLaVA is available via Ollama."""
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Check for llava or similar vision models
            return any("llava" in name.lower() for name in model_names)
        except Exception:
            return False
    
    def analyze_image(
        self,
        image_path: Path | str,
        prompt: str = "Describe this image in detail.",
        max_tokens: int = 1024,
    ) -> VLMResponse:
        """Analyze image using LLaVA."""
        image_b64 = self._load_image_base64(image_path)
        
        response = self._client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        
        return VLMResponse(
            description=data.get("response", ""),
            model=self.model,
            provider=self.name,
            tokens_used=data.get("eval_count", 0),
            cost_usd=0.0,  # Local is free
            raw_response=data,
        )


class OpenAIVisionProvider(VLMProvider):
    """OpenAI GPT-4V provider."""
    
    name = "openai"
    
    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = httpx.Client(timeout=120.0)
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def analyze_image(
        self,
        image_path: Path | str,
        prompt: str = "Describe this image in detail.",
        max_tokens: int = 1024,
    ) -> VLMResponse:
        """Analyze image using GPT-4V."""
        image_b64 = self._load_image_base64(image_path)
        mime_type = self._get_mime_type(image_path)
        
        response = self._client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_b64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        # Calculate cost (GPT-4o pricing)
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost = (input_tokens * 2.5 + output_tokens * 10.0) / 1_000_000
        
        return VLMResponse(
            description=data["choices"][0]["message"]["content"],
            model=self.model,
            provider=self.name,
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            raw_response=data,
        )


class AnthropicVisionProvider(VLMProvider):
    """Anthropic Claude Vision provider."""
    
    name = "anthropic"
    
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = httpx.Client(timeout=120.0)
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def analyze_image(
        self,
        image_path: Path | str,
        prompt: str = "Describe this image in detail.",
        max_tokens: int = 1024,
    ) -> VLMResponse:
        """Analyze image using Claude Vision."""
        image_b64 = self._load_image_base64(image_path)
        mime_type = self._get_mime_type(image_path)
        
        response = self._client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        
        # Calculate cost (Claude pricing)
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cost = (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000
        
        return VLMResponse(
            description=data["content"][0]["text"],
            model=self.model,
            provider=self.name,
            tokens_used=input_tokens + output_tokens,
            cost_usd=cost,
            raw_response=data,
        )


def get_vlm_provider(
    name: str = "auto",
    offline: bool = False,
    model: str | None = None,
) -> VLMProvider:
    """
    Get a VLM provider by name with automatic fallback.
    
    Args:
        name: Provider name ("llava", "openai", "anthropic", "auto")
        offline: If True, only use local providers
        model: Optional model override
    
    Returns:
        An available VLMProvider
    
    Raises:
        RuntimeError: If no provider is available
    """
    if name == "llava" or (name == "auto" and offline):
        provider = LLaVAProvider(model=model or "llava:7b")
        if provider.is_available():
            return provider
        if name == "llava":
            raise RuntimeError(
                "LLaVA not available. Run: ollama pull llava:7b"
            )
    
    if offline:
        raise RuntimeError(
            "No offline VLM provider available. Install LLaVA."
        )
    
    if name == "openai":
        provider = OpenAIVisionProvider(model=model)
        if provider.is_available():
            return provider
        raise RuntimeError("OpenAI API key not configured.")
    
    if name == "anthropic":
        provider = AnthropicVisionProvider(model=model)
        if provider.is_available():
            return provider
        raise RuntimeError("Anthropic API key not configured.")
    
    # Auto mode: try in order
    if name == "auto":
        # Try LLaVA first (free, private)
        llava = LLaVAProvider()
        if llava.is_available():
            return llava
        
        # Try OpenAI
        openai = OpenAIVisionProvider()
        if openai.is_available():
            return openai
        
        # Try Anthropic
        anthropic = AnthropicVisionProvider()
        if anthropic.is_available():
            return anthropic
        
        raise RuntimeError(
            "No VLM provider available. Options:\n"
            "1. Install LLaVA: ollama pull llava:7b\n"
            "2. Set OPENAI_API_KEY environment variable\n"
            "3. Set ANTHROPIC_API_KEY environment variable"
        )
    
    raise ValueError(f"Unknown VLM provider: {name}")
