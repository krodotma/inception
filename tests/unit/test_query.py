"""Unit tests for query layer modules."""

import pytest
from inception.query.engine import (
    QueryType,
    QueryResult,
    EvidenceChain,
    QueryEngine,
)


class TestQueryType:
    """Tests for QueryType enumeration."""
    
    def test_query_types(self):
        """Test query type values."""
        assert QueryType.TEMPORAL.value == "temporal"
        assert QueryType.ENTITY.value == "entity"
        assert QueryType.CLAIM.value == "claim"
        assert QueryType.FULL_TEXT.value == "full_text"
        assert QueryType.GRAPH.value == "graph"


class TestQueryResult:
    """Tests for QueryResult dataclass."""
    
    def test_query_result_creation(self):
        """Test creating a query result."""
        result = QueryResult(
            query_type=QueryType.ENTITY,
            query_text="Python",
            total_count=5,
            execution_time_ms=12.5,
        )
        
        assert result.query_type == QueryType.ENTITY
        assert result.total_count == 5
        assert result.execution_time_ms == 12.5
    
    def test_empty_result(self):
        """Test empty result detection."""
        empty = QueryResult(query_type=QueryType.FULL_TEXT, total_count=0)
        non_empty = QueryResult(query_type=QueryType.FULL_TEXT, total_count=3)
        
        assert empty.is_empty
        assert not non_empty.is_empty
    
    def test_result_with_nodes(self):
        """Test result with nodes."""
        from inception.db.records import NodeRecord, Confidence
        from inception.db.keys import NodeKind
        
        node = NodeRecord(
            nid=1,
            kind=NodeKind.ENTITY,
            payload={"name": "Python"},
        )
        
        result = QueryResult(
            query_type=QueryType.ENTITY,
            nodes=[node],
            total_count=1,
        )
        
        assert len(result.nodes) == 1
        assert result.nodes[0].payload["name"] == "Python"


class TestEvidenceChain:
    """Tests for EvidenceChain dataclass."""
    
    def test_evidence_chain_creation(self):
        """Test creating an evidence chain."""
        chain = EvidenceChain(target_nid=42)
        
        assert chain.target_nid == 42
        assert chain.depth == 0
        assert chain.chain_confidence == 1.0
    
    def test_chain_with_edges(self):
        """Test chain with edges."""
        from inception.db.keys import EdgeType
        
        chain = EvidenceChain(
            target_nid=1,
            chain=[
                (1, EdgeType.MENTIONS, 2),
                (2, EdgeType.SUPPORTS, 3),
            ],
        )
        
        assert chain.depth == 2
    
    def test_chain_with_evidence(self):
        """Test chain with evidence nodes."""
        from inception.db.records import NodeRecord, Confidence
        from inception.db.keys import NodeKind
        
        node = NodeRecord(
            nid=2,
            kind=NodeKind.CLAIM,
            payload={"text": "Evidence"},
            confidence=Confidence(overall=0.8),
        )
        
        chain = EvidenceChain(
            target_nid=1,
            evidence_nodes=[node],
        )
        
        assert len(chain.evidence_nodes) == 1


class TestQueryEngineStructure:
    """Tests for QueryEngine structure (no DB required)."""
    
    def test_query_engine_methods(self):
        """Test that QueryEngine has expected methods."""
        assert hasattr(QueryEngine, "query_temporal")
        assert hasattr(QueryEngine, "query_entities")
        assert hasattr(QueryEngine, "query_claims")
        assert hasattr(QueryEngine, "query_procedures")
        assert hasattr(QueryEngine, "full_text_search")
        assert hasattr(QueryEngine, "get_neighbors")
        assert hasattr(QueryEngine, "build_evidence_chain")
        assert hasattr(QueryEngine, "find_contradictions")
        assert hasattr(QueryEngine, "get_gaps")
