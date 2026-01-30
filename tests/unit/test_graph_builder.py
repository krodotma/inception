"""
Unit tests for graph/builder.py

Tests for graph building:
- GraphBuildResult: Result data class
- GraphBuilder: Main builder
"""

import pytest

try:
    from inception.graph.builder import (
        GraphBuildResult,
        GraphBuilder,
        build_graph,
    )
    HAS_BUILDER = True
except ImportError:
    HAS_BUILDER = False


@pytest.mark.skipif(not HAS_BUILDER, reason="builder module not available")
class TestGraphBuildResult:
    """Tests for GraphBuildResult dataclass."""
    
    def test_creation_minimal(self):
        """Test creating minimal result."""
        result = GraphBuildResult(source_nid=1)
        
        assert result.source_nid == 1
        assert result.edge_count == 0
    
    def test_creation_full(self):
        """Test creating full result."""
        result = GraphBuildResult(
            source_nid=1,
            span_nids=[1, 2, 3],
            node_nids=[4, 5, 6],
            edge_count=10,
            entity_count=5,
            claim_count=3,
            procedure_count=2,
            gap_count=1,
        )
        
        assert len(result.span_nids) == 3
        assert result.entity_count == 5


@pytest.mark.skipif(not HAS_BUILDER, reason="builder module not available")
class TestGraphBuilder:
    """Tests for GraphBuilder."""
    
    def test_creation_without_db(self):
        """Test creating builder without explicit db."""
        builder = GraphBuilder()
        
        assert builder is not None
    
    def test_creation_with_db(self):
        """Test creating builder with explicit db."""
        builder = GraphBuilder(db=None)  # Will use default
        
        assert builder is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
