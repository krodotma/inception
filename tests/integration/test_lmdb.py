"""
Integration tests for LMDB operations.
"""

import pytest
import tempfile
from pathlib import Path

from inception.db.lmdb_env import InceptionDB
from inception.db.records import (
    SourceRecord,
    ArtifactRecord,
    SpanRecord,
    NodeRecord,
    EdgeRecord,
    VideoAnchor,
    Confidence,
)
from inception.db.keys import (
    SourceType,
    SpanType,
    NodeKind,
    EdgeType,
    ObjectType,
)
from inception.db.graphtag import compute_graphtag
from inception.config import Config


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.lmdb.path = Path(tmpdir) / "test_db"
        db = InceptionDB(config=config)
        yield db
        db.close()


class TestInceptionDB:
    """Integration tests for InceptionDB."""
    
    def test_create_database(self, temp_db: InceptionDB):
        """Test database creation."""
        assert temp_db.path.exists()
        meta = temp_db.get_meta()
        assert meta.schema_version == "0.1.0"
    
    def test_allocate_nid(self, temp_db: InceptionDB):
        """Test NID allocation."""
        nid1 = temp_db.allocate_nid()
        nid2 = temp_db.allocate_nid()
        nid3 = temp_db.allocate_nid()
        
        assert nid1 < nid2 < nid3
        assert nid2 == nid1 + 1
        assert nid3 == nid2 + 1
    
    def test_source_crud(self, temp_db: InceptionDB):
        """Test source CRUD operations."""
        nid = temp_db.allocate_nid()
        source = SourceRecord(
            nid=nid,
            source_type=SourceType.YOUTUBE_VIDEO,
            uri="https://youtube.com/watch?v=test123",
            title="Test Video",
        )
        
        # Create
        temp_db.put_source(source)
        
        # Read
        retrieved = temp_db.get_source(nid)
        assert retrieved is not None
        assert retrieved.nid == nid
        assert retrieved.title == "Test Video"
        
        # Non-existent
        assert temp_db.get_source(99999) is None
    
    def test_iter_sources(self, temp_db: InceptionDB):
        """Test iterating over sources."""
        # Create multiple sources
        for i in range(5):
            nid = temp_db.allocate_nid()
            source = SourceRecord(
                nid=nid,
                source_type=SourceType.WEB_PAGE,
                uri=f"https://example.com/page{i}",
            )
            temp_db.put_source(source)
        
        # Iterate
        sources = list(temp_db.iter_sources())
        assert len(sources) == 5
    
    def test_span_with_temporal_index(self, temp_db: InceptionDB):
        """Test span storage with temporal indexing."""
        src_nid = temp_db.allocate_nid()
        
        # Create source first
        source = SourceRecord(
            nid=src_nid,
            source_type=SourceType.YOUTUBE_VIDEO,
            uri="https://youtube.com/watch?v=test",
        )
        temp_db.put_source(source)
        
        # Create spans at different timestamps
        spans = []
        for t in [0, 1000, 2000, 3000, 4000]:
            span_nid = temp_db.allocate_nid()
            span = SpanRecord(
                nid=span_nid,
                span_type=SpanType.VIDEO,
                source_nid=src_nid,
                anchor=VideoAnchor(t0_ms=t, t1_ms=t + 500),
                text=f"Content at {t}ms",
            )
            temp_db.put_span(span)
            spans.append(span)
        
        # Query by time range
        results = temp_db.query_spans_by_time(src_nid, 1000, 3000)
        assert len(results) >= 2  # Should include spans starting at 1000, 2000
    
    def test_node_crud(self, temp_db: InceptionDB):
        """Test node CRUD operations."""
        nid = temp_db.allocate_nid()
        node = NodeRecord(
            nid=nid,
            kind=NodeKind.CLAIM,
            payload={"text": "Python is great", "subject": "Python"},
            confidence=Confidence(aleatoric=0.9, epistemic=0.8),
            evidence_spans=[10, 11],
        )
        
        # Create
        temp_db.put_node(node)
        
        # Read
        retrieved = temp_db.get_node(nid)
        assert retrieved is not None
        assert retrieved.kind == NodeKind.CLAIM
        assert retrieved.payload["text"] == "Python is great"
    
    def test_edge_crud(self, temp_db: InceptionDB):
        """Test edge CRUD operations."""
        from_nid = temp_db.allocate_nid()
        to_nid = temp_db.allocate_nid()
        
        edge = EdgeRecord(
            edge_type=EdgeType.SUPPORTS,
            polarity=1,
            weight=0.9,
        )
        
        # Create
        temp_db.put_edge(from_nid, EdgeType.SUPPORTS, to_nid, edge)
        
        # Read
        retrieved = temp_db.get_edge(from_nid, EdgeType.SUPPORTS, to_nid)
        assert retrieved is not None
        assert retrieved.weight == 0.9
    
    def test_get_edges_from(self, temp_db: InceptionDB):
        """Test getting all edges from a node."""
        from_nid = temp_db.allocate_nid()
        
        # Create multiple edges
        for i, edge_type in enumerate([EdgeType.MENTIONS, EdgeType.SUPPORTS, EdgeType.REQUIRES]):
            to_nid = temp_db.allocate_nid()
            edge = EdgeRecord(edge_type=edge_type, weight=0.5 + i * 0.1)
            temp_db.put_edge(from_nid, edge_type, to_nid, edge)
        
        # Get all edges
        edges = temp_db.get_edges_from(from_nid)
        assert len(edges) == 3
        
        # Get filtered edges
        support_edges = temp_db.get_edges_from(from_nid, EdgeType.SUPPORTS)
        assert len(support_edges) == 1
    
    def test_graphtag_mapping(self, temp_db: InceptionDB):
        """Test graphtag to NID mapping."""
        nid = temp_db.allocate_nid()
        content = {"type": "claim", "text": "Test claim"}
        graphtag = compute_graphtag(content)
        
        # Store mapping
        temp_db.put_graphtag(graphtag, ObjectType.NODE, nid)
        
        # Retrieve
        result = temp_db.get_nid_by_graphtag(graphtag)
        assert result is not None
        obj_type, retrieved_nid = result
        assert obj_type == ObjectType.NODE
        assert retrieved_nid == nid
    
    def test_stats(self, temp_db: InceptionDB):
        """Test database statistics."""
        # Add some data
        for _ in range(3):
            nid = temp_db.allocate_nid()
            source = SourceRecord(
                nid=nid,
                source_type=SourceType.PDF,
                uri=f"/path/to/doc{nid}.pdf",
            )
            temp_db.put_source(source)
        
        stats = temp_db.stats()
        assert stats["src"] == 3
        assert stats["meta"] == 1
    
    def test_transaction_isolation(self, temp_db: InceptionDB):
        """Test that transactions are properly isolated."""
        nid = temp_db.allocate_nid()
        
        with temp_db.write_txn() as txn:
            source = SourceRecord(
                nid=nid,
                source_type=SourceType.WEB_PAGE,
                uri="https://example.com",
            )
            temp_db.put_source(source, txn)
            
            # Should be visible within transaction
            retrieved = temp_db.get_source(nid, txn)
            assert retrieved is not None
        
        # Should be visible after commit
        retrieved = temp_db.get_source(nid)
        assert retrieved is not None


class TestDatabasePersistence:
    """Tests for database persistence across restarts."""
    
    def test_data_persists(self):
        """Test that data persists after closing and reopening."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "persist_test"
            
            # Create and populate
            config = Config()
            config.lmdb.path = db_path
            db1 = InceptionDB(config=config)
            
            nid = db1.allocate_nid()
            source = SourceRecord(
                nid=nid,
                source_type=SourceType.YOUTUBE_VIDEO,
                uri="https://youtube.com/watch?v=persist",
                title="Persistence Test",
            )
            db1.put_source(source)
            db1.close()
            
            # Reopen and verify
            db2 = InceptionDB(config=config)
            retrieved = db2.get_source(nid)
            assert retrieved is not None
            assert retrieved.title == "Persistence Test"
            db2.close()
    
    def test_nid_allocation_persists(self):
        """Test that NID allocation continues from last value after restart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nid_test"
            
            config = Config()
            config.lmdb.path = db_path
            
            # Allocate some NIDs
            db1 = InceptionDB(config=config)
            for _ in range(10):
                nid = db1.allocate_nid()
                node = NodeRecord(
                    nid=nid,
                    kind=NodeKind.ENTITY,
                    payload={"name": f"Entity {nid}"},
                )
                db1.put_node(node)
            last_nid = nid
            db1.close()
            
            # Reopen and continue
            db2 = InceptionDB(config=config)
            new_nid = db2.allocate_nid()
            assert new_nid > last_nid
            db2.close()
