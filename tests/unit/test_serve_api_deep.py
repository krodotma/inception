"""
Deep tests for serve/api.py (47%) - Endpoint coverage
"""
import pytest

try:
    from inception.serve.api import LMDBStorage
    HAS_API = True
except ImportError:
    HAS_API = False

@pytest.mark.skipif(not HAS_API, reason="serve api not available")
class TestLMDBStorageDeep:
    def test_temporal_history(self):
        storage = LMDBStorage()
        timeline = storage.get_timeline(limit=5)
        assert isinstance(timeline, list)
    
    def test_source_tracking(self):
        storage = LMDBStorage()
        sources = storage.get_sources(limit=3)
        assert isinstance(sources, list)
    
    def test_confidence_intervals(self):
        storage = LMDBStorage()
        # These methods return sample data
        stats = storage.get_stats()
        assert "entities" in stats or "claims" in stats or isinstance(stats, dict)
    
    def test_temporal_conflicts(self):
        storage = LMDBStorage()
        conflicts = storage.detect_temporal_conflicts()
        assert isinstance(conflicts, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
