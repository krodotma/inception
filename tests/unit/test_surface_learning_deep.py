"""Tests for surface/learning.py (73%)"""
import pytest

try:
    from inception.surface.learning import LearningEngine, LearningConfig
    HAS_LEARNING = True
except ImportError:
    HAS_LEARNING = False


@pytest.mark.skipif(not HAS_LEARNING, reason="LearningEngine not available")
class TestLearningEngine:
    def test_creation(self):
        engine = LearningEngine()
        assert engine is not None


@pytest.mark.skipif(not HAS_LEARNING, reason="LearningConfig not available")
class TestLearningConfig:
    def test_creation(self):
        config = LearningConfig()
        assert config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
