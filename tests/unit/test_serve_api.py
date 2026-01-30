"""
Unit tests for serve/api.py

Tests for API components:
- LMDBStorage: Database adapter
- Pydantic models: Response schemas
"""

import pytest
from inception.serve.api import (
    # Storage
    LMDBStorage,
    # Models
    EntityResponse,
    ClaimResponse,
)


# =============================================================================
# Test: LMDBStorage
# =============================================================================

class TestLMDBStorage:
    """Tests for LMDBStorage adapter."""
    
    def test_creation_with_defaults(self):
        """Test creating storage with defaults."""
        storage = LMDBStorage()
        
        assert storage is not None
        assert storage.db_path is not None
    
    def test_creation_with_custom_path(self):
        """Test creating storage with custom path."""
        storage = LMDBStorage(db_path="/tmp/test-inception.lmdb")
        
        assert "/tmp/" in storage.db_path
    
    def test_get_entities(self):
        """Test getting entities."""
        storage = LMDBStorage()
        
        entities = storage.get_entities(limit=10)
        
        assert isinstance(entities, list)
    
    def test_get_entities_with_type_filter(self):
        """Test getting entities with type filter."""
        storage = LMDBStorage()
        
        entities = storage.get_entities(type_filter="person", limit=5)
        
        assert isinstance(entities, list)
    
    def test_get_entities_with_search(self):
        """Test getting entities with search."""
        storage = LMDBStorage()
        
        entities = storage.get_entities(search="test", limit=5)
        
        assert isinstance(entities, list)
    
    def test_get_entity(self):
        """Test getting single entity."""
        storage = LMDBStorage()
        
        entity = storage.get_entity("entity-001")
        
        # May return None or entity dict
        assert entity is None or isinstance(entity, dict)
    
    def test_get_claims(self):
        """Test getting claims."""
        storage = LMDBStorage()
        
        claims = storage.get_claims(limit=10)
        
        assert isinstance(claims, list)
    
    def test_get_claims_by_entity(self):
        """Test getting claims by entity."""
        storage = LMDBStorage()
        
        claims = storage.get_claims(entity_id="entity-001", limit=5)
        
        assert isinstance(claims, list)
    
    def test_get_gaps(self):
        """Test getting knowledge gaps."""
        storage = LMDBStorage()
        
        gaps = storage.get_gaps()
        
        assert isinstance(gaps, list)
    
    def test_get_stats(self):
        """Test getting database stats."""
        storage = LMDBStorage()
        
        stats = storage.get_stats()
        
        assert isinstance(stats, dict)
    
    def test_get_graph_data(self):
        """Test getting graph data."""
        storage = LMDBStorage()
        
        graph = storage.get_graph_data()
        
        assert isinstance(graph, dict)
        assert "nodes" in graph
        assert "edges" in graph
    
    def test_health(self):
        """Test health check."""
        storage = LMDBStorage()
        
        health = storage.health()
        
        assert isinstance(health, dict)
        assert "status" in health
    
    def test_get_sources(self):
        """Test getting sources."""
        storage = LMDBStorage()
        
        sources = storage.get_sources(limit=10)
        
        assert isinstance(sources, list)
    
    def test_get_timeline(self):
        """Test getting timeline."""
        storage = LMDBStorage()
        
        timeline = storage.get_timeline(limit=10)
        
        assert isinstance(timeline, list)
    
    def test_detect_temporal_conflicts(self):
        """Test detecting temporal conflicts."""
        storage = LMDBStorage()
        
        conflicts = storage.detect_temporal_conflicts()
        
        assert isinstance(conflicts, list)


# =============================================================================
# Test: Pydantic Models
# =============================================================================

class TestEntityResponse:
    """Tests for EntityResponse model."""
    
    def test_creation(self):
        """Test creating entity response."""
        entity = EntityResponse(
            id="ent-001",
            name="Test Entity",
            type="person",
        )
        
        assert entity.id == "ent-001"
        assert entity.name == "Test Entity"
    
    def test_with_description(self):
        """Test entity with description."""
        entity = EntityResponse(
            id="ent-002",
            name="Entity",
            description="A test entity",
        )
        
        assert entity.description == "A test entity"
    
    def test_default_confidence(self):
        """Test default confidence."""
        entity = EntityResponse(id="e", name="n")
        
        assert entity.confidence == 1.0


class TestClaimResponse:
    """Tests for ClaimResponse model."""
    
    def test_creation(self):
        """Test creating claim response."""
        claim = ClaimResponse(
            id="claim-001",
            statement="Test statement",
            entity_id="ent-001",
        )
        
        assert claim.id == "claim-001"
        assert claim.entity_id == "ent-001"
    
    def test_with_confidence(self):
        """Test claim with custom confidence."""
        claim = ClaimResponse(
            id="c",
            statement="s",
            entity_id="e",
            confidence=0.85,
        )
        
        assert claim.confidence == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
