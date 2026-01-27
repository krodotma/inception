"""
Vector index and hybrid search implementation.

Design:
- OPUS-3: VectorIndex coordinates LMDB sync and batch operations
- GEMINI-PRO: HybridSearcher combines vector + LMDB filtering
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

from inception.enhance.vectors.embedding import EmbeddingModel, get_embedding_model
from inception.enhance.vectors.store import (
    VectorStore,
    ChromaVectorStore,
    InMemoryVectorStore,
    VectorSearchResult,
)

logger = logging.getLogger(__name__)


@dataclass
class IndexStats:
    """Statistics about the vector index."""
    
    total_vectors: int
    embedding_model: str
    embedding_dimension: int
    store_type: str


class VectorIndex:
    """
    Main coordinator for vector indexing.
    
    Handles synchronization with LMDB, batch operations,
    and index management.
    """
    
    def __init__(
        self,
        store: VectorStore | None = None,
        embedding_model: EmbeddingModel | None = None,
        path: Path | str | None = None,
        model_name: str = "default",
    ):
        """
        Initialize the vector index.
        
        Args:
            store: Vector store to use (creates ChromaDB if None)
            embedding_model: Embedding model (creates default if None)
            path: Path for ChromaDB storage
            model_name: Embedding model name if creating default
        """
        self.embedding_model = embedding_model or get_embedding_model(model_name)
        
        if store is not None:
            self.store = store
        elif path is not None:
            self.store = ChromaVectorStore(
                path=path,
                embedding_dimension=self.embedding_model.dimension,
            )
        else:
            # Default to in-memory for testing
            self.store = InMemoryVectorStore()
    
    def index_texts(
        self,
        nids: Sequence[int],
        texts: Sequence[str],
        metadatas: Sequence[dict[str, Any]] | None = None,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> int:
        """
        Index a batch of texts.
        
        Args:
            nids: Node IDs
            texts: Texts to embed
            metadatas: Optional metadata for each text
            batch_size: Batch size for embedding
            show_progress: Show progress bar
        
        Returns:
            Number of texts indexed
        """
        if not nids:
            return 0
        
        # Generate embeddings
        embeddings = self.embedding_model.encode_batch(
            texts,
            batch_size=batch_size,
            show_progress=show_progress,
        )
        
        # Add to store
        self.store.add(
            nids=nids,
            embeddings=embeddings,
            texts=texts,
            metadatas=metadatas,
        )
        
        logger.info(f"Indexed {len(nids)} vectors")
        return len(nids)
    
    def index_from_db(
        self,
        db,  # InceptionDB
        node_kinds: Sequence[str] | None = None,
        source_nids: Sequence[int] | None = None,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> int:
        """
        Index nodes from the Inception database.
        
        Args:
            db: InceptionDB instance
            node_kinds: Optional filter by node kind
            source_nids: Optional filter by source NID
            batch_size: Batch size
            show_progress: Show progress
        
        Returns:
            Number of nodes indexed
        """
        # Collect nodes to index
        nids = []
        texts = []
        metadatas = []
        
        for node in db.iter_nodes():
            # Apply filters
            if node_kinds and node.kind.name not in node_kinds:
                continue
            
            # Get text from payload
            text = self._get_node_text(node)
            if not text:
                continue
            
            nids.append(node.nid)
            texts.append(text)
            metadatas.append({
                "node_kind": node.kind.name,
                "confidence": node.payload.get("confidence", 1.0),
            })
        
        if not nids:
            return 0
        
        return self.index_texts(
            nids=nids,
            texts=texts,
            metadatas=metadatas,
            batch_size=batch_size,
            show_progress=show_progress,
        )
    
    def _get_node_text(self, node) -> str:
        """Extract text from a node for embedding."""
        payload = node.payload
        
        # Try common text fields
        for field in ["text", "name", "title", "description", "goal"]:
            if field in payload and payload[field]:
                return str(payload[field])
        
        # For claims, combine SPO
        if "subject" in payload and "predicate" in payload:
            parts = [
                payload.get("subject", ""),
                payload.get("predicate", ""),
                payload.get("object", ""),
            ]
            return " ".join(p for p in parts if p)
        
        return ""
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """
        Search for similar nodes.
        
        Args:
            query: Search query text
            top_k: Number of results
            filter_metadata: Optional metadata filter
        
        Returns:
            List of search results
        """
        # Embed query
        query_embedding = self.embedding_model.encode_single(query)
        
        # Search store
        return self.store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )
    
    def find_similar(
        self,
        nid: int,
        top_k: int = 10,
        exclude_self: bool = True,
    ) -> list[VectorSearchResult]:
        """
        Find nodes similar to a given node.
        
        Args:
            nid: Node ID to find similar nodes for
            top_k: Number of results
            exclude_self: Exclude the query node from results
        
        Returns:
            List of similar nodes
        """
        # Get existing embedding (search for exact NID)
        # This is a workaround - ideally we'd fetch the embedding directly
        results = self.store.search(
            query_embedding=[0.0] * self.embedding_model.dimension,
            top_k=self.stats.total_vectors,
        )
        
        # Find the target node's text
        target_text = None
        for r in results:
            if r.nid == nid:
                target_text = r.text
                break
        
        if not target_text:
            return []
        
        # Search using the text
        similar = self.search(target_text, top_k=top_k + 1)
        
        if exclude_self:
            similar = [r for r in similar if r.nid != nid]
        
        return similar[:top_k]
    
    def delete(self, nids: Sequence[int]) -> None:
        """Delete nodes from the index."""
        self.store.delete(nids)
    
    def clear(self) -> None:
        """Clear the entire index."""
        self.store.clear()
    
    @property
    def stats(self) -> IndexStats:
        """Get index statistics."""
        return IndexStats(
            total_vectors=self.store.count(),
            embedding_model=self.embedding_model.model_name,
            embedding_dimension=self.embedding_model.dimension,
            store_type=type(self.store).__name__,
        )


class HybridSearcher:
    """
    Hybrid search combining vector similarity with LMDB filters.
    
    Design by GEMINI-PRO:
    1. Vector search returns top-N candidates
    2. LMDB filter reduces to final top-k
    """
    
    def __init__(
        self,
        vector_index: VectorIndex,
        db=None,  # InceptionDB
    ):
        """
        Initialize hybrid searcher.
        
        Args:
            vector_index: Vector index for similarity search
            db: InceptionDB for metadata filtering
        """
        self.vector_index = vector_index
        self.db = db
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        candidate_multiplier: int = 10,
        node_kinds: Sequence[str] | None = None,
        source_nids: Sequence[int] | None = None,
        min_confidence: float | None = None,
    ) -> list[VectorSearchResult]:
        """
        Hybrid search with vector + metadata filtering.
        
        Args:
            query: Search query
            top_k: Final number of results
            candidate_multiplier: How many more candidates to fetch
            node_kinds: Filter by node kind
            source_nids: Filter by source
            min_confidence: Minimum confidence threshold
        
        Returns:
            Filtered and ranked results
        """
        # Phase 1: Get vector candidates
        candidates = self.vector_index.search(
            query=query,
            top_k=top_k * candidate_multiplier,
        )
        
        # Phase 2: Apply filters
        filtered = []
        for result in candidates:
            # Node kind filter
            if node_kinds and result.node_kind not in node_kinds:
                continue
            
            # Source filter (if we have DB access)
            if source_nids and self.db:
                # Check if node belongs to any of the source NIDs
                # This would require edge traversal
                pass  # TODO: Implement with DB access
            
            # Confidence filter
            if min_confidence and result.confidence < min_confidence:
                continue
            
            filtered.append(result)
            
            if len(filtered) >= top_k:
                break
        
        return filtered
    
    def search_by_example(
        self,
        example_nids: Sequence[int],
        top_k: int = 10,
        exclude_examples: bool = True,
    ) -> list[VectorSearchResult]:
        """
        Search for nodes similar to a set of examples.
        
        Combines embeddings of example nodes.
        """
        if not example_nids:
            return []
        
        # Get embeddings for examples and average them
        all_results = []
        for nid in example_nids:
            results = self.vector_index.find_similar(nid, top_k=top_k * 2)
            all_results.extend(results)
        
        # Deduplicate and sort by score
        seen = set(example_nids) if exclude_examples else set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x.score, reverse=True):
            if r.nid not in seen:
                seen.add(r.nid)
                unique_results.append(r)
                if len(unique_results) >= top_k:
                    break
        
        return unique_results
