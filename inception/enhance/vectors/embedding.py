"""
Embedding model wrapper for sentence-transformers.

Design by OPUS-2: Use all-MiniLM-L6-v2 as default (fast, 384 dims),
with option for all-mpnet-base-v2 for higher quality.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Sequence

import numpy as np

logger = logging.getLogger(__name__)

# Model configurations
MODELS = {
    "default": "all-MiniLM-L6-v2",
    "fast": "all-MiniLM-L6-v2",
    "quality": "all-mpnet-base-v2",
    "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",
}


class EmbeddingModel:
    """
    Wrapper for sentence-transformers embedding models.
    
    Supports batch encoding with caching for efficiency.
    """
    
    def __init__(
        self,
        model_name: str = "default",
        device: str | None = None,
        cache_size: int = 1000,
    ):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Model name or alias ("default", "fast", "quality")
            device: Device to use ("cpu", "cuda", "mps", None for auto)
            cache_size: LRU cache size for embeddings
        """
        # Resolve alias
        self.model_name = MODELS.get(model_name, model_name)
        self.device = device
        self._model = None
        self._dimension: int | None = None
        
        # Create cached encode function
        self._encode_cached = lru_cache(maxsize=cache_size)(self._encode_single)
    
    @property
    def model(self):
        """Lazy-load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                
                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                )
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: uv add sentence-transformers"
                )
        return self._model
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            # Get dimension from a test embedding
            test_embedding = self.encode_single("test")
            self._dimension = len(test_embedding)
        return self._dimension
    
    def _encode_single(self, text: str) -> tuple[float, ...]:
        """Encode a single text (for caching)."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return tuple(embedding.tolist())
    
    def encode_single(self, text: str) -> list[float]:
        """
        Encode a single text to embedding.
        
        Uses LRU cache for repeated texts.
        """
        return list(self._encode_cached(text))
    
    def encode_batch(
        self,
        texts: Sequence[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """
        Encode multiple texts efficiently.
        
        Args:
            texts: Sequence of texts to encode
            batch_size: Batch size for encoding
            show_progress: Show progress bar
        
        Returns:
            List of embeddings (list of floats each)
        """
        if not texts:
            return []
        
        embeddings = self.model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
        
        return [emb.tolist() for emb in embeddings]
    
    def similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        a = np.array(embedding1)
        b = np.array(embedding2)
        
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        
        if norm == 0:
            return 0.0
        
        return float((dot / norm + 1) / 2)  # Normalize to 0-1


@lru_cache(maxsize=4)
def get_embedding_model(
    model_name: str = "default",
    device: str | None = None,
) -> EmbeddingModel:
    """
    Get or create an embedding model (cached).
    
    Args:
        model_name: Model name or alias
        device: Device to use
    
    Returns:
        EmbeddingModel instance
    """
    return EmbeddingModel(model_name=model_name, device=device)
