"""
Vision Language Model enhancement module.

Provides visual understanding capabilities for diagrams,
charts, code screenshots, and other visual content.

Team Design:
- OPUS-2: LLaVA + GPT-4V providers
- OPUS-1: Structured visual entity extraction
- GEMINI-PRO: Keyframe → VLM → LLM pipeline
- SONNET: CLI integration
"""

from inception.enhance.vision.providers import (
    VLMProvider,
    LLaVAProvider,
    OpenAIVisionProvider,
    get_vlm_provider,
)
from inception.enhance.vision.analyzer import (
    VisionAnalyzer,
    ImageAnalysis,
)

__all__ = [
    "VLMProvider",
    "LLaVAProvider",
    "OpenAIVisionProvider",
    "get_vlm_provider",
    "VisionAnalyzer",
    "ImageAnalysis",
]
