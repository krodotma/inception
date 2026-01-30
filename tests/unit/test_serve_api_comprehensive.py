"""
Comprehensive tests for serve/api.py (47%) - all endpoints
"""
import pytest

try:
    from inception.serve.api import LMDBStorage
    HAS_API = True
except ImportError:
    HAS_API = False

@pytest.mark.skipif(not HAS_API, reason="serve api not available")
class TestLMDBStorageComprehensive:
    def test_creation_default(self):
        storage = LMDBStorage()
        assert storage is not None
    
    def test_creation_custom_path(self):
        storage = LMDBStorage(db_path="/tmp/test.lmdb")
        assert storage.db_path == "/tmp/test.lmdb"
    
    def test_get_entities(self):
        storage = LMDBStorage()
        entities = storage.get_entities(limit=5)
        assert isinstance(entities, list)
    
    def test_get_entities_filtered(self):
        storage = LMDBStorage()
        entities = storage.get_entities(type_filter="PERSON", limit=5)
        assert isinstance(entities, list)
    
    def test_get_entity(self):
        storage = LMDBStorage()
        entity = storage.get_entity("nonexistent")
        assert entity is None
    
    def test_get_claims(self):
        storage = LMDBStorage()
        claims = storage.get_claims(limit=5)
        assert isinstance(claims, list)
    
    def test_get_gaps(self):
        storage = LMDBStorage()
        gaps = storage.get_gaps()
        assert isinstance(gaps, list)
    
    def test_get_stats(self):
        storage = LMDBStorage()
        stats = storage.get_stats()
        assert isinstance(stats, dict)
    
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
        timeline = storage.get_timeline(limit=5)
        assert isinstance(timeline, list)
    
    def test_detect_temporal_conflicts(self):
        storage = LMDBStorage()
        conflicts = storage.detect_temporal_conflicts()
        assert isinstance(conflicts, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
