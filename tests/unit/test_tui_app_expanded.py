"""
Expanded unit tests for tui/app.py

Tests for TUI widgets and API client.
"""

import pytest

try:
    from inception.tui.app import (
        InceptionAPI,
        StatCard,
        EntityCard,
        GapCard,
        EntityDetailModal,
        HelpModal,
    )
    HAS_TUI = True
except ImportError:
    HAS_TUI = False


@pytest.mark.skipif(not HAS_TUI, reason="tui module not available")
class TestInceptionAPI:
    """Tests for InceptionAPI client."""
    
    def test_creation_default(self):
        """Test creating with default URL."""
        api = InceptionAPI()
        
        assert api.base_url == "http://localhost:8000"
    
    def test_creation_custom_url(self):
        """Test creating with custom URL."""
        api = InceptionAPI(base_url="http://api.example.com")
        
        assert api.base_url == "http://api.example.com"
    
    def test_has_client(self):
        """Test API has httpx client."""
        api = InceptionAPI()
        
        assert api.client is not None


@pytest.mark.skipif(not HAS_TUI, reason="tui module not available")
class TestStatCard:
    """Tests for StatCard widget."""
    
    def test_creation(self):
        """Test creating stat card."""
        card = StatCard(title="Entities", initial="42")
        
        assert card.title == "Entities"
        assert card.value == "42"
    
    def test_with_color(self):
        """Test with custom color."""
        card = StatCard(title="Test", initial="0", color="green")
        
        assert card.color == "green"


@pytest.mark.skipif(not HAS_TUI, reason="tui module not available")
class TestEntityCard:
    """Tests for EntityCard widget."""
    
    def test_creation(self):
        """Test creating entity card."""
        entity = {"id": "e1", "name": "Apple", "type": "ORG"}
        card = EntityCard(entity=entity)
        
        assert card.entity["id"] == "e1"


@pytest.mark.skipif(not HAS_TUI, reason="tui module not available")
class TestGapCard:
    """Tests for GapCard widget."""
    
    def test_creation(self):
        """Test creating gap card."""
        gap = {"id": "g1", "description": "Missing info", "severity": "HIGH"}
        card = GapCard(gap=gap)
        
        assert card.gap["id"] == "g1"


@pytest.mark.skipif(not HAS_TUI, reason="tui module not available")
class TestEntityDetailModal:
    """Tests for EntityDetailModal screen."""
    
    def test_creation(self):
        """Test creating modal."""
        entity = {"id": "e1", "name": "Test", "type": "entity"}
        modal = EntityDetailModal(entity=entity)
        
        assert modal.entity["id"] == "e1"
        assert modal.claims == []
    
    def test_with_claims(self):
        """Test modal with claims."""
        entity = {"id": "e1", "name": "Test", "type": "entity"}
        claims = [{"id": "c1", "statement": "Claim 1"}]
        modal = EntityDetailModal(entity=entity, claims=claims)
        
        assert len(modal.claims) == 1


@pytest.mark.skipif(not HAS_TUI, reason="tui module not available")
class TestHelpModal:
    """Tests for HelpModal screen."""
    
    def test_has_bindings(self):
        """Test modal has key bindings."""
        assert hasattr(HelpModal, "BINDINGS")
        assert len(HelpModal.BINDINGS) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
