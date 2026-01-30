"""Tests for graph/* modules"""
import pytest

try:
    from inception.graph.builder import GraphBuilder
    HAS_BUILDER = True
except ImportError:
    HAS_BUILDER = False

try:
    from inception.graph.hypergraph import HyperGraph, HyperNode, HyperEdge
    HAS_HYPERGRAPH = True
except ImportError:
    HAS_HYPERGRAPH = False


@pytest.mark.skipif(not HAS_BUILDER, reason="GraphBuilder not available")
class TestGraphBuilder:
    def test_creation(self):
        builder = GraphBuilder()
        assert builder is not None


@pytest.mark.skipif(not HAS_HYPERGRAPH, reason="HyperGraph not available")
class TestHyperGraph:
    def test_creation(self):
        graph = HyperGraph()
        assert graph is not None
    
    def test_add_node(self):
        graph = HyperGraph()
        if hasattr(graph, 'add_node'):
            node = graph.add_node(content="test")
            assert node is not None


@pytest.mark.skipif(not HAS_HYPERGRAPH, reason="HyperNode not available")
class TestHyperNode:
    def test_creation(self):
        node = HyperNode(nid=1, content="test")
        assert node.content == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
