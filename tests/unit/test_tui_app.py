"""
Unit tests for tui/app.py

Tests for TUI components that can be tested without full app:
- InceptionAPI: HTTP client
- Data classes and widgets
"""

import pytest
from unittest.mock import AsyncMock, patch


# =============================================================================
# Test: InceptionAPI (without network)
# =============================================================================

class TestInceptionAPI:
    """Tests for InceptionAPI client."""
    
    def test_creation_with_defaults(self):
        """Test creating API client with defaults."""
        from inception.tui.app import InceptionAPI
        
        api = InceptionAPI()
        
        assert api.base_url == "http://localhost:8000"
    
    def test_creation_with_custom_url(self):
        """Test creating API with custom URL."""
        from inception.tui.app import InceptionAPI
        
        api = InceptionAPI(base_url="http://api.example.com")
        
        assert api.base_url == "http://api.example.com"


# =============================================================================
# Test: Widgets (testing their render methods)
# =============================================================================

class TestStatCard:
    """Tests for StatCard widget."""
    
    def test_creation(self):
        """Test creating a stat card."""
        from inception.tui.app import StatCard
        
        card = StatCard(title="Test", initial="42", color="blue")
        
        assert card.title == "Test"
        assert card.value == "42"
        assert card.color == "blue"


class TestEntityCard:
    """Tests for EntityCard widget."""
    
    def test_creation(self):
        """Test creating an entity card."""
        from inception.tui.app import EntityCard
        
        entity = {"id": "ent-001", "name": "Test Entity", "type": "person"}
        card = EntityCard(entity=entity)
        
        assert card.entity["id"] == "ent-001"


class TestGapCard:
    """Tests for GapCard widget."""
    
    def test_creation(self):
        """Test creating a gap card."""
        from inception.tui.app import GapCard
        
        gap = {"id": "gap-001", "description": "Missing data", "severity": "high"}
        card = GapCard(gap=gap)
        
        assert card.gap["id"] == "gap-001"


# =============================================================================
# Test: Modal Screens
# =============================================================================

class TestEntityDetailModal:
    """Tests for EntityDetailModal screen."""
    
    def test_creation(self):
        """Test creating entity detail modal."""
        from inception.tui.app import EntityDetailModal
        
        entity = {"id": "e1", "name": "Entity", "type": "concept"}
        modal = EntityDetailModal(entity=entity)
        
        assert modal.entity["id"] == "e1"
    
    def test_with_claims(self):
        """Test modal with claims."""
        from inception.tui.app import EntityDetailModal
        
        entity = {"id": "e1", "name": "Entity"}
        claims = [{"id": "c1", "statement": "Test claim"}]
        modal = EntityDetailModal(entity=entity, claims=claims)
        
        assert len(modal.claims) == 1


class TestHelpModal:
    """Tests for HelpModal screen."""
    
    def test_creation(self):
        """Test creating help modal."""
        from inception.tui.app import HelpModal
        
        modal = HelpModal()
        
        assert modal is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
