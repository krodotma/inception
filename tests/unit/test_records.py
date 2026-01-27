"""
Unit tests for record schemas.
"""

import pytest
from datetime import datetime

from inception.db.records import (
    Confidence,
    SpanQuality,
    VideoAnchor,
    DocumentAnchor,
    WebAnchor,
    IngestPolicy,
    MetaRecord,
    SourceRecord,
    ArtifactRecord,
    SpanRecord,
    NodeRecord,
    EdgeRecord,
    ClaimPayload,
    ProcedurePayload,
    ProcedureStep,
    EntityPayload,
    GapPayload,
)
from inception.db.keys import (
    SourceType,
    SpanType,
    NodeKind,
    EdgeType,
)


class TestConfidence:
    """Tests for Confidence model."""
    
    def test_default_values(self):
        """Test default confidence values."""
        conf = Confidence()
        assert conf.aleatoric == 1.0
        assert conf.epistemic == 1.0
    
    def test_combined_score(self):
        """Test combined confidence calculation."""
        conf = Confidence(aleatoric=0.8, epistemic=0.9)
        assert conf.combined == pytest.approx(0.72)
    
    def test_validation_bounds(self):
        """Test that values must be in [0, 1]."""
        with pytest.raises(ValueError):
            Confidence(aleatoric=1.5)
        with pytest.raises(ValueError):
            Confidence(epistemic=-0.1)


class TestAnchors:
    """Tests for anchor types."""
    
    def test_video_anchor(self):
        """Test VideoAnchor creation and duration."""
        anchor = VideoAnchor(t0_ms=1000, t1_ms=5000)
        assert anchor.kind == "time"
        assert anchor.duration_ms == 4000
    
    def test_document_anchor(self):
        """Test DocumentAnchor creation."""
        anchor = DocumentAnchor(page=5, x0=0.1, y0=0.2, x1=0.9, y1=0.8)
        assert anchor.kind == "page"
        assert anchor.page == 5
    
    def test_web_anchor(self):
        """Test WebAnchor creation."""
        anchor = WebAnchor(selector="div.content", char_start=100, char_end=500)
        assert anchor.kind == "web"
        assert anchor.selector == "div.content"


class TestMetaRecord:
    """Tests for MetaRecord."""
    
    def test_default_values(self):
        """Test default meta record values."""
        meta = MetaRecord()
        assert meta.schema_version == "0.1.0"
        assert "claims" in meta.capabilities
    
    def test_pack_unpack_roundtrip(self):
        """Test serialization roundtrip."""
        meta = MetaRecord(
            schema_version="0.2.0",
            pipeline_version="0.2.0",
            model_versions={"whisper": "large-v3"},
        )
        packed = meta.pack()
        unpacked = MetaRecord.unpack(packed)
        
        assert unpacked.schema_version == meta.schema_version
        assert unpacked.model_versions == meta.model_versions


class TestSourceRecord:
    """Tests for SourceRecord."""
    
    def test_creation(self):
        """Test source record creation."""
        source = SourceRecord(
            nid=1,
            source_type=SourceType.YOUTUBE_VIDEO,
            uri="https://youtube.com/watch?v=abc123",
            title="Test Video",
        )
        assert source.nid == 1
        assert source.source_type == SourceType.YOUTUBE_VIDEO
    
    def test_pack_unpack_roundtrip(self):
        """Test serialization roundtrip."""
        source = SourceRecord(
            nid=42,
            source_type=SourceType.PDF,
            uri="/path/to/document.pdf",
            content_hash="abc123",
            title="My Document",
            page_count=100,
        )
        packed = source.pack()
        unpacked = SourceRecord.unpack(packed)
        
        assert unpacked.nid == source.nid
        assert unpacked.source_type == source.source_type
        assert unpacked.title == source.title
        assert unpacked.page_count == source.page_count


class TestSpanRecord:
    """Tests for SpanRecord."""
    
    def test_video_span(self):
        """Test video span creation."""
        span = SpanRecord(
            nid=1,
            span_type=SpanType.VIDEO,
            source_nid=100,
            anchor=VideoAnchor(t0_ms=0, t1_ms=5000),
            text="Hello world",
        )
        assert span.span_type == SpanType.VIDEO
        assert span.anchor.kind == "time"
    
    def test_document_span(self):
        """Test document span creation."""
        span = SpanRecord(
            nid=2,
            span_type=SpanType.DOCUMENT,
            source_nid=100,
            anchor=DocumentAnchor(page=0),
            text="Page content",
        )
        assert span.span_type == SpanType.DOCUMENT
        assert span.anchor.kind == "page"
    
    def test_pack_unpack_roundtrip(self):
        """Test serialization roundtrip."""
        span = SpanRecord(
            nid=1,
            span_type=SpanType.VIDEO,
            source_nid=100,
            anchor=VideoAnchor(t0_ms=1000, t1_ms=2000),
            text="Test content",
            quality=SpanQuality(asr_confidence=0.95),
            scene_type="slide",
        )
        packed = span.pack()
        unpacked = SpanRecord.unpack(packed)
        
        assert unpacked.nid == span.nid
        assert unpacked.text == span.text
        assert unpacked.scene_type == span.scene_type


class TestNodeRecord:
    """Tests for NodeRecord."""
    
    def test_claim_node(self):
        """Test claim node creation."""
        payload = ClaimPayload(
            text="Python is a programming language",
            subject="Python",
            predicate="is",
            object="a programming language",
        )
        node = NodeRecord(
            nid=1,
            kind=NodeKind.CLAIM,
            payload=payload.model_dump(),
            evidence_spans=[10, 11],
            confidence=Confidence(aleatoric=0.9, epistemic=0.8),
        )
        assert node.kind == NodeKind.CLAIM
        
        claim = node.get_claim_payload()
        assert claim is not None
        assert claim.text == "Python is a programming language"
    
    def test_procedure_node(self):
        """Test procedure node creation."""
        payload = ProcedurePayload(
            title="Install Python",
            steps=[
                ProcedureStep(index=0, text="Download installer"),
                ProcedureStep(index=1, text="Run installer"),
            ],
        )
        node = NodeRecord(
            nid=2,
            kind=NodeKind.PROCEDURE,
            payload=payload.model_dump(),
        )
        
        proc = node.get_procedure_payload()
        assert proc is not None
        assert len(proc.steps) == 2
    
    def test_pack_unpack_roundtrip(self):
        """Test serialization roundtrip."""
        node = NodeRecord(
            nid=1,
            kind=NodeKind.ENTITY,
            payload=EntityPayload(
                name="Python",
                entity_type="PRODUCT",
                aliases=["CPython"],
            ).model_dump(),
            source_nids=[100],
        )
        packed = node.pack()
        unpacked = NodeRecord.unpack(packed)
        
        assert unpacked.nid == node.nid
        assert unpacked.kind == node.kind
        assert unpacked.payload["name"] == "Python"


class TestEdgeRecord:
    """Tests for EdgeRecord."""
    
    def test_creation(self):
        """Test edge record creation."""
        edge = EdgeRecord(
            edge_type=EdgeType.SUPPORTS,
            polarity=1,
            weight=0.9,
        )
        assert edge.edge_type == EdgeType.SUPPORTS
        assert edge.polarity == 1
    
    def test_pack_unpack_roundtrip(self):
        """Test serialization roundtrip."""
        edge = EdgeRecord(
            edge_type=EdgeType.CONTRADICTS,
            polarity=-1,
            weight=0.7,
            metadata={"reason": "temporal_conflict"},
        )
        packed = edge.pack()
        unpacked = EdgeRecord.unpack(packed)
        
        assert unpacked.edge_type == edge.edge_type
        assert unpacked.polarity == edge.polarity
        assert unpacked.metadata == edge.metadata
