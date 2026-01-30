"""Tests for surface modules at 91%+ to push toward 100%"""
import pytest

try:
    from inception.surface.stigmergic import TraceType, NeuralTrace, StigmergicWorkspace, EmergentTopology
    HAS_STIG = True
except ImportError:
    HAS_STIG = False

try:
    from inception.surface.safety import SafetyChecker, SafetyConfig, SafetyLevel
    HAS_SAFETY = True
except ImportError:
    HAS_SAFETY = False

try:
    from inception.surface.reactive import ReactiveEngine, ReactiveConfig
    HAS_REACTIVE = True
except ImportError:
    HAS_REACTIVE = False


@pytest.mark.skipif(not HAS_STIG, reason="stigmergic not available")
class TestNeuralTraceDeep:
    def test_create_with_embedding(self):
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="/test",
            agent_id="agent1",
            embedding=[0.1, 0.2, 0.3],
        )
        assert trace.embedding_dim == 3
    
    def test_attention_computation(self):
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="/test",
            agent_id="agent1",
            embedding=[0.1, 0.2, 0.3],
        )
        score = trace.compute_attention([0.1, 0.2, 0.3])
        assert score >= 0


@pytest.mark.skipif(not HAS_SAFETY, reason="safety not available")
class TestSafetyLevelDeep:
    def test_levels_exist(self):
        assert SafetyLevel.LOW is not None
        assert SafetyLevel.MEDIUM is not None
        assert SafetyLevel.HIGH is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
