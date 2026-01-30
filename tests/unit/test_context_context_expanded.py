"""
Expanded unit tests for context/context.py

Tests for Inception context.
"""

import pytest

try:
    from inception.context.context import (
        InceptionContext,
        ContextDiff,
    )
    HAS_CONTEXT = True
except ImportError:
    HAS_CONTEXT = False


@pytest.mark.skipif(not HAS_CONTEXT, reason="context module not available")
class TestInceptionContext:
    """Tests for InceptionContext."""
    
    def test_creation(self):
        """Test creating context."""
        ctx = InceptionContext(context_id="c1", session_id="s1")
        
        assert ctx is not None
        assert ctx.context_id == "c1"
    
    def test_has_state(self):
        """Test context has state attribute."""
        ctx = InceptionContext(context_id="c2", session_id="s2")
        
        assert hasattr(ctx, "state")
    
    def test_has_entelexis(self):
        """Test context has entelexis attribute."""
        ctx = InceptionContext(context_id="c3", session_id="s3")
        
        assert hasattr(ctx, "entelexis")
    
    def test_activate(self):
        """Test context activate method."""
        ctx = InceptionContext(context_id="c4", session_id="s4")
        
        assert hasattr(ctx, "activate")


@pytest.mark.skipif(not HAS_CONTEXT, reason="context module not available")
class TestContextDiff:
    """Tests for ContextDiff."""
    
    def test_is_class(self):
        """Test ContextDiff is a class."""
        assert isinstance(ContextDiff, type)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
