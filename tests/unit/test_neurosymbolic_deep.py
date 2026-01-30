"""Tests for surface/neurosymbolic.py (57%)"""
import pytest

try:
    from inception.surface.neurosymbolic import NeuroSymbolicBridge, NeuralSymbol
    HAS_NS = True
except ImportError:
    HAS_NS = False


@pytest.mark.skipif(not HAS_NS, reason="NeuroSymbolicBridge not available")
class TestNeuroSymbolicBridge:
    def test_creation(self):
        bridge = NeuroSymbolicBridge()
        assert bridge is not None


@pytest.mark.skipif(not HAS_NS, reason="NeuralSymbol not available")
class TestNeuralSymbol:
    def test_creation(self):
        symbol = NeuralSymbol(name="test", embedding=[0.1, 0.2, 0.3])
        assert symbol.name == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
