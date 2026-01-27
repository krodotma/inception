"""
LLM-enhanced extraction module.

Provides hybrid spaCy + LLM extraction for improved claim, entity,
and procedure detection with multi-provider support.
"""

from inception.enhance.llm.providers import (
    LLMProvider,
    OllamaProvider,
    OpenRouterProvider,
    CloudProvider,
    get_provider,
)
from inception.enhance.llm.extractor import (
    LLMExtractor,
    LLMExtractionResult,
)
from inception.enhance.llm.prompts import (
    CLAIM_EXTRACTION_PROMPT,
    ENTITY_EXTRACTION_PROMPT,
    PROCEDURE_EXTRACTION_PROMPT,
)

__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "OpenRouterProvider",
    "CloudProvider",
    "get_provider",
    "LLMExtractor",
    "LLMExtractionResult",
    "CLAIM_EXTRACTION_PROMPT",
    "ENTITY_EXTRACTION_PROMPT",
    "PROCEDURE_EXTRACTION_PROMPT",
]
