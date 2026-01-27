"""
Graph builder module.

Constructs the knowledge hypergraph from extracted semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from inception.db import InceptionDB, get_db
from inception.db.records import (
    SourceRecord,
    SpanRecord,
    NodeRecord,
    EdgeRecord,
    Confidence,
    VideoAnchor,
)
from inception.db.keys import (
    SourceType,
    SpanType,
    NodeKind,
    EdgeType,
    ObjectType,
)
from inception.db.graphtag import compute_graphtag

from inception.analyze.entities import Entity, EntityExtractionResult
from inception.analyze.claims import Claim, ClaimExtractionResult
from inception.analyze.procedures import Procedure, ProcedureExtractionResult
from inception.analyze.gaps import Gap, GapDetectionResult


@dataclass
class GraphBuildResult:
    """Result of graph building operation."""
    
    source_nid: int
    
    # Created records
    span_nids: list[int] = field(default_factory=list)
    node_nids: list[int] = field(default_factory=list)
    edge_count: int = 0
    
    # Statistics
    entity_count: int = 0
    claim_count: int = 0
    procedure_count: int = 0
    gap_count: int = 0


class GraphBuilder:
    """
    Builder for knowledge hypergraph.
    
    Takes extracted semantics and constructs nodes, edges, and spans.
    """
    
    def __init__(self, db: InceptionDB | None = None):
        """
        Initialize the builder.
        
        Args:
            db: Database instance (uses default if not provided)
        """
        self.db = db or get_db()
    
    def build_from_extraction(
        self,
        source_nid: int,
        spans: list[dict[str, Any]],
        entities: EntityExtractionResult | None = None,
        claims: ClaimExtractionResult | None = None,
        procedures: ProcedureExtractionResult | None = None,
        gaps: GapDetectionResult | None = None,
    ) -> GraphBuildResult:
        """
        Build graph from extracted components.
        
        Args:
            source_nid: Source record NID
            spans: List of span data dicts
            entities: Extracted entities
            claims: Extracted claims
            procedures: Extracted procedures
            gaps: Detected gaps
        
        Returns:
            GraphBuildResult with created record info
        """
        result = GraphBuildResult(source_nid=source_nid)
        
        with self.db.write_txn() as txn:
            # Create span records
            span_nid_map: dict[int, int] = {}  # index -> nid
            for i, span_data in enumerate(spans):
                span_nid = self._create_span(source_nid, span_data, txn)
                span_nid_map[i] = span_nid
                result.span_nids.append(span_nid)
            
            # Create entity nodes
            entity_nid_map: dict[str, int] = {}  # normalized text -> nid
            if entities:
                for entity in entities.get_unique_entities():
                    node_nid = self._create_entity_node(entity, source_nid, txn)
                    entity_nid_map[entity.normalized or entity.text.lower()] = node_nid
                    result.node_nids.append(node_nid)
                    result.entity_count += 1
            
            # Create claim nodes
            claim_nid_map: dict[int, int] = {}  # sentence_idx -> nid
            if claims:
                for claim in claims.claims:
                    # Find relevant span
                    evidence_spans = self._find_spans_for_range(
                        span_nid_map, spans, claim.start_char, claim.end_char
                    )
                    
                    node_nid = self._create_claim_node(claim, source_nid, evidence_spans, txn)
                    claim_nid_map[claim.sentence_idx] = node_nid
                    result.node_nids.append(node_nid)
                    result.claim_count += 1
                    
                    # Create edges to mentioned entities
                    for entity_text, entity_nid in entity_nid_map.items():
                        if entity_text in claim.text.lower():
                            self._create_edge(
                                node_nid, EdgeType.MENTIONS, entity_nid,
                                weight=0.8, txn=txn
                            )
                            result.edge_count += 1
            
            # Create procedure nodes
            if procedures:
                for procedure in procedures.procedures:
                    node_nid = self._create_procedure_node(procedure, source_nid, txn)
                    result.node_nids.append(node_nid)
                    result.procedure_count += 1
            
            # Create gap nodes
            if gaps:
                for gap in gaps.gaps:
                    node_nid = self._create_gap_node(gap, source_nid, txn)
                    result.node_nids.append(node_nid)
                    result.gap_count += 1
            
            # Infer edges between claims
            if claims and len(claims.claims) > 1:
                edge_count = self._infer_claim_edges(
                    claims.claims, claim_nid_map, txn
                )
                result.edge_count += edge_count
        
        return result
    
    def _create_span(
        self,
        source_nid: int,
        span_data: dict[str, Any],
        txn,
    ) -> int:
        """Create a span record."""
        nid = self.db.allocate_nid()
        
        # Determine span type and anchor
        span_type = SpanType.VIDEO
        anchor: Any = VideoAnchor(
            t0_ms=span_data.get("start_ms", 0),
            t1_ms=span_data.get("end_ms", 0),
        )
        
        span = SpanRecord(
            nid=nid,
            span_type=span_type,
            source_nid=source_nid,
            anchor=anchor,
            text=span_data.get("text"),
            scene_type=span_data.get("scene_type"),
        )
        
        self.db.put_span(span, txn)
        
        # Index by time
        if span_data.get("start_ms") is not None:
            self.db.index_span_by_time(
                source_nid, span_data["start_ms"], nid, txn
            )
        
        return nid
    
    def _create_entity_node(
        self,
        entity: Entity,
        source_nid: int,
        txn,
    ) -> int:
        """Create an entity node."""
        nid = self.db.allocate_nid()
        
        payload = {
            "name": entity.text,
            "entity_type": entity.entity_type,
            "normalized": entity.normalized,
        }
        
        if entity.wikidata_id:
            payload["wikidata_id"] = entity.wikidata_id
        
        node = NodeRecord(
            nid=nid,
            kind=NodeKind.ENTITY,
            payload=payload,
            source_nids=[source_nid],
            confidence=Confidence(epistemic=entity.confidence),
        )
        
        self.db.put_node(node, txn)
        
        # Store graphtag mapping
        graphtag = compute_graphtag(payload)
        self.db.put_graphtag(graphtag, ObjectType.NODE, nid, txn)
        
        return nid
    
    def _create_claim_node(
        self,
        claim: Claim,
        source_nid: int,
        evidence_spans: list[int],
        txn,
    ) -> int:
        """Create a claim node."""
        nid = self.db.allocate_nid()
        
        payload = {
            "text": claim.text,
            "subject": claim.subject,
            "predicate": claim.predicate,
            "object": claim.object,
            "modality": claim.modality,
            "hedges": claim.hedges,
        }
        
        node = NodeRecord(
            nid=nid,
            kind=NodeKind.CLAIM,
            payload=payload,
            evidence_spans=evidence_spans,
            source_nids=[source_nid],
            confidence=claim.confidence,
        )
        
        self.db.put_node(node, txn)
        
        return nid
    
    def _create_procedure_node(
        self,
        procedure: Procedure,
        source_nid: int,
        txn,
    ) -> int:
        """Create a procedure node."""
        nid = self.db.allocate_nid()
        
        steps = []
        for step in procedure.steps:
            steps.append({
                "index": step.index,
                "text": step.text,
                "action_verb": step.action_verb,
            })
        
        payload = {
            "title": procedure.title,
            "goal": procedure.goal,
            "steps": steps,
            "prerequisites": procedure.prerequisites,
        }
        
        node = NodeRecord(
            nid=nid,
            kind=NodeKind.PROCEDURE,
            payload=payload,
            source_nids=[source_nid],
            confidence=procedure.confidence,
        )
        
        self.db.put_node(node, txn)
        
        return nid
    
    def _create_gap_node(
        self,
        gap: Gap,
        source_nid: int,
        txn,
    ) -> int:
        """Create a gap node."""
        nid = self.db.allocate_nid()
        
        payload = {
            "gap_type": gap.gap_type.value,
            "description": gap.description,
            "context": gap.context_text,
            "severity": gap.severity,
            "is_aleatoric": gap.is_aleatoric,
            "is_epistemic": gap.is_epistemic,
        }
        
        node = NodeRecord(
            nid=nid,
            kind=NodeKind.GAP,
            payload=payload,
            source_nids=[source_nid],
            confidence=Confidence(epistemic=gap.confidence),
        )
        
        self.db.put_node(node, txn)
        
        return nid
    
    def _create_edge(
        self,
        from_nid: int,
        edge_type: EdgeType,
        to_nid: int,
        weight: float = 1.0,
        polarity: int = 1,
        txn=None,
    ) -> None:
        """Create an edge between nodes."""
        edge = EdgeRecord(
            edge_type=edge_type,
            polarity=polarity,
            weight=weight,
        )
        self.db.put_edge(from_nid, edge_type, to_nid, edge, txn)
    
    def _find_spans_for_range(
        self,
        span_nid_map: dict[int, int],
        spans: list[dict[str, Any]],
        start_char: int,
        end_char: int,
    ) -> list[int]:
        """Find span NIDs that cover a character range."""
        # For now, return all spans (simplified)
        # In a real implementation, we'd track char offsets per span
        return list(span_nid_map.values())[:1]  # First span for now
    
    def _infer_claim_edges(
        self,
        claims: list[Claim],
        claim_nid_map: dict[int, int],
        txn,
    ) -> int:
        """Infer edges between claims."""
        edge_count = 0
        
        from inception.analyze.claims import compute_claim_similarity, detect_contradiction
        
        for i, claim1 in enumerate(claims):
            for j, claim2 in enumerate(claims):
                if i >= j:
                    continue
                
                nid1 = claim_nid_map.get(claim1.sentence_idx)
                nid2 = claim_nid_map.get(claim2.sentence_idx)
                
                if not nid1 or not nid2:
                    continue
                
                # Check for contradiction
                is_contradiction, conf = detect_contradiction(claim1, claim2)
                if is_contradiction and conf > 0.5:
                    self._create_edge(
                        nid1, EdgeType.CONTRADICTS, nid2,
                        weight=conf, polarity=-1, txn=txn
                    )
                    edge_count += 1
                    continue
                
                # Check for similarity (potential support)
                similarity = compute_claim_similarity(claim1, claim2)
                if similarity > 0.5:
                    self._create_edge(
                        nid1, EdgeType.RELATED_TO, nid2,
                        weight=similarity, txn=txn
                    )
                    edge_count += 1
        
        return edge_count


def build_graph(
    source_nid: int,
    spans: list[dict[str, Any]],
    entities: EntityExtractionResult | None = None,
    claims: ClaimExtractionResult | None = None,
    procedures: ProcedureExtractionResult | None = None,
    gaps: GapDetectionResult | None = None,
) -> GraphBuildResult:
    """
    Convenience function to build graph from extractions.
    
    Args:
        source_nid: Source record NID
        spans: Span data
        entities: Entity extraction result
        claims: Claim extraction result
        procedures: Procedure extraction result
        gaps: Gap detection result
    
    Returns:
        GraphBuildResult
    """
    builder = GraphBuilder()
    return builder.build_from_extraction(
        source_nid, spans, entities, claims, procedures, gaps
    )
