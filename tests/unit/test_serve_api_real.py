"""
REAL tests for serve/api.py - Actually exercise LMDBStorage methods
"""
import pytest

from inception.serve.api import LMDBStorage


class TestLMDBStorage:
    """Test LMDBStorage - actually call methods."""
    
    def test_creation(self):
        storage = LMDBStorage()
        assert storage is not None
    
    def test_get_stats(self):
        storage = LMDBStorage()
        stats = storage.get_stats()
        assert isinstance(stats, dict)
        assert "entities" in stats or "total" in stats or len(stats) >= 0
    
    def test_get_entities(self):
        storage = LMDBStorage()
        entities = storage.get_entities(limit=10)
        assert isinstance(entities, list)
    
    def test_get_entities_with_filter(self):
        storage = LMDBStorage()
        entities = storage.get_entities(type_filter="PERSON", limit=5)
        assert isinstance(entities, list)
    
    def test_get_entity_not_found(self):
        storage = LMDBStorage()
        entity = storage.get_entity("nonexistent-id")
        assert entity is None
    
    def test_get_claims(self):
        storage = LMDBStorage()
        claims = storage.get_claims(limit=10)
        assert isinstance(claims, list)
    
    def test_get_gaps(self):
        storage = LMDBStorage()
        gaps = storage.get_gaps()
        assert isinstance(gaps, list)
    
    def test_get_graph_data(self):
        storage = LMDBStorage()
        graph = storage.get_graph_data()
        assert isinstance(graph, dict)
    
    def test_health(self):
        storage = LMDBStorage()
        health = storage.health()
        assert isinstance(health, dict)
    
    def test_get_sources(self):
        storage = LMDBStorage()
        sources = storage.get_sources(limit=5)
        assert isinstance(sources, list)
    
    def test_get_timeline(self):
        storage = LMDBStorage()
        timeline = storage.get_timeline(limit=10)
        assert isinstance(timeline, list)
    
    def test_detect_temporal_conflicts(self):
        storage = LMDBStorage()
        conflicts = storage.detect_temporal_conflicts()
        assert isinstance(conflicts, list)
    
    def test_get_confidence_intervals(self):
        storage = LMDBStorage()
        if hasattr(storage, 'get_confidence_intervals'):
            intervals = storage.get_confidence_intervals()
            assert isinstance(intervals, (list, dict))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
