"""
Database layer for Inception.

Provides LMDB storage with MessagePack serialization and
structured key encoding for the temporal knowledge hypergraph.
"""

from inception.db.lmdb_env import InceptionDB, get_db
from inception.db.keys import (
    encode_nid_key,
    decode_nid_key,
    encode_edge_key,
    decode_edge_key,
    encode_temporal_key,
    decode_temporal_key,
)
from inception.db.graphtag import compute_graphtag, graphtag_to_bytes, bytes_to_graphtag
from inception.db.records import (
    SourceRecord,
    ArtifactRecord,
    SpanRecord,
    NodeRecord,
    EdgeRecord,
    MetaRecord,
)

__all__ = [
    # Database
    "InceptionDB",
    "get_db",
    # Keys
    "encode_nid_key",
    "decode_nid_key",
    "encode_edge_key",
    "decode_edge_key",
    "encode_temporal_key",
    "decode_temporal_key",
    # Graphtag
    "compute_graphtag",
    "graphtag_to_bytes",
    "bytes_to_graphtag",
    # Records
    "SourceRecord",
    "ArtifactRecord",
    "SpanRecord",
    "NodeRecord",
    "EdgeRecord",
    "MetaRecord",
]
