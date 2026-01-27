"""
Vector embedding and semantic search module.

Provides semantic similarity search over the knowledge graph using
sentence-transformers for embeddings and ChromaDB for storage.

Team Design:
- OPUS-2: sentence-transformers + ChromaDB
- OPUS-1: Rich metadata schema
- OPUS-3: Batch operations + abstract interface
- GEMINI-PRO: Hybrid LMDB + vector search
- SONNET: CLI integration
"""

from inception.enhance.vectors.embedding import (
    EmbeddingModel,
    get_embedding_model,
)
from inception.enhance.vectors.store import (
    VectorStore,
    ChromaVectorStore,
    VectorSearchResult,
)
from inception.enhance.vectors.index import (
    VectorIndex,
    HybridSearcher,
)

__all__ = [
    "EmbeddingModel",
    "get_embedding_model",
    "VectorStore",
    "ChromaVectorStore",
    "VectorSearchResult",
    "VectorIndex",
    "HybridSearcher",
]
