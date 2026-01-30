"""Tests for context/context.py (94%) to push toward 100%"""
import pytest
from inception.context.context import InceptionContext


class TestInceptionContextDeep:
    def test_creation(self):
        ctx = InceptionContext(context_id="test-ctx", session_id="test-session")
        assert ctx.context_id == "test-ctx"
    
    def test_creation_minimal(self):
        ctx = InceptionContext(context_id="ctx1", session_id="sess1")
        assert ctx is not None
    
    def test_session_id(self):
        ctx = InceptionContext(context_id="ctx", session_id="my-session")
        assert ctx.session_id == "my-session"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
