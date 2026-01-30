"""
Expanded unit tests for surface/neurosymbolic.py

Tests for neurosymbolic integration.
"""

import pytest

try:
    from inception.surface.neurosymbolic import (
        NeurosymbolicBridge,
        SymbolicGrounding,
        NeuralEncoder,
        GroundingStrategy,
    )
    HAS_NEUROSYMBOLIC = True
except ImportError:
    HAS_NEUROSYMBOLIC = False


@pytest.mark.skipif(not HAS_NEUROSYMBOLIC, reason="neurosymbolic module not available")
class TestGroundingStrategy:
    """Tests for GroundingStrategy enum."""
    
    def test_strategies_exist(self):
        """Test grounding strategies exist."""
        assert len(list(GroundingStrategy)) > 0


@pytest.mark.skipif(not HAS_NEUROSYMBOLIC, reason="neurosymbolic module not available")
class TestSymbolicGrounding:
    """Tests for SymbolicGrounding dataclass."""
    
    def test_creation(self):
        """Test creating grounding."""
        grounding = SymbolicGrounding(
            symbol_id="sym1",
            grounding_type=list(GroundingStrategy)[0],
        )
        
        assert grounding.symbol_id == "sym1"
    
    def test_with_confidence(self):
        """Test grounding with confidence."""
        grounding = SymbolicGrounding(
            symbol_id="sym2",
            grounding_type=list(GroundingStrategy)[0],
            confidence=0.85,
        )
        
        assert grounding.confidence == 0.85


@pytest.mark.skipif(not HAS_NEUROSYMBOLIC, reason="neurosymbolic module not available")
class TestNeuralEncoder:
    """Tests for NeuralEncoder."""
    
    def test_creation(self):
        """Test creating encoder."""
        encoder = NeuralEncoder()
        
        assert encoder is not None


@pytest.mark.skipif(not HAS_NEUROSYMBOLIC, reason="neurosymbolic module not available")
class TestNeurosymbolicBridge:
    """Tests for NeurosymbolicBridge."""
    
    def test_creation(self):
        """Test creating bridge."""
        bridge = NeurosymbolicBridge()
        
        assert bridge is not None
    
    def test_ground(self):
        """Test grounding symbol."""
        bridge = NeurosymbolicBridge()
        
        result = bridge.ground("concept")
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
