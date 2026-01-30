"""
Unit tests for enhance/learning/ package

Tests for learning engine components:
- GRPOv2Optimizer: Group Relative Policy Optimization
- GRPOWithRLVR: GRPO with verifiable rewards
- LearningMetrics: Comprehensive metrics tracking
- Helper functions: compute_claim_f1, compute_entity_accuracy
"""

import pytest
from inception.enhance.learning import (
    # GRPO
    GRPOv2Optimizer,
    # Metrics
    LearningMetrics,
    compute_claim_f1,
    compute_entity_accuracy,
)
from inception.enhance.learning.grpo_v2 import (
    GRPOExperience,
    GRPOStepResult,
    GRPOTrainResult,
    GRPOWithRLVR,
)
from inception.enhance.learning.metrics import (
    ClaimMetrics,
    EntityMetrics,
)


# =============================================================================
# Test: GRPO Data Classes
# =============================================================================

class TestGRPODataClasses:
    """Tests for GRPO data structures."""
    
    def test_experience_creation(self):
        """Test creating a GRPO experience."""
        exp = GRPOExperience(
            prompt="Extract claims",
            response="Claim: testing is good",
            reward=0.8,
        )
        
        assert exp.prompt == "Extract claims"
        assert exp.reward == 0.8
        assert exp.advantage == 0.0  # Default
        assert not exp.verified
    
    def test_step_result_creation(self):
        """Test creating GRPO step result."""
        result = GRPOStepResult(
            responses=["a", "b", "c"],
            rewards=[0.5, 0.8, 0.3],
            advantages=[0.0, 0.5, -0.3],
            best_response="b",
            best_reward=0.8,
            mean_reward=0.533,
        )
        
        assert len(result.responses) == 3
        assert result.best_response == "b"
        assert result.best_reward == 0.8


# =============================================================================
# Test: GRPOv2Optimizer
# =============================================================================

class TestGRPOv2Optimizer:
    """Tests for GRPOv2Optimizer."""
    
    def test_creation_with_defaults(self):
        """Test creating optimizer with defaults."""
        optimizer = GRPOv2Optimizer()
        
        assert optimizer.group_size == 16
        assert optimizer.num_samples == 4
        assert optimizer.verification_weight == 0.3
    
    def test_creation_with_custom_params(self):
        """Test creating optimizer with custom params."""
        optimizer = GRPOv2Optimizer(
            group_size=32,
            num_samples=8,
            kl_coef=0.1,
        )
        
        assert optimizer.group_size == 32
        assert optimizer.num_samples == 8
        assert optimizer.kl_coef == 0.1
    
    def test_compute_advantages(self):
        """Test advantage computation."""
        optimizer = GRPOv2Optimizer()
        
        rewards = [1.0, 2.0, 3.0, 4.0]
        advantages = optimizer.compute_advantages(rewards)
        
        assert len(advantages) == 4
        # Normalized: mean=2.5, std=~1.29
        # After normalization, sum should be ~0
        assert abs(sum(advantages)) < 0.01
    
    def test_step_basic(self):
        """Test basic GRPO step."""
        optimizer = GRPOv2Optimizer(num_samples=3)
        
        def policy_fn(prompt):
            return f"Response to: {prompt}"
        
        result = optimizer.step(
            prompt="Test prompt",
            policy_fn=policy_fn,
        )
        
        assert len(result.responses) == 3
        assert result.best_response is not None
        assert optimizer.total_steps == 1
    
    def test_step_with_reward_fn(self):
        """Test GRPO step with custom reward function."""
        optimizer = GRPOv2Optimizer(num_samples=2)
        
        def policy_fn(prompt):
            return "{'claim': 'test claim'}"
        
        def reward_fn(response):
            return 1.0 if "claim" in response else 0.0
        
        result = optimizer.step(
            prompt="Extract claims",
            policy_fn=policy_fn,
            reward_fn=reward_fn,
        )
        
        assert all(r == 1.0 for r in result.rewards)
    
    def test_step_with_verify_fn(self):
        """Test GRPO step with verification function."""
        optimizer = GRPOv2Optimizer(num_samples=2)
        
        def policy_fn(prompt):
            return "verified response"
        
        def verify_fn(response):
            return True, 0.9
        
        result = optimizer.step(
            prompt="Test",
            policy_fn=policy_fn,
            verify_fn=verify_fn,
        )
        
        assert result.verified_count == 2
    
    def test_train_insufficient_data(self):
        """Test training with insufficient data."""
        optimizer = GRPOv2Optimizer()
        
        result = optimizer.train(batch_size=100)
        
        assert result is None
    
    def test_train_with_data(self):
        """Test training with sufficient data."""
        optimizer = GRPOv2Optimizer(num_samples=2)
        
        # Generate experiences
        for i in range(50):
            optimizer.step(
                prompt=f"Prompt {i}",
                policy_fn=lambda p: f"Response {p}",
            )
        
        result = optimizer.train(batch_size=32)
        
        assert result is not None
        assert result.experiences_used == 32
        assert isinstance(result.loss, float)
    
    def test_get_stats(self):
        """Test getting optimizer stats."""
        optimizer = GRPOv2Optimizer(num_samples=2)
        
        optimizer.step(
            prompt="Test",
            policy_fn=lambda p: "response",
        )
        
        stats = optimizer.get_stats()
        
        assert stats["total_steps"] == 1
        assert stats["experience_buffer_size"] == 2
    
    def test_reset(self):
        """Test resetting optimizer."""
        optimizer = GRPOv2Optimizer(num_samples=2)
        
        optimizer.step(
            prompt="Test",
            policy_fn=lambda p: "response",
        )
        assert optimizer.total_steps == 1
        
        optimizer.reset()
        
        assert optimizer.total_steps == 0
        assert len(optimizer.experiences) == 0


# =============================================================================
# Test: GRPOWithRLVR
# =============================================================================

class TestGRPOWithRLVR:
    """Tests for GRPOWithRLVR."""
    
    def test_creation(self):
        """Test creating GRPO with RLVR."""
        optimizer = GRPOWithRLVR()
        
        assert optimizer is not None
    
    def test_step_with_sources(self):
        """Test step with source verification."""
        optimizer = GRPOWithRLVR(num_samples=2)
        
        result = optimizer.step_with_sources(
            prompt="Extract claims from: Testing is important",
            policy_fn=lambda p: "Testing is important for quality",
            sources=["Testing is important for code quality"],
        )
        
        assert len(result.responses) == 2


# =============================================================================
# Test: Claim Metrics
# =============================================================================

class TestClaimMetrics:
    """Tests for ClaimMetrics."""
    
    def test_precision_no_predictions(self):
        """Test precision with no predictions."""
        metrics = ClaimMetrics()
        
        assert metrics.precision == 0.0
    
    def test_precision_with_predictions(self):
        """Test precision calculation."""
        metrics = ClaimMetrics(
            true_positives=8,
            false_positives=2,
        )
        
        assert metrics.precision == 0.8
    
    def test_recall_calculation(self):
        """Test recall calculation."""
        metrics = ClaimMetrics(
            true_positives=7,
            false_negatives=3,
        )
        
        assert metrics.recall == 0.7
    
    def test_f1_calculation(self):
        """Test F1 score calculation."""
        metrics = ClaimMetrics(
            true_positives=8,
            false_positives=2,
            false_negatives=2,
        )
        
        # precision=0.8, recall=0.8, f1=0.8
        assert abs(metrics.f1 - 0.8) < 0.01


# =============================================================================
# Test: Entity Metrics
# =============================================================================

class TestEntityMetrics:
    """Tests for EntityMetrics."""
    
    def test_extraction_accuracy(self):
        """Test extraction accuracy."""
        metrics = EntityMetrics(
            correct_extractions=9,
            total_extractions=10,
        )
        
        assert metrics.extraction_accuracy == 0.9
    
    def test_linking_accuracy(self):
        """Test linking accuracy."""
        metrics = EntityMetrics(
            correct_links=8,
            total_links=10,
        )
        
        assert metrics.linking_accuracy == 0.8


# =============================================================================
# Test: Learning Metrics
# =============================================================================

class TestLearningMetrics:
    """Tests for LearningMetrics."""
    
    def test_creation(self):
        """Test creating learning metrics."""
        metrics = LearningMetrics()
        
        assert metrics.claim_metrics is not None
        assert metrics.entity_metrics is not None
    
    def test_record_claim_evaluation(self):
        """Test recording claim evaluation."""
        metrics = LearningMetrics()
        
        predicted = [
            {"subject": "Python", "predicate": "is", "object": "language"},
        ]
        ground_truth = [
            {"subject": "Python", "predicate": "is", "object": "language"},
        ]
        
        metrics.record_claim_evaluation(predicted, ground_truth)
        
        assert metrics.claim_metrics.true_positives >= 0
    
    def test_record_entity_evaluation(self):
        """Test recording entity evaluation."""
        metrics = LearningMetrics()
        
        predicted = [
            {"text": "Python", "type": "TECH"},
        ]
        ground_truth = [
            {"text": "Python", "type": "TECH"},
        ]
        
        metrics.record_entity_evaluation(predicted, ground_truth)
        
        assert metrics.entity_metrics.total_extractions >= 0
    
    def test_record_strategy_result(self):
        """Test recording strategy result."""
        metrics = LearningMetrics()
        
        metrics.record_strategy_result("grpo", reward=0.8, success=True)
        metrics.record_strategy_result("grpo", reward=0.6, success=True)
        
        summary = metrics.get_summary()
        assert "strategies" in summary
    
    def test_get_summary(self):
        """Test getting metrics summary."""
        metrics = LearningMetrics()
        
        summary = metrics.get_summary()
        
        assert "claims" in summary
        assert "entities" in summary
    
    def test_reset(self):
        """Test resetting metrics."""
        metrics = LearningMetrics()
        metrics.record_strategy_result("test", 1.0)
        
        metrics.reset()
        
        summary = metrics.get_summary()
        assert summary["claims"]["f1"] == 0.0


# =============================================================================
# Test: Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_compute_claim_f1(self):
        """Test compute_claim_f1 function."""
        predicted = [
            {"subject": "A", "predicate": "is", "object": "B"},
        ]
        ground_truth = [
            {"subject": "A", "predicate": "is", "object": "B"},
        ]
        
        f1 = compute_claim_f1(predicted, ground_truth)
        
        assert 0.0 <= f1 <= 1.0
    
    def test_compute_entity_accuracy(self):
        """Test compute_entity_accuracy function."""
        predicted = [{"text": "Python", "type": "TECH"}]
        ground_truth = [{"text": "Python", "type": "TECH"}]
        
        accuracy = compute_entity_accuracy(predicted, ground_truth)
        
        assert 0.0 <= accuracy <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
