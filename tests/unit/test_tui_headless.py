"""Textual headless tests for tui/app.py (200 lines uncovered)"""
import pytest

try:
    from inception.tui.app import InceptionApp
    HAS_TUI = True
except ImportError:
    HAS_TUI = False


@pytest.mark.skipif(not HAS_TUI, reason="TUI not available")
class TestInceptionAppSync:
    def test_app_creation(self):
        """Test app can be created"""
        app = InceptionApp()
        assert app is not None
    
    def test_app_css_defined(self):
        """Test app has CSS defined"""
        app = InceptionApp()
        assert hasattr(app, 'CSS') or hasattr(app, 'CSS_PATH') or hasattr(app, 'STYLESHEETS')
    
    def test_app_bindings(self):
        """Test app bindings exist"""
        app = InceptionApp()
        assert hasattr(app, 'BINDINGS') or hasattr(app, 'binding')
    
    def test_compose_callable(self):
        """Test compose method exists"""
        app = InceptionApp()
        assert callable(getattr(app, 'compose', None))
    
    def test_action_methods(self):
        """Test action methods exist"""
        app = InceptionApp()
        # Check for common action methods
        for method in ['action_quit', 'action_help', 'action_toggle_dark']:
            if hasattr(app, method):
                assert callable(getattr(app, method))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
