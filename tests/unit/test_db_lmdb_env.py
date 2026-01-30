"""
Unit tests for db/lmdb_env.py

Tests for LMDB environment management.
"""

import pytest
import tempfile
from pathlib import Path

try:
    from inception.db.lmdb_env import LMDBEnvironment
    HAS_LMDB_ENV = True
except ImportError:
    HAS_LMDB_ENV = False


@pytest.mark.skipif(not HAS_LMDB_ENV, reason="lmdb_env module not available")
class TestLMDBEnvironment:
    """Tests for LMDBEnvironment."""
    
    def test_creation_temp(self):
        """Test creating with temp path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env = LMDBEnvironment(path=Path(tmpdir) / "test.lmdb")
            
            assert env is not None
    
    def test_open_close(self):
        """Test open and close cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env = LMDBEnvironment(path=Path(tmpdir) / "test.lmdb")
            env.open()
            env.close()
    
    def test_transaction_context(self):
        """Test read transaction context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env = LMDBEnvironment(path=Path(tmpdir) / "test.lmdb")
            env.open()
            
            with env.begin() as txn:
                assert txn is not None
            
            env.close()
    
    def test_write_and_read(self):
        """Test basic write and read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env = LMDBEnvironment(path=Path(tmpdir) / "test.lmdb")
            env.open()
            
            with env.begin(write=True) as txn:
                txn.put(b"key1", b"value1")
            
            with env.begin() as txn:
                value = txn.get(b"key1")
                assert value == b"value1"
            
            env.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
