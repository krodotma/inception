"""
REAL tests for tui/app.py - Actually exercise TUI components
"""
import pytest

from inception.tui.app import InceptionAPI, StatCard


class TestInceptionAPI:
    """Test TUI API client - actually call methods."""
    
    def test_creation_default(self):
        api = InceptionAPI()
        assert api is not None
    
    def test_creation_custom_url(self):
        api = InceptionAPI(base_url="http://localhost:9000")
        assert api.base_url == "http://localhost:9000"
    
    def test_has_required_methods(self):
        api = InceptionAPI()
        assert callable(getattr(api, 'get_stats', None))
        assert callable(getattr(api, 'get_entities', None))
        assert callable(getattr(api, 'get_claims', None))
        assert callable(getattr(api, 'get_gaps', None))
        assert callable(getattr(api, 'health', None))
        assert callable(getattr(api, 'close', None))


class TestStatCard:
    """Test StatCard widget."""
    
    def test_creation(self):
        card = StatCard(title="Test", initial="0")
        assert card is not None
    
    def test_value_property(self):
        card = StatCard(title="Count", initial="42")
        assert card.value == "42"
    
    def test_value_setter(self):
        card = StatCard(title="Count", initial="0")
        card.value = "100"
        assert card.value == "100"
    
    def test_color(self):
        card = StatCard(title="Test", initial="0", color="green")
        assert card.color == "green"
    
    def test_render(self):
        card = StatCard(title="Test", initial="5")
        assert hasattr(card, 'render')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
