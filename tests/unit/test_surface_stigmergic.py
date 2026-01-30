"""
Unit tests for surface/stigmergic.py

Tests for stigmergic coordination layer:
- TraceType: Types of traces
- NeuralTrace: Trace with embeddings
- StigmergicWorkspace: Shared coordination space
"""

import pytest
from inception.surface.stigmergic import (
    # Enums
    TraceType,
    # Data classes
    NeuralTrace,
    # Workspace
    StigmergicWorkspace,
)


# =============================================================================
# Test: TraceType
# =============================================================================

class TestTraceType:
    """Tests for TraceType enum."""
    
    def test_trace_type_values(self):
        """Test trace type values."""
        assert TraceType.MARKER.value == "marker"
        assert TraceType.SIGNAL.value == "signal"
        assert TraceType.GRADIENT.value == "gradient"
        assert TraceType.SEMANTIC.value == "semantic"
        assert TraceType.CLAIM.value == "claim"


# =============================================================================
# Test: NeuralTrace
# =============================================================================

class TestNeuralTrace:
    """Tests for NeuralTrace dataclass."""
    
    def test_create(self):
        """Test creating a trace."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="node_a",
            agent_id="agent-001",
        )
        
        assert trace is not None
        assert trace.trace_type == TraceType.MARKER
        assert trace.location == "node_a"
    
    def test_create_with_embedding(self):
        """Test creating trace with embedding."""
        trace = NeuralTrace.create(
            trace_type=TraceType.SEMANTIC,
            location="concept_x",
            agent_id="agent-001",
            embedding=[0.1, 0.2, 0.3],
        )
        
        assert trace.embedding is not None
    
    def test_create_with_symbols(self):
        """Test creating trace with symbols."""
        trace = NeuralTrace.create(
            trace_type=TraceType.CLAIM,
            location="fact_1",
            agent_id="agent-001",
            symbols={"type": "claim", "verified": True},
        )
        
        assert trace.symbols["type"] == "claim"
    
    def test_decay(self):
        """Test trace decay."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="node",
            agent_id="agent",
            strength=1.0,
        )
        
        original_strength = trace.strength
        trace.decay(delta_seconds=100)
        
        assert trace.strength <= original_strength
    
    def test_reinforce(self):
        """Test trace reinforcement."""
        trace = NeuralTrace.create(
            trace_type=TraceType.SIGNAL,
            location="node",
            agent_id="agent",
            strength=0.5,
        )
        
        original_strength = trace.strength
        trace.reinforce(signal=0.3)
        
        assert trace.strength >= original_strength
    
    def test_is_active(self):
        """Test checking if trace is active."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="node",
            agent_id="agent",
            strength=0.5,
        )
        
        assert trace.is_active() is True
    
    def test_add_symbol(self):
        """Test adding symbol to trace."""
        trace = NeuralTrace.create(
            trace_type=TraceType.CLAIM,
            location="loc",
            agent_id="agent",
        )
        
        trace.add_symbol("key", "value")
        
        assert trace.symbols.get("key") == "value"
    
    def test_match_symbols(self):
        """Test symbol matching."""
        trace = NeuralTrace.create(
            trace_type=TraceType.CLAIM,
            location="loc",
            agent_id="agent",
            symbols={"type": "fact", "domain": "science"},
        )
        
        score = trace.match_symbols({"type": "fact"})
        
        assert score >= 0
    
    def test_to_dict(self):
        """Test serialization."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="node",
            agent_id="agent",
        )
        
        data = trace.to_dict()
        
        assert "trace_id" in data
        assert "location" in data
    
    def test_from_dict(self):
        """Test deserialization."""
        trace = NeuralTrace.create(
            trace_type=TraceType.SIGNAL,
            location="node",
            agent_id="agent",
        )
        
        data = trace.to_dict()
        restored = NeuralTrace.from_dict(data)
        
        assert restored.trace_id == trace.trace_id


# =============================================================================
# Test: StigmergicWorkspace
# =============================================================================

class TestStigmergicWorkspace:
    """Tests for StigmergicWorkspace."""
    
    def test_creation_with_defaults(self):
        """Test creating workspace with defaults."""
        ws = StigmergicWorkspace()
        
        assert ws.workspace_id == "default"
    
    def test_creation_with_custom_id(self):
        """Test creating workspace with custom ID."""
        ws = StigmergicWorkspace(workspace_id="test-ws")
        
        assert ws.workspace_id == "test-ws"
    
    def test_deposit(self):
        """Test depositing a trace."""
        ws = StigmergicWorkspace()
        
        trace = ws.deposit(
            trace_type=TraceType.MARKER,
            location="node_a",
            agent_id="agent-001",
        )
        
        assert trace is not None
        assert trace.location == "node_a"
    
    def test_deposit_with_embedding(self):
        """Test depositing trace with embedding."""
        ws = StigmergicWorkspace()
        
        trace = ws.deposit(
            trace_type=TraceType.SEMANTIC,
            location="concept_x",
            agent_id="agent-001",
            embedding=[0.1, 0.2, 0.3],
        )
        
        assert trace.embedding is not None
    
    def test_sense_by_location(self):
        """Test sensing traces at location."""
        ws = StigmergicWorkspace()
        
        ws.deposit(TraceType.MARKER, "loc_a", "agent-001")
        ws.deposit(TraceType.MARKER, "loc_a", "agent-002")
        ws.deposit(TraceType.MARKER, "loc_b", "agent-003")
        
        sensed = ws.sense(location="loc_a")
        
        assert len(sensed) >= 1
    
    def test_sense_by_type(self):
        """Test sensing traces by type."""
        ws = StigmergicWorkspace()
        
        ws.deposit(TraceType.MARKER, "loc", "agent-001")
        ws.deposit(TraceType.SIGNAL, "loc", "agent-002")
        
        sensed = ws.sense(location="loc", trace_type=TraceType.MARKER)
        
        # Should filter by type
        assert all(t.trace_type == TraceType.MARKER for t, _ in sensed)
    
    def test_reinforce(self):
        """Test reinforcing a trace."""
        ws = StigmergicWorkspace()
        
        trace = ws.deposit(TraceType.MARKER, "loc", "agent", strength=0.5)
        original = trace.strength
        
        ws.reinforce(trace.trace_id, signal=0.5)
        
        assert trace.strength >= original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
