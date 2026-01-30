"""
Deep unit tests for db/hyperknowledge_lmdb.py

Tests for LMDB-backed hyperknowledge storage.
"""

import pytest
import tempfile
from pathlib import Path

try:
    from inception.db.hyperknowledge_lmdb import (
        LMDBHyperKnowledgeStore,
    )
    HAS_HK_LMDB = True
except ImportError:
    HAS_HK_LMDB = False


@pytest.mark.skipif(not HAS_HK_LMDB, reason="hyperknowledge_lmdb module not available")
class TestLMDBHyperKnowledgeStore:
    """Tests for LMDBHyperKnowledgeStore."""
    
    def test_creation_temp(self):
        """Test creating with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LMDBHyperKnowledgeStore(path=Path(tmpdir) / "test.lmdb")
            
            assert store is not None
    
    def test_open_close(self):
        """Test open and close."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LMDBHyperKnowledgeStore(path=Path(tmpdir) / "test.lmdb")
            store.open()
            store.close()
    
    def test_get_nonexistent(self):
        """Test getting nonexistent node."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LMDBHyperKnowledgeStore(path=Path(tmpdir) / "test.lmdb")
            store.open()
            
            node = store.get(9999)
            
            assert node is None
            store.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
