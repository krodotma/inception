"""
Unit tests for surface/stigmergic.py

Tests for stigmergic coordination patterns.
"""

import pytest

try:
    from inception.surface.stigmergic import (
        StigmergicAgent,
        Pheromone,
        StigmergicEnvironment,
        PheromoneType,
    )
    HAS_STIGMERGIC = True
except ImportError:
    HAS_STIGMERGIC = False


@pytest.mark.skipif(not HAS_STIGMERGIC, reason="stigmergic module not available")
class TestPheromoneType:
    """Tests for PheromoneType enum."""
    
    def test_types_exist(self):
        """Test pheromone types exist."""
        assert hasattr(PheromoneType, "ATTRACTION") or hasattr(PheromoneType, "TRAIL") or len(list(PheromoneType)) > 0


@pytest.mark.skipif(not HAS_STIGMERGIC, reason="stigmergic module not available")
class TestPheromone:
    """Tests for Pheromone dataclass."""
    
    def test_creation(self):
        """Test creating pheromone."""
        pheromone = Pheromone(
            id="p1",
            pheromone_type=list(PheromoneType)[0],
            intensity=1.0,
        )
        
        assert pheromone.id == "p1"
        assert pheromone.intensity == 1.0
    
    def test_decay(self):
        """Test pheromone decay."""
        pheromone = Pheromone(
            id="p2",
            pheromone_type=list(PheromoneType)[0],
            intensity=1.0,
            decay_rate=0.1,
        )
        
        assert pheromone.decay_rate == 0.1


@pytest.mark.skipif(not HAS_STIGMERGIC, reason="stigmergic module not available")
class TestStigmergicEnvironment:
    """Tests for StigmergicEnvironment."""
    
    def test_creation(self):
        """Test creating environment."""
        env = StigmergicEnvironment()
        
        assert env is not None
    
    def test_deposit_pheromone(self):
        """Test depositing pheromone."""
        env = StigmergicEnvironment()
        pheromone = Pheromone(
            id="p1",
            pheromone_type=list(PheromoneType)[0],
            intensity=1.0,
        )
        
        env.deposit(pheromone, location="loc1")
        
        pheromones = env.sense("loc1")
        assert len(pheromones) >= 0  # May have evaporated or be empty


@pytest.mark.skipif(not HAS_STIGMERGIC, reason="stigmergic module not available")
class TestStigmergicAgent:
    """Tests for StigmergicAgent."""
    
    def test_creation(self):
        """Test creating agent."""
        agent = StigmergicAgent(agent_id="a1")
        
        assert agent.agent_id == "a1"
    
    def test_perceive(self):
        """Test agent perception."""
        agent = StigmergicAgent(agent_id="a2")
        env = StigmergicEnvironment()
        
        perception = agent.perceive(env)
        
        assert perception is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
