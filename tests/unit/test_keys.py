"""
Unit tests for key encoding/decoding.
"""

import pytest
from inception.db.keys import (
    ObjectType,
    EdgeType,
    SpanType,
    NodeKind,
    SourceType,
    encode_nid_key,
    decode_nid_key,
    encode_edge_key,
    decode_edge_key,
    encode_temporal_key,
    decode_temporal_key,
    encode_page_key,
    decode_page_key,
    encode_gt2nid_value,
    decode_gt2nid_value,
    make_prefix_key,
    make_range_end_key,
)


class TestNIDKeyEncoding:
    """Tests for NID key encoding/decoding."""
    
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding are inverses."""
        for nid in [0, 1, 255, 256, 65535, 2**32, 2**63]:
            key = encode_nid_key(nid)
            assert decode_nid_key(key) == nid
    
    def test_key_length(self):
        """Test that encoded keys are 8 bytes."""
        assert len(encode_nid_key(0)) == 8
        assert len(encode_nid_key(2**63)) == 8
    
    def test_ordering(self):
        """Test that encoded keys maintain ordering."""
        keys = [encode_nid_key(i) for i in [0, 1, 100, 1000, 2**32]]
        assert keys == sorted(keys)
    
    def test_big_endian(self):
        """Test that encoding is big-endian."""
        key = encode_nid_key(1)
        assert key == b"\x00\x00\x00\x00\x00\x00\x00\x01"
        
        key = encode_nid_key(256)
        assert key == b"\x00\x00\x00\x00\x00\x00\x01\x00"


class TestEdgeKeyEncoding:
    """Tests for edge key encoding/decoding."""
    
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding are inverses."""
        from_nid = 123
        edge_type = EdgeType.SUPPORTS
        to_nid = 456
        
        key = encode_edge_key(from_nid, edge_type, to_nid)
        result = decode_edge_key(key)
        
        assert result.from_nid == from_nid
        assert result.edge_type == edge_type
        assert result.to_nid == to_nid
    
    def test_key_length(self):
        """Test that edge keys are 17 bytes."""
        key = encode_edge_key(1, EdgeType.MENTIONS, 2)
        assert len(key) == 17
    
    def test_ordering_by_from_nid(self):
        """Test that edge keys order by from_nid first."""
        key1 = encode_edge_key(1, EdgeType.MENTIONS, 100)
        key2 = encode_edge_key(2, EdgeType.MENTIONS, 1)
        assert key1 < key2
    
    def test_ordering_by_edge_type(self):
        """Test that edge keys order by edge_type second."""
        key1 = encode_edge_key(1, EdgeType.MENTIONS, 100)  # type=1
        key2 = encode_edge_key(1, EdgeType.SUPPORTS, 100)  # type=10
        assert key1 < key2


class TestTemporalKeyEncoding:
    """Tests for temporal index key encoding/decoding."""
    
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding are inverses."""
        src_nid = 1
        timestamp_ms = 1234567890
        span_nid = 999
        
        key = encode_temporal_key(src_nid, timestamp_ms, span_nid)
        result = decode_temporal_key(key)
        
        assert result.src_nid == src_nid
        assert result.timestamp_ms == timestamp_ms
        assert result.span_nid == span_nid
    
    def test_negative_timestamps(self):
        """Test that negative timestamps work (for relative times)."""
        key = encode_temporal_key(1, -1000, 1)
        result = decode_temporal_key(key)
        assert result.timestamp_ms == -1000
    
    def test_timestamp_ordering(self):
        """Test that timestamps order correctly."""
        key1 = encode_temporal_key(1, 0, 1)
        key2 = encode_temporal_key(1, 1000, 1)
        key3 = encode_temporal_key(1, 2000, 1)
        assert key1 < key2 < key3
    
    def test_negative_before_positive(self):
        """Test that negative timestamps come before positive."""
        key1 = encode_temporal_key(1, -1000, 1)
        key2 = encode_temporal_key(1, 0, 1)
        key3 = encode_temporal_key(1, 1000, 1)
        assert key1 < key2 < key3


class TestPageKeyEncoding:
    """Tests for page index key encoding/decoding."""
    
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding are inverses."""
        src_nid = 1
        page = 5
        y_pos = 100
        span_nid = 999
        
        key = encode_page_key(src_nid, page, y_pos, span_nid)
        result = decode_page_key(key)
        
        assert result.src_nid == src_nid
        assert result.page == page
        assert result.y_pos == y_pos
        assert result.span_nid == span_nid
    
    def test_page_ordering(self):
        """Test that pages order correctly."""
        key1 = encode_page_key(1, 0, 0, 1)
        key2 = encode_page_key(1, 1, 0, 1)
        key3 = encode_page_key(1, 2, 0, 1)
        assert key1 < key2 < key3
    
    def test_y_ordering_within_page(self):
        """Test that y positions order correctly within a page."""
        key1 = encode_page_key(1, 1, 0, 1)
        key2 = encode_page_key(1, 1, 100, 1)
        key3 = encode_page_key(1, 1, 200, 1)
        assert key1 < key2 < key3


class TestGt2NidValueEncoding:
    """Tests for graphtag to NID mapping value encoding."""
    
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding are inverses."""
        for obj_type in ObjectType:
            value = encode_gt2nid_value(obj_type, 12345)
            result_type, result_nid = decode_gt2nid_value(value)
            assert result_type == obj_type
            assert result_nid == 12345
    
    def test_value_length(self):
        """Test that values are 9 bytes."""
        value = encode_gt2nid_value(ObjectType.NODE, 1)
        assert len(value) == 9


class TestPrefixKeys:
    """Tests for prefix key utilities."""
    
    def test_make_prefix_key(self):
        """Test prefix key creation."""
        prefix = make_prefix_key(1)
        assert prefix == encode_nid_key(1)
    
    def test_range_end_key(self):
        """Test range end key calculation."""
        prefix = make_prefix_key(1)
        end = make_range_end_key(prefix)
        assert end > prefix
    
    def test_range_end_key_excludes_next(self):
        """Test that range end key excludes the next NID."""
        prefix = make_prefix_key(1)
        end = make_range_end_key(prefix)
        next_nid_key = make_prefix_key(2)
        assert end <= next_nid_key


class TestEnums:
    """Tests for enum values."""
    
    def test_edge_types(self):
        """Test that edge types have expected values."""
        assert EdgeType.MENTIONS.value == 1
        assert EdgeType.SUPPORTS.value == 10
        assert EdgeType.CONTRADICTS.value == 11
    
    def test_source_types(self):
        """Test that source types have expected values."""
        assert SourceType.YOUTUBE_VIDEO.value == 1
        assert SourceType.PDF.value == 20
    
    def test_node_kinds(self):
        """Test that node kinds have expected values."""
        assert NodeKind.ENTITY.value == 1
        assert NodeKind.CLAIM.value == 3
        assert NodeKind.GAP.value == 8
