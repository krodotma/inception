"""
REAL tests for surface/stigmergic.py - Actually execute code paths
"""
import pytest
import tempfile
from pathlib import Path

from inception.surface.stigmergic import (
    TraceType, NeuralTrace, StigmergicWorkspace, EmergentTopology
)


class TestTraceType:
    """Test TraceType enum."""
    
    def test_all_types_exist(self):
        """Verify all trace types are defined."""
        assert TraceType.MARKER.value == "marker"
        assert TraceType.SIGNAL.value == "signal"
        assert TraceType.GRADIENT.value == "gradient"
        assert TraceType.STRUCTURAL.value == "structural"
        assert TraceType.SEMANTIC.value == "semantic"
        assert TraceType.CLAIM.value == "claim"
        assert TraceType.HANDOFF.value == "handoff"
        assert TraceType.BROADCAST.value == "broadcast"


class TestNeuralTrace:
    """Test NeuralTrace dataclass - actually exercise methods."""
    
    def test_create_factory(self):
        """Test creating trace via factory method."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="test/location",
            agent_id="agent-1",
            embedding=[0.1, 0.2, 0.3],
            symbols={"key": "value"},
            strength=0.8,
        )
        
        assert trace.trace_id is not None
        assert trace.trace_type == TraceType.MARKER
        assert trace.location == "test/location"
        assert trace.agent_id == "agent-1"
        assert trace.embedding == [0.1, 0.2, 0.3]
        assert trace.embedding_dim == 3
        assert trace.symbols == {"key": "value"}
        assert trace.strength == 0.8
    
    def test_decay(self):
        """Test exponential decay."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="test",
            agent_id="agent-1",
            strength=1.0,
        )
        
        original_strength = trace.strength
        trace.decay(delta_seconds=100)  # Decay for 100 seconds
        
        assert trace.strength < original_strength
        assert trace.strength > 0
    
    def test_reinforce(self):
        """Test reinforcement with momentum."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="test",
            agent_id="agent-1",
            strength=0.5,
        )
        
        original_strength = trace.strength
        trace.reinforce(signal=1.0, visitor_id="agent-2")
        
        assert trace.strength > original_strength
        assert trace.visit_count == 2
        assert "agent-2" in trace.visitors
    
    def test_backward_gradient(self):
        """Test gradient backpropagation."""
        trace = NeuralTrace.create(
            trace_type=TraceType.GRADIENT,
            location="test",
            agent_id="agent-1",
        )
        trace.attention_scores = {"agent-2": 0.8, "agent-3": 0.2}
        
        grads = trace.backward(upstream_gradient=2.0)
        
        assert "agent-2" in grads
        assert "agent-3" in grads
        assert grads["agent-2"] > grads["agent-3"]
    
    def test_compute_attention(self):
        """Test attention computation."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="test",
            agent_id="agent-1",
            embedding=[1.0, 0.0, 0.0],
        )
        
        # Same direction = high attention
        score = trace.compute_attention([1.0, 0.0, 0.0])
        assert score > 0.5
        
        # Orthogonal = zero attention
        score_orth = trace.compute_attention([0.0, 1.0, 0.0])
        assert abs(score_orth) < 0.01
    
    def test_update_embedding(self):
        """Test embedding update via EMA."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="test",
            agent_id="agent-1",
            embedding=[1.0, 0.0, 0.0],
        )
        
        trace.update_embedding([0.0, 1.0, 0.0], blend=0.5)
        
        # Should be blend of both
        assert abs(trace.embedding[0] - 0.5) < 0.01
        assert abs(trace.embedding[1] - 0.5) < 0.01
    
    def test_add_and_match_symbols(self):
        """Test symbolic operations."""
        trace = NeuralTrace.create(
            trace_type=TraceType.SEMANTIC,
            location="test",
            agent_id="agent-1",
        )
        
        trace.add_symbol("type", "entity")
        trace.add_symbol("category", "person")
        
        # Perfect match
        score = trace.match_symbols({"type": "entity"})
        assert score == 1.0
        
        # Partial match
        score = trace.match_symbols({"type": "entity", "category": "place"})
        assert score == 0.5
    
    def test_is_active(self):
        """Test activity check."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="test",
            agent_id="agent-1",
            strength=1.0,
        )
        
        assert trace.is_active() is True
        
        trace.strength = 0.001
        assert trace.is_active() is False
    
    def test_serialization(self):
        """Test to_dict and from_dict."""
        trace = NeuralTrace.create(
            trace_type=TraceType.MARKER,
            location="test",
            agent_id="agent-1",
            embedding=[0.1, 0.2],
            symbols={"key": "val"},
        )
        
        d = trace.to_dict()
        restored = NeuralTrace.from_dict(d)
        
        assert restored.trace_id == trace.trace_id
        assert restored.location == trace.location
        assert restored.embedding == trace.embedding


class TestStigmergicWorkspace:
    """Test StigmergicWorkspace - actually execute deposit/sense/etc."""
    
    def test_deposit_and_sense(self):
        """Test basic deposit and sense."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        # Deposit a trace
        trace = workspace.deposit(
            trace_type=TraceType.MARKER,
            location="location/a",
            agent_id="agent-1",
            embedding=[1.0, 0.0],
            symbols={"type": "test"},
            strength=1.0,
        )
        
        assert trace.trace_id in workspace.trace_index
        
        # Sense it
        results = workspace.sense(location="location", top_k=5)
        
        assert len(results) == 1
        assert results[0][0].trace_id == trace.trace_id
    
    def test_sense_with_attention(self):
        """Test sensing with attention query."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        # Deposit traces with different embeddings
        workspace.deposit(
            trace_type=TraceType.MARKER,
            location="loc",
            agent_id="agent-1",
            embedding=[1.0, 0.0],
            strength=1.0,
        )
        workspace.deposit(
            trace_type=TraceType.MARKER,
            location="loc",
            agent_id="agent-2",
            embedding=[0.0, 1.0],
            strength=1.0,
        )
        
        # Query with [1, 0] embedding
        results = workspace.sense(
            location="loc",
            query_embedding=[1.0, 0.0],
        )
        
        assert len(results) == 2
        # First result should be the matching one
        assert results[0][0].agent_id == "agent-1"
    
    def test_reinforce_trace(self):
        """Test reinforcing an existing trace."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        trace = workspace.deposit(
            trace_type=TraceType.MARKER,
            location="loc",
            agent_id="agent-1",
            strength=0.5,
        )
        
        new_strength = workspace.reinforce(trace.trace_id, signal=1.0)
        
        assert new_strength is not None
        assert new_strength > 0.5
    
    def test_backward_propagation(self):
        """Test gradient backprop through workspace."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        trace = workspace.deposit(
            trace_type=TraceType.GRADIENT,
            location="loc",
            agent_id="agent-1",
        )
        trace.attention_scores = {"agent-2": 0.5}
        
        grads = workspace.backward(trace.trace_id, upstream_gradient=1.0)
        
        assert "agent-2" in grads
    
    def test_structure_modification(self):
        """Test sematectonic stigmergy."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        workspace.modify_structure("config/key", {"value": 42}, "agent-1")
        
        result = workspace.read_structure("config/key")
        assert result == {"value": 42}
    
    def test_claim_and_release(self):
        """Test exclusive access claims."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        # First claim succeeds
        claim = workspace.claim("resource/1", "agent-1")
        assert claim is not None
        
        # Second claim by different agent fails
        claim2 = workspace.claim("resource/1", "agent-2")
        assert claim2 is None
        
        # Release by owner
        released = workspace.release("resource/1", "agent-1")
        assert released is True
    
    def test_handoff(self):
        """Test agent handoff."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        handoff = workspace.handoff(
            location="task/1",
            from_agent="agent-1",
            to_agent="agent-2",
            context_embedding=[0.5, 0.5],
            context_symbols={"status": "in_progress"},
        )
        
        assert handoff.trace_type == TraceType.HANDOFF
        assert handoff.symbols["to_agent"] == "agent-2"
    
    def test_broadcast(self):
        """Test broadcast message."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        msg = workspace.broadcast(
            message_embedding=[0.1, 0.2],
            message_symbols={"event": "alert"},
            agent_id="agent-1",
        )
        
        assert msg.trace_type == TraceType.BROADCAST
        assert msg.location == "__broadcast__"
    
    def test_get_topology(self):
        """Test topology analysis."""
        workspace = StigmergicWorkspace(workspace_id="test")
        
        # Create several traces
        for i in range(5):
            workspace.deposit(
                trace_type=TraceType.MARKER,
                location=f"loc/{i % 2}",
                agent_id=f"agent-{i}",
            )
        
        topology = workspace.get_topology()
        
        assert topology["total_traces"] >= 5
        assert topology["active_locations"] >= 1
    
    def test_event_listener(self):
        """Test event system."""
        workspace = StigmergicWorkspace(workspace_id="test")
        events = []
        
        def listener(event, trace):
            events.append((event, trace.trace_id))
        
        workspace.on(listener)
        
        workspace.deposit(
            trace_type=TraceType.MARKER,
            location="loc",
            agent_id="agent-1",
        )
        
        assert len(events) == 1
        assert events[0][0] == "deposit"
    
    def test_persistence(self):
        """Test saving and loading traces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create workspace with persistence
            ws1 = StigmergicWorkspace(
                workspace_id="test",
                persist_dir=Path(tmpdir),
            )
            
            trace = ws1.deposit(
                trace_type=TraceType.MARKER,
                location="loc",
                agent_id="agent-1",
            )
            trace_id = trace.trace_id
            
            # Load in new workspace
            ws2 = StigmergicWorkspace(
                workspace_id="test",
                persist_dir=Path(tmpdir),
            )
            
            assert trace_id in ws2.trace_index


class TestEmergentTopology:
    """Test emergent topology analyzer."""
    
    def test_analyze_empty(self):
        """Test analysis of empty workspace."""
        workspace = StigmergicWorkspace(workspace_id="test")
        analyzer = EmergentTopology(workspace)
        
        result = analyzer.analyze()
        
        assert result["phase"] == "dormant"
    
    def test_analyze_with_traces(self):
        """Test analysis with traces."""
        workspace = StigmergicWorkspace(workspace_id="test")
        analyzer = EmergentTopology(workspace)
        
        # Add some traces
        for i in range(10):
            workspace.deposit(
                trace_type=TraceType.MARKER,
                location=f"hub/{i % 3}",
                agent_id=f"agent-{i % 4}",
            )
        
        result = analyzer.analyze()
        
        assert result["phase"] in ["exploring", "organizing", "structured"]
        assert result["metrics"]["total_traces"] >= 10
    
    def test_gradient_flow_analysis(self):
        """Test gradient flow detection."""
        workspace = StigmergicWorkspace(workspace_id="test")
        analyzer = EmergentTopology(workspace)
        
        # Create trace with gradient
        trace = workspace.deposit(
            trace_type=TraceType.GRADIENT,
            location="loc",
            agent_id="agent-1",
        )
        trace.strength_gradient = 5.0
        
        result = analyzer.analyze()
        
        assert result["gradient_flow"]["positive"] >= 5.0
    
    def test_visualize(self):
        """Test ASCII visualization."""
        workspace = StigmergicWorkspace(workspace_id="test")
        analyzer = EmergentTopology(workspace)
        
        workspace.deposit(
            trace_type=TraceType.MARKER,
            location="loc",
            agent_id="agent-1",
        )
        
        viz = analyzer.visualize()
        
        assert isinstance(viz, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
