"""
Unit tests for context/context.py

Comprehensive tests for the Context Object System:
- InceptionContext and related data classes
- ContextSerializer (serialization/deserialization)
- ContextStore (LMDB persistence)
- ContextQuery (query API)
- EntelexisDiscovery, DomainTracker, IdeaLifecycle
- ProjectIdeaLinker, ContactRegistry
- ContextDiff, ContextEventEmitter
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from inception.context.context import (
    # Core types
    ContextState,
    ContextMetadata,
    EntelexisRef,
    DomainRef,
    IdeaRef,
    ProjectRef,
    ContactRef,
    DialogState,
    DialecticalState,
    InceptionContext,
    # Serialization
    ContextSerializer,
    # Persistence
    ContextStore,
    ContextQuery,
    # Discovery/Tracking
    EntelexisDiscovery,
    DomainTracker,
    IdeaState,
    IdeaLifecycle,
    ProjectIdeaLinker,
    ContactRegistry,
    # Diff
    ContextDiff,
    ContextDiffer,
    # Events
    ContextEventType,
    ContextEvent,
    ContextEventEmitter,
)


# =============================================================================
# Test: Data Classes
# =============================================================================

class TestContextState:
    """Tests for ContextState enum."""
    
    def test_all_states_exist(self):
        """Test all context states are defined."""
        assert ContextState.INITIALIZING.value == "initializing"
        assert ContextState.ACTIVE.value == "active"
        assert ContextState.SUSPENDED.value == "suspended"
        assert ContextState.COMPLETED.value == "completed"
        assert ContextState.ARCHIVED.value == "archived"


class TestContextMetadata:
    """Tests for ContextMetadata."""
    
    def test_defaults(self):
        """Test default values."""
        meta = ContextMetadata()
        assert meta.created_by == "system"
        assert meta.version == 1
        assert meta.tags == []


class TestInceptionContext:
    """Tests for InceptionContext."""
    
    def test_basic_creation(self):
        """Test creating a context."""
        ctx = InceptionContext(context_id="ctx-001", session_id="sess-001")
        assert ctx.context_id == "ctx-001"
        assert ctx.state == ContextState.INITIALIZING
    
    def test_touch_updates_metadata(self):
        """Test touch() updates version and timestamp."""
        ctx = InceptionContext(context_id="ctx-001", session_id="sess-001")
        old_version = ctx.metadata.version
        ctx.touch()
        assert ctx.metadata.version == old_version + 1
    
    def test_activate(self):
        """Test activate() method."""
        ctx = InceptionContext(context_id="ctx-001", session_id="sess-001")
        ctx.activate()
        assert ctx.state == ContextState.ACTIVE
    
    def test_suspend(self):
        """Test suspend() method."""
        ctx = InceptionContext(context_id="ctx-001", session_id="sess-001")
        ctx.activate()
        ctx.suspend()
        assert ctx.state == ContextState.SUSPENDED
    
    def test_complete(self):
        """Test complete() method."""
        ctx = InceptionContext(context_id="ctx-001", session_id="sess-001")
        ctx.complete()
        assert ctx.state == ContextState.COMPLETED


# =============================================================================
# Test: Serialization
# =============================================================================

class TestContextSerializer:
    """Tests for ContextSerializer."""
    
    def test_to_dict_basic(self):
        """Test basic serialization to dict."""
        ctx = InceptionContext(context_id="ctx-001", session_id="sess-001")
        data = ContextSerializer.to_dict(ctx)
        
        assert data["context_id"] == "ctx-001"
        assert data["session_id"] == "sess-001"
        assert data["state"] == "initializing"
    
    def test_to_dict_with_entelexis(self):
        """Test serialization with entelexis."""
        ctx = InceptionContext(context_id="ctx-001", session_id="sess-001")
        ctx.entelexis = EntelexisRef(
            purpose_id="purpose-1",
            purpose_name="Test purpose",
            state="focused",
            confidence=0.85,
        )
        data = ContextSerializer.to_dict(ctx)
        
        assert data["entelexis"]["purpose_id"] == "purpose-1"
        assert data["entelexis"]["confidence"] == 0.85
    
    def test_from_dict_basic(self):
        """Test basic deserialization from dict."""
        data = {
            "context_id": "ctx-002",
            "session_id": "sess-002",
            "state": "active",
            "metadata": {
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T01:00:00",
                "created_by": "test",
                "version": 2,
                "tags": ["important"],
            },
        }
        ctx = ContextSerializer.from_dict(data)
        
        assert ctx.context_id == "ctx-002"
        assert ctx.state == ContextState.ACTIVE
        assert ctx.metadata.version == 2
        assert "important" in ctx.metadata.tags
    
    def test_from_dict_with_domains(self):
        """Test deserialization with domains."""
        data = {
            "context_id": "ctx-003",
            "session_id": "sess-003",
            "domains": [
                {"domain_id": "dom-1", "name": "ML", "type": "subject", "depth": 0},
            ],
            "active_domain_id": "dom-1",
        }
        ctx = ContextSerializer.from_dict(data)
        
        assert len(ctx.domains) == 1
        assert ctx.domains[0].name == "ML"
        assert ctx.active_domain_id == "dom-1"
    
    def test_from_dict_with_ideas(self):
        """Test deserialization with ideas."""
        data = {
            "context_id": "ctx-004",
            "session_id": "sess-004",
            "ideas": [
                {"idea_id": "idea-1", "title": "Test idea", "state": "nascent"},
            ],
        }
        ctx = ContextSerializer.from_dict(data)
        
        assert len(ctx.ideas) == 1
        assert ctx.ideas[0].title == "Test idea"
    
    def test_from_dict_with_projects(self):
        """Test deserialization with projects."""
        data = {
            "context_id": "ctx-005",
            "session_id": "sess-005",
            "projects": [
                {"project_id": "proj-1", "name": "Test project", "status": "active", "idea_ids": ["idea-1"]},
            ],
        }
        ctx = ContextSerializer.from_dict(data)
        
        assert len(ctx.projects) == 1
        assert ctx.projects[0].name == "Test project"
    
    def test_from_dict_with_contacts(self):
        """Test deserialization with contacts."""
        data = {
            "context_id": "ctx-006",
            "session_id": "sess-006",
            "contacts": [
                {"contact_id": "c-1", "name": "Alice", "type": "human"},
            ],
        }
        ctx = ContextSerializer.from_dict(data)
        
        assert len(ctx.contacts) == 1
        assert ctx.contacts[0].name == "Alice"
    
    def test_from_dict_with_dialog(self):
        """Test deserialization with dialog state."""
        data = {
            "context_id": "ctx-007",
            "session_id": "sess-007",
            "dialog": {
                "turn_count": 5,
                "last_speaker": "agent",
                "topic_stack": ["testing"],
                "pending_questions": ["How to test?"],
            },
        }
        ctx = ContextSerializer.from_dict(data)
        
        assert ctx.dialog.turn_count == 5
        assert ctx.dialog.last_speaker == "agent"
    
    def test_from_dict_with_dialectical(self):
        """Test deserialization with dialectical state."""
        data = {
            "context_id": "ctx-008",
            "session_id": "sess-008",
            "dialectical": {
                "thesis": "A is true",
                "antithesis": "A is false",
                "synthesis": None,
                "mode": "steelman",
                "contradictions": [],
            },
        }
        ctx = ContextSerializer.from_dict(data)
        
        assert ctx.dialectical.thesis == "A is true"
        assert ctx.dialectical.mode == "steelman"
    
    def test_to_json_and_back(self):
        """Test JSON roundtrip."""
        ctx = InceptionContext(context_id="ctx-rt", session_id="sess-rt")
        ctx.entelexis = EntelexisRef("p1", "Purpose", "focused", 0.9)
        
        json_str = ContextSerializer.to_json(ctx)
        restored = ContextSerializer.from_json(json_str)
        
        assert restored.context_id == ctx.context_id
        assert restored.entelexis.purpose_name == "Purpose"


# =============================================================================
# Test: Context Store
# =============================================================================

class TestContextStore:
    """Tests for ContextStore."""
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading a context."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx = InceptionContext(context_id="ctx-store-1", session_id="sess-store-1")
            store.save(ctx)
            
            loaded = store.load("ctx-store-1")
            assert loaded is not None
            assert loaded.context_id == "ctx-store-1"
        finally:
            store.close()
    
    def test_load_missing(self, tmp_path):
        """Test loading non-existent context."""
        store = ContextStore(tmp_path / "context_db")
        try:
            result = store.load("nonexistent")
            assert result is None
        finally:
            store.close()
    
    def test_load_by_session(self, tmp_path):
        """Test loading contexts by session."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx1 = InceptionContext(context_id="ctx-s1", session_id="session-A")
            ctx2 = InceptionContext(context_id="ctx-s2", session_id="session-A")
            ctx3 = InceptionContext(context_id="ctx-s3", session_id="session-B")
            
            store.save(ctx1)
            store.save(ctx2)
            store.save(ctx3)
            
            session_a_contexts = store.load_by_session("session-A")
            assert len(session_a_contexts) == 2
        finally:
            store.close()
    
    def test_get_history(self, tmp_path):
        """Test getting version history."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx = InceptionContext(context_id="ctx-hist", session_id="sess-hist")
            store.save(ctx)
            
            ctx.touch()
            store.save(ctx)
            
            history = store.get_history("ctx-hist")
            assert len(history) >= 1
        finally:
            store.close()
    
    def test_delete(self, tmp_path):
        """Test deleting a context."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx = InceptionContext(context_id="ctx-del", session_id="sess-del")
            store.save(ctx)
            
            assert store.load("ctx-del") is not None
            store.delete("ctx-del")
            assert store.load("ctx-del") is None
        finally:
            store.close()


# =============================================================================
# Test: Context Query
# =============================================================================

class TestContextQuery:
    """Tests for ContextQuery."""
    
    def test_query_by_state(self, tmp_path):
        """Test filtering by state."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx1 = InceptionContext(context_id="cq-1", session_id="sess-q")
            ctx1.activate()
            ctx2 = InceptionContext(context_id="cq-2", session_id="sess-q")
            
            store.save(ctx1)
            store.save(ctx2)
            
            query = ContextQuery(store)
            results = query.where_state(ContextState.ACTIVE).execute()
            
            assert all(c.state == ContextState.ACTIVE for c in results)
        finally:
            store.close()
    
    def test_query_by_tag(self, tmp_path):
        """Test filtering by tag."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx = InceptionContext(context_id="cq-tag", session_id="sess-q")
            ctx.metadata.tags = ["important"]
            store.save(ctx)
            
            query = ContextQuery(store)
            results = query.where_tag("important").execute()
            
            assert len(results) >= 1
        finally:
            store.close()
    
    def test_query_by_domain(self, tmp_path):
        """Test filtering by domain."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx = InceptionContext(context_id="cq-dom", session_id="sess-q")
            ctx.domains.append(DomainRef("dom-1", "ML", "subject"))
            store.save(ctx)
            
            query = ContextQuery(store)
            results = query.where_domain("dom-1").execute()
            
            assert len(results) >= 1
        finally:
            store.close()
    
    def test_query_by_project(self, tmp_path):
        """Test filtering by project."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx = InceptionContext(context_id="cq-proj", session_id="sess-q")
            ctx.projects.append(ProjectRef("proj-1", "Test", "active"))
            store.save(ctx)
            
            query = ContextQuery(store)
            results = query.where_project("proj-1").execute()
            
            assert len(results) >= 1
        finally:
            store.close()
    
    def test_query_by_agent(self, tmp_path):
        """Test filtering by active agent."""
        store = ContextStore(tmp_path / "context_db")
        try:
            ctx = InceptionContext(context_id="cq-agent", session_id="sess-q")
            ctx.active_agent_ids = ["ARCHON"]
            store.save(ctx)
            
            query = ContextQuery(store)
            results = query.where_agent("ARCHON").execute()
            
            assert len(results) >= 1
        finally:
            store.close()


# =============================================================================
# Test: Discovery and Tracking
# =============================================================================

class TestEntelexisDiscovery:
    """Tests for EntelexisDiscovery."""
    
    def test_discover_from_project(self):
        """Test discovering purposes from active project."""
        ctx = InceptionContext(context_id="ctx-ent", session_id="sess-ent")
        ctx.projects.append(ProjectRef("proj-1", "Coverage", "active"))
        ctx.active_project_id = "proj-1"
        
        discovery = EntelexisDiscovery()
        purposes = discovery.discover_from_context(ctx)
        
        assert any("project:proj-1" in p.purpose_id for p in purposes)
    
    def test_discover_from_idea(self):
        """Test discovering purposes from active idea."""
        ctx = InceptionContext(context_id="ctx-ent", session_id="sess-ent")
        ctx.ideas.append(IdeaRef("idea-1", "Test Idea", "developing"))
        ctx.active_idea_id = "idea-1"
        
        discovery = EntelexisDiscovery()
        purposes = discovery.discover_from_context(ctx)
        
        assert any("idea:idea-1" in p.purpose_id for p in purposes)
    
    def test_discover_from_dialectical(self):
        """Test discovering purposes from dialectical state."""
        ctx = InceptionContext(context_id="ctx-ent", session_id="sess-ent")
        ctx.dialectical.thesis = "Testing is important"
        
        discovery = EntelexisDiscovery()
        purposes = discovery.discover_from_context(ctx)
        
        assert any("dialectical" in p.purpose_id for p in purposes)


class TestDomainTracker:
    """Tests for DomainTracker."""
    
    def test_track_domain_change(self):
        """Test tracking domain changes."""
        ctx = InceptionContext(context_id="ctx-dt", session_id="sess-dt")
        tracker = DomainTracker()
        
        tracker.track_domain_change(ctx, "dom-1")
        
        assert ctx.active_domain_id == "dom-1"
        assert len(tracker.domain_history) == 1
    
    def test_get_domain_time(self):
        """Test calculating time in domain."""
        ctx = InceptionContext(context_id="ctx-dt", session_id="sess-dt")
        tracker = DomainTracker()
        
        tracker.track_domain_change(ctx, "dom-1")
        
        time_spent = tracker.get_domain_time("dom-1")
        assert time_spent >= 0


class TestIdeaLifecycle:
    """Tests for IdeaLifecycle."""
    
    def test_transition_idea(self):
        """Test transitioning idea state."""
        ctx = InceptionContext(context_id="ctx-il", session_id="sess-il")
        ctx.ideas.append(IdeaRef("idea-1", "Test", "nascent"))
        
        lifecycle = IdeaLifecycle()
        lifecycle.transition(ctx, "idea-1", IdeaState.DEVELOPING)
        
        assert ctx.ideas[0].state == "developing"
        assert len(lifecycle.transitions) == 1
    
    def test_get_lifecycle(self):
        """Test getting idea lifecycle history."""
        ctx = InceptionContext(context_id="ctx-il", session_id="sess-il")
        ctx.ideas.append(IdeaRef("idea-1", "Test", "nascent"))
        
        lifecycle = IdeaLifecycle()
        lifecycle.transition(ctx, "idea-1", IdeaState.DEVELOPING)
        lifecycle.transition(ctx, "idea-1", IdeaState.MATURE)
        
        history = lifecycle.get_lifecycle("idea-1")
        assert len(history) == 2


class TestProjectIdeaLinker:
    """Tests for ProjectIdeaLinker."""
    
    def test_link_idea_to_project(self):
        """Test linking an idea to a project."""
        ctx = InceptionContext(context_id="ctx-pil", session_id="sess-pil")
        ctx.projects.append(ProjectRef("proj-1", "Test Project", "active"))
        
        linker = ProjectIdeaLinker()
        result = linker.link_idea_to_project(ctx, "idea-1", "proj-1")
        
        assert result is True
        assert "idea-1" in ctx.projects[0].idea_ids
    
    def test_link_to_nonexistent_project(self):
        """Test linking to non-existent project."""
        ctx = InceptionContext(context_id="ctx-pil", session_id="sess-pil")
        
        linker = ProjectIdeaLinker()
        result = linker.link_idea_to_project(ctx, "idea-1", "nonexistent")
        
        assert result is False
    
    def test_get_project_ideas(self):
        """Test getting ideas for a project."""
        ctx = InceptionContext(context_id="ctx-pil", session_id="sess-pil")
        ctx.projects.append(ProjectRef("proj-1", "Test Project", "active", ["idea-1"]))
        ctx.ideas.append(IdeaRef("idea-1", "Test Idea", "developing"))
        
        linker = ProjectIdeaLinker()
        ideas = linker.get_project_ideas(ctx, "proj-1")
        
        assert len(ideas) == 1
        assert ideas[0].idea_id == "idea-1"


class TestContactRegistry:
    """Tests for ContactRegistry."""
    
    def test_register_new_contact(self):
        """Test registering a new contact."""
        ctx = InceptionContext(context_id="ctx-cr", session_id="sess-cr")
        contact = ContactRef("c-1", "Alice", "human", "participant", True)
        
        registry = ContactRegistry()
        registry.register_contact(ctx, contact)
        
        assert len(ctx.contacts) == 1
        assert ctx.contacts[0].name == "Alice"
    
    def test_update_existing_contact(self):
        """Test updating an existing contact."""
        ctx = InceptionContext(context_id="ctx-cr", session_id="sess-cr")
        ctx.contacts.append(ContactRef("c-1", "Alice", "human", "participant", True))
        
        registry = ContactRegistry()
        updated = ContactRef("c-1", "Alice Smith", "human", "admin", True)
        registry.register_contact(ctx, updated)
        
        assert len(ctx.contacts) == 1
        assert ctx.contacts[0].name == "Alice Smith"
        assert ctx.contacts[0].role == "admin"
    
    def test_activate_agent(self):
        """Test activating an agent."""
        ctx = InceptionContext(context_id="ctx-cr", session_id="sess-cr")
        
        registry = ContactRegistry()
        registry.activate_agent(ctx, "ARCHON")
        
        assert "ARCHON" in ctx.active_agent_ids
    
    def test_deactivate_agent(self):
        """Test deactivating an agent."""
        ctx = InceptionContext(context_id="ctx-cr", session_id="sess-cr")
        ctx.active_agent_ids = ["ARCHON"]
        
        registry = ContactRegistry()
        registry.deactivate_agent(ctx, "ARCHON")
        
        assert "ARCHON" not in ctx.active_agent_ids
    
    def test_get_active_agents(self):
        """Test getting active agents."""
        ctx = InceptionContext(context_id="ctx-cr", session_id="sess-cr")
        ctx.contacts.append(ContactRef("ARCHON", "Archon", "agent"))
        ctx.active_agent_ids = ["ARCHON"]
        
        registry = ContactRegistry()
        agents = registry.get_active_agents(ctx)
        
        assert len(agents) == 1
        assert agents[0].contact_id == "ARCHON"


# =============================================================================
# Test: Context Diff
# =============================================================================

class TestContextDiff:
    """Tests for ContextDiff."""
    
    def test_change_count(self):
        """Test change count property."""
        diff = ContextDiff(from_version=1, to_version=2, changes=[{"field": "state"}])
        assert diff.change_count == 1


class TestContextDiffer:
    """Tests for ContextDiffer."""
    
    def test_detect_state_change(self):
        """Test detecting state changes."""
        old = InceptionContext(context_id="ctx", session_id="sess")
        new = InceptionContext(context_id="ctx", session_id="sess")
        new.activate()
        new.metadata.version = 2
        
        differ = ContextDiffer()
        diff = differ.diff(old, new)
        
        assert any(c["field"] == "state" for c in diff.changes)
    
    def test_detect_domain_added(self):
        """Test detecting added domains."""
        old = InceptionContext(context_id="ctx", session_id="sess")
        new = InceptionContext(context_id="ctx", session_id="sess")
        new.domains.append(DomainRef("dom-1", "ML", "subject"))
        
        differ = ContextDiffer()
        diff = differ.diff(old, new)
        
        assert any(c.get("action") == "added" for c in diff.changes)
    
    def test_detect_dialectical_change(self):
        """Test detecting dialectical changes."""
        old = InceptionContext(context_id="ctx", session_id="sess")
        new = InceptionContext(context_id="ctx", session_id="sess")
        new.dialectical.thesis = "New thesis"
        
        differ = ContextDiffer()
        diff = differ.diff(old, new)
        
        assert any("dialectical" in c["field"] for c in diff.changes)


# =============================================================================
# Test: Context Events
# =============================================================================

class TestContextEvent:
    """Tests for ContextEvent."""
    
    def test_to_bus_format(self):
        """Test conversion to bus format."""
        event = ContextEvent(
            event_type=ContextEventType.ACTIVATED,
            context_id="ctx-1",
            session_id="sess-1",
            payload={"test": "data"},
        )
        
        bus_format = event.to_bus_format()
        
        assert "inception.context.context_activated" in bus_format["type"]
        assert bus_format["context_id"] == "ctx-1"


class TestContextEventEmitter:
    """Tests for ContextEventEmitter."""
    
    def test_emit_stores_event(self):
        """Test that emit stores events."""
        emitter = ContextEventEmitter()
        event = ContextEvent(
            event_type=ContextEventType.CREATED,
            context_id="ctx-1",
            session_id="sess-1",
            payload={},
        )
        
        emitter.emit(event)
        
        assert len(emitter.event_log) == 1
    
    def test_emit_state_change(self):
        """Test emitting state change events."""
        ctx = InceptionContext(context_id="ctx-1", session_id="sess-1")
        ctx.state = ContextState.ACTIVE
        
        emitter = ContextEventEmitter()
        emitter.emit_state_change(ctx, ContextState.INITIALIZING)
        
        assert len(emitter.event_log) == 1
        assert emitter.event_log[0].event_type == ContextEventType.ACTIVATED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
