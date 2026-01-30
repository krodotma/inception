"""
Property-based tests for database invariants.
"""

import pytest

# Skip entire module if hypothesis is not installed
hypothesis = pytest.importorskip("hypothesis")
given = hypothesis.given
st = hypothesis.strategies
settings = hypothesis.settings

from inception.db.keys import (
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
    EdgeType,
    ObjectType,
)
from inception.db.graphtag import (
    compute_graphtag,
    graphtag_to_bytes,
    bytes_to_graphtag,
)


class TestKeyEncodingProperties:
    """Property-based tests for key encoding."""
    
    @given(st.integers(min_value=0, max_value=2**63 - 1))
    @settings(max_examples=100)
    def test_nid_roundtrip(self, nid: int):
        """NID encoding is its own inverse."""
        assert decode_nid_key(encode_nid_key(nid)) == nid
    
    @given(
        st.integers(min_value=0, max_value=2**63 - 1),
        st.integers(min_value=0, max_value=2**63 - 1),
    )
    @settings(max_examples=100)
    def test_nid_ordering_preserved(self, a: int, b: int):
        """Key ordering matches integer ordering."""
        key_a = encode_nid_key(a)
        key_b = encode_nid_key(b)
        
        if a < b:
            assert key_a < key_b
        elif a > b:
            assert key_a > key_b
        else:
            assert key_a == key_b
    
    @given(
        st.integers(min_value=0, max_value=2**63 - 1),
        st.sampled_from(list(EdgeType)),
        st.integers(min_value=0, max_value=2**63 - 1),
    )
    @settings(max_examples=100)
    def test_edge_key_roundtrip(self, from_nid: int, edge_type: EdgeType, to_nid: int):
        """Edge key encoding is its own inverse."""
        key = encode_edge_key(from_nid, edge_type, to_nid)
        result = decode_edge_key(key)
        
        assert result.from_nid == from_nid
        assert result.edge_type == edge_type
        assert result.to_nid == to_nid
    
    @given(
        st.integers(min_value=0, max_value=2**63 - 1),
        st.integers(min_value=-(2**62), max_value=2**62 - 1),
        st.integers(min_value=0, max_value=2**63 - 1),
    )
    @settings(max_examples=100)
    def test_temporal_key_roundtrip(self, src_nid: int, timestamp_ms: int, span_nid: int):
        """Temporal key encoding is its own inverse."""
        key = encode_temporal_key(src_nid, timestamp_ms, span_nid)
        result = decode_temporal_key(key)
        
        assert result.src_nid == src_nid
        assert result.timestamp_ms == timestamp_ms
        assert result.span_nid == span_nid
    
    @given(
        st.integers(min_value=0, max_value=2**63 - 1),
        st.integers(min_value=-(2**62), max_value=2**62 - 1),
        st.integers(min_value=-(2**62), max_value=2**62 - 1),
    )
    @settings(max_examples=100)
    def test_temporal_ordering(self, src_nid: int, t1: int, t2: int):
        """Temporal keys order by timestamp within same source."""
        key1 = encode_temporal_key(src_nid, t1, 1)
        key2 = encode_temporal_key(src_nid, t2, 1)
        
        if t1 < t2:
            assert key1 < key2
        elif t1 > t2:
            assert key1 > key2
    
    @given(
        st.integers(min_value=0, max_value=2**63 - 1),
        st.integers(min_value=0, max_value=65535),
        st.integers(min_value=0, max_value=65535),
        st.integers(min_value=0, max_value=2**63 - 1),
    )
    @settings(max_examples=100)
    def test_page_key_roundtrip(self, src_nid: int, page: int, y_pos: int, span_nid: int):
        """Page key encoding is its own inverse."""
        key = encode_page_key(src_nid, page, y_pos, span_nid)
        result = decode_page_key(key)
        
        assert result.src_nid == src_nid
        assert result.page == page
        assert result.y_pos == y_pos
        assert result.span_nid == span_nid
    
    @given(
        st.sampled_from(list(ObjectType)),
        st.integers(min_value=0, max_value=2**63 - 1),
    )
    @settings(max_examples=50)
    def test_gt2nid_value_roundtrip(self, obj_type: ObjectType, nid: int):
        """Graphtag value encoding is its own inverse."""
        value = encode_gt2nid_value(obj_type, nid)
        result_type, result_nid = decode_gt2nid_value(value)
        
        assert result_type == obj_type
        assert result_nid == nid


class TestGraphtagProperties:
    """Property-based tests for graphtag computation."""
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_graphtag_deterministic(self, text: str):
        """Same input always produces same graphtag."""
        tag1 = compute_graphtag(text)
        tag2 = compute_graphtag(text)
        assert tag1 == tag2
    
    @given(st.binary(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_graphtag_bytes_roundtrip(self, data: bytes):
        """Graphtag bytes conversion is its own inverse."""
        tag = compute_graphtag(data)
        as_bytes = graphtag_to_bytes(tag)
        back = bytes_to_graphtag(as_bytes)
        assert back == tag
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnop"),
            st.one_of(st.integers(), st.text(max_size=50)),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=50)
    def test_dict_key_order_independent(self, d: dict):
        """Dict key order doesn't affect graphtag."""
        tag1 = compute_graphtag(d)
        # Reverse the dict
        reversed_d = dict(reversed(list(d.items())))
        tag2 = compute_graphtag(reversed_d)
        assert tag1 == tag2
