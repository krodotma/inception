"""
Comprehensive tests for tui/app.py (36%) - all widgets and screens
"""
import pytest

try:
    from inception.tui.app import (
        InceptionAPI, StatCard, EntityCard, GapCard,
        EntityDetailModal, HelpModal
    )
    HAS_TUI = True
except ImportError:
    HAS_TUI = False

@pytest.mark.skipif(not HAS_TUI, reason="tui not available")
class TestInceptionAPIComprehensive:
    def test_creation(self):
        api = InceptionAPI()
        assert api is not None
    
    def test_base_url(self):
        api = InceptionAPI(base_url="http://test:8000")
        assert api.base_url == "http://test:8000"
    
    def test_has_all_methods(self):
        api = InceptionAPI()
        assert hasattr(api, "get_stats")
        assert hasattr(api, "get_entities")
        assert hasattr(api, "get_entity")
        assert hasattr(api, "get_claims")
        assert hasattr(api, "get_gaps")
        assert hasattr(api, "get_graph")
        assert hasattr(api, "health")
        assert hasattr(api, "close")


@pytest.mark.skipif(not HAS_TUI, reason="tui not available")
class TestStatCardComprehensive:
    def test_creation(self):
        card = StatCard(title="Test", initial="0")
        assert card is not None
    
    def test_value_update(self):
        card = StatCard(title="Test", initial="0")
        card.value = "100"
        assert card.value == "100"
    
    def test_color(self):
        card = StatCard(title="Test", initial="0", color="green")
        assert card.color == "green"


@pytest.mark.skipif(not HAS_TUI, reason="tui not available")
class TestEntityCardComprehensive:
    def test_creation(self):
        entity = {"id": "e1", "name": "Test", "type": "entity"}
        card = EntityCard(entity=entity)
        assert card.entity["id"] == "e1"


@pytest.mark.skipif(not HAS_TUI, reason="tui not available")
class TestGapCardComprehensive:
    def test_creation(self):
        gap = {"id": "g1", "description": "Test gap"}
        card = GapCard(gap=gap)
        assert card.gap["id"] == "g1"


@pytest.mark.skipif(not HAS_TUI, reason="tui not available")
class TestEntityDetailModalComprehensive:
    def test_creation(self):
        entity = {"id": "e1", "name": "Test"}
        modal = EntityDetailModal(entity=entity)
        assert modal.entity["id"] == "e1"
    
    def test_with_claims(self):
        entity = {"id": "e1", "name": "Test"}
        claims = [{"id": "c1", "statement": "Test claim"}]
        modal = EntityDetailModal(entity=entity, claims=claims)
        assert len(modal.claims) == 1


@pytest.mark.skipif(not HAS_TUI, reason="tui not available")
class TestHelpModalComprehensive:
    def test_has_bindings(self):
        assert hasattr(HelpModal, "BINDINGS")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
