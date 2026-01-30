"""
Query module for searching the knowledge hypergraph.

Provides temporal, entity, claim, and graph traversal queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator

from inception.db import InceptionDB, get_db
from inception.db.records import (
    SourceRecord,
    SpanRecord,
    NodeRecord,
    EdgeRecord,
)
from inception.db.keys import NodeKind, EdgeType


class QueryType(str, Enum):
    """Types of queries."""
    TEMPORAL = "temporal"
    ENTITY = "entity"
    CLAIM = "claim"
    PROCEDURE = "procedure"
    FULL_TEXT = "full_text"
    GRAPH = "graph"


@dataclass
class QueryResult:
    """Result of a query operation."""
    
    query_type: QueryType
    query_text: str | None = None
    
    # Results
    nodes: list[NodeRecord] = field(default_factory=list)
    spans: list[SpanRecord] = field(default_factory=list)
    sources: list[SourceRecord] = field(default_factory=list)
    
    # Metadata
    total_count: int = 0
    execution_time_ms: float = 0.0
    
    @property
    def is_empty(self) -> bool:
        return self.total_count == 0


@dataclass
class VectorSearchResult:
    """Result of vector similarity search."""
    
    query_text: str
    query_vector: list[float] | None = None
    
    # Results with similarity scores
    results: list[tuple[int, float, NodeRecord | None]] = field(default_factory=list)  # (nid, score, node)
    
    execution_time_ms: float = 0.0
    
    @property
    def top_node(self) -> NodeRecord | None:
        """Get the most similar node."""
        if self.results:
            return self.results[0][2]
        return None


@dataclass
class EvidenceChain:
    """Chain of evidence supporting a claim or node."""
    
    target_nid: int
    chain: list[tuple[int, EdgeType, int]] = field(default_factory=list)
    
    # Evidence nodes
    evidence_nodes: list[NodeRecord] = field(default_factory=list)
    evidence_spans: list[SpanRecord] = field(default_factory=list)
    
    # Confidence
    chain_confidence: float = 1.0
    
    @property
    def depth(self) -> int:
        return len(self.chain)


class QueryEngine:
    """
    Query engine for the knowledge hypergraph.
    
    Supports temporal, semantic, and graph-based queries.
    """
    
    def __init__(self, db: InceptionDB | None = None):
        """
        Initialize the query engine.
        
        Args:
            db: Database instance
        """
        self.db = db or get_db()
    
    def query_temporal(
        self,
        source_nid: int,
        start_ms: int,
        end_ms: int,
    ) -> QueryResult:
        """
        Query spans within a time range.
        
        Args:
            source_nid: Source to query
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds
        
        Returns:
            QueryResult with matching spans
        """
        import time
        start_time = time.time()
        
        spans = []
        
        with self.db.read_txn() as txn:
            for span_nid in self.db.query_spans_by_time(
                source_nid, start_ms, end_ms, txn
            ):
                span = self.db.get_span(span_nid, txn)
                if span:
                    spans.append(span)
        
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResult(
            query_type=QueryType.TEMPORAL,
            query_text=f"{start_ms}ms - {end_ms}ms",
            spans=spans,
            total_count=len(spans),
            execution_time_ms=execution_time,
        )
    
    def query_entities(
        self,
        entity_type: str | None = None,
        name_pattern: str | None = None,
        source_nid: int | None = None,
        limit: int = 100,
    ) -> QueryResult:
        """
        Query entity nodes.
        
        Args:
            entity_type: Filter by entity type
            name_pattern: Filter by name pattern (case-insensitive contains)
            source_nid: Filter by source
            limit: Maximum results
        
        Returns:
            QueryResult with matching entities
        """
        import time
        start_time = time.time()
        
        nodes = []
        
        for node in self.db.iter_nodes():
            if node.kind != NodeKind.ENTITY:
                continue
            
            # Apply filters
            if entity_type and node.payload.get("entity_type") != entity_type:
                continue
            
            if name_pattern:
                name = node.payload.get("name", "").lower()
                if name_pattern.lower() not in name:
                    continue
            
            if source_nid and source_nid not in (node.source_nids or []):
                continue
            
            nodes.append(node)
            
            if len(nodes) >= limit:
                break
        
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResult(
            query_type=QueryType.ENTITY,
            query_text=f"type={entity_type}, pattern={name_pattern}",
            nodes=nodes,
            total_count=len(nodes),
            execution_time_ms=execution_time,
        )
    
    def query_claims(
        self,
        modality: str | None = None,
        subject_pattern: str | None = None,
        hedged_only: bool = False,
        source_nid: int | None = None,
        limit: int = 100,
    ) -> QueryResult:
        """
        Query claim nodes.
        
        Args:
            modality: Filter by modality (assertion, negation, possibility)
            subject_pattern: Filter by subject pattern
            hedged_only: Only return hedged claims
            source_nid: Filter by source
            limit: Maximum results
        
        Returns:
            QueryResult with matching claims
        """
        import time
        start_time = time.time()
        
        nodes = []
        
        for node in self.db.iter_nodes():
            if node.kind != NodeKind.CLAIM:
                continue
            
            # Apply filters
            if modality and node.payload.get("modality") != modality:
                continue
            
            if subject_pattern:
                subject = node.payload.get("subject", "")
                if subject and subject_pattern.lower() not in subject.lower():
                    continue
            
            if hedged_only:
                hedges = node.payload.get("hedges", [])
                if not hedges:
                    continue
            
            if source_nid and source_nid not in (node.source_nids or []):
                continue
            
            nodes.append(node)
            
            if len(nodes) >= limit:
                break
        
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResult(
            query_type=QueryType.CLAIM,
            query_text=f"modality={modality}, subject={subject_pattern}",
            nodes=nodes,
            total_count=len(nodes),
            execution_time_ms=execution_time,
        )
    
    def query_procedures(
        self,
        title_pattern: str | None = None,
        min_steps: int | None = None,
        source_nid: int | None = None,
        limit: int = 100,
    ) -> QueryResult:
        """
        Query procedure nodes.
        
        Args:
            title_pattern: Filter by title pattern
            min_steps: Minimum number of steps
            source_nid: Filter by source
            limit: Maximum results
        
        Returns:
            QueryResult with matching procedures
        """
        import time
        start_time = time.time()
        
        nodes = []
        
        for node in self.db.iter_nodes():
            if node.kind != NodeKind.PROCEDURE:
                continue
            
            # Apply filters
            if title_pattern:
                title = node.payload.get("title", "")
                if title and title_pattern.lower() not in title.lower():
                    continue
            
            if min_steps:
                steps = node.payload.get("steps", [])
                if len(steps) < min_steps:
                    continue
            
            if source_nid and source_nid not in (node.source_nids or []):
                continue
            
            nodes.append(node)
            
            if len(nodes) >= limit:
                break
        
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResult(
            query_type=QueryType.PROCEDURE,
            query_text=f"title={title_pattern}, min_steps={min_steps}",
            nodes=nodes,
            total_count=len(nodes),
            execution_time_ms=execution_time,
        )
    
    def full_text_search(
        self,
        query: str,
        node_kinds: list[NodeKind] | None = None,
        source_nid: int | None = None,
        limit: int = 100,
    ) -> QueryResult:
        """
        Full-text search across nodes.
        
        Args:
            query: Search query (case-insensitive)
            node_kinds: Filter by node kinds
            source_nid: Filter by source
            limit: Maximum results
        
        Returns:
            QueryResult with matching nodes
        """
        import time
        start_time = time.time()
        
        query_lower = query.lower()
        nodes = []
        
        for node in self.db.iter_nodes():
            # Filter by kind
            if node_kinds and node.kind not in node_kinds:
                continue
            
            if source_nid and source_nid not in (node.source_nids or []):
                continue
            
            # Search in payload
            payload_str = str(node.payload).lower()
            if query_lower in payload_str:
                nodes.append(node)
                
                if len(nodes) >= limit:
                    break
        
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResult(
            query_type=QueryType.FULL_TEXT,
            query_text=query,
            nodes=nodes,
            total_count=len(nodes),
            execution_time_ms=execution_time,
        )
    
    def get_neighbors(
        self,
        nid: int,
        edge_types: list[EdgeType] | None = None,
        direction: str = "both",  # "outgoing", "incoming", "both"
    ) -> list[tuple[int, EdgeType, NodeRecord | None]]:
        """
        Get neighboring nodes connected by edges.
        
        Args:
            nid: Node NID
            edge_types: Filter by edge types
            direction: Edge direction to follow
        
        Returns:
            List of (neighbor_nid, edge_type, neighbor_node)
        """
        neighbors = []
        
        with self.db.read_txn() as txn:
            # Outgoing edges
            if direction in ("outgoing", "both"):
                for to_nid, edge in self.db.iter_edges_from(nid, txn):
                    if edge_types and edge.edge_type not in edge_types:
                        continue
                    neighbor = self.db.get_node(to_nid, txn)
                    neighbors.append((to_nid, edge.edge_type, neighbor))
            
            # Incoming edges (would need reverse index)
            # For now, scan all edges (inefficient but complete)
            if direction in ("incoming", "both"):
                for node in self.db.iter_nodes():
                    for to_nid, edge in self.db.iter_edges_from(node.nid, txn):
                        if to_nid == nid:
                            if edge_types and edge.edge_type not in edge_types:
                                continue
                            neighbors.append((node.nid, edge.edge_type, node))
        
        return neighbors
    
    def build_evidence_chain(
        self,
        target_nid: int,
        max_depth: int = 3,
    ) -> EvidenceChain:
        """
        Build evidence chain supporting a node.
        
        Args:
            target_nid: Target node NID
            max_depth: Maximum traversal depth
        
        Returns:
            EvidenceChain with supporting evidence
        """
        chain = EvidenceChain(target_nid=target_nid)
        visited = {target_nid}
        
        with self.db.read_txn() as txn:
            # Get target node
            target_node = self.db.get_node(target_nid, txn)
            if not target_node:
                return chain
            
            # Get direct evidence spans
            for span_nid in target_node.evidence_spans:
                span = self.db.get_span(span_nid, txn)
                if span:
                    chain.evidence_spans.append(span)
            
            # Traverse supporting edges
            queue = [(target_nid, 0)]
            
            while queue:
                current_nid, depth = queue.pop(0)
                
                if depth >= max_depth:
                    continue
                
                for to_nid, edge in self.db.iter_edges_from(current_nid, txn):
                    if to_nid in visited:
                        continue
                    
                    # Only follow support-type edges
                    if edge.edge_type in (EdgeType.SUPPORTS, EdgeType.MENTIONS, EdgeType.RELATED_TO):
                        visited.add(to_nid)
                        chain.chain.append((current_nid, edge.edge_type, to_nid))
                        
                        neighbor = self.db.get_node(to_nid, txn)
                        if neighbor:
                            chain.evidence_nodes.append(neighbor)
                            
                            # Add neighbor's evidence spans
                            for span_nid in neighbor.evidence_spans:
                                span = self.db.get_span(span_nid, txn)
                                if span and span not in chain.evidence_spans:
                                    chain.evidence_spans.append(span)
                        
                        queue.append((to_nid, depth + 1))
        
        # Compute chain confidence
        if chain.evidence_nodes:
            confidences = [n.confidence.combined for n in chain.evidence_nodes]
            chain.chain_confidence = sum(confidences) / len(confidences)
        
        return chain
    
    def find_contradictions(
        self,
        source_nid: int | None = None,
    ) -> list[tuple[NodeRecord, NodeRecord, float]]:
        """
        Find contradicting claims.
        
        Args:
            source_nid: Filter by source
        
        Returns:
            List of (claim1, claim2, confidence) tuples
        """
        contradictions = []
        
        with self.db.read_txn() as txn:
            for node in self.db.iter_nodes():
                if node.kind != NodeKind.CLAIM:
                    continue
                
                if source_nid and source_nid not in (node.source_nids or []):
                    continue
                
                # Check outgoing contradiction edges
                for to_nid, edge in self.db.iter_edges_from(node.nid, txn):
                    if edge.edge_type == EdgeType.CONTRADICTS:
                        other = self.db.get_node(to_nid, txn)
                        if other:
                            contradictions.append((node, other, edge.weight))
        
        return contradictions
    
    def get_gaps(
        self,
        source_nid: int | None = None,
        severity: str | None = None,
    ) -> list[NodeRecord]:
        """
        Get gap nodes.
        
        Args:
            source_nid: Filter by source
            severity: Filter by severity
        
        Returns:
            List of gap nodes
        """
        gaps = []
        
        for node in self.db.iter_nodes():
            if node.kind != NodeKind.GAP:
                continue
            
            if source_nid and source_nid not in (node.source_nids or []):
                continue
            
            if severity and node.payload.get("severity") != severity:
                continue
            
            gaps.append(node)
        
        return gaps
    
    def vector_search(
        self,
        query: str,
        top_k: int = 10,
        node_kinds: list[NodeKind] | None = None,
        min_similarity: float = 0.0,
    ) -> VectorSearchResult:
        """
        Semantic vector search using embeddings.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            node_kinds: Filter by node kinds
            min_similarity: Minimum similarity threshold
        
        Returns:
            VectorSearchResult with similar nodes
        """
        import time
        start_time = time.time()
        
        # Placeholder - actual implementation would:
        # 1. Embed the query using sentence-transformers
        # 2. Search the vector index (HNSW/FAISS)
        # 3. Return top-k results with similarity scores
        
        # For now, fall back to full-text search simulation
        query_lower = query.lower()
        results = []
        
        for node in self.db.iter_nodes():
            if node_kinds and node.kind not in node_kinds:
                continue
            
            # Simple text similarity as placeholder
            payload_str = str(node.payload).lower()
            if query_lower in payload_str:
                # Simulate similarity score based on match position
                score = 0.7 + (0.3 * (1.0 / (payload_str.find(query_lower) + 1)))
                score = min(score, 1.0)
                
                if score >= min_similarity:
                    results.append((node.nid, score, node))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]
        
        execution_time = (time.time() - start_time) * 1000
        
        return VectorSearchResult(
            query_text=query,
            query_vector=None,  # Would be actual embedding
            results=results,
            execution_time_ms=execution_time,
        )


def query_temporal(
    source_nid: int,
    start_ms: int,
    end_ms: int,
) -> QueryResult:
    """Convenience function for temporal query."""
    engine = QueryEngine()
    return engine.query_temporal(source_nid, start_ms, end_ms)


def query_entities(
    entity_type: str | None = None,
    name_pattern: str | None = None,
    limit: int = 100,
) -> QueryResult:
    """Convenience function for entity query."""
    engine = QueryEngine()
    return engine.query_entities(entity_type, name_pattern, limit=limit)


def query_claims(
    modality: str | None = None,
    hedged_only: bool = False,
    limit: int = 100,
) -> QueryResult:
    """Convenience function for claim query."""
    engine = QueryEngine()
    return engine.query_claims(modality, hedged_only=hedged_only, limit=limit)


def full_text_search(query: str, limit: int = 100) -> QueryResult:
    """Convenience function for full-text search."""
    engine = QueryEngine()
    return engine.full_text_search(query, limit=limit)
