"""
Unit tests for mesh/coordination.py

Tests for agent mesh:
- TopologyType, AgentRole, MeshState: Enums
- MeshAgent, MeshMessage: Data classes
- StarCoordinator, PeerDebateTopology: Coordinators
"""

import pytest
from datetime import datetime

try:
    from inception.mesh.coordination import (
        TopologyType,
        AgentRole,
        MeshState,
        MeshAgent,
        MeshMessage,
        StarCoordinator,
        DebatePosition,
        DebateRound,
        PeerDebateTopology,
    )
    HAS_MESH = True
except ImportError:
    HAS_MESH = False


@pytest.mark.skipif(not HAS_MESH, reason="mesh module not available")
class TestTopologyType:
    """Tests for TopologyType enum."""
    
    def test_values(self):
        """Test topology values."""
        assert TopologyType.STAR.value == "star"
        assert TopologyType.PEER.value == "peer"
        assert TopologyType.DEBATE.value == "debate"


@pytest.mark.skipif(not HAS_MESH, reason="mesh module not available")
class TestAgentRole:
    """Tests for AgentRole enum."""
    
    def test_values(self):
        """Test role values."""
        assert AgentRole.COORDINATOR.value == "coordinator"
        assert AgentRole.WORKER.value == "worker"
        assert AgentRole.SPECIALIST.value == "specialist"


@pytest.mark.skipif(not HAS_MESH, reason="mesh module not available")
class TestMeshState:
    """Tests for MeshState enum."""
    
    def test_values(self):
        """Test state values."""
        assert MeshState.FORMING.value == "forming"
        assert MeshState.ACTIVE.value == "active"
        assert MeshState.CONSENSUS.value == "consensus"


@pytest.mark.skipif(not HAS_MESH, reason="mesh module not available")
class TestMeshAgent:
    """Tests for MeshAgent dataclass."""
    
    def test_creation(self):
        """Test creating agent."""
        agent = MeshAgent(
            id="agent-001",
            name="Test Agent",
            role=AgentRole.WORKER,
        )
        
        assert agent.id == "agent-001"
        assert agent.role == AgentRole.WORKER
    
    def test_with_capabilities(self):
        """Test agent with capabilities."""
        agent = MeshAgent(
            id="agent-002",
            name="Specialist",
            role=AgentRole.SPECIALIST,
            capabilities=["nlp", "vision"],
        )
        
        assert "nlp" in agent.capabilities


@pytest.mark.skipif(not HAS_MESH, reason="mesh module not available")
class TestMeshMessage:
    """Tests for MeshMessage dataclass."""
    
    def test_creation(self):
        """Test creating message."""
        msg = MeshMessage(
            id="msg-001",
            from_agent_id="agent-001",
            to_agent_id="agent-002",
            message_type="task",
            payload={"data": "test"},
        )
        
        assert msg.from_agent_id == "agent-001"
        assert msg.message_type == "task"


@pytest.mark.skipif(not HAS_MESH, reason="mesh module not available")
class TestStarCoordinator:
    """Tests for StarCoordinator."""
    
    def test_creation(self):
        """Test creating coordinator."""
        coord = StarCoordinator("coord-001", "Main Coordinator")
        
        assert coord.coordinator.id == "coord-001"
    
    def test_add_worker(self):
        """Test adding worker."""
        coord = StarCoordinator("coord-001", "Main")
        worker = MeshAgent(id="worker-001", name="Worker", role=AgentRole.WORKER)
        
        coord.add_worker(worker)
        
        assert "worker-001" in coord.workers
    
    def test_get_status(self):
        """Test getting status."""
        coord = StarCoordinator("coord-001", "Main")
        
        status = coord.get_status()
        
        assert isinstance(status, dict)
        assert "total_workers" in status  # API uses 'total_workers' not 'worker_count'


@pytest.mark.skipif(not HAS_MESH, reason="mesh module not available")
class TestDebatePosition:
    """Tests for DebatePosition enum."""
    
    def test_values(self):
        """Test position values."""
        assert DebatePosition.PROPOSER.value == "proposer"
        assert DebatePosition.OPPONENT.value == "opponent"


@pytest.mark.skipif(not HAS_MESH, reason="mesh module not available")
class TestPeerDebateTopology:
    """Tests for PeerDebateTopology."""
    
    def test_creation(self):
        """Test creating debate."""
        debate = PeerDebateTopology("Should AI be regulated?")
        
        assert debate.topic == "Should AI be regulated?"
    
    def test_add_debater(self):
        """Test adding debater."""
        debate = PeerDebateTopology("Topic")
        agent = MeshAgent(id="d1", name="Debater 1", role=AgentRole.SPECIALIST)
        
        debate.add_debater(agent, DebatePosition.PROPOSER)
        
        assert "d1" in debate.agents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
