"""Tests for enhance/learning/compound_optimizer.py (33%)"""
import pytest
from inception.enhance.learning import CompoundOptimizer, LearningMetrics


class TestCompoundOptimizer:
    def test_creation(self):
        opt = CompoundOptimizer()
        assert opt is not None
    
    def test_has_optimize_method(self):
        opt = CompoundOptimizer()
        assert hasattr(opt, 'optimize') or hasattr(opt, 'step')


class TestLearningMetrics:
    def test_creation(self):
        metrics = LearningMetrics()
        assert metrics is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
