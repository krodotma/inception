"""
Vision analyzer for extracting structured information from images.

Integrates with keyframe extraction to analyze visual content
and enrich the knowledge graph with visual entities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from inception.enhance.vision.providers import VLMProvider, get_vlm_provider

logger = logging.getLogger(__name__)


# Specialized prompts for different visual content types
PROMPTS = {
    "default": """Analyze this image and describe:
1. What type of content is this (diagram, code, chart, photo, etc.)?
2. What are the main elements visible?
3. What relationships or flows are shown?
4. Any text visible in the image?

Be detailed and structured in your response.""",

    "diagram": """This appears to be a diagram or flowchart. Analyze it:
1. What type of diagram is this (flowchart, architecture, UML, etc.)?
2. List all entities/boxes/nodes visible
3. Describe the connections and relationships between them
4. What is the overall flow or structure?
5. Any labels or annotations?

Output as structured list.""",

    "code": """This image contains code or a code screenshot. Analyze it:
1. What programming language is this?
2. What functions, classes, or methods are visible?
3. What does this code appear to do?
4. Any visible imports or dependencies?
5. Any comments or documentation visible?

Extract the code if possible, or describe its structure.""",

    "chart": """This appears to be a chart or graph. Analyze it:
1. What type of chart is this (bar, line, pie, scatter, etc.)?
2. What are the axes/labels?
3. What data is being represented?
4. What are the key data points or trends?
5. Any notable observations?

Try to extract approximate values if visible.""",

    "ui": """This appears to be a user interface screenshot. Analyze it:
1. What application or website is this?
2. What UI components are visible (buttons, forms, menus, etc.)?
3. What is the layout structure?
4. What actions appear to be available?
5. Any text content visible?

Describe the UI structure and purpose.""",
}


@dataclass
class ImageAnalysis:
    """Result of analyzing an image."""
    
    image_path: str
    content_type: str  # diagram, code, chart, ui, photo, unknown
    description: str
    entities: list[str] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    extracted_text: list[str] = field(default_factory=list)
    
    # VLM metadata
    provider: str = ""
    model: str = ""
    tokens_used: int = 0
    cost_usd: float = 0.0


class VisionAnalyzer:
    """
    Analyzes images using Vision Language Models.
    
    Supports automatic content type detection and specialized
    prompts for different visual content.
    """
    
    def __init__(
        self,
        provider: VLMProvider | None = None,
        provider_name: str = "auto",
        offline: bool = False,
    ):
        """
        Initialize the vision analyzer.
        
        Args:
            provider: Pre-configured VLM provider
            provider_name: Provider name for auto-selection
            offline: Use only offline-capable providers
        """
        self.provider = provider or get_vlm_provider(
            name=provider_name,
            offline=offline,
        )
        self._total_tokens = 0
        self._total_cost = 0.0
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used across all analyses."""
        return self._total_tokens
    
    @property
    def total_cost(self) -> float:
        """Total cost in USD across all analyses."""
        return self._total_cost
    
    def analyze(
        self,
        image_path: Path | str,
        content_type: str | None = None,
        custom_prompt: str | None = None,
    ) -> ImageAnalysis:
        """
        Analyze an image.
        
        Args:
            image_path: Path to the image file
            content_type: Optional hint about content type
            custom_prompt: Optional custom prompt
        
        Returns:
            ImageAnalysis with extracted information
        """
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        # Determine prompt
        if custom_prompt:
            prompt = custom_prompt
        elif content_type and content_type in PROMPTS:
            prompt = PROMPTS[content_type]
        else:
            prompt = PROMPTS["default"]
        
        # Analyze with VLM
        try:
            response = self.provider.analyze_image(path, prompt)
            
            self._total_tokens += response.tokens_used
            self._total_cost += response.cost_usd
            
            # Parse response
            description = response.description
            detected_type = self._detect_content_type(description)
            entities = self._extract_entities(description)
            text = self._extract_text(description)
            
            return ImageAnalysis(
                image_path=str(path),
                content_type=content_type or detected_type,
                description=description,
                entities=entities,
                extracted_text=text,
                provider=response.provider,
                model=response.model,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
            )
            
        except Exception as e:
            logger.error(f"Vision analysis failed for {path}: {e}")
            return ImageAnalysis(
                image_path=str(path),
                content_type="error",
                description=f"Analysis failed: {e}",
            )
    
    def analyze_keyframes(
        self,
        keyframe_paths: list[Path | str],
        show_progress: bool = False,
    ) -> list[ImageAnalysis]:
        """
        Analyze multiple keyframes.
        
        Args:
            keyframe_paths: List of keyframe image paths
            show_progress: Show progress indicator
        
        Returns:
            List of ImageAnalysis results
        """
        results = []
        
        for i, path in enumerate(keyframe_paths):
            if show_progress:
                logger.info(f"Analyzing keyframe {i+1}/{len(keyframe_paths)}")
            
            result = self.analyze(path)
            results.append(result)
        
        return results
    
    def _detect_content_type(self, description: str) -> str:
        """Detect content type from description."""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["diagram", "flowchart", "architecture", "uml"]):
            return "diagram"
        elif any(word in description_lower for word in ["code", "programming", "function", "class", "python", "javascript"]):
            return "code"
        elif any(word in description_lower for word in ["chart", "graph", "bar", "line", "pie", "data"]):
            return "chart"
        elif any(word in description_lower for word in ["interface", "ui", "button", "menu", "screen"]):
            return "ui"
        elif any(word in description_lower for word in ["photo", "photograph", "person", "scene"]):
            return "photo"
        else:
            return "unknown"
    
    def _extract_entities(self, description: str) -> list[str]:
        """Extract entity mentions from description."""
        # Simple extraction - look for capitalized terms
        # In production, would use NLP or LLM
        entities = []
        words = description.split()
        
        for i, word in enumerate(words):
            # Skip first word of sentences
            if i > 0 and words[i-1][-1] not in ".!?":
                if word and word[0].isupper() and len(word) > 2:
                    # Clean punctuation
                    clean = word.strip(".,!?;:")
                    if clean and clean not in entities:
                        entities.append(clean)
        
        return entities[:20]  # Limit to 20 entities
    
    def _extract_text(self, description: str) -> list[str]:
        """Extract quoted text from description."""
        text = []
        in_quote = False
        current = []
        
        for char in description:
            if char in "\"'":
                if in_quote:
                    text.append("".join(current))
                    current = []
                in_quote = not in_quote
            elif in_quote:
                current.append(char)
        
        return text
