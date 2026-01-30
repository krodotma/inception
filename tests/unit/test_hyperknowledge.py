"""
HyperKnowledge Tests
Phase 5, Steps 137-139

Tests for:
- Core data structures (hypergraph, versioning)
- LMDB persistence (commit, query, diff)
- Temporal queries (Allen intervals)
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from inception.db.hyperknowledge import (
    KnowledgeHyperGraph,
    HyperNode,
    HyperEdge,
    VersionedContent,
    SourceChain,
    SourceReference,
    ProvenanceStep,
    AllenInterval,
    AllenRelation,
    TemporalIndex,
    UncertaintyModel,
    VersionDAG,
    NodeType,
    EdgeType,
    create_node,
    create_edge,
)

from inception.db.hyperknowledge_lmdb import (
    HyperKnowledgeLMDB,
    open_hyperknowledge,
)


# =============================================================================
# Test: VersionedContent DAG
# =============================================================================

class TestVersionedContent:
    """Tests for git-like versioned content."""
    
    def test_initial_version(self):
        """Test creating initial content."""
        vc = VersionedContent("Hello World")
        
        assert vc.head is not None
        assert vc.get() == "Hello World"
        assert len(vc.versions) == 1
    
    def test_commit_creates_history(self):
        """Test that commits create version history."""
        vc = VersionedContent("v1")
        vc.commit("v2", "Second version")
        vc.commit("v3", "Third version")
        
        history = vc.history()
        assert len(history) == 3
        assert history[0].content == "v3"
        assert history[2].content == "v1"
    
    def test_diff_between_versions(self):
        """Test diffing two versions."""
        vc = VersionedContent("original")
        h1 = vc.head
        vc.commit("modified", "Changed content")
        h2 = vc.head
        
        diff = vc.diff(h1, h2)
        assert diff["changed"] is True
        assert diff["content_a"] == "original"
        assert diff["content_b"] == "modified"
    
    def test_branch_and_merge(self):
        """Test branching and merging."""
        vc = VersionedContent("main content")
        base = vc.head
        
        # Create branch
        vc.create_branch("feature", base)
        
        # Commit to feature
        vc.commit("feature content", "Feature change", branch="feature")
        
        # Merge back
        merged = vc.merge("feature", "main")
        
        assert merged in vc.versions
        assert vc.get() == "feature content"


# =============================================================================
# Test: AllenInterval
# =============================================================================

class TestAllenInterval:
    """Tests for Allen's interval algebra."""
    
    def test_before_relation(self):
        """Test A before B."""
        a = AllenInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10),
        )
        b = AllenInterval(
            start=datetime(2024, 1, 15),
            end=datetime(2024, 1, 20),
        )
        
        assert a.relation_to(b) == AllenRelation.BEFORE
        assert b.relation_to(a) == AllenRelation.AFTER
    
    def test_meets_relation(self):
        """Test A meets B (A ends exactly when B starts)."""
        a = AllenInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10),
        )
        b = AllenInterval(
            start=datetime(2024, 1, 10),
            end=datetime(2024, 1, 20),
        )
        
        assert a.relation_to(b) == AllenRelation.MEETS
    
    def test_during_relation(self):
        """Test A during B (A is contained within B)."""
        a = AllenInterval(
            start=datetime(2024, 1, 5),
            end=datetime(2024, 1, 15),
        )
        b = AllenInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 20),
        )
        
        assert a.relation_to(b) == AllenRelation.DURING
        assert b.relation_to(a) == AllenRelation.CONTAINS
    
    def test_equals_relation(self):
        """Test A equals B."""
        a = AllenInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10),
        )
        b = AllenInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10),
        )
        
        assert a.relation_to(b) == AllenRelation.EQUALS
    
    def test_contains_point(self):
        """Test point-in-interval checking."""
        interval = AllenInterval(
            start=datetime(2024, 1, 5),
            end=datetime(2024, 1, 15),
        )
        
        assert interval.contains_point(datetime(2024, 1, 10))
        assert not interval.contains_point(datetime(2024, 1, 1))
        assert not interval.contains_point(datetime(2024, 1, 20))


# =============================================================================
# Test: TemporalIndex
# =============================================================================

class TestTemporalIndex:
    """Tests for temporal indexing."""
    
    def test_query_at_point(self):
        """Test querying entities valid at a point."""
        index = TemporalIndex()
        
        # Entity A: valid Jan 1-10
        index.add_interval("entity_a", AllenInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10),
        ))
        
        # Entity B: valid Jan 5-15
        index.add_interval("entity_b", AllenInterval(
            start=datetime(2024, 1, 5),
            end=datetime(2024, 1, 15),
        ))
        
        # Query Jan 7: both valid
        valid = index.query_at(datetime(2024, 1, 7))
        assert "entity_a" in valid
        assert "entity_b" in valid
        
        # Query Jan 12: only B valid
        valid = index.query_at(datetime(2024, 1, 12))
        assert "entity_a" not in valid
        assert "entity_b" in valid
    
    def test_query_range(self):
        """Test querying entities valid during a range."""
        index = TemporalIndex()
        
        index.add_interval("early", AllenInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 5),
        ))
        index.add_interval("middle", AllenInterval(
            start=datetime(2024, 1, 5),
            end=datetime(2024, 1, 15),
        ))
        index.add_interval("late", AllenInterval(
            start=datetime(2024, 1, 20),
            end=datetime(2024, 1, 25),
        ))
        
        # Query Jan 4-10: early and middle overlap
        valid = index.query_range(datetime(2024, 1, 4), datetime(2024, 1, 10))
        assert "early" in valid
        assert "middle" in valid
        assert "late" not in valid


# =============================================================================
# Test: UncertaintyModel
# =============================================================================

class TestUncertaintyModel:
    """Tests for uncertainty quantification."""
    
    def test_combined_confidence(self):
        """Test combined confidence calculation."""
        um = UncertaintyModel(epistemic=0.8, aleatoric=0.6)
        
        assert um.combined == 0.7
        # combined=0.7 is exactly on the boundary (> 0.7 is high, > 0.5 is moderate)
        assert um.certainty_level == "moderate"
    
    def test_update_from_sources(self):
        """Test updating confidence from multiple sources."""
        um = UncertaintyModel()
        
        um.update_from_source("source_1", 0.9)
        um.update_from_source("source_2", 0.85)
        
        assert len(um.source_confidences) == 2
        assert um.epistemic > 0.8
    
    def test_conflict_detection(self):
        """Test that high variance triggers conflict flag."""
        um = UncertaintyModel()
        
        um.update_from_source("agree_1", 0.9)
        um.update_from_source("agree_2", 0.88)
        
        assert not um.has_conflict
        
        um.update_from_source("disagree", 0.2)
        
        assert um.has_conflict
    
    def test_fusion(self):
        """Test fusing two uncertainty models."""
        um1 = UncertaintyModel(epistemic=0.8, aleatoric=0.7)
        um1.source_confidences = {"s1": 0.8, "s2": 0.75}
        
        um2 = UncertaintyModel(epistemic=0.6, aleatoric=0.8)
        um2.source_confidences = {"s3": 0.6}
        
        fused = um1.fuse_with(um2)
        
        assert len(fused.source_confidences) == 3
        assert 0.6 < fused.epistemic < 0.8


# =============================================================================
# Test: SourceChain Provenance
# =============================================================================

class TestSourceChain:
    """Tests for provenance tracking."""
    
    def test_source_chain_creation(self):
        """Test creating a provenance chain."""
        chain = SourceChain()
        
        chain.add_source(SourceReference(
            source_id="vid_001",
            source_type="video",
            title="Lecture on AI",
            timestamp="12:34",
            authority=0.9,
        ))
        
        chain.add_step(ProvenanceStep(
            step_id="step_1",
            action="extracted",
            agent="DECOMP",
            confidence=0.95,
        ))
        
        chain.add_step(ProvenanceStep(
            step_id="step_2",
            action="validated",
            agent="EVAL-PRIME",
            confidence=0.9,
        ))
        
        assert len(chain.sources) == 1
        assert len(chain.steps) == 2
        assert chain.get_derivation_path() == ["extracted", "validated"]
    
    def test_aggregate_confidence(self):
        """Test confidence propagation through chain."""
        chain = SourceChain()
        
        chain.add_step(ProvenanceStep(
            step_id="s1", action="extracted", agent="A", confidence=0.9
        ))
        chain.add_step(ProvenanceStep(
            step_id="s2", action="fused", agent="B", confidence=0.8
        ))
        
        # 0.9 * 0.8 = 0.72
        assert abs(chain.compute_aggregate_confidence() - 0.72) < 0.01


# =============================================================================
# Test: KnowledgeHyperGraph
# =============================================================================

class TestKnowledgeHyperGraph:
    """Tests for the core hypergraph."""
    
    def test_add_node_and_edge(self):
        """Test adding nodes and edges."""
        graph = KnowledgeHyperGraph()
        
        node1 = create_node(NodeType.ENTITY, {"name": "Python"})
        node2 = create_node(NodeType.CLAIM, {"text": "Python is popular"})
        
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = create_edge(EdgeType.ASSERTS, [node1.id], [node2.id])
        graph.add_edge(edge)
        
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        
        edges = graph.get_edges_for_node(node1.id)
        assert len(edges) == 1
    
    def test_query_at_timestamp(self):
        """Test temporal filtering of graph."""
        graph = KnowledgeHyperGraph()
        
        # Node valid in January
        node1 = create_node(
            NodeType.ENTITY,
            {"name": "Old Fact"},
            valid_from=datetime(2024, 1, 1),
            valid_until=datetime(2024, 1, 31),
        )
        
        # Node valid in February
        node2 = create_node(
            NodeType.ENTITY,
            {"name": "New Fact"},
            valid_from=datetime(2024, 2, 1),
            valid_until=datetime(2024, 2, 28),
        )
        
        graph.add_node(node1)
        graph.add_node(node2)
        
        # Query January 15
        jan_view = graph.query_at(datetime(2024, 1, 15))
        assert len(jan_view.nodes) == 1
        assert node1.id in jan_view.nodes
        
        # Query February 15
        feb_view = graph.query_at(datetime(2024, 2, 15))
        assert len(feb_view.nodes) == 1
        assert node2.id in feb_view.nodes


# =============================================================================
# Test: VersionDAG
# =============================================================================

class TestVersionDAG:
    """Tests for graph-level versioning."""
    
    def test_commit_and_log(self):
        """Test creating commits and viewing log."""
        dag = VersionDAG()
        
        dag.commit("Initial", ["n1", "n2"], [])
        dag.commit("Added edge", ["n1"], ["e1"])
        dag.commit("Modified", ["n1", "n3"], ["e1", "e2"])
        
        log = dag.log(10)
        assert len(log) == 3
        assert log[0].message == "Modified"
        assert log[2].message == "Initial"
    
    def test_branch_and_checkout(self):
        """Test branch creation and checkout."""
        dag = VersionDAG()
        
        h1 = dag.commit("Main commit", [], [])
        dag.create_branch("feature")
        
        # Checkout feature
        dag.checkout("feature")
        h2 = dag.commit("Feature commit", ["f1"], [])
        
        # Checkout main
        dag.checkout("main")
        assert dag.head == h1
        
        # Checkout feature
        dag.checkout("feature")
        assert dag.head == h2


# =============================================================================
# Test: HyperKnowledgeLMDB Persistence
# =============================================================================

class TestHyperKnowledgeLMDB:
    """Tests for LMDB persistence layer."""
    
    @pytest.fixture
    def db(self):
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = open_hyperknowledge(tmpdir)
            yield db
            db.close()
    
    def test_put_and_get_node(self, db):
        """Test storing and retrieving nodes."""
        node = create_node(NodeType.ENTITY, {"name": "Test"})
        db.put_node(node)
        
        retrieved = db.get_node(node.id)
        assert retrieved is not None
        assert retrieved.get("id") == node.id
    
    def test_commit_and_history(self, db):
        """Test committing and retrieving history."""
        graph = KnowledgeHyperGraph()
        node = create_node(NodeType.CLAIM, {"text": "Test claim"})
        graph.add_node(node)
        
        h1 = db.commit(graph, "First commit")
        
        node2 = create_node(NodeType.ENTITY, {"name": "Entity"})
        graph.add_node(node2)
        
        h2 = db.commit(graph, "Second commit")
        
        history = db.get_history()
        assert len(history) == 2
        assert history[0]["hash"] == h2
        assert history[1]["hash"] == h1
    
    def test_diff_between_commits(self, db):
        """Test diffing two commits."""
        graph = KnowledgeHyperGraph()
        
        node1 = create_node(NodeType.ENTITY, {"name": "A"})
        graph.add_node(node1)
        h1 = db.commit(graph, "Add A")
        
        node2 = create_node(NodeType.ENTITY, {"name": "B"})
        graph.add_node(node2)
        h2 = db.commit(graph, "Add B")
        
        diff = db.diff(h1, h2)
        
        assert diff["from_commit"] == h1
        assert diff["to_commit"] == h2
        assert node2.id in diff["nodes_added"]
    
    def test_temporal_query(self, db):
        """Test temporal querying."""
        node = create_node(
            NodeType.CLAIM,
            {"text": "Valid in January"},
            valid_from=datetime(2024, 1, 1),
            valid_until=datetime(2024, 1, 31),
        )
        db.put_node(node)
        
        # Query within range
        results = db.query_at(datetime(2024, 1, 15))
        assert any(r.get("id") == node.id for r in results)
        
        # Query outside range
        results = db.query_at(datetime(2024, 6, 15))
        assert not any(r.get("id") == node.id for r in results)
    
    def test_statistics(self, db):
        """Test getting database statistics."""
        graph = KnowledgeHyperGraph()
        
        for i in range(5):
            node = create_node(NodeType.ENTITY, {"name": f"Entity {i}"})
            graph.add_node(node)
        
        for i in range(3):
            edge = create_edge(EdgeType.ASSERTS, ["a"], ["b"])
            graph.add_edge(edge)
        
        db.commit(graph, "Initial data")
        
        stats = db.get_statistics()
        assert stats["nodes"] >= 5
        assert stats["edges"] >= 3
        assert stats["commits"] >= 1


# =============================================================================
# Integration Test
# =============================================================================

class TestHyperKnowledgeIntegration:
    """End-to-end integration tests."""
    
    def test_full_workflow(self):
        """Test complete workflow: create, commit, query, diff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = open_hyperknowledge(tmpdir)
            
            # Create initial graph
            graph = KnowledgeHyperGraph()
            
            entity = create_node(
                NodeType.ENTITY,
                {"name": "Python", "type": "programming_language"},
                valid_from=datetime(1991, 2, 20),
            )
            entity.uncertainty = UncertaintyModel(epistemic=0.95, aleatoric=0.99)
            entity.source_chain = SourceChain()
            entity.source_chain.add_source(SourceReference(
                source_id="wiki_python",
                source_type="webpage",
                title="Python (programming language)",
                url="https://en.wikipedia.org/wiki/Python",
                authority=0.8,
            ))
            
            claim = create_node(
                NodeType.CLAIM,
                {"text": "Python was created by Guido van Rossum"},
            )
            claim.uncertainty = UncertaintyModel(epistemic=0.99, aleatoric=0.99)
            
            graph.add_node(entity)
            graph.add_node(claim)
            
            edge = create_edge(
                EdgeType.ASSERTS,
                [entity.id],
                [claim.id],
                confidence=0.98,
            )
            graph.add_edge(edge)
            
            # Commit
            h1 = db.commit(graph, "Add Python entity and claim")
            
            # Add more data
            skill = create_node(
                NodeType.SKILL,
                {"name": "Write Python function", "steps": ["def", "return"]},
            )
            graph.add_node(skill)
            
            h2 = db.commit(graph, "Add skill")
            
            # Query and verify
            stats = db.get_statistics()
            assert stats["nodes"] >= 3
            assert stats["commits"] == 2
            
            # Diff
            diff = db.diff(h1, h2)
            assert skill.id in diff["nodes_added"]
            
            # Temporal query
            results = db.temporal_query(
                start=datetime(1991, 1, 1),
                end=datetime(2024, 12, 31),
            )
            assert len(results) >= 1
            
            db.close()


# =============================================================================
# Additional Coverage Tests
# =============================================================================

class TestHyperNodeCoverage:
    """Additional tests for HyperNode coverage gaps."""
    
    def test_content_hash(self):
        """Test line 71: HyperNode.content_hash() method."""
        node = create_node(NodeType.ENTITY, {"name": "test"})
        
        # content_hash should return current hash
        hash1 = node.content_hash()
        assert isinstance(hash1, str)
        assert len(hash1) > 0


class TestVersionedContentCoverage:
    """Additional tests for VersionedContent coverage gaps."""
    
    def test_get_returns_none_for_missing_version(self):
        """Test line 240: get() returns None for missing version."""
        vc = VersionedContent("content")
        
        result = vc.get("nonexistent_hash")
        assert result is None
    
    def test_current_hash_returns_empty_when_no_head(self):
        """Test line 244: current_hash() with no head."""
        vc = VersionedContent.__new__(VersionedContent)
        vc.head = None
        vc.versions = {}
        vc.branches = {}
        
        assert vc.current_hash() == ""
    
    def test_history_breaks_on_missing_version(self):
        """Test line 257: history() handles missing version in chain."""
        vc = VersionedContent("v1")
        vc.commit("v2", "Second")
        
        # Force a break in the chain
        v = list(vc.versions.values())[0]
        if v.parent_hashes:
            # Remove the parent to force break
            del vc.versions[v.parent_hashes[0]]
        
        # Should not crash, just return what it can
        history = vc.history()
        assert len(history) >= 1
    
    def test_diff_returns_error_for_missing_version(self):
        """Test line 267: diff() returns error for missing version."""
        vc = VersionedContent("content")
        
        result = vc.diff("missing_a", "missing_b")
        assert "error" in result
        assert result["error"] == "Version not found"
    
    def test_merge_raises_for_missing_branch(self):
        """Test line 289: merge() raises for missing branch."""
        vc = VersionedContent("content")
        
        with pytest.raises(ValueError, match="not found"):
            vc.merge("nonexistent_branch", "main")


class TestKnowledgeHyperGraphCoverage:
    """Additional tests for KnowledgeHyperGraph coverage gaps."""
    
    def test_get_node_returns_none_for_missing(self):
        """Test line 122: get_node returns None for missing ID."""
        graph = KnowledgeHyperGraph()
        
        result = graph.get_node("nonexistent_id")
        assert result is None
    
    def test_query_at_filters_edges_properly(self):
        """Test lines 143-145: edge filtering in query_at."""
        now = datetime.now()
        past = now - timedelta(days=10)
        future = now + timedelta(days=10)
        
        graph = KnowledgeHyperGraph()
        
        # Add node valid in past
        node1 = create_node(NodeType.ENTITY, {"name": "past"})
        node1.valid_from = past - timedelta(days=5)
        node1.valid_until = past - timedelta(days=1)
        graph.add_node(node1)
        
        # Add node valid now
        node2 = create_node(NodeType.ENTITY, {"name": "current"})
        node2.valid_from = past
        node2.valid_until = future
        graph.add_node(node2)
        
        # Add edge that connects both
        edge = create_edge(EdgeType.MENTIONS, [node1.id], [node2.id])
        graph.add_edge(edge)
        
        # Query at current time - past node should be filtered out
        # Edge should also be filtered because node1 is not present
        filtered = graph.query_at(now)
        
        assert node2.id in filtered.nodes
        # Edge should NOT be in filtered because source (node1) is not present
        assert edge.id not in filtered.edges


class TestAllenIntervalCoverage:
    """Additional tests for AllenInterval coverage gaps."""
    
    def test_is_ongoing_property(self):
        """Test line 427: is_ongoing property."""
        now = datetime.now()
        
        # Ongoing interval (no end)
        ongoing = AllenInterval(start=now, end=None)
        assert ongoing.is_ongoing is True
        
        # Closed interval
        closed = AllenInterval(start=now, end=now + timedelta(hours=1))
        assert closed.is_ongoing is False
    
    def test_duration_seconds_none_for_ongoing(self):
        """Test lines 432-434: duration_seconds returns None for ongoing."""
        now = datetime.now()
        
        ongoing = AllenInterval(start=now, end=None)
        assert ongoing.duration_seconds is None
        
        closed = AllenInterval(start=now, end=now + timedelta(seconds=3600))
        assert ongoing.duration_seconds is None
        assert closed.duration_seconds == 3600.0
    
    def test_relation_met_by(self):
        """Test line 456: MET_BY relation."""
        now = datetime.now()
        
        a = AllenInterval(start=now + timedelta(hours=2), end=now + timedelta(hours=3))
        b = AllenInterval(start=now, end=now + timedelta(hours=2))
        
        # a starts exactly when b ends -> a is MET_BY b
        assert a.relation_to(b) == AllenRelation.MET_BY
    
    def test_relation_starts(self):
        """Test line 460: STARTS relation."""
        now = datetime.now()
        
        a = AllenInterval(start=now, end=now + timedelta(hours=1))
        b = AllenInterval(start=now, end=now + timedelta(hours=2))
        
        # a starts same time as b but ends earlier -> a STARTS b
        assert a.relation_to(b) == AllenRelation.STARTS
    
    def test_relation_started_by(self):
        """Test line 462: STARTED_BY relation."""
        now = datetime.now()
        
        a = AllenInterval(start=now, end=now + timedelta(hours=2))
        b = AllenInterval(start=now, end=now + timedelta(hours=1))
        
        # a starts same time as b but ends later -> a STARTED_BY b
        assert a.relation_to(b) == AllenRelation.STARTED_BY
    
    def test_relation_finishes(self):
        """Test line 464: FINISHES relation."""
        now = datetime.now()
        
        a = AllenInterval(start=now + timedelta(hours=1), end=now + timedelta(hours=2))
        b = AllenInterval(start=now, end=now + timedelta(hours=2))
        
        # a ends same time as b but starts later -> a FINISHES b
        assert a.relation_to(b) == AllenRelation.FINISHES
    
    def test_relation_finished_by(self):
        """Test line 466: FINISHED_BY relation."""
        now = datetime.now()
        
        a = AllenInterval(start=now, end=now + timedelta(hours=2))
        b = AllenInterval(start=now + timedelta(hours=1), end=now + timedelta(hours=2))
        
        # a ends same time as b but starts earlier -> a FINISHED_BY b
        assert a.relation_to(b) == AllenRelation.FINISHED_BY


class TestVersionDAGCoverage:
    """Additional tests for VersionDAG coverage gaps."""
    
    def test_checkout_commit_directly(self):
        """Test lines 683-686: checkout a commit hash directly."""
        dag = VersionDAG()
        h1 = dag.commit({"node": "1"}, [], [], "First")
        h2 = dag.commit({"node": "2"}, [], [], "Second")
        
        # Checkout by commit hash (not branch name)
        result = dag.checkout(h1)
        
        assert result is not None
        assert dag.head == h1
    
    def test_checkout_returns_none_for_invalid_ref(self):
        """Test line 686: checkout returns None for invalid ref."""
        dag = VersionDAG()
        dag.commit({"node": "1"}, [], [], "First")
        
        result = dag.checkout("nonexistent_ref")
        assert result is None
    
    def test_log_breaks_on_missing_commit(self):
        """Test line 706: log handles missing commit in chain."""
        dag = VersionDAG()
        h1 = dag.commit({"node": "1"}, [], [], "First")
        h2 = dag.commit({"node": "2"}, [], [], "Second")
        
        # Remove h1 to break the chain
        del dag.commits[h1]
        
        # Log should return what it can
        log = dag.log()
        assert len(log) >= 1
    
    def test_diff_returns_error_for_missing_commit(self):
        """Test lines 712-718: diff returns error for missing commit."""
        dag = VersionDAG()
        dag.commit({"node": "1"}, [], [], "First")
        
        result = dag.diff("missing_a", "missing_b")
        assert "error" in result
        assert result["error"] == "Commit not found"
    
    def test_query_at_returns_none_for_missing(self):
        """Test lines 729-732: query_at returns None for missing commit."""
        dag = VersionDAG()
        
        result = dag.query_at("nonexistent_commit")
        assert result is None
    
    def test_query_at_returns_none_for_no_snapshot(self):
        """Test lines 730-731: query_at returns None when snapshot is empty."""
        dag = VersionDAG()
        h = dag.commit(None, [], [], "No snapshot")  # snapshot is None
        
        result = dag.query_at(h)
        assert result is None


class TestFactoryFunctionsCoverage:
    """Test factory function coverage."""
    
    def test_create_hypergraph(self):
        """Test line 741: create_hypergraph factory."""
        from inception.db.hyperknowledge import create_hypergraph
        
        graph = create_hypergraph()
        assert isinstance(graph, KnowledgeHyperGraph)
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

