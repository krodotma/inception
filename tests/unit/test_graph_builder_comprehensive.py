"""
Tests for graph/builder.py (25%) - targeting GraphBuilder and build_graph
"""
import pytest

try:
    from inception.graph.builder import GraphBuilder, GraphBuildResult, build_graph
    HAS_BUILDER = True
except ImportError:
    HAS_BUILDER = False

try:
    from inception.db import InceptionDB
    HAS_DB = True
except ImportError:
    HAS_DB = False


@pytest.mark.skipif(not HAS_BUILDER, reason="GraphBuilder not available")
class TestGraphBuildResult:
    """Test GraphBuildResult dataclass."""
    
    def test_creation_default(self):
        result = GraphBuildResult(source_nid=1)
        assert result.source_nid == 1
        assert result.edge_count == 0
    
    def test_creation_full(self):
        result = GraphBuildResult(
            source_nid=1,
            span_nids=[10, 20],
            node_nids=[100, 200],
            edge_count=5,
            entity_count=3,
            claim_count=2,
        )
        assert result.source_nid == 1
        assert len(result.span_nids) == 2
        assert result.edge_count == 5


@pytest.mark.skipif(not HAS_BUILDER, reason="GraphBuilder not available")
class TestGraphBuilder:
    """Test GraphBuilder class."""
    
    def test_creation_default(self):
        """Create builder with default DB."""
        builder = GraphBuilder()
        assert builder is not None
    
    def test_has_db(self):
        """Verify builder has DB reference."""
        builder = GraphBuilder()
        assert hasattr(builder, 'db')
    
    def test_has_build_method(self):
        """Verify build_from_extraction method exists."""
        builder = GraphBuilder()
        assert hasattr(builder, 'build_from_extraction')
        assert callable(builder.build_from_extraction)


@pytest.mark.skipif(not HAS_BUILDER, reason="build_graph not available")
class TestBuildGraphFunction:
    """Test build_graph convenience function."""
    
    def test_function_exists(self):
        """Verify function is callable."""
        assert callable(build_graph)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
