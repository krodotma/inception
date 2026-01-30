"""Tests for enhance/learning/textgrad_optimizer.py (25%)"""
import pytest
from inception.enhance.learning import TextGradOptimizer


class TestTextGradOptimizer:
    def test_creation(self):
        opt = TextGradOptimizer()
        assert opt is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
