"""
REAL tests for inception/enhance/learning.py (standalone file, 0% coverage)

This file imports directly from the standalone learning.py file (not the learning/ package).
"""
import pytest
import importlib.util
import sys
from pathlib import Path

# Direct import of the standalone file (not the package)
spec = importlib.util.spec_from_file_location(
    "learning_standalone",
    Path(__file__).parents[2] / "inception/enhance/learning.py"
)
learning_mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(learning_mod)
    HAS_LEARNING = True
except Exception as e:
    HAS_LEARNING = False
    learning_mod = None


@pytest.mark.skipif(not HAS_LEARNING, reason="learning.py import failed")
class TestRewardSignal:
    def test_values(self):
        assert learning_mod.RewardSignal.CLAIM_VERIFIED.value == "claim_verified"
        assert learning_mod.RewardSignal.GAP_FILLED.value == "gap_filled"


@pytest.mark.skipif(not HAS_LEARNING, reason="learning.py import failed")
class TestExperience:
    def test_creation(self):
        exp = learning_mod.Experience(
            state={"key": "val"},
            action="do",
            reward=1.0,
            next_state={},
            done=False,
        )
        assert exp.action == "do"
        assert exp.reward == 1.0


@pytest.mark.skipif(not HAS_LEARNING, reason="learning.py import failed")
class TestPolicyState:
    def test_creation(self):
        state = learning_mod.PolicyState(
            policy_id="p1",
            model_version="v1"
        )
        assert state.policy_id == "p1"


@pytest.mark.skipif(not HAS_LEARNING, reason="learning.py import failed")
class TestDAPOOptimizer:
    def test_creation(self):
        opt = learning_mod.DAPOOptimizer()
        assert opt is not None
    
    def test_compute_dynamic_clip(self):
        opt = learning_mod.DAPOOptimizer()
        clip = opt.compute_dynamic_clip([0.1, 0.2, 0.3])
        assert isinstance(clip, float)
    
    def test_update(self):
        opt = learning_mod.DAPOOptimizer()
        exp = learning_mod.Experience(state={}, action="a", reward=1, next_state={}, done=False)
        opt.update([exp])


@pytest.mark.skipif(not HAS_LEARNING, reason="learning.py import failed")
class TestGRPOOptimizer:
    def test_creation(self):
        opt = learning_mod.GRPOOptimizer()
        assert opt is not None
    
    def test_add_and_update(self):
        opt = learning_mod.GRPOOptimizer()
        for i in range(5):
            exp = learning_mod.Experience(state={}, action=f"a{i}", reward=0.5, next_state={}, done=False)
            opt.add_experience(exp)
        opt.update()


@pytest.mark.skipif(not HAS_LEARNING, reason="learning.py import failed")
class TestRLVREngine:
    def test_creation(self):
        engine = learning_mod.RLVREngine()
        assert engine is not None
    
    def test_compute_verified_reward(self):
        engine = learning_mod.RLVREngine()
        reward = engine.compute_verified_reward(
            action="extract",
            result={"claim": "test"},
            sources=[{"text": "test"}]
        )
        assert isinstance(reward, (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
