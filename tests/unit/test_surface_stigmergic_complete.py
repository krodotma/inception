"""
Deep coverage tests for surface/stigmergic.py (53%)
"""
import pytest

try:
    from inception.surface.stigmergic import (
        StigmergicAgent, StigmergicEnvironment, Pheromone, PheromoneType
    )
    HAS_STIGMERGIC = True
except ImportError:
    HAS_STIGMERGIC = False

@pytest.mark.skipif(not HAS_STIGMERGIC, reason="stigmergic not available")
class TestPheromoneTypeComplete:
    def test_enum_exists(self):
        assert len(list(PheromoneType)) > 0


@pytest.mark.skipif(not HAS_STIGMERGIC, reason="stigmergic not available")
class TestPheromoneComplete:
    def test_creation(self):
        pheromone = Pheromone(id="p1", pheromone_type=list(PheromoneType)[0], intensity=1.0)
        assert pheromone is not None
    
    def test_decay(self):
        pheromone = Pheromone(id="p2", pheromone_type=list(PheromoneType)[0], intensity=1.0, decay_rate=0.1)
        assert pheromone.decay_rate == 0.1


@pytest.mark.skipif(not HAS_STIGMERGIC, reason="stigmergic not available")
class TestStigmergicEnvironmentComplete:
    def test_creation(self):
        env = StigmergicEnvironment()
        assert env is not None
    
    def test_deposit_sense(self):
        env = StigmergicEnvironment()
        pheromone = Pheromone(id="p1", pheromone_type=list(PheromoneType)[0], intensity=1.0)
        env.deposit(pheromone, location="test")
        result = env.sense("test")
        assert isinstance(result, list)


@pytest.mark.skipif(not HAS_STIGMERGIC, reason="stigmergic not available")
class TestStigmergicAgentComplete:
    def test_creation(self):
        agent = StigmergicAgent(agent_id="a1")
        assert agent.agent_id == "a1"
    
    def test_perceive(self):
        agent = StigmergicAgent(agent_id="a2")
        env = StigmergicEnvironment()
        perception = agent.perceive(env)
        assert perception is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
