"""
Vector store abstraction and implementations.

Design by OPUS-3: Abstract interface for ChromaDB with future Qdrant support.
Metadata schema by OPUS-1.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Result from a vector similarity search."""
    
    nid: int
    score: float  # Similarity score (0-1, higher is better)
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def node_kind(self) -> str | None:
        """Get node kind from metadata."""
        return self.metadata.get("node_kind")
    
    @property
    def source_nids(self) -> list[int]:
        """Get source NIDs from metadata."""
        return self.metadata.get("source_nids", [])
    
    @property
    def confidence(self) -> float:
        """Get confidence from metadata."""
        return self.metadata.get("confidence", 1.0)


class VectorStore(ABC):
    """Abstract vector store interface."""
    
    @abstractmethod
    def add(
        self,
        nids: Sequence[int],
        embeddings: Sequence[list[float]],
        texts: Sequence[str],
        metadatas: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        """Add vectors to the store."""
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    def delete(self, nids: Sequence[int]) -> None:
        """Delete vectors by NID."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total number of vectors."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all vectors."""
        pass


class ChromaVectorStore(VectorStore):
    """
    ChromaDB-based vector store.
    
    Uses persistent storage for durability.
    """
    
    def __init__(
        self,
        path: Path | str,
        collection_name: str = "inception_nodes",
        embedding_dimension: int = 384,
    ):
        """
        Initialize ChromaDB store.
        
        Args:
            path: Path to store data
            collection_name: Name of the collection
            embedding_dimension: Expected embedding dimension
        """
        self.path = Path(path)
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        
        self._client = None
        self._collection = None
    
    @property
    def client(self):
        """Lazy-load ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                self.path.mkdir(parents=True, exist_ok=True)
                
                self._client = chromadb.PersistentClient(
                    path=str(self.path),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                    ),
                )
                logger.info(f"Initialized ChromaDB at: {self.path}")
            except ImportError:
                raise ImportError(
                    "chromadb not installed. Run: uv add chromadb"
                )
        return self._client
    
    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"dimension": self.embedding_dimension},
            )
        return self._collection
    
    def add(
        self,
        nids: Sequence[int],
        embeddings: Sequence[list[float]],
        texts: Sequence[str],
        metadatas: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        """Add vectors to ChromaDB."""
        if not nids:
            return
        
        # ChromaDB requires string IDs
        ids = [str(nid) for nid in nids]
        
        # Default metadata if not provided
        if metadatas is None:
            metadatas = [{}] * len(nids)
        
        # Ensure metadata is serializable (convert lists to strings)
        processed_metadatas = []
        for meta in metadatas:
            processed = {}
            for k, v in meta.items():
                if isinstance(v, list):
                    processed[k] = ",".join(str(x) for x in v)
                else:
                    processed[k] = v
            processed_metadatas.append(processed)
        
        self.collection.upsert(
            ids=ids,
            embeddings=list(embeddings),
            documents=list(texts),
            metadatas=processed_metadatas,
        )
        
        logger.debug(f"Added {len(nids)} vectors to ChromaDB")
    
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors in ChromaDB."""
        # Build where clause for filtering
        where = None
        if filter_metadata:
            where = {}
            for k, v in filter_metadata.items():
                where[k] = {"$eq": v}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        # Convert to VectorSearchResult
        search_results = []
        
        if results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            documents = results["documents"][0] if results["documents"] else [""] * len(ids)
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
            distances = results["distances"][0] if results["distances"] else [0.0] * len(ids)
            
            for i, nid_str in enumerate(ids):
                # Convert distance to similarity (ChromaDB uses L2 by default)
                # Lower distance = higher similarity
                # Use 1 / (1 + distance) to normalize
                distance = distances[i] if i < len(distances) else 0.0
                similarity = 1.0 / (1.0 + distance)
                
                # Parse metadata (convert comma-separated back to lists)
                meta = metadatas[i] if i < len(metadatas) else {}
                if "source_nids" in meta and isinstance(meta["source_nids"], str):
                    meta["source_nids"] = [int(x) for x in meta["source_nids"].split(",") if x]
                
                search_results.append(VectorSearchResult(
                    nid=int(nid_str),
                    score=similarity,
                    text=documents[i] if i < len(documents) else "",
                    metadata=meta,
                ))
        
        return search_results
    
    def delete(self, nids: Sequence[int]) -> None:
        """Delete vectors by NID."""
        if not nids:
            return
        
        ids = [str(nid) for nid in nids]
        self.collection.delete(ids=ids)
        logger.debug(f"Deleted {len(nids)} vectors from ChromaDB")
    
    def count(self) -> int:
        """Get total number of vectors."""
        return self.collection.count()
    
    def clear(self) -> None:
        """Clear all vectors."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self._collection = None
        logger.info(f"Cleared ChromaDB collection: {self.collection_name}")


class InMemoryVectorStore(VectorStore):
    """
    In-memory vector store for testing.
    
    Uses numpy for similarity calculations.
    """
    
    def __init__(self):
        """Initialize in-memory store."""
        self._vectors: dict[int, dict[str, Any]] = {}
    
    def add(
        self,
        nids: Sequence[int],
        embeddings: Sequence[list[float]],
        texts: Sequence[str],
        metadatas: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        """Add vectors to memory."""
        import numpy as np
        
        if metadatas is None:
            metadatas = [{}] * len(nids)
        
        for nid, emb, text, meta in zip(nids, embeddings, texts, metadatas):
            self._vectors[nid] = {
                "embedding": np.array(emb),
                "text": text,
                "metadata": meta,
            }
    
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search in memory using cosine similarity."""
        import numpy as np
        
        query = np.array(query_embedding)
        query_norm = np.linalg.norm(query)
        
        if query_norm == 0:
            return []
        
        scores = []
        for nid, data in self._vectors.items():
            # Apply metadata filter
            if filter_metadata:
                match = all(
                    data["metadata"].get(k) == v
                    for k, v in filter_metadata.items()
                )
                if not match:
                    continue
            
            # Calculate cosine similarity
            emb = data["embedding"]
            emb_norm = np.linalg.norm(emb)
            
            if emb_norm == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(query, emb) / (query_norm * emb_norm))
                similarity = (similarity + 1) / 2  # Normalize to 0-1
            
            scores.append((nid, similarity, data))
        
        # Sort by similarity (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        results = []
        for nid, score, data in scores[:top_k]:
            results.append(VectorSearchResult(
                nid=nid,
                score=score,
                text=data["text"],
                metadata=data["metadata"],
            ))
        
        return results
    
    def delete(self, nids: Sequence[int]) -> None:
        """Delete vectors from memory."""
        for nid in nids:
            self._vectors.pop(nid, None)
    
    def count(self) -> int:
        """Get total number of vectors."""
        return len(self._vectors)
    
    def clear(self) -> None:
        """Clear all vectors."""
        self._vectors.clear()
