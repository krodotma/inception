"""Tests for tui/app.py (36% coverage)"""
import pytest

try:
    from inception.tui.app import InceptionApp
    HAS_TUI = True
except ImportError:
    HAS_TUI = False


@pytest.mark.skipif(not HAS_TUI, reason="InceptionApp not available")
class TestInceptionApp:
    def test_creation(self):
        app = InceptionApp()
        assert app is not None
    
    def test_has_compose(self):
        app = InceptionApp()
        assert hasattr(app, 'compose')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
