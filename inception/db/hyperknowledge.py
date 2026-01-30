"""
HyperKnowledge Architecture - Core Data Structures
Phase 5, Steps 121-125

Implements:
- KnowledgeHyperGraph schema
- VersionedContent DAG
- SourceChain provenance
- AllenInterval storage
- UncertaintyModel
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional, TypeVar, Generic

# =============================================================================
# Step 121: KnowledgeHyperGraph Schema
# =============================================================================

class NodeType(Enum):
    """Types of nodes in the hypergraph."""
    ENTITY = auto()
    CLAIM = auto()
    PROCEDURE = auto()
    SKILL = auto()
    SOURCE = auto()
    GAP = auto()
    CONCEPT = auto()
    EVENT = auto()


class EdgeType(Enum):
    """Types of edges/hyperedges."""
    ASSERTS = auto()      # source → claim
    MENTIONS = auto()     # source → entity
    REQUIRES = auto()     # procedure → entity/skill
    CONFLICTS = auto()    # claim ↔ claim
    SUPPORTS = auto()     # claim → claim
    TEMPORAL = auto()     # event → event (Allen relation)
    DERIVED = auto()      # claim → claim (inference)
    RESOLVES = auto()     # source → gap


@dataclass
class HyperNode:
    """A node in the hypergraph with versioned content."""
    id: str
    node_type: NodeType
    content: VersionedContent
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Temporal validity
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    # Uncertainty
    uncertainty: Optional[UncertaintyModel] = None
    
    # Provenance
    source_chain: Optional[SourceChain] = None
    
    def content_hash(self) -> str:
        """Get hash of current content version."""
        return self.content.current_hash()


@dataclass
class HyperEdge:
    """A hyperedge connecting multiple nodes."""
    id: str
    edge_type: EdgeType
    source_ids: list[str]
    target_ids: list[str]
    weight: float = 1.0
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # For temporal edges
    allen_relation: Optional[AllenRelation] = None


@dataclass
class KnowledgeHyperGraph:
    """
    The core hypergraph structure with versioning, provenance, and temporality.
    Schema: HyperKG = (N, E, V, S, T, U)
    where:
      N = set of HyperNodes
      E = set of HyperEdges
      V = VersionDAG for each node
      S = SourceChain provenance
      T = Temporal intervals (Allen)
      U = Uncertainty model
    """
    
    nodes: dict[str, HyperNode] = field(default_factory=dict)
    edges: dict[str, HyperEdge] = field(default_factory=dict)
    
    # Global version management
    version_dag: VersionDAG = field(default_factory=lambda: VersionDAG())
    current_commit: Optional[str] = None
    
    def add_node(self, node: HyperNode) -> str:
        """Add a node to the hypergraph."""
        self.nodes[node.id] = node
        return node.id
    
    def add_edge(self, edge: HyperEdge) -> str:
        """Add a hyperedge to the hypergraph."""
        self.edges[edge.id] = edge
        return edge.id
    
    def get_node(self, node_id: str) -> Optional[HyperNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_edges_for_node(self, node_id: str) -> list[HyperEdge]:
        """Get all edges connected to a node."""
        return [
            e for e in self.edges.values()
            if node_id in e.source_ids or node_id in e.target_ids
        ]
    
    def query_at(self, timestamp: datetime) -> KnowledgeHyperGraph:
        """Return a view of the graph at a specific timestamp."""
        filtered = KnowledgeHyperGraph()
        
        for node in self.nodes.values():
            if node.valid_from and node.valid_from > timestamp:
                continue
            if node.valid_until and node.valid_until < timestamp:
                continue
            filtered.nodes[node.id] = node
        
        for edge in self.edges.values():
            if all(sid in filtered.nodes for sid in edge.source_ids):
                if all(tid in filtered.nodes for tid in edge.target_ids):
                    filtered.edges[edge.id] = edge
        
        return filtered
    
    def get_statistics(self) -> dict[str, Any]:
        """Get hypergraph statistics."""
        type_counts = {}
        for node in self.nodes.values():
            t = node.node_type.name
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": type_counts,
            "current_commit": self.current_commit,
        }


# =============================================================================
# Step 122: VersionedContent DAG
# =============================================================================

@dataclass
class ContentVersion:
    """A single version of content."""
    hash: str
    content: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    author: str = "system"
    message: str = ""
    parent_hashes: list[str] = field(default_factory=list)
    
    @staticmethod
    def compute_hash(content: Any) -> str:
        """Compute content hash."""
        if isinstance(content, str):
            data = content.encode()
        else:
            data = str(content).encode()
        return hashlib.sha256(data).hexdigest()[:16]


@dataclass
class VersionedContent:
    """
    Git-like versioned content with DAG structure.
    Supports branching, merging, and history traversal.
    """
    
    versions: dict[str, ContentVersion] = field(default_factory=dict)
    head: Optional[str] = None
    branches: dict[str, str] = field(default_factory=dict)  # name → hash
    
    def __init__(self, initial_content: Any = None):
        self.versions = {}
        self.head = None
        self.branches = {"main": None}
        
        if initial_content is not None:
            self.commit(initial_content, "Initial version")
    
    def commit(
        self,
        content: Any,
        message: str = "",
        author: str = "system",
        branch: str = "main",
    ) -> str:
        """Create a new version."""
        content_hash = ContentVersion.compute_hash(content)
        
        parent_hashes = []
        if self.head:
            parent_hashes.append(self.head)
        
        version = ContentVersion(
            hash=content_hash,
            content=content,
            author=author,
            message=message,
            parent_hashes=parent_hashes,
        )
        
        self.versions[content_hash] = version
        self.head = content_hash
        self.branches[branch] = content_hash
        
        return content_hash
    
    def get(self, version_hash: Optional[str] = None) -> Any:
        """Get content at a specific version (or head)."""
        h = version_hash or self.head
        if h and h in self.versions:
            return self.versions[h].content
        return None
    
    def current_hash(self) -> str:
        """Get current head hash."""
        return self.head or ""
    
    def history(self, limit: int = 10) -> list[ContentVersion]:
        """Get version history from head."""
        result = []
        current = self.head
        
        while current and len(result) < limit:
            if current in self.versions:
                v = self.versions[current]
                result.append(v)
                current = v.parent_hashes[0] if v.parent_hashes else None
            else:
                break
        
        return result
    
    def diff(self, hash_a: str, hash_b: str) -> dict[str, Any]:
        """Compare two versions."""
        a = self.versions.get(hash_a)
        b = self.versions.get(hash_b)
        
        if not a or not b:
            return {"error": "Version not found"}
        
        return {
            "from": hash_a,
            "to": hash_b,
            "content_a": a.content,
            "content_b": b.content,
            "changed": a.content != b.content,
        }
    
    def create_branch(self, name: str, from_hash: Optional[str] = None) -> str:
        """Create a new branch."""
        base = from_hash or self.head
        self.branches[name] = base
        return base or ""
    
    def merge(self, source_branch: str, target_branch: str = "main") -> str:
        """Merge source branch into target."""
        source_hash = self.branches.get(source_branch)
        target_hash = self.branches.get(target_branch)
        
        if not source_hash:
            raise ValueError(f"Branch {source_branch} not found")
        
        source_content = self.versions[source_hash].content
        
        # Simple merge: just use source content
        # In production, would do 3-way merge
        merged_hash = self.commit(
            source_content,
            f"Merge {source_branch} into {target_branch}",
            branch=target_branch,
        )
        
        # Add both parents
        self.versions[merged_hash].parent_hashes = [target_hash, source_hash]
        
        return merged_hash


# =============================================================================
# Step 123: SourceChain Provenance
# =============================================================================

@dataclass
class SourceReference:
    """A reference to a source of information."""
    source_id: str
    source_type: str  # 'video', 'webpage', 'pdf', 'rfc', 'book'
    title: str
    url: Optional[str] = None
    timestamp: Optional[str] = None  # e.g., "3:42" for video
    page_ref: Optional[str] = None   # e.g., "§1.4" for RFC
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    authority: float = 0.5
    freshness: float = 0.5


@dataclass
class ProvenanceStep:
    """A single step in the provenance chain."""
    step_id: str
    action: str  # 'extracted', 'inferred', 'fused', 'validated'
    agent: str   # which agent/system performed this
    timestamp: datetime = field(default_factory=datetime.utcnow)
    input_refs: list[str] = field(default_factory=list)
    output_ref: Optional[str] = None
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceChain:
    """
    Complete provenance chain tracking how knowledge was derived.
    Follows the chain: Source → Extract → Infer → Fuse → Validate
    """
    
    chain_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sources: list[SourceReference] = field(default_factory=list)
    steps: list[ProvenanceStep] = field(default_factory=list)
    
    def add_source(self, source: SourceReference) -> None:
        """Add a source reference."""
        self.sources.append(source)
    
    def add_step(self, step: ProvenanceStep) -> None:
        """Add a provenance step."""
        self.steps.append(step)
    
    def get_root_sources(self) -> list[SourceReference]:
        """Get original sources at the root of the chain."""
        return self.sources
    
    def get_derivation_path(self) -> list[str]:
        """Get the sequence of actions in derivation."""
        return [s.action for s in self.steps]
    
    def compute_aggregate_confidence(self) -> float:
        """Compute confidence through the chain."""
        if not self.steps:
            return 1.0
        
        # Multiply confidences (conservative)
        conf = 1.0
        for step in self.steps:
            conf *= step.confidence
        
        return conf
    
    def to_summary(self) -> dict[str, Any]:
        """Get provenance summary."""
        return {
            "chain_id": self.chain_id,
            "source_count": len(self.sources),
            "step_count": len(self.steps),
            "derivation_path": self.get_derivation_path(),
            "aggregate_confidence": self.compute_aggregate_confidence(),
        }


# =============================================================================
# Step 124: AllenInterval Storage
# =============================================================================

class AllenRelation(Enum):
    """Allen's 13 interval relations."""
    BEFORE = "before"           # A ends before B starts
    AFTER = "after"            # A starts after B ends
    MEETS = "meets"            # A ends exactly when B starts
    MET_BY = "met_by"          # A starts exactly when B ends
    OVERLAPS = "overlaps"      # A starts before B, A ends during B
    OVERLAPPED_BY = "overlapped_by"
    STARTS = "starts"          # A starts with B, A ends before B
    STARTED_BY = "started_by"
    DURING = "during"          # A is contained within B
    CONTAINS = "contains"      # A contains B
    FINISHES = "finishes"      # A ends with B, A starts after B
    FINISHED_BY = "finished_by"
    EQUALS = "equals"          # A and B are identical


@dataclass
class AllenInterval:
    """
    A temporal interval with Allen relation support.
    Represents a validity window for knowledge.
    """
    
    interval_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    start: datetime = field(default_factory=datetime.utcnow)
    end: Optional[datetime] = None  # None = ongoing
    
    # Optional precision markers
    start_precision: str = "exact"  # exact, approximate, unknown
    end_precision: str = "exact"
    
    @property
    def is_ongoing(self) -> bool:
        """Check if interval is still active."""
        return self.end is None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get duration in seconds."""
        if self.end is None:
            return None
        return (self.end - self.start).total_seconds()
    
    def contains_point(self, point: datetime) -> bool:
        """Check if a point in time is within this interval."""
        if point < self.start:
            return False
        if self.end and point > self.end:
            return False
        return True
    
    def relation_to(self, other: AllenInterval) -> AllenRelation:
        """Compute Allen relation to another interval."""
        a_start, a_end = self.start, self.end or datetime.max
        b_start, b_end = other.start, other.end or datetime.max
        
        if a_end < b_start:
            return AllenRelation.BEFORE
        if a_start > b_end:
            return AllenRelation.AFTER
        if a_end == b_start:
            return AllenRelation.MEETS
        if a_start == b_end:
            return AllenRelation.MET_BY
        if a_start == b_start and a_end == b_end:
            return AllenRelation.EQUALS
        if a_start == b_start and a_end < b_end:
            return AllenRelation.STARTS
        if a_start == b_start and a_end > b_end:
            return AllenRelation.STARTED_BY
        if a_end == b_end and a_start > b_start:
            return AllenRelation.FINISHES
        if a_end == b_end and a_start < b_start:
            return AllenRelation.FINISHED_BY
        if a_start > b_start and a_end < b_end:
            return AllenRelation.DURING
        if a_start < b_start and a_end > b_end:
            return AllenRelation.CONTAINS
        if a_start < b_start and a_end < b_end and a_end > b_start:
            return AllenRelation.OVERLAPS
        return AllenRelation.OVERLAPPED_BY


@dataclass
class TemporalIndex:
    """Index for efficient temporal queries."""
    
    intervals: dict[str, AllenInterval] = field(default_factory=dict)
    entity_intervals: dict[str, list[str]] = field(default_factory=dict)  # entity_id → interval_ids
    
    def add_interval(self, entity_id: str, interval: AllenInterval) -> None:
        """Add an interval for an entity."""
        self.intervals[interval.interval_id] = interval
        if entity_id not in self.entity_intervals:
            self.entity_intervals[entity_id] = []
        self.entity_intervals[entity_id].append(interval.interval_id)
    
    def query_at(self, point: datetime) -> list[str]:
        """Get all entity IDs valid at a point in time."""
        valid = []
        for entity_id, interval_ids in self.entity_intervals.items():
            for iid in interval_ids:
                interval = self.intervals.get(iid)
                if interval and interval.contains_point(point):
                    valid.append(entity_id)
                    break
        return valid
    
    def query_range(self, start: datetime, end: datetime) -> list[str]:
        """Get all entity IDs valid during a range."""
        range_interval = AllenInterval(start=start, end=end)
        valid = []
        
        for entity_id, interval_ids in self.entity_intervals.items():
            for iid in interval_ids:
                interval = self.intervals.get(iid)
                if interval:
                    rel = interval.relation_to(range_interval)
                    if rel not in (AllenRelation.BEFORE, AllenRelation.AFTER):
                        valid.append(entity_id)
                        break
        
        return valid


# =============================================================================
# Step 125: UncertaintyModel
# =============================================================================

@dataclass
class UncertaintyModel:
    """
    Dual-uncertainty model: epistemic (knowledge) + aleatoric (inherent).
    
    Epistemic: Reducible uncertainty due to lack of knowledge
    Aleatoric: Irreducible uncertainty inherent to the phenomenon
    """
    
    epistemic: float = 0.5  # 0-1, higher = more certain about our knowledge
    aleatoric: float = 0.5  # 0-1, higher = phenomenon is less random
    
    # Confidence from different sources
    source_confidences: dict[str, float] = field(default_factory=dict)
    
    # Conflict tracking
    has_conflict: bool = False
    conflict_sources: list[str] = field(default_factory=list)
    
    @property
    def combined(self) -> float:
        """Combined confidence score."""
        return (self.epistemic + self.aleatoric) / 2
    
    @property
    def certainty_level(self) -> str:
        """Human-readable certainty level."""
        c = self.combined
        if c > 0.9:
            return "very_high"
        if c > 0.7:
            return "high"
        if c > 0.5:
            return "moderate"
        if c > 0.3:
            return "low"
        return "very_low"
    
    def update_from_source(self, source_id: str, confidence: float) -> None:
        """Update uncertainty based on a source."""
        self.source_confidences[source_id] = confidence
        
        # Recompute epistemic based on source agreement
        if len(self.source_confidences) > 1:
            values = list(self.source_confidences.values())
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            
            # High variance = conflict = lower epistemic
            if variance > 0.1:
                self.has_conflict = True
                self.epistemic = max(0.1, mean - variance)
            else:
                self.epistemic = mean
    
    def fuse_with(self, other: UncertaintyModel) -> UncertaintyModel:
        """Fuse two uncertainty models (Bayesian-ish)."""
        # Combine source confidences
        merged_sources = {**self.source_confidences, **other.source_confidences}
        
        # Weighted average based on source count
        n1, n2 = len(self.source_confidences) or 1, len(other.source_confidences) or 1
        total = n1 + n2
        
        fused = UncertaintyModel(
            epistemic=(self.epistemic * n1 + other.epistemic * n2) / total,
            aleatoric=(self.aleatoric * n1 + other.aleatoric * n2) / total,
            source_confidences=merged_sources,
            has_conflict=self.has_conflict or other.has_conflict,
            conflict_sources=self.conflict_sources + other.conflict_sources,
        )
        
        return fused
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "epistemic": self.epistemic,
            "aleatoric": self.aleatoric,
            "combined": self.combined,
            "certainty_level": self.certainty_level,
            "has_conflict": self.has_conflict,
            "source_count": len(self.source_confidences),
        }


# =============================================================================
# Step 126: VersionDAG (git-like)
# =============================================================================

@dataclass
class Commit:
    """A commit in the version DAG."""
    hash: str
    message: str
    author: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    parent_hashes: list[str] = field(default_factory=list)
    
    # Snapshot of changed node IDs
    changed_nodes: list[str] = field(default_factory=list)
    changed_edges: list[str] = field(default_factory=list)
    
    # Full graph snapshot (optional, for checkpointing)
    snapshot: Optional[dict[str, Any]] = None


@dataclass
class VersionDAG:
    """
    Git-like version control for the entire hypergraph.
    Supports commits, branches, and time-travel queries.
    """
    
    commits: dict[str, Commit] = field(default_factory=dict)
    branches: dict[str, str] = field(default_factory=dict)  # name → commit hash
    head: Optional[str] = None
    current_branch: str = "main"
    
    def __post_init__(self):
        if "main" not in self.branches:
            self.branches["main"] = None
    
    def commit(
        self,
        message: str,
        changed_nodes: list[str] = None,
        changed_edges: list[str] = None,
        author: str = "system",
        snapshot: dict[str, Any] = None,
    ) -> str:
        """Create a new commit."""
        import time
        
        # Generate deterministic hash
        content = f"{message}{time.time()}{changed_nodes}{changed_edges}"
        commit_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
        
        parent_hashes = [self.head] if self.head else []
        
        commit = Commit(
            hash=commit_hash,
            message=message,
            author=author,
            parent_hashes=parent_hashes,
            changed_nodes=changed_nodes or [],
            changed_edges=changed_edges or [],
            snapshot=snapshot,
        )
        
        self.commits[commit_hash] = commit
        self.head = commit_hash
        self.branches[self.current_branch] = commit_hash
        
        return commit_hash
    
    def checkout(self, ref: str) -> Optional[Commit]:
        """Checkout a branch or commit."""
        if ref in self.branches:
            self.current_branch = ref
            self.head = self.branches[ref]
        elif ref in self.commits:
            self.head = ref
        else:
            return None
        
        return self.commits.get(self.head)
    
    def create_branch(self, name: str) -> str:
        """Create a new branch at current head."""
        self.branches[name] = self.head
        return self.head or ""
    
    def log(self, limit: int = 10) -> list[Commit]:
        """Get commit history from head."""
        result = []
        current = self.head
        
        while current and len(result) < limit:
            if current in self.commits:
                c = self.commits[current]
                result.append(c)
                current = c.parent_hashes[0] if c.parent_hashes else None
            else:
                break
        
        return result
    
    def diff(self, hash_a: str, hash_b: str) -> dict[str, Any]:
        """Compare two commits."""
        a = self.commits.get(hash_a)
        b = self.commits.get(hash_b)
        
        if not a or not b:
            return {"error": "Commit not found"}
        
        return {
            "from": hash_a,
            "to": hash_b,
            "nodes_changed_in_a": a.changed_nodes,
            "nodes_changed_in_b": b.changed_nodes,
            "edges_changed_in_a": a.changed_edges,
            "edges_changed_in_b": b.changed_edges,
        }
    
    def query_at(self, commit_hash: str) -> Optional[dict[str, Any]]:
        """Get graph snapshot at a commit."""
        commit = self.commits.get(commit_hash)
        if commit and commit.snapshot:
            return commit.snapshot
        return None


# =============================================================================
# Factory Functions
# =============================================================================

def create_hypergraph() -> KnowledgeHyperGraph:
    """Create a new empty hypergraph."""
    return KnowledgeHyperGraph()


def create_node(
    node_type: NodeType,
    content: Any,
    **kwargs,
) -> HyperNode:
    """Create a new hypergraph node."""
    return HyperNode(
        id=str(uuid.uuid4())[:8],
        node_type=node_type,
        content=VersionedContent(content),
        **kwargs,
    )


def create_edge(
    edge_type: EdgeType,
    sources: list[str],
    targets: list[str],
    **kwargs,
) -> HyperEdge:
    """Create a new hyperedge."""
    return HyperEdge(
        id=str(uuid.uuid4())[:8],
        edge_type=edge_type,
        source_ids=sources,
        target_ids=targets,
        **kwargs,
    )
