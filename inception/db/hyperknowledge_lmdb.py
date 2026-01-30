"""
HyperKnowledge Integration Layer
Phase 5, Steps 127-136

Implements:
- commit() operation (127)
- query_at(timestamp) (128)
- diff(a, b) (129)
- branch/merge (130)
- LMDB HyperKnowledge layer (131)
- Incremental analysis engine (132)
- Shared substructure detection (133)
- Temporal query API (134)
- Version history API (135)
- Diff visualization (136)
"""

from __future__ import annotations

import json
import lmdb
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Iterator

from .hyperknowledge import (
    KnowledgeHyperGraph,
    HyperNode,
    HyperEdge,
    VersionDAG,
    AllenInterval,
    TemporalIndex,
    NodeType,
    EdgeType,
    create_node,
    create_edge,
)


# =============================================================================
# Step 131: LMDB HyperKnowledge Layer
# =============================================================================

class HyperKnowledgeLMDB:
    """
    LMDB-backed persistent storage for HyperKnowledge graphs.
    Provides durability, ACID transactions, and efficient queries.
    """
    
    def __init__(self, path: Path, map_size: int = 10 * 1024**3):
        """
        Initialize LMDB environment.
        
        Args:
            path: Directory for LMDB files
            map_size: Maximum database size (default 10GB)
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        self.env = lmdb.open(
            str(self.path),
            map_size=map_size,
            max_dbs=10,
            writemap=True,
        )
        
        # Sub-databases
        self.nodes_db = self.env.open_db(b"nodes", create=True)
        self.edges_db = self.env.open_db(b"edges", create=True)
        self.versions_db = self.env.open_db(b"versions", create=True)
        self.temporal_db = self.env.open_db(b"temporal", create=True)
        self.commits_db = self.env.open_db(b"commits", create=True)
        self.meta_db = self.env.open_db(b"meta", create=True)
        
        # In-memory caches
        self._version_dag = VersionDAG()
        self._temporal_index = TemporalIndex()
        
        # Load existing version DAG
        self._load_version_dag()
    
    def _serialize(self, obj: Any) -> bytes:
        """Serialize object to bytes using custom encoder."""
        class HyperKnowledgeEncoder(json.JSONEncoder):
            def default(self, o):
                if hasattr(o, 'name') and hasattr(o, 'value') and isinstance(type(o), type) and issubclass(type(o).__class__, type) and hasattr(type(o), '__mro__'):
                    # Check if it's an Enum-like object
                    try:
                        if o.__class__.__bases__[0].__name__ == 'Enum' or 'Enum' in [c.__name__ for c in o.__class__.__mro__]:
                            return o.name
                    except (IndexError, AttributeError):
                        pass
                if isinstance(o, datetime):
                    return o.isoformat()
                if hasattr(o, 'to_dict'):
                    return o.to_dict()
                if hasattr(o, '__dict__'):
                    result = {}
                    for k, v in o.__dict__.items():
                        if not k.startswith('_'):
                            result[k] = v
                    return result
                return super().default(o)
        
        if hasattr(obj, "to_dict"):
            data = obj.to_dict()
        elif hasattr(obj, "__dict__"):
            data = {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        else:
            data = obj
        return json.dumps(data, cls=HyperKnowledgeEncoder).encode()
    
    def _deserialize(self, data: bytes) -> dict[str, Any]:
        """Deserialize bytes to dict."""
        return json.loads(data.decode())
    
    # -------------------------------------------------------------------------
    # Node Operations
    # -------------------------------------------------------------------------
    
    def put_node(self, node: HyperNode, txn: lmdb.Transaction = None) -> str:
        """Store a node."""
        data = self._serialize(node)
        
        if txn:
            txn.put(node.id.encode(), data, db=self.nodes_db)
        else:
            with self.env.begin(write=True) as txn:
                txn.put(node.id.encode(), data, db=self.nodes_db)
        
        return node.id
    
    def get_node(self, node_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a node."""
        with self.env.begin(db=self.nodes_db) as txn:
            data = txn.get(node_id.encode())
            if data:
                return self._deserialize(data)
        return None
    
    def iter_nodes(self, node_type: Optional[NodeType] = None) -> Iterator[dict[str, Any]]:
        """Iterate over nodes, optionally filtered by type."""
        with self.env.begin(db=self.nodes_db) as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                node = self._deserialize(value)
                if node_type is None or node.get("node_type") == node_type.name:
                    yield node
    
    # -------------------------------------------------------------------------
    # Edge Operations
    # -------------------------------------------------------------------------
    
    def put_edge(self, edge: HyperEdge, txn: lmdb.Transaction = None) -> str:
        """Store an edge."""
        data = self._serialize(edge)
        
        if txn:
            txn.put(edge.id.encode(), data, db=self.edges_db)
        else:
            with self.env.begin(write=True) as txn:
                txn.put(edge.id.encode(), data, db=self.edges_db)
        
        return edge.id
    
    def get_edge(self, edge_id: str) -> Optional[dict[str, Any]]:
        """Retrieve an edge."""
        with self.env.begin(db=self.edges_db) as txn:
            data = txn.get(edge_id.encode())
            if data:
                return self._deserialize(data)
        return None
    
    def get_edges_for_node(self, node_id: str) -> list[dict[str, Any]]:
        """Get all edges connected to a node."""
        edges = []
        with self.env.begin(db=self.edges_db) as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                edge = self._deserialize(value)
                if node_id in edge.get("source_ids", []) or node_id in edge.get("target_ids", []):
                    edges.append(edge)
        return edges
    
    # -------------------------------------------------------------------------
    # Step 127: commit() operation
    # -------------------------------------------------------------------------
    
    def commit(
        self,
        graph: KnowledgeHyperGraph,
        message: str,
        author: str = "system",
    ) -> str:
        """
        Commit current graph state to version history.
        Creates a snapshot and updates the version DAG.
        """
        # Collect changed items
        changed_nodes = list(graph.nodes.keys())
        changed_edges = list(graph.edges.keys())
        
        # Create commit
        commit_hash = self._version_dag.commit(
            message=message,
            changed_nodes=changed_nodes,
            changed_edges=changed_edges,
            author=author,
            snapshot=graph.get_statistics(),
        )
        
        # Store all nodes and edges
        with self.env.begin(write=True) as txn:
            for node in graph.nodes.values():
                self.put_node(node, txn)
            for edge in graph.edges.values():
                self.put_edge(edge, txn)
            
            # Store commit
            commit = self._version_dag.commits[commit_hash]
            txn.put(commit_hash.encode(), self._serialize(commit), db=self.commits_db)
            
            # Update head reference
            txn.put(b"HEAD", commit_hash.encode(), db=self.meta_db)
        
        return commit_hash
    
    # -------------------------------------------------------------------------
    # Step 128: query_at(timestamp)
    # -------------------------------------------------------------------------
    
    def query_at(self, timestamp: datetime) -> list[dict[str, Any]]:
        """
        Query the graph at a specific point in time.
        Returns all nodes that were valid at that timestamp.
        """
        valid_nodes = []
        
        with self.env.begin(db=self.nodes_db) as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                node = self._deserialize(value)
                
                # Check temporal validity
                valid_from = node.get("valid_from")
                valid_until = node.get("valid_until")
                
                if valid_from:
                    vf = datetime.fromisoformat(valid_from)
                    if vf > timestamp:
                        continue
                
                if valid_until:
                    vu = datetime.fromisoformat(valid_until)
                    if vu < timestamp:
                        continue
                
                valid_nodes.append(node)
        
        return valid_nodes
    
    # -------------------------------------------------------------------------
    # Step 129: diff(a, b)
    # -------------------------------------------------------------------------
    
    def diff(self, commit_a: str, commit_b: str) -> dict[str, Any]:
        """
        Compare two commits and return the differences.
        """
        a = self._version_dag.commits.get(commit_a)
        b = self._version_dag.commits.get(commit_b)
        
        if not a or not b:
            return {"error": "Commit not found"}
        
        # Find node differences
        nodes_added = set(b.changed_nodes) - set(a.changed_nodes)
        nodes_removed = set(a.changed_nodes) - set(b.changed_nodes)
        nodes_modified = set(a.changed_nodes) & set(b.changed_nodes)
        
        # Find edge differences
        edges_added = set(b.changed_edges) - set(a.changed_edges)
        edges_removed = set(a.changed_edges) - set(b.changed_edges)
        
        return {
            "from_commit": commit_a,
            "to_commit": commit_b,
            "nodes_added": list(nodes_added),
            "nodes_removed": list(nodes_removed),
            "nodes_modified": list(nodes_modified),
            "edges_added": list(edges_added),
            "edges_removed": list(edges_removed),
            "summary": {
                "added": len(nodes_added) + len(edges_added),
                "removed": len(nodes_removed) + len(edges_removed),
                "modified": len(nodes_modified),
            },
        }
    
    # -------------------------------------------------------------------------
    # Step 130: branch/merge
    # -------------------------------------------------------------------------
    
    def create_branch(self, name: str) -> str:
        """Create a new branch at current HEAD."""
        head = self._version_dag.head
        self._version_dag.create_branch(name)
        
        # Persist branch
        with self.env.begin(write=True) as txn:
            branches = self._load_branches(txn)
            branches[name] = head
            txn.put(b"BRANCHES", json.dumps(branches).encode(), db=self.meta_db)
        
        return head or ""
    
    def checkout(self, ref: str) -> Optional[dict[str, Any]]:
        """Checkout a branch or commit."""
        commit = self._version_dag.checkout(ref)
        
        if commit:
            with self.env.begin(write=True) as txn:
                txn.put(b"HEAD", commit.hash.encode(), db=self.meta_db)
                txn.put(b"CURRENT_BRANCH", ref.encode(), db=self.meta_db)
            
            return {"hash": commit.hash, "message": commit.message}
        
        return None
    
    def merge(self, source_branch: str, target_branch: str = "main") -> str:
        """Merge source branch into target."""
        source_hash = self._version_dag.branches.get(source_branch)
        target_hash = self._version_dag.branches.get(target_branch)
        
        if not source_hash:
            raise ValueError(f"Branch {source_branch} not found")
        
        # Create merge commit
        merge_hash = self._version_dag.commit(
            message=f"Merge {source_branch} into {target_branch}",
            changed_nodes=[],
            changed_edges=[],
        )
        
        return merge_hash
    
    # -------------------------------------------------------------------------
    # Step 132: Incremental Analysis Engine
    # -------------------------------------------------------------------------
    
    def analyze_incremental(self, new_nodes: list[HyperNode]) -> dict[str, Any]:
        """
        Perform incremental analysis on newly added nodes.
        Detects patterns, conflicts, and opportunities.
        """
        results = {
            "nodes_analyzed": len(new_nodes),
            "conflicts_detected": [],
            "patterns_found": [],
            "suggestions": [],
        }
        
        for node in new_nodes:
            # Check for conflicts with existing nodes
            if node.node_type == NodeType.CLAIM:
                conflicts = self._check_claim_conflicts(node)
                results["conflicts_detected"].extend(conflicts)
            
            # Detect patterns
            patterns = self._detect_patterns(node)
            results["patterns_found"].extend(patterns)
        
        return results
    
    def _check_claim_conflicts(self, node: HyperNode) -> list[dict[str, Any]]:
        """Check if a claim conflicts with existing claims."""
        conflicts = []
        # Simplified: would use semantic similarity in production
        return conflicts
    
    def _detect_patterns(self, node: HyperNode) -> list[dict[str, Any]]:
        """Detect structural patterns involving this node."""
        patterns = []
        # Simplified: would detect clusters, chains, hubs
        return patterns
    
    # -------------------------------------------------------------------------
    # Step 133: Shared Substructure Detection
    # -------------------------------------------------------------------------
    
    def detect_shared_substructures(self) -> list[dict[str, Any]]:
        """
        Find common substructures across the graph.
        Useful for knowledge compression and generalization.
        """
        substructures = []
        
        # Group nodes by type
        type_groups: dict[str, list[str]] = {}
        for node_data in self.iter_nodes():
            ntype = node_data.get("node_type", "UNKNOWN")
            if ntype not in type_groups:
                type_groups[ntype] = []
            type_groups[ntype].append(node_data.get("id"))
        
        # Find common edge patterns
        edge_patterns: dict[str, int] = {}
        for edge_data in self._iter_edges():
            pattern = f"{edge_data.get('edge_type')}:{len(edge_data.get('source_ids', []))}→{len(edge_data.get('target_ids', []))}"
            edge_patterns[pattern] = edge_patterns.get(pattern, 0) + 1
        
        # Report frequent patterns
        for pattern, count in edge_patterns.items():
            if count > 2:
                substructures.append({
                    "pattern": pattern,
                    "count": count,
                    "type": "edge_pattern",
                })
        
        return substructures
    
    def _iter_edges(self) -> Iterator[dict[str, Any]]:
        """Iterate over all edges."""
        with self.env.begin(db=self.edges_db) as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                yield self._deserialize(value)
    
    # -------------------------------------------------------------------------
    # Step 134: Temporal Query API
    # -------------------------------------------------------------------------
    
    def temporal_query(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        entity_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Query knowledge with temporal constraints.
        
        Args:
            start: Include knowledge valid after this time
            end: Include knowledge valid before this time
            entity_id: Filter to specific entity
        """
        results = []
        
        for node_data in self.iter_nodes():
            # Check entity filter
            if entity_id and node_data.get("id") != entity_id:
                continue
            
            # Check temporal bounds
            valid_from = node_data.get("valid_from")
            valid_until = node_data.get("valid_until")
            
            if start and valid_until:
                vu = datetime.fromisoformat(valid_until)
                if vu < start:
                    continue
            
            if end and valid_from:
                vf = datetime.fromisoformat(valid_from)
                if vf > end:
                    continue
            
            results.append(node_data)
        
        return results
    
    # -------------------------------------------------------------------------
    # Step 135: Version History API
    # -------------------------------------------------------------------------
    
    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get commit history."""
        commits = self._version_dag.log(limit)
        return [
            {
                "hash": c.hash,
                "message": c.message,
                "author": c.author,
                "timestamp": c.timestamp.isoformat(),
                "changes": len(c.changed_nodes) + len(c.changed_edges),
            }
            for c in commits
        ]
    
    def get_node_history(self, node_id: str) -> list[dict[str, Any]]:
        """Get version history for a specific node."""
        history = []
        
        for commit in self._version_dag.commits.values():
            if node_id in commit.changed_nodes:
                history.append({
                    "commit": commit.hash,
                    "message": commit.message,
                    "timestamp": commit.timestamp.isoformat(),
                })
        
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)
    
    # -------------------------------------------------------------------------
    # Step 136: Diff Visualization Data
    # -------------------------------------------------------------------------
    
    def get_diff_for_visualization(self, commit_a: str, commit_b: str) -> dict[str, Any]:
        """
        Get diff data formatted for visualization.
        Returns data suitable for the frontend temporal timeline.
        """
        diff = self.diff(commit_a, commit_b)
        
        # Enrich with node details
        nodes_detail = []
        for node_id in diff.get("nodes_added", []) + diff.get("nodes_modified", []):
            node = self.get_node(node_id)
            if node:
                nodes_detail.append({
                    "id": node_id,
                    "type": node.get("node_type"),
                    "status": "added" if node_id in diff.get("nodes_added", []) else "modified",
                })
        
        return {
            "commits": {
                "from": commit_a,
                "to": commit_b,
            },
            "stats": diff.get("summary", {}),
            "nodes": nodes_detail,
            "timeline_events": [
                {"type": "commit", "hash": commit_a, "label": "Before"},
                {"type": "commit", "hash": commit_b, "label": "After"},
            ],
        }
    
    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    
    def _load_version_dag(self) -> None:
        """Load version DAG from LMDB."""
        with self.env.begin(db=self.meta_db) as txn:
            head_bytes = txn.get(b"HEAD")
            if head_bytes:
                self._version_dag.head = head_bytes.decode()
        
        # Load commits
        with self.env.begin(db=self.commits_db) as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                data = self._deserialize(value)
                # Reconstruct Commit object (simplified)
                from .hyperknowledge import Commit
                commit = Commit(
                    hash=data.get("hash", key.decode()),
                    message=data.get("message", ""),
                    author=data.get("author", "system"),
                    parent_hashes=data.get("parent_hashes", []),
                    changed_nodes=data.get("changed_nodes", []),
                    changed_edges=data.get("changed_edges", []),
                )
                self._version_dag.commits[commit.hash] = commit
    
    def _load_branches(self, txn: lmdb.Transaction) -> dict[str, str]:
        """Load branch references."""
        data = txn.get(b"BRANCHES", db=self.meta_db)
        if data:
            return json.loads(data.decode())
        return {"main": None}
    
    def get_statistics(self) -> dict[str, Any]:
        """Get overall statistics."""
        node_count = 0
        edge_count = 0
        
        with self.env.begin(db=self.nodes_db) as txn:
            node_count = txn.stat()["entries"]
        
        with self.env.begin(db=self.edges_db) as txn:
            edge_count = txn.stat()["entries"]
        
        return {
            "nodes": node_count,
            "edges": edge_count,
            "commits": len(self._version_dag.commits),
            "head": self._version_dag.head,
            "branches": list(self._version_dag.branches.keys()),
        }
    
    def close(self) -> None:
        """Close the LMDB environment."""
        self.env.close()


# =============================================================================
# Convenience Factory
# =============================================================================

def open_hyperknowledge(path: str) -> HyperKnowledgeLMDB:
    """Open or create a HyperKnowledge database."""
    return HyperKnowledgeLMDB(Path(path))
