"""
Record schemas for LMDB storage.

Each record type is defined as a Pydantic model for validation
and provides MessagePack serialization methods.
"""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Any, Literal

import msgpack
from pydantic import BaseModel, Field

from inception.db.keys import (
    EdgeType,
    NodeKind,
    SourceType,
    SpanType,
)


class Confidence(BaseModel):
    """Confidence scores split into aleatoric and epistemic components."""
    
    aleatoric: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence accounting for inherent noise/ambiguity (ASR errors, OCR blur)"
    )
    epistemic: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence accounting for missing information/context"
    )
    
    @property
    def combined(self) -> float:
        """Combined confidence score (product of both components)."""
        return self.aleatoric * self.epistemic


class SpanQuality(BaseModel):
    """Quality metrics for a span's extracted content."""
    
    asr_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    ocr_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    alignment_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class VideoAnchor(BaseModel):
    """Anchor for video/audio spans."""
    
    kind: Literal["time"] = "time"
    t0_ms: int = Field(description="Start time in milliseconds")
    t1_ms: int = Field(description="End time in milliseconds")
    
    @property
    def duration_ms(self) -> int:
        return self.t1_ms - self.t0_ms


class DocumentAnchor(BaseModel):
    """Anchor for document spans (PDF, PPTX, etc)."""
    
    kind: Literal["page"] = "page"
    page: int = Field(ge=0, description="Page number (0-indexed)")
    x0: float | None = Field(default=None, description="Left edge (0-1 normalized)")
    y0: float | None = Field(default=None, description="Top edge (0-1 normalized)")
    x1: float | None = Field(default=None, description="Right edge (0-1 normalized)")
    y1: float | None = Field(default=None, description="Bottom edge (0-1 normalized)")


class WebAnchor(BaseModel):
    """Anchor for web page spans."""
    
    kind: Literal["web"] = "web"
    selector: str | None = Field(default=None, description="CSS selector or XPath")
    block_id: str | None = Field(default=None, description="Readability block ID")
    char_start: int | None = Field(default=None, description="Character offset start")
    char_end: int | None = Field(default=None, description="Character offset end")


# Type alias for anchor union
Anchor = VideoAnchor | DocumentAnchor | WebAnchor


class IngestPolicy(BaseModel):
    """Policy for how to ingest a source."""
    
    allow_download: bool = True
    max_depth: int = 1  # For web crawling
    topic_rules: list[str] = Field(default_factory=list)
    date_since: datetime | None = None
    date_until: datetime | None = None


class MetaRecord(BaseModel):
    """Metadata record for the database."""
    
    schema_version: str = "0.1.0"
    pipeline_version: str = "0.1.0"
    model_versions: dict[str, str] = Field(default_factory=dict)
    capabilities: list[str] = Field(
        default_factory=lambda: ["claims", "procedures", "entities"]
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    
    def pack(self) -> bytes:
        """Serialize to MessagePack."""
        return msgpack.packb(self.model_dump(mode="json"))
    
    @classmethod
    def unpack(cls, data: bytes) -> MetaRecord:
        """Deserialize from MessagePack."""
        return cls.model_validate(msgpack.unpackb(data))


class SourceRecord(BaseModel):
    """Record for an ingested source (URL, file, etc)."""
    
    nid: int = Field(description="Numeric ID")
    source_type: SourceType
    uri: str = Field(description="Original URI or file path")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    content_hash: str | None = Field(default=None, description="SHA256 of content")
    license_hint: str | None = Field(default=None)
    ingest_policy: IngestPolicy = Field(default_factory=IngestPolicy)
    parent_nid: int | None = Field(default=None, description="Parent source (channel/playlist)")
    
    # Metadata from source
    title: str | None = None
    description: str | None = None
    author: str | None = None
    duration_ms: int | None = None  # For video/audio
    page_count: int | None = None  # For documents
    
    def pack(self) -> bytes:
        """Serialize to MessagePack."""
        return msgpack.packb(self.model_dump(mode="json"))
    
    @classmethod
    def unpack(cls, data: bytes) -> SourceRecord:
        """Deserialize from MessagePack."""
        return cls.model_validate(msgpack.unpackb(data))


class ArtifactRecord(BaseModel):
    """Record for a raw artifact (downloaded file, extracted keyframe, etc)."""
    
    nid: int = Field(description="Numeric ID")
    source_nid: int = Field(description="Source this artifact belongs to")
    artifact_type: str = Field(description="Type: video, audio, image, transcript, etc")
    path: str = Field(description="Relative path to artifact file")
    content_hash: str = Field(description="SHA256 of file content")
    mime_type: str | None = None
    size_bytes: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def pack(self) -> bytes:
        """Serialize to MessagePack."""
        return msgpack.packb(self.model_dump(mode="json"))
    
    @classmethod
    def unpack(cls, data: bytes) -> ArtifactRecord:
        """Deserialize from MessagePack."""
        return cls.model_validate(msgpack.unpackb(data))


class SpanRecord(BaseModel):
    """Record for a temporal or spatial span in a source."""
    
    nid: int = Field(description="Numeric ID")
    span_type: SpanType
    source_nid: int = Field(description="Source this span belongs to")
    anchor: Anchor = Field(description="Location anchor (time, page, web)")
    artifact_nids: list[int] = Field(default_factory=list, description="Related artifacts")
    text: str | None = Field(default=None, description="Extracted text content")
    quality: SpanQuality = Field(default_factory=SpanQuality)
    
    # Optional scene/segment metadata
    scene_type: str | None = Field(default=None, description="slide, talking_head, diagram, code, etc")
    keyframe_path: str | None = Field(default=None, description="Path to keyframe image")
    
    def pack(self) -> bytes:
        """Serialize to MessagePack."""
        data = self.model_dump(mode="json")
        return msgpack.packb(data)
    
    @classmethod
    def unpack(cls, data: bytes) -> SpanRecord:
        """Deserialize from MessagePack."""
        return cls.model_validate(msgpack.unpackb(data))


class ClaimPayload(BaseModel):
    """Payload for a claim node."""
    
    text: str = Field(description="Normalized claim statement")
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    hedging: list[str] = Field(default_factory=list, description="Hedging words found")
    negated: bool = False


class ProcedureStep(BaseModel):
    """A single step in a procedure."""
    
    index: int
    text: str
    prerequisites: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProcedurePayload(BaseModel):
    """Payload for a procedure node."""
    
    title: str
    steps: list[ProcedureStep]
    prerequisites: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)


class EntityPayload(BaseModel):
    """Payload for an entity node."""
    
    name: str
    entity_type: str = Field(description="PERSON, ORG, PRODUCT, CONCEPT, etc")
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None


class GapPayload(BaseModel):
    """Payload for a gap node (explicit missing knowledge)."""
    
    gap_kind: Literal["epistemic", "aleatoric"]
    description: str
    blocking_nids: list[int] = Field(default_factory=list, description="Claims blocked by this gap")
    resolution_hints: list[str] = Field(default_factory=list)


class SignPayload(BaseModel):
    """Payload for a semiotic sign node."""
    
    sign_type: str = Field(description="diagram, chart, code, icon, etc")
    signifier: str = Field(description="What is observed")
    signified: str = Field(description="What it represents")
    interpretant: str | None = Field(default=None, description="How to act on it")


# Type alias for payload union
NodePayload = ClaimPayload | ProcedurePayload | EntityPayload | GapPayload | SignPayload | dict[str, Any]


class NodeRecord(BaseModel):
    """Record for a semantic node in the knowledge graph."""
    
    nid: int = Field(description="Numeric ID")
    kind: NodeKind
    payload: dict[str, Any] = Field(description="Kind-specific content")
    evidence_spans: list[int] = Field(default_factory=list, description="Span NIDs as evidence")
    confidence: Confidence = Field(default_factory=Confidence)
    source_nids: list[int] = Field(default_factory=list, description="Source NIDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Verification state
    verification_state: Literal["unverified", "internal", "corroborated", "contradicted"] = "unverified"
    
    def pack(self) -> bytes:
        """Serialize to MessagePack."""
        return msgpack.packb(self.model_dump(mode="json"))
    
    @classmethod
    def unpack(cls, data: bytes) -> NodeRecord:
        """Deserialize from MessagePack."""
        return cls.model_validate(msgpack.unpackb(data))
    
    def get_claim_payload(self) -> ClaimPayload | None:
        """Get payload as ClaimPayload if this is a claim node."""
        if self.kind != NodeKind.CLAIM:
            return None
        return ClaimPayload.model_validate(self.payload)
    
    def get_procedure_payload(self) -> ProcedurePayload | None:
        """Get payload as ProcedurePayload if this is a procedure node."""
        if self.kind != NodeKind.PROCEDURE:
            return None
        return ProcedurePayload.model_validate(self.payload)


class EdgeRecord(BaseModel):
    """Record for a relationship edge in the knowledge graph."""
    
    edge_type: EdgeType
    polarity: int = Field(default=0, ge=-1, le=1, description="-1, 0, or +1")
    weight: float = Field(default=1.0, ge=0.0)
    valid_time_start: datetime | None = None
    valid_time_end: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def pack(self) -> bytes:
        """Serialize to MessagePack."""
        return msgpack.packb(self.model_dump(mode="json"))
    
    @classmethod
    def unpack(cls, data: bytes) -> EdgeRecord:
        """Deserialize from MessagePack."""
        return cls.model_validate(msgpack.unpackb(data))


class ConflictSet(BaseModel):
    """A set of contradicting claims."""
    
    claim_nids: list[int] = Field(min_length=2)
    conflict_type: Literal["correction", "supersession", "disagreement"]
    evidence_summary: str
    resolution_hint: str | None = None
    
    def pack(self) -> bytes:
        """Serialize to MessagePack."""
        return msgpack.packb(self.model_dump(mode="json"))
    
    @classmethod
    def unpack(cls, data: bytes) -> ConflictSet:
        """Deserialize from MessagePack."""
        return cls.model_validate(msgpack.unpackb(data))
