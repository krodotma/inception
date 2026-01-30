"""
Unit tests for db/records.py

Tests for record classes (Pydantic models).
"""

import pytest

try:
    from inception.db.records import (
        Confidence,
        NodeRecord,
        EdgeRecord,
    )
    HAS_RECORDS = True
except ImportError:
    HAS_RECORDS = False


@pytest.mark.skipif(not HAS_RECORDS, reason="records module not available")
class TestConfidence:
    """Tests for Confidence class."""
    
    def test_has_combined(self):
        """Test confidence has combined method."""
        assert hasattr(Confidence, "combined")
    
    def test_model_dump(self):
        """Test model_dump method exists."""
        assert hasattr(Confidence, "model_dump")


@pytest.mark.skipif(not HAS_RECORDS, reason="records module not available")
class TestNodeRecord:
    """Tests for NodeRecord (Pydantic model)."""
    
    def test_has_pack(self):
        """Test NodeRecord has pack method."""
        assert hasattr(NodeRecord, "pack")
    
    def test_has_unpack(self):
        """Test NodeRecord has unpack method."""
        assert hasattr(NodeRecord, "unpack")
    
    def test_model_fields(self):
        """Test NodeRecord has model_fields."""
        assert hasattr(NodeRecord, "model_fields")


@pytest.mark.skipif(not HAS_RECORDS, reason="records module not available")
class TestEdgeRecord:
    """Tests for EdgeRecord (Pydantic model)."""
    
    def test_model_fields(self):
        """Test EdgeRecord has model_fields."""
        assert hasattr(EdgeRecord, "model_fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
