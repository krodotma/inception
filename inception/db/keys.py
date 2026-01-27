"""
Key encoding utilities for LMDB.

All keys use big-endian encoding for proper lexicographic ordering
in LMDB range scans.
"""

from __future__ import annotations

import struct
from enum import IntEnum
from typing import NamedTuple


class ObjectType(IntEnum):
    """Object type codes for gt2nid and other mappings."""
    
    SOURCE = 1
    ARTIFACT = 2
    SPAN = 3
    NODE = 4
    EDGE = 5


class EdgeType(IntEnum):
    """Edge type codes for the edge database."""
    
    # Structural edges
    MENTIONS = 1
    CONTAINS = 2
    DERIVED_FROM = 3
    
    # Semantic edges
    SUPPORTS = 10
    CONTRADICTS = 11
    REQUIRES = 12
    DEPENDS_ON = 13
    
    # Temporal edges
    TEMPORAL_BEFORE = 20
    TEMPORAL_AFTER = 21
    CONCURRENT = 22
    
    # Identity edges
    SAME_AS = 30
    SIMILAR_TO = 31
    
    # Gap edges
    BLOCKS = 40
    RESOLVES = 41


class SpanType(IntEnum):
    """Span type codes."""
    
    VIDEO = 1
    AUDIO = 2
    DOCUMENT = 3
    WEB = 4


class NodeKind(IntEnum):
    """Node kind codes."""
    
    ENTITY = 1
    CONCEPT = 2
    CLAIM = 3
    PROCEDURE = 4
    DECISION = 5
    ACTION = 6
    QUESTION = 7
    GAP = 8
    SIGN = 9  # Semiotic sign


class SourceType(IntEnum):
    """Source type codes."""
    
    YOUTUBE_VIDEO = 1
    YOUTUBE_CHANNEL = 2
    YOUTUBE_PLAYLIST = 3
    WEB_PAGE = 10
    WEB_SITE = 11
    PDF = 20
    DOCX = 21
    PPTX = 22
    XLSX = 23
    EPUB = 24
    LOCAL_VIDEO = 30
    LOCAL_AUDIO = 31


# Key encoding/decoding functions

def encode_nid_key(nid: int) -> bytes:
    """
    Encode a NID (numeric ID) as a big-endian 8-byte key.
    
    Args:
        nid: The numeric ID (uint64)
    
    Returns:
        8-byte big-endian encoded key
    
    Examples:
        >>> encode_nid_key(1).hex()
        '0000000000000001'
        >>> encode_nid_key(256).hex()
        '0000000000000100'
    """
    return struct.pack(">Q", nid)


def decode_nid_key(key: bytes) -> int:
    """
    Decode a big-endian 8-byte key to a NID.
    
    Args:
        key: 8-byte big-endian encoded key
    
    Returns:
        The numeric ID (uint64)
    
    Examples:
        >>> decode_nid_key(bytes.fromhex('0000000000000001'))
        1
    """
    return struct.unpack(">Q", key)[0]


class EdgeKey(NamedTuple):
    """Decoded edge key."""
    
    from_nid: int
    edge_type: EdgeType
    to_nid: int


def encode_edge_key(from_nid: int, edge_type: EdgeType | int, to_nid: int) -> bytes:
    """
    Encode an edge key as from_nid:edge_type:to_nid.
    
    Uses 8 bytes for from_nid, 1 byte for edge_type, 8 bytes for to_nid.
    This allows efficient range scans for all edges from a node.
    
    Args:
        from_nid: Source node NID
        edge_type: Edge type code
        to_nid: Target node NID
    
    Returns:
        17-byte encoded key
    
    Examples:
        >>> key = encode_edge_key(1, EdgeType.MENTIONS, 2)
        >>> len(key)
        17
    """
    if isinstance(edge_type, EdgeType):
        edge_type = edge_type.value
    return struct.pack(">QBQ", from_nid, edge_type, to_nid)


def decode_edge_key(key: bytes) -> EdgeKey:
    """
    Decode an edge key back to its components.
    
    Args:
        key: 17-byte encoded edge key
    
    Returns:
        EdgeKey namedtuple with from_nid, edge_type, to_nid
    """
    from_nid, edge_type_val, to_nid = struct.unpack(">QBQ", key)
    return EdgeKey(from_nid, EdgeType(edge_type_val), to_nid)


class TemporalKey(NamedTuple):
    """Decoded temporal index key."""
    
    src_nid: int
    timestamp_ms: int
    span_nid: int


def encode_temporal_key(src_nid: int, timestamp_ms: int, span_nid: int) -> bytes:
    """
    Encode a temporal index key.
    
    Format: src_nid (8) + timestamp_ms (8) + span_nid (8) = 24 bytes
    
    Timestamps are stored as signed int64 (milliseconds since epoch)
    but packed with an offset to ensure proper ordering for negative values.
    
    Args:
        src_nid: Source NID this span belongs to
        timestamp_ms: Start timestamp in milliseconds (can be negative for relative)
        span_nid: The span's NID
    
    Returns:
        24-byte encoded key
    """
    # Add offset to handle negative timestamps while maintaining order
    # Using 2^63 as offset: negative values become 0..2^63-1, positive become 2^63..2^64-1
    offset_ts = timestamp_ms + (1 << 63)
    return struct.pack(">QQQ", src_nid, offset_ts, span_nid)


def decode_temporal_key(key: bytes) -> TemporalKey:
    """
    Decode a temporal index key.
    
    Args:
        key: 24-byte encoded temporal key
    
    Returns:
        TemporalKey namedtuple
    """
    src_nid, offset_ts, span_nid = struct.unpack(">QQQ", key)
    timestamp_ms = offset_ts - (1 << 63)
    return TemporalKey(src_nid, timestamp_ms, span_nid)


class PageKey(NamedTuple):
    """Decoded page index key."""
    
    src_nid: int
    page: int
    y_pos: int
    span_nid: int


def encode_page_key(src_nid: int, page: int, y_pos: int, span_nid: int) -> bytes:
    """
    Encode a page/layout index key.
    
    Format: src_nid (8) + page (2) + y_pos (2) + span_nid (8) = 20 bytes
    
    Args:
        src_nid: Source NID this span belongs to
        page: Page number (0-65535)
        y_pos: Y position on page (0-65535)
        span_nid: The span's NID
    
    Returns:
        20-byte encoded key
    """
    return struct.pack(">QHHQ", src_nid, page, y_pos, span_nid)


def decode_page_key(key: bytes) -> PageKey:
    """
    Decode a page index key.
    
    Args:
        key: 20-byte encoded page key
    
    Returns:
        PageKey namedtuple
    """
    src_nid, page, y_pos, span_nid = struct.unpack(">QHHQ", key)
    return PageKey(src_nid, page, y_pos, span_nid)


def encode_gt2nid_value(object_type: ObjectType | int, nid: int) -> bytes:
    """
    Encode a gt2nid mapping value.
    
    Format: object_type (1) + nid (8) = 9 bytes
    
    Args:
        object_type: Type of object (source, artifact, span, node, edge)
        nid: The object's NID
    
    Returns:
        9-byte encoded value
    """
    if isinstance(object_type, ObjectType):
        object_type = object_type.value
    return struct.pack(">BQ", object_type, nid)


def decode_gt2nid_value(value: bytes) -> tuple[ObjectType, int]:
    """
    Decode a gt2nid mapping value.
    
    Args:
        value: 9-byte encoded value
    
    Returns:
        Tuple of (object_type, nid)
    """
    object_type_val, nid = struct.unpack(">BQ", value)
    return ObjectType(object_type_val), nid


def make_prefix_key(nid: int) -> bytes:
    """
    Create a prefix key for range scans.
    
    Useful for finding all edges from a node, all spans from a source, etc.
    
    Args:
        nid: The NID to use as prefix
    
    Returns:
        8-byte prefix key
    """
    return encode_nid_key(nid)


def make_range_end_key(prefix: bytes) -> bytes:
    """
    Create an end key for range scans.
    
    Returns the next key after all keys starting with the given prefix.
    
    Args:
        prefix: The prefix key
    
    Returns:
        End key for range scan
    """
    # Increment the last byte, handling overflow
    prefix_list = list(prefix)
    for i in range(len(prefix_list) - 1, -1, -1):
        if prefix_list[i] < 255:
            prefix_list[i] += 1
            return bytes(prefix_list)
        prefix_list[i] = 0
    # All bytes were 255, return a key that's definitely after
    return prefix + b"\xff"
