"""
Inception enhancement modules.

Provides advanced capabilities beyond the core extraction pipeline:
- LLM-enhanced extraction
- Vector embeddings and semantic search
- Visual language model integration
"""

from inception.enhance.llm import (
    LLMProvider,
    LLMExtractor,
    LLMExtractionResult,
    get_provider,
)
from inception.enhance.vectors import (
    VectorIndex,
    HybridSearcher,
    VectorSearchResult,
    get_embedding_model,
)

__all__ = [
    # LLM
    "LLMProvider",
    "LLMExtractor",
    "LLMExtractionResult",
    "get_provider",
    # Vectors
    "VectorIndex",
    "HybridSearcher",
    "VectorSearchResult",
    "get_embedding_model",
]
