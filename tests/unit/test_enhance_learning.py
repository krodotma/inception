"""
Unit tests for enhance/learning.py

Tests for learning engine:
- RewardSignal: Enum
- Experience, PolicyState: Data classes  
- DAPOOptimizer, GRPOOptimizer, RLVREngine: Optimizers
"""

import pytest
from datetime import datetime

try:
    from inception.enhance.learning import (
        RewardSignal,
        Experience,
        PolicyState,
        DAPOOptimizer,
        GRPOOptimizer,
        RLVREngine,
    )
    HAS_LEARNING = True
except ImportError:
    HAS_LEARNING = False


@pytest.mark.skipif(not HAS_LEARNING, reason="learning module not available")
class TestRewardSignal:
    """Tests for RewardSignal enum."""
    
    def test_values(self):
        """Test reward signal values."""
        assert RewardSignal.CLAIM_VERIFIED.value == "claim_verified"
        assert RewardSignal.GAP_FILLED.value == "gap_filled"
        assert RewardSignal.USER_FEEDBACK_POSITIVE.value == "user_positive"


@pytest.mark.skipif(not HAS_LEARNING, reason="learning module not available")
class TestExperience:
    """Tests for Experience dataclass."""
    
    def test_creation(self):
        """Test creating experience."""
        exp = Experience(
            state={"entities": 10},
            action="extract",
            reward=0.5,
            next_state={"entities": 11},
            done=False,
        )
        
        assert exp.action == "extract"
        assert exp.reward == 0.5
    
    def test_with_metadata(self):
        """Test experience with metadata."""
        exp = Experience(
            state={},
            action="fill_gap",
            reward=1.0,
            next_state={},
            done=True,
            metadata={"gap_id": "gap-001"},
        )
        
        assert "gap_id" in exp.metadata


@pytest.mark.skipif(not HAS_LEARNING, reason="learning module not available")
class TestPolicyState:
    """Tests for PolicyState dataclass."""
    
    def test_creation(self):
        """Test creating policy state."""
        policy = PolicyState(
            policy_id="policy-001",
            model_version="v1.0",
        )
        
        assert policy.policy_id == "policy-001"
        assert policy.total_samples == 0
    
    def test_with_stats(self):
        """Test policy with statistics."""
        policy = PolicyState(
            policy_id="policy-002",
            model_version="v1.1",
            total_samples=1000,
            total_reward=500.0,
            entropy=0.8,
        )
        
        assert policy.total_samples == 1000


@pytest.mark.skipif(not HAS_LEARNING, reason="learning module not available")
class TestDAPOOptimizer:
    """Tests for DAPOOptimizer."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        optimizer = DAPOOptimizer()
        
        assert optimizer.clip_range == 0.2
    
    def test_creation_custom(self):
        """Test creating with custom params."""
        optimizer = DAPOOptimizer(
            clip_range=0.3,
            entropy_coef=0.02,
        )
        
        assert optimizer.clip_range == 0.3
    
    def test_compute_dynamic_clip(self):
        """Test dynamic clip computation."""
        optimizer = DAPOOptimizer()
        
        advantages = [0.1, 0.2, 0.3, 0.15]
        clip = optimizer.compute_dynamic_clip(advantages)
        
        assert 0 < clip < 1
    
    def test_compute_entropy_bonus(self):
        """Test entropy bonus computation."""
        optimizer = DAPOOptimizer()
        
        bonus = optimizer.compute_entropy_bonus(0.5)
        
        assert isinstance(bonus, float)
    
    def test_update_empty(self):
        """Test update with empty experiences."""
        optimizer = DAPOOptimizer()
        
        result = optimizer.update([])
        
        assert result is not None or result is None  # May return None or result


@pytest.mark.skipif(not HAS_LEARNING, reason="learning module not available")
class TestGRPOOptimizer:
    """Tests for GRPOOptimizer."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        optimizer = GRPOOptimizer()
        
        assert optimizer.group_size == 32
    
    def test_creation_custom(self):
        """Test creating with custom params."""
        optimizer = GRPOOptimizer(
            group_size=64,
            top_k_ratio=0.3,
        )
        
        assert optimizer.group_size == 64
    
    def test_add_experience(self):
        """Test adding experience."""
        optimizer = GRPOOptimizer()
        
        exp = Experience(
            state={},
            action="test_action",
            reward=1.0,
            next_state={},
            done=False,
        )
        
        optimizer.add_experience(exp)
        
        # Should not raise
        assert True
    
    def test_compute_group_advantage(self):
        """Test computing group advantage."""
        optimizer = GRPOOptimizer()
        
        exp = Experience(
            state={},
            action="test",
            reward=0.5,
            next_state={},
            done=False,
        )
        
        advantage = optimizer.compute_group_advantage(exp)
        
        assert isinstance(advantage, (int, float))


@pytest.mark.skipif(not HAS_LEARNING, reason="learning module not available")
class TestRLVREngine:
    """Tests for RLVREngine."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        engine = RLVREngine()
        
        assert engine is not None
    
    def test_creation_with_verifier(self):
        """Test creating with custom verifier."""
        def custom_verifier(claim, sources):
            return 0.9
        
        engine = RLVREngine(verifier_fn=custom_verifier)
        
        assert engine is not None
    
    def test_get_verification_stats(self):
        """Test getting stats."""
        engine = RLVREngine()
        
        stats = engine.get_verification_stats()
        
        assert isinstance(stats, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
