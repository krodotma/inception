"""
Deep tests for tui/app.py (36%) - Widget coverage
"""
import pytest

try:
    from inception.tui.app import InceptionAPI, StatCard
    HAS_TUI = True
except ImportError:
    HAS_TUI = False

@pytest.mark.skipif(not HAS_TUI, reason="tui not available")
class TestInceptionAPIDeep:
    def test_has_async_methods(self):
        api = InceptionAPI()
        assert hasattr(api, "get_stats")
        assert hasattr(api, "get_entities")
        assert hasattr(api, "get_claims")
    
    def test_has_close(self):
        api = InceptionAPI()
        assert hasattr(api, "close")


@pytest.mark.skipif(not HAS_TUI, reason="tui not available")
class TestStatCardDeep:
    def test_render_method(self):
        card = StatCard(title="Test", initial="42")
        assert hasattr(card, "render")
    
    def test_value_reactive(self):
        card = StatCard(title="Test", initial="0")
        card.value = "100"
        assert card.value == "100"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
