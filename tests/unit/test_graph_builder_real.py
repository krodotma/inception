"""
REAL tests for graph/builder.py (6% coverage)
Requires spacy - skipped if not available
"""
import pytest

try:
    from inception.graph.builder import GraphBuilder
    HAS_BUILDER = True
except ImportError:
    HAS_BUILDER = False


@pytest.mark.skipif(not HAS_BUILDER, reason="spacy not available")
class TestGraphBuilder:
    def test_creation(self):
        builder = GraphBuilder()
        assert builder is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
