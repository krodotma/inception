"""
LMDB environment and database operations.

Provides the main InceptionDB class for interacting with the
temporal knowledge hypergraph stored in LMDB.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Generator

import lmdb

from inception.config import Config, get_config
from inception.db.keys import (
    ObjectType,
    EdgeType,
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
from inception.db.graphtag import graphtag_to_bytes, bytes_to_graphtag
from inception.db.records import (
    MetaRecord,
    SourceRecord,
    ArtifactRecord,
    SpanRecord,
    NodeRecord,
    EdgeRecord,
)


# Sub-database names
DB_META = b"meta"
DB_SRC = b"src"
DB_ART = b"art"
DB_SPAN = b"span"
DB_NODE = b"node"
DB_EDGE = b"edge"
DB_GT2NID = b"gt2nid"
DB_TINDEX = b"tindex"
DB_PINDEX = b"pindex"

ALL_DBS = [DB_META, DB_SRC, DB_ART, DB_SPAN, DB_NODE, DB_EDGE, DB_GT2NID, DB_TINDEX, DB_PINDEX]


class InceptionDB:
    """
    Main database interface for Inception.
    
    Wraps LMDB with typed operations for the knowledge hypergraph.
    """
    
    def __init__(self, path: Path | str | None = None, config: Config | None = None):
        """
        Initialize the database.
        
        Args:
            path: Path to the LMDB directory. If None, uses config default.
            config: Configuration object. If None, uses global config.
        """
        self.config = config or get_config()
        self.path = Path(path) if path else self.config.lmdb.path
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Initialize LMDB environment
        self.env = lmdb.open(
            str(self.path),
            map_size=self.config.lmdb.map_size,
            max_dbs=self.config.lmdb.max_dbs,
            create=True,
        )
        
        # Open all sub-databases
        self._dbs: dict[bytes, lmdb.Environment] = {}
        with self.env.begin(write=True) as txn:
            for db_name in ALL_DBS:
                self._dbs[db_name] = self.env.open_db(db_name, txn=txn, create=True)
        
        # NID allocator (thread-safe)
        self._nid_lock = threading.Lock()
        self._next_nid = self._load_next_nid()
        
        # Initialize meta if not exists
        self._ensure_meta()
    
    def _load_next_nid(self) -> int:
        """Load the next available NID from the database."""
        # Find the maximum NID across all typed databases
        max_nid = 0
        with self.env.begin() as txn:
            for db_name in [DB_SRC, DB_ART, DB_SPAN, DB_NODE]:
                db = self._dbs[db_name]
                cursor = txn.cursor(db)
                if cursor.last():
                    nid = decode_nid_key(cursor.key())
                    max_nid = max(max_nid, nid)
        return max_nid + 1
    
    def _ensure_meta(self) -> None:
        """Ensure meta record exists."""
        with self.env.begin(write=True) as txn:
            db = self._dbs[DB_META]
            if txn.get(b"config", db=db) is None:
                meta = MetaRecord(
                    schema_version=self.config.schema_version,
                    pipeline_version=self.config.pipeline_version,
                )
                txn.put(b"config", meta.pack(), db=db)
    
    def allocate_nid(self) -> int:
        """Allocate a new unique NID (thread-safe)."""
        with self._nid_lock:
            nid = self._next_nid
            self._next_nid += 1
            return nid
    
    def close(self) -> None:
        """Close the database."""
        self.env.close()
    
    def __enter__(self) -> InceptionDB:
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
    
    @contextmanager
    def write_txn(self) -> Generator[lmdb.Transaction, None, None]:
        """Context manager for write transactions."""
        with self.env.begin(write=True) as txn:
            yield txn
    
    @contextmanager
    def read_txn(self) -> Generator[lmdb.Transaction, None, None]:
        """Context manager for read transactions."""
        with self.env.begin() as txn:
            yield txn
    
    # === Meta operations ===
    
    def get_meta(self) -> MetaRecord:
        """Get the database metadata."""
        with self.env.begin() as txn:
            data = txn.get(b"config", db=self._dbs[DB_META])
            if data is None:
                return MetaRecord()
            return MetaRecord.unpack(data)
    
    def update_meta(self, **kwargs) -> MetaRecord:
        """Update metadata fields."""
        from datetime import datetime
        
        with self.env.begin(write=True) as txn:
            db = self._dbs[DB_META]
            data = txn.get(b"config", db=db)
            meta = MetaRecord.unpack(data) if data else MetaRecord()
            
            for key, value in kwargs.items():
                if hasattr(meta, key):
                    setattr(meta, key, value)
            
            meta.last_modified = datetime.utcnow()
            txn.put(b"config", meta.pack(), db=db)
            return meta
    
    # === Source operations ===
    
    def put_source(self, source: SourceRecord, txn: lmdb.Transaction | None = None) -> None:
        """Store a source record."""
        key = encode_nid_key(source.nid)
        
        def _put(t: lmdb.Transaction) -> None:
            t.put(key, source.pack(), db=self._dbs[DB_SRC])
        
        if txn:
            _put(txn)
        else:
            with self.write_txn() as t:
                _put(t)
    
    def get_source(self, nid: int, txn: lmdb.Transaction | None = None) -> SourceRecord | None:
        """Get a source record by NID."""
        key = encode_nid_key(nid)
        
        def _get(t: lmdb.Transaction) -> SourceRecord | None:
            data = t.get(key, db=self._dbs[DB_SRC])
            return SourceRecord.unpack(data) if data else None
        
        if txn:
            return _get(txn)
        with self.read_txn() as t:
            return _get(t)
    
    def iter_sources(self, txn: lmdb.Transaction | None = None) -> Iterator[SourceRecord]:
        """Iterate over all source records."""
        def _iter(t: lmdb.Transaction) -> Iterator[SourceRecord]:
            cursor = t.cursor(self._dbs[DB_SRC])
            for _, value in cursor:
                yield SourceRecord.unpack(value)
        
        if txn:
            yield from _iter(txn)
        else:
            with self.read_txn() as t:
                yield from _iter(t)
    
    # === Artifact operations ===
    
    def put_artifact(self, artifact: ArtifactRecord, txn: lmdb.Transaction | None = None) -> None:
        """Store an artifact record."""
        key = encode_nid_key(artifact.nid)
        
        def _put(t: lmdb.Transaction) -> None:
            t.put(key, artifact.pack(), db=self._dbs[DB_ART])
        
        if txn:
            _put(txn)
        else:
            with self.write_txn() as t:
                _put(t)
    
    def get_artifact(self, nid: int, txn: lmdb.Transaction | None = None) -> ArtifactRecord | None:
        """Get an artifact record by NID."""
        key = encode_nid_key(nid)
        
        def _get(t: lmdb.Transaction) -> ArtifactRecord | None:
            data = t.get(key, db=self._dbs[DB_ART])
            return ArtifactRecord.unpack(data) if data else None
        
        if txn:
            return _get(txn)
        with self.read_txn() as t:
            return _get(t)
    
    # === Span operations ===
    
    def put_span(self, span: SpanRecord, txn: lmdb.Transaction | None = None) -> None:
        """Store a span record and update indexes."""
        key = encode_nid_key(span.nid)
        
        def _put(t: lmdb.Transaction) -> None:
            t.put(key, span.pack(), db=self._dbs[DB_SPAN])
            
            # Update temporal index for video/audio spans
            if hasattr(span.anchor, "t0_ms"):
                tkey = encode_temporal_key(span.source_nid, span.anchor.t0_ms, span.nid)
                t.put(tkey, b"", db=self._dbs[DB_TINDEX])
            
            # Update page index for document spans
            if hasattr(span.anchor, "page"):
                y0 = int((span.anchor.y0 or 0) * 65535)
                pkey = encode_page_key(span.source_nid, span.anchor.page, y0, span.nid)
                t.put(pkey, b"", db=self._dbs[DB_PINDEX])
        
        if txn:
            _put(txn)
        else:
            with self.write_txn() as t:
                _put(t)
    
    def get_span(self, nid: int, txn: lmdb.Transaction | None = None) -> SpanRecord | None:
        """Get a span record by NID."""
        key = encode_nid_key(nid)
        
        def _get(t: lmdb.Transaction) -> SpanRecord | None:
            data = t.get(key, db=self._dbs[DB_SPAN])
            return SpanRecord.unpack(data) if data else None
        
        if txn:
            return _get(txn)
        with self.read_txn() as t:
            return _get(t)
    
    def query_spans_by_time(
        self,
        source_nid: int,
        t0_ms: int,
        t1_ms: int,
        txn: lmdb.Transaction | None = None,
    ) -> list[SpanRecord]:
        """Query spans within a time range for a source."""
        start_key = encode_temporal_key(source_nid, t0_ms, 0)
        end_key = encode_temporal_key(source_nid, t1_ms, (1 << 64) - 1)
        
        def _query(t: lmdb.Transaction) -> list[SpanRecord]:
            spans = []
            cursor = t.cursor(self._dbs[DB_TINDEX])
            if cursor.set_range(start_key):
                while cursor.key() <= end_key:
                    tkey = decode_temporal_key(cursor.key())
                    span = self.get_span(tkey.span_nid, t)
                    if span:
                        spans.append(span)
                    if not cursor.next():
                        break
            return spans
        
        if txn:
            return _query(txn)
        with self.read_txn() as t:
            return _query(t)
    
    # === Node operations ===
    
    def put_node(self, node: NodeRecord, txn: lmdb.Transaction | None = None) -> None:
        """Store a node record."""
        key = encode_nid_key(node.nid)
        
        def _put(t: lmdb.Transaction) -> None:
            t.put(key, node.pack(), db=self._dbs[DB_NODE])
        
        if txn:
            _put(txn)
        else:
            with self.write_txn() as t:
                _put(t)
    
    def get_node(self, nid: int, txn: lmdb.Transaction | None = None) -> NodeRecord | None:
        """Get a node record by NID."""
        key = encode_nid_key(nid)
        
        def _get(t: lmdb.Transaction) -> NodeRecord | None:
            data = t.get(key, db=self._dbs[DB_NODE])
            return NodeRecord.unpack(data) if data else None
        
        if txn:
            return _get(txn)
        with self.read_txn() as t:
            return _get(t)
    
    def iter_nodes(self, txn: lmdb.Transaction | None = None) -> Iterator[NodeRecord]:
        """Iterate over all node records."""
        def _iter(t: lmdb.Transaction) -> Iterator[NodeRecord]:
            cursor = t.cursor(self._dbs[DB_NODE])
            for _, value in cursor:
                yield NodeRecord.unpack(value)
        
        if txn:
            yield from _iter(txn)
        else:
            with self.read_txn() as t:
                yield from _iter(t)
    
    # === Edge operations ===
    
    def put_edge(
        self,
        from_nid: int,
        edge_type: EdgeType,
        to_nid: int,
        edge: EdgeRecord,
        txn: lmdb.Transaction | None = None,
    ) -> None:
        """Store an edge record."""
        key = encode_edge_key(from_nid, edge_type, to_nid)
        
        def _put(t: lmdb.Transaction) -> None:
            t.put(key, edge.pack(), db=self._dbs[DB_EDGE])
        
        if txn:
            _put(txn)
        else:
            with self.write_txn() as t:
                _put(t)
    
    def get_edge(
        self,
        from_nid: int,
        edge_type: EdgeType,
        to_nid: int,
        txn: lmdb.Transaction | None = None,
    ) -> EdgeRecord | None:
        """Get an edge record."""
        key = encode_edge_key(from_nid, edge_type, to_nid)
        
        def _get(t: lmdb.Transaction) -> EdgeRecord | None:
            data = t.get(key, db=self._dbs[DB_EDGE])
            return EdgeRecord.unpack(data) if data else None
        
        if txn:
            return _get(txn)
        with self.read_txn() as t:
            return _get(t)
    
    def get_edges_from(
        self,
        from_nid: int,
        edge_type: EdgeType | None = None,
        txn: lmdb.Transaction | None = None,
    ) -> list[tuple[EdgeType, int, EdgeRecord]]:
        """Get all edges from a node, optionally filtered by type."""
        prefix = make_prefix_key(from_nid)
        
        def _query(t: lmdb.Transaction) -> list[tuple[EdgeType, int, EdgeRecord]]:
            edges = []
            cursor = t.cursor(self._dbs[DB_EDGE])
            if cursor.set_range(prefix):
                while cursor.key().startswith(prefix):
                    ekey = decode_edge_key(cursor.key())
                    if edge_type is None or ekey.edge_type == edge_type:
                        edge = EdgeRecord.unpack(cursor.value())
                        edges.append((ekey.edge_type, ekey.to_nid, edge))
                    if not cursor.next():
                        break
            return edges
        
        if txn:
            return _query(txn)
        with self.read_txn() as t:
            return _query(t)
    
    # === Graphtag operations ===
    
    def put_graphtag(
        self,
        graphtag: str,
        object_type: ObjectType,
        nid: int,
        txn: lmdb.Transaction | None = None,
    ) -> None:
        """Store a graphtag → NID mapping."""
        key = graphtag_to_bytes(graphtag)
        value = encode_gt2nid_value(object_type, nid)
        
        def _put(t: lmdb.Transaction) -> None:
            t.put(key, value, db=self._dbs[DB_GT2NID])
        
        if txn:
            _put(txn)
        else:
            with self.write_txn() as t:
                _put(t)
    
    def get_nid_by_graphtag(
        self,
        graphtag: str,
        txn: lmdb.Transaction | None = None,
    ) -> tuple[ObjectType, int] | None:
        """Get NID by graphtag."""
        key = graphtag_to_bytes(graphtag)
        
        def _get(t: lmdb.Transaction) -> tuple[ObjectType, int] | None:
            value = t.get(key, db=self._dbs[DB_GT2NID])
            return decode_gt2nid_value(value) if value else None
        
        if txn:
            return _get(txn)
        with self.read_txn() as t:
            return _get(t)
    
    # === Statistics ===
    
    def stats(self) -> dict[str, int]:
        """Get database statistics."""
        with self.env.begin() as txn:
            stats = {}
            for db_name in ALL_DBS:
                db = self._dbs[db_name]
                db_stats = txn.stat(db)
                stats[db_name.decode()] = db_stats["entries"]
            return stats


# Global database instance
_db: InceptionDB | None = None


def get_db(path: Path | str | None = None, config: Config | None = None) -> InceptionDB:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = InceptionDB(path=path, config=config)
    return _db


def close_db() -> None:
    """Close the global database instance."""
    global _db
    if _db is not None:
        _db.close()
        _db = None
