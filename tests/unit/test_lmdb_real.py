"""Tests for db/hyperknowledge_lmdb.py (61% coverage)"""
import pytest
import tempfile
from pathlib import Path

try:
    from inception.db.hyperknowledge_lmdb import LMDBStorage
    HAS_LMDB = True
except ImportError:
    HAS_LMDB = False


@pytest.mark.skipif(not HAS_LMDB, reason="LMDBStorage not available")
class TestLMDBStorage:
    def test_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LMDBStorage(path=Path(tmpdir) / "test.lmdb")
            assert storage is not None
    
    def test_put_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LMDBStorage(path=Path(tmpdir) / "test.lmdb")
            if hasattr(storage, 'put') and hasattr(storage, 'get'):
                storage.put("key1", {"value": 1})
                result = storage.get("key1")
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
