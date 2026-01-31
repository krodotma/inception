"""
Integration tests for Textual TUI app.
Tests the terminal UI with headless mode.
"""
import pytest

try:
    from textual.app import App
    from textual.pilot import Pilot
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False

try:
    from inception.tui.app import InceptionApp
    HAS_TUI = True
except ImportError:
    HAS_TUI = False


@pytest.mark.skipif(not HAS_TEXTUAL, reason="Textual not available")
class TestTextualIntegration:
    """Test Textual framework basics."""
    
    def test_textual_import(self):
        """Verify Textual imports."""
        from textual.app import App
        from textual.widgets import Static
        assert App is not None
    
    def test_simple_app(self):
        """Test creating a simple app."""
        class SimpleApp(App):
            pass
        app = SimpleApp()
        assert app is not None


@pytest.mark.skipif(not HAS_TUI or not HAS_TEXTUAL, reason="InceptionApp or Textual not available")
class TestInceptionTUIIntegration:
    """Test InceptionApp TUI."""
    
    def test_app_creation(self):
        """Create InceptionApp."""
        app = InceptionApp()
        assert app is not None
    
    def test_app_css(self):
        """Verify app has CSS."""
        app = InceptionApp()
        assert hasattr(app, 'CSS') or hasattr(app, 'CSS_PATH') or hasattr(app, 'STYLESHEETS')
    
    def test_app_bindings(self):
        """Verify app has key bindings."""
        app = InceptionApp()
        assert hasattr(app, 'BINDINGS') or hasattr(app, 'binding')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
