"""
Expanded unit tests for serve/api.py

Tests for LMDBStorage, response models, and API endpoints.
"""

import pytest

try:
    from inception.serve.api import (
        LMDBStorage,
        EntityResponse,
        ClaimResponse,
    )
    HAS_API = True
except ImportError:
    HAS_API = False


@pytest.mark.skipif(not HAS_API, reason="api module not available")
class TestLMDBStorage:
    """Tests for LMDBStorage class."""
    
    def test_creation_default(self):
        """Test creating with default path."""
        storage = LMDBStorage()
        
        import os
        assert storage.db_path == os.path.expanduser("~/.inception/knowledge.lmdb")
    
    def test_creation_custom_path(self):
        """Test creating with custom path."""
        storage = LMDBStorage(db_path="/tmp/test.lmdb")
        
        assert storage.db_path == "/tmp/test.lmdb"
    
    def test_get_entities_returns_list(self):
        """Test get_entities returns list."""
        storage = LMDBStorage()
        
        entities = storage.get_entities(limit=5)
        
        assert isinstance(entities, list)
    
    def test_get_entities_with_filter(self):
        """Test get_entities with type filter."""
        storage = LMDBStorage()
        
        entities = storage.get_entities(type_filter="PERSON", limit=5)
        
        assert isinstance(entities, list)
    
    def test_get_claims_returns_list(self):
        """Test get_claims returns list."""
        storage = LMDBStorage()
        
        claims = storage.get_claims(limit=5)
        
        assert isinstance(claims, list)
    
    def test_get_gaps_returns_list(self):
        """Test get_gaps returns list."""
        storage = LMDBStorage()
        
        gaps = storage.get_gaps()
        
        assert isinstance(gaps, list)
    
    def test_get_stats_returns_dict(self):
        """Test get_stats returns dict."""
        storage = LMDBStorage()
        
        stats = storage.get_stats()
        
        assert isinstance(stats, dict)
    
    def test_health_returns_dict(self):
        """Test health check returns dict."""
        storage = LMDBStorage()
        
        health = storage.health()
        
        assert isinstance(health, dict)
        assert "status" in health
    
    def test_get_graph_data(self):
        """Test graph data retrieval."""
        storage = LMDBStorage()
        
        graph = storage.get_graph_data()
        
        assert isinstance(graph, dict)
    
    def test_get_sources(self):
        """Test sources retrieval."""
        storage = LMDBStorage()
        
        sources = storage.get_sources(limit=5)
        
        assert isinstance(sources, list)
    
    def test_get_entity_nonexistent(self):
        """Test getting nonexistent entity."""
        storage = LMDBStorage()
        
        entity = storage.get_entity("nonexistent-entity-id")
        
        assert entity is None
    
    def test_get_timeline(self):
        """Test timeline retrieval."""
        storage = LMDBStorage()
        
        timeline = storage.get_timeline(limit=5)
        
        assert isinstance(timeline, list)


@pytest.mark.skipif(not HAS_API, reason="api module not available")
class TestEntityResponse:
    """Tests for EntityResponse model."""
    
    def test_creation(self):
        """Test creating response."""
        resp = EntityResponse(id="e1", name="Test")
        
        assert resp.id == "e1"
        assert resp.name == "Test"
        assert resp.type == "entity"
    
    def test_with_confidence(self):
        """Test with confidence."""
        resp = EntityResponse(id="e2", name="Test2", confidence=0.9)
        
        assert resp.confidence == 0.9


@pytest.mark.skipif(not HAS_API, reason="api module not available")
class TestClaimResponse:
    """Tests for ClaimResponse model."""
    
    def test_creation(self):
        """Test creating response."""
        resp = ClaimResponse(id="c1", statement="Test claim", entity_id="e1")
        
        assert resp.id == "c1"
        assert resp.entity_id == "e1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
