"""Deep TUI tests using Textual testing patterns"""
import pytest

try:
    from textual.app import App
    from inception.tui.app import InceptionApp
    HAS_TUI = True
except ImportError:
    HAS_TUI = False


@pytest.mark.skipif(not HAS_TUI, reason="TUI not available")
class TestInceptionAppDeep:
    def test_app_creation(self):
        app = InceptionApp()
        assert app is not None
        assert isinstance(app, App)
    
    def test_app_css(self):
        app = InceptionApp()
        # Check CSS is defined
        assert hasattr(app, 'CSS') or hasattr(app, 'CSS_PATH')
    
    def test_app_bindings(self):
        app = InceptionApp()
        if hasattr(app, 'BINDINGS'):
            assert isinstance(app.BINDINGS, (list, tuple))
    
    def test_compose_method(self):
        app = InceptionApp()
        assert hasattr(app, 'compose')
        assert callable(app.compose)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
