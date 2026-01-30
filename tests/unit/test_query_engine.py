"""
Unit tests for query/engine.py

Tests for query execution:
- QueryType: Enum
- QueryResult, VectorSearchResult, EvidenceChain: Results
- QueryEngine: Main engine
"""

import pytest

try:
    from inception.query.engine import (
        QueryType,
        QueryResult,
        VectorSearchResult,
        EvidenceChain,
        QueryEngine,
    )
    from inception.db.keys import NodeKind
    HAS_QUERY = True
except ImportError:
    HAS_QUERY = False


@pytest.mark.skipif(not HAS_QUERY, reason="query module not available")
class TestQueryType:
    """Tests for QueryType enum."""
    
    def test_values(self):
        """Test query type values."""
        assert QueryType.TEMPORAL.value == "temporal"
        assert QueryType.ENTITY.value == "entity"
        assert QueryType.CLAIM.value == "claim"
        assert QueryType.GRAPH.value == "graph"


@pytest.mark.skipif(not HAS_QUERY, reason="query module not available")
class TestQueryResult:
    """Tests for QueryResult dataclass."""
    
    def test_creation(self):
        """Test creating result."""
        result = QueryResult(query_type=QueryType.ENTITY)
        
        assert result.query_type == QueryType.ENTITY
        assert result.is_empty is True  # property
    
    def test_with_query_text(self):
        """Test result with query text."""
        result = QueryResult(
            query_type=QueryType.FULL_TEXT,
            query_text="machine learning",
        )
        
        assert result.query_text == "machine learning"
    
    def test_total_count(self):
        """Test total count."""
        result = QueryResult(
            query_type=QueryType.ENTITY,
            total_count=50,
        )
        
        assert result.total_count == 50


@pytest.mark.skipif(not HAS_QUERY, reason="query module not available")
class TestVectorSearchResult:
    """Tests for VectorSearchResult dataclass."""
    
    def test_creation(self):
        """Test creating result."""
        result = VectorSearchResult(query_text="test query")
        
        assert result.query_text == "test query"
        assert result.top_node is None  # property
    
    def test_with_results(self):
        """Test with results."""
        result = VectorSearchResult(
            query_text="test",
            results=[(1, 0.95, None), (2, 0.85, None)],
        )
        
        assert len(result.results) == 2


@pytest.mark.skipif(not HAS_QUERY, reason="query module not available")
class TestEvidenceChain:
    """Tests for EvidenceChain dataclass."""
    
    def test_creation(self):
        """Test creating chain."""
        chain = EvidenceChain(target_nid=100)
        
        assert chain.target_nid == 100
        assert chain.depth == 0  # property
    
    def test_with_chain(self):
        """Test with evidence chain."""
        from inception.db.keys import EdgeType
        
        chain = EvidenceChain(
            target_nid=100,
            chain=[(1, EdgeType.SUPPORTS, 2), (2, EdgeType.SUPPORTS, 100)],
        )
        
        assert chain.depth == 2  # property


@pytest.mark.skipif(not HAS_QUERY, reason="query module not available")
class TestQueryEngine:
    """Tests for QueryEngine."""
    
    def test_creation(self):
        """Test creating engine."""
        engine = QueryEngine()
        
        assert engine is not None
    
    def test_query_entities(self):
        """Test querying entities."""
        engine = QueryEngine()
        
        result = engine.query_entities(limit=10)
        
        assert isinstance(result, QueryResult)
    
    def test_query_claims(self):
        """Test querying claims."""
        engine = QueryEngine()
        
        result = engine.query_claims(limit=10)
        
        assert isinstance(result, QueryResult)
    
    def test_full_text_search(self):
        """Test full text search."""
        engine = QueryEngine()
        
        result = engine.full_text_search("test query", limit=10)
        
        assert isinstance(result, QueryResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
