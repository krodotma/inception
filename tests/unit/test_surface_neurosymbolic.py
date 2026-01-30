"""
Unit tests for surface/neurosymbolic.py

Tests for neurosymbolic bridge layer:
- NeuralToSymbolicBridge: Neural to symbolic translation
- SymbolicToNeuralBridge: Symbolic to neural translation
"""

import pytest
from inception.surface.neurosymbolic import (
    # Enums
    ReasoningMode,
    # Data classes
    GroundingResult,
    EmbeddingResult,
    # Bridges
    NeuralToSymbolicBridge,
    SymbolicToNeuralBridge,
)


# =============================================================================
# Test: Enums
# =============================================================================

class TestReasoningMode:
    """Tests for ReasoningMode enum."""
    
    def test_mode_values(self):
        """Test reasoning mode values."""
        assert ReasoningMode.NEURAL_FIRST.value == "neural_first"
        assert ReasoningMode.SYMBOLIC_FIRST.value == "symbolic_first"
        assert ReasoningMode.INTERLEAVED.value == "interleaved"
        assert ReasoningMode.PARALLEL.value == "parallel"


# =============================================================================
# Test: GroundingResult
# =============================================================================

class TestGroundingResult:
    """Tests for GroundingResult dataclass."""
    
    def test_creation_success(self):
        """Test creating successful grounding result."""
        result = GroundingResult(
            success=True,
            concept="entity",
            confidence=0.85,
            explanation="Matched to entity concept",
        )
        
        assert result.success is True
        assert result.concept == "entity"
    
    def test_creation_failure(self):
        """Test creating failed grounding result."""
        result = GroundingResult(
            success=False,
            concept=None,
            confidence=0.2,
            explanation="No matching concept found",
        )
        
        assert result.success is False
    
    def test_is_high_confidence(self):
        """Test high confidence check."""
        high = GroundingResult(True, "X", 0.95, "High")
        low = GroundingResult(True, "Y", 0.5, "Low")
        
        # is_high_confidence may be property or method - test it exists
        if callable(getattr(high, 'is_high_confidence', None)):
            assert high.is_high_confidence() is True
        else:
            assert high.is_high_confidence is True


# =============================================================================
# Test: EmbeddingResult
# =============================================================================

class TestEmbeddingResult:
    """Tests for EmbeddingResult dataclass."""
    
    def test_creation(self):
        """Test creating embedding result."""
        result = EmbeddingResult(
            success=True,
            embedding=[0.1, 0.2, 0.3],
            dimension=3,
            explanation="Embedded successfully",
            source_concept="test",
        )
        
        assert result.dimension == 3
        assert len(result.embedding) == 3


# =============================================================================
# Test: NeuralToSymbolicBridge
# =============================================================================

class TestNeuralToSymbolicBridge:
    """Tests for NeuralToSymbolicBridge."""
    
    def test_creation_with_defaults(self):
        """Test creating bridge with defaults."""
        bridge = NeuralToSymbolicBridge()
        
        assert bridge is not None
    
    def test_creation_with_custom_threshold(self):
        """Test creating bridge with custom threshold."""
        bridge = NeuralToSymbolicBridge(similarity_threshold=0.9)
        
        assert bridge.similarity_threshold == 0.9
    
    def test_embed_to_concept(self):
        """Test grounding embedding to concept."""
        bridge = NeuralToSymbolicBridge()
        
        # Use a pseudo-embedding
        embedding = [0.1, 0.2, 0.3] * 20  # 60 dimensions
        
        result = bridge.embed_to_concept(embedding, top_k=3)
        
        assert isinstance(result, GroundingResult)
    
    def test_cluster_to_category(self):
        """Test mapping cluster to category."""
        bridge = NeuralToSymbolicBridge()
        
        cluster = [
            [0.1] * 64,
            [0.2] * 64,
            [0.3] * 64,
        ]
        
        result = bridge.cluster_to_category(cluster)
        
        assert isinstance(result, GroundingResult)
    
    def test_attention_to_salience(self):
        """Test extracting salient tokens."""
        bridge = NeuralToSymbolicBridge()
        
        attention = [0.1, 0.3, 0.6, 0.05, 0.2]
        tokens = ["the", "quick", "fox", "is", "brown"]
        
        salient = bridge.attention_to_salience(attention, tokens, threshold=0.15)
        
        assert isinstance(salient, list)
    
    def test_confidence_to_probability(self):
        """Test calibrating confidence."""
        bridge = NeuralToSymbolicBridge()
        
        prob = bridge.confidence_to_probability(0.8)
        
        assert 0 <= prob <= 1
    
    def test_register_concept(self):
        """Test registering a new concept."""
        bridge = NeuralToSymbolicBridge()
        
        bridge.register_concept("custom", [0.5] * 64)
        
        assert "custom" in bridge.concept_embeddings


# =============================================================================
# Test: SymbolicToNeuralBridge
# =============================================================================

class TestSymbolicToNeuralBridge:
    """Tests for SymbolicToNeuralBridge."""
    
    def test_creation_with_defaults(self):
        """Test creating bridge with defaults."""
        bridge = SymbolicToNeuralBridge()
        
        assert bridge is not None
        assert bridge.embedding_dim == 64
    
    def test_creation_with_custom_dim(self):
        """Test creating bridge with custom dimension."""
        bridge = SymbolicToNeuralBridge(embedding_dim=128)
        
        assert bridge.embedding_dim == 128
    
    def test_concept_to_embed(self):
        """Test embedding a concept."""
        bridge = SymbolicToNeuralBridge()
        
        result = bridge.concept_to_embed("entity")
        
        assert isinstance(result, EmbeddingResult)
    
    def test_relation_to_operation(self):
        """Test mapping relation to operation."""
        bridge = SymbolicToNeuralBridge()
        
        result = bridge.relation_to_operation("is_a", "entity", "concept")
        
        # Should return some embedding
        assert result is not None
    
    def test_register_concept(self):
        """Test registering a concept."""
        bridge = SymbolicToNeuralBridge()
        
        bridge.register_concept("my_concept", [0.1] * 64)
        
        assert "my_concept" in bridge.concept_embeddings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
