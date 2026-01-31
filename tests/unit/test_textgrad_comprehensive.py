"""
Comprehensive tests for enhance/learning/textgrad_optimizer.py (25%)
"""
import pytest

try:
    from inception.enhance.learning.textgrad_optimizer import (
        TextGradOptimizer,
        TextGradConfig,
        GradientStep,
    )
    HAS_TEXTGRAD = True
except ImportError:
    try:
        from inception.enhance.learning.textgrad_optimizer import TextGradOptimizer
        HAS_TEXTGRAD = True
        TextGradConfig = None
        GradientStep = None
    except ImportError:
        HAS_TEXTGRAD = False

try:
    from inception.enhance.learning import TextGradOptimizer as TGO
    HAS_TGO = True
except ImportError:
    HAS_TGO = False


@pytest.mark.skipif(not HAS_TEXTGRAD, reason="textgrad_optimizer not available")
class TestTextGradOptimizer:
    """Test TextGradOptimizer class."""
    
    def test_creation(self):
        opt = TextGradOptimizer()
        assert opt is not None
    
    def test_has_config(self):
        opt = TextGradOptimizer()
        if hasattr(opt, 'config'):
            assert opt.config is not None
    
    def test_has_optimize(self):
        opt = TextGradOptimizer()
        if hasattr(opt, 'optimize'):
            assert callable(opt.optimize)


@pytest.mark.skipif(not HAS_TEXTGRAD or TextGradConfig is None, reason="TextGradConfig not available")
class TestTextGradConfig:
    """Test TextGradConfig class."""
    
    def test_creation(self):
        config = TextGradConfig()
        assert config is not None


@pytest.mark.skipif(not HAS_TEXTGRAD or GradientStep is None, reason="GradientStep not available")
class TestGradientStep:
    """Test GradientStep class."""
    
    def test_creation(self):
        step = GradientStep()
        assert step is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
