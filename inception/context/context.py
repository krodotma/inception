"""
Context Object System
Phase 9, Steps 201-220

Implements:
- InceptionContext schema (201)
- Context serialization (202)
- Context persistence (LMDB) (203)
- Context query API (204)
- Entelexis discovery (205)
- Domain tracking (206)
- Idea lifecycle tracking (207)
- Project → idea → concept linking (208)
- Contact/agent tracking (209)
- Context diff (210)
- Context to bus events (211)
"""

from __future__ import annotations

import hashlib
import json
import lmdb
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic
from abc import ABC, abstractmethod


# =============================================================================
# Step 201: InceptionContext Schema
# =============================================================================

class ContextState(Enum):
    """States of a context."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class ContextMetadata:
    """Metadata for a context."""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    version: int = 1
    tags: list[str] = field(default_factory=list)


@dataclass
class EntelexisRef:
    """Reference to an Entelexis purpose."""
    purpose_id: str
    purpose_name: str
    state: str
    confidence: float = 0.5


@dataclass
class DomainRef:
    """Reference to a domain."""
    domain_id: str
    name: str
    type: str  # 'subject', 'process', 'technology'
    depth: int = 0  # 0 = root domain


@dataclass
class IdeaRef:
    """Reference to an idea."""
    idea_id: str
    title: str
    state: str  # 'nascent', 'developing', 'mature', 'archived'
    parent_id: Optional[str] = None


@dataclass
class ProjectRef:
    """Reference to a project."""
    project_id: str
    name: str
    status: str  # 'planning', 'active', 'paused', 'completed'
    idea_ids: list[str] = field(default_factory=list)


@dataclass
class ContactRef:
    """Reference to a contact (human or agent)."""
    contact_id: str
    name: str
    type: str  # 'human', 'agent', 'system'
    role: str = "participant"
    active: bool = True


@dataclass
class DialogState:
    """State of a dialog/conversation."""
    turn_count: int = 0
    last_speaker: str = "user"
    topic_stack: list[str] = field(default_factory=list)
    pending_questions: list[str] = field(default_factory=list)


@dataclass
class DialecticalState:
    """State of dialectical reasoning."""
    thesis: Optional[str] = None
    antithesis: Optional[str] = None
    synthesis: Optional[str] = None
    mode: str = "exploratory"  # 'exploratory', 'steelman', 'assumptions', 'synthesis'
    contradictions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class InceptionContext:
    """
    The master context object for Inception sessions.
    
    Contains all stateful information about a knowledge session:
    - Purpose alignment (Entelexis)
    - Domain focus
    - Ideas being explored
    - Projects in scope
    - Participants (humans and agents)
    - Dialog state
    - Dialectical reasoning state
    """
    
    # Identity
    context_id: str
    session_id: str
    
    # Metadata
    metadata: ContextMetadata = field(default_factory=ContextMetadata)
    state: ContextState = ContextState.INITIALIZING
    
    # Entelexis (Purpose)
    entelexis: Optional[EntelexisRef] = None
    
    # Domain Focus
    domains: list[DomainRef] = field(default_factory=list)
    active_domain_id: Optional[str] = None
    
    # Ideas
    ideas: list[IdeaRef] = field(default_factory=list)
    active_idea_id: Optional[str] = None
    
    # Projects
    projects: list[ProjectRef] = field(default_factory=list)
    active_project_id: Optional[str] = None
    
    # Participants
    contacts: list[ContactRef] = field(default_factory=list)
    active_agent_ids: list[str] = field(default_factory=list)
    
    # Dialog State
    dialog: DialogState = field(default_factory=DialogState)
    
    # Dialectical State
    dialectical: DialecticalState = field(default_factory=DialecticalState)
    
    # Knowledge Graph References
    knowledge_graph_id: Optional[str] = None
    commit_hash: Optional[str] = None
    
    # Arbitrary extensions
    extensions: dict[str, Any] = field(default_factory=dict)
    
    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.metadata.updated_at = datetime.utcnow()
        self.metadata.version += 1
    
    def activate(self) -> None:
        """Activate the context."""
        self.state = ContextState.ACTIVE
        self.touch()
    
    def suspend(self) -> None:
        """Suspend the context."""
        self.state = ContextState.SUSPENDED
        self.touch()
    
    def complete(self) -> None:
        """Mark context as completed."""
        self.state = ContextState.COMPLETED
        self.touch()


# =============================================================================
# Step 202: Context Serialization
# =============================================================================

class ContextSerializer:
    """Serializer for InceptionContext."""
    
    @staticmethod
    def to_dict(ctx: InceptionContext) -> dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "context_id": ctx.context_id,
            "session_id": ctx.session_id,
            "state": ctx.state.value,
            "metadata": {
                "created_at": ctx.metadata.created_at.isoformat(),
                "updated_at": ctx.metadata.updated_at.isoformat(),
                "created_by": ctx.metadata.created_by,
                "version": ctx.metadata.version,
                "tags": ctx.metadata.tags,
            },
            "entelexis": {
                "purpose_id": ctx.entelexis.purpose_id,
                "purpose_name": ctx.entelexis.purpose_name,
                "state": ctx.entelexis.state,
                "confidence": ctx.entelexis.confidence,
            } if ctx.entelexis else None,
            "domains": [
                {"domain_id": d.domain_id, "name": d.name, "type": d.type, "depth": d.depth}
                for d in ctx.domains
            ],
            "active_domain_id": ctx.active_domain_id,
            "ideas": [
                {"idea_id": i.idea_id, "title": i.title, "state": i.state, "parent_id": i.parent_id}
                for i in ctx.ideas
            ],
            "active_idea_id": ctx.active_idea_id,
            "projects": [
                {"project_id": p.project_id, "name": p.name, "status": p.status, "idea_ids": p.idea_ids}
                for p in ctx.projects
            ],
            "active_project_id": ctx.active_project_id,
            "contacts": [
                {"contact_id": c.contact_id, "name": c.name, "type": c.type, "role": c.role, "active": c.active}
                for c in ctx.contacts
            ],
            "active_agent_ids": ctx.active_agent_ids,
            "dialog": {
                "turn_count": ctx.dialog.turn_count,
                "last_speaker": ctx.dialog.last_speaker,
                "topic_stack": ctx.dialog.topic_stack,
                "pending_questions": ctx.dialog.pending_questions,
            },
            "dialectical": {
                "thesis": ctx.dialectical.thesis,
                "antithesis": ctx.dialectical.antithesis,
                "synthesis": ctx.dialectical.synthesis,
                "mode": ctx.dialectical.mode,
                "contradictions": ctx.dialectical.contradictions,
            },
            "knowledge_graph_id": ctx.knowledge_graph_id,
            "commit_hash": ctx.commit_hash,
            "extensions": ctx.extensions,
        }
    
    @staticmethod
    def from_dict(data: dict[str, Any]) -> InceptionContext:
        """Deserialize context from dictionary."""
        ctx = InceptionContext(
            context_id=data["context_id"],
            session_id=data["session_id"],
        )
        
        ctx.state = ContextState(data.get("state", "initializing"))
        
        if meta := data.get("metadata"):
            ctx.metadata = ContextMetadata(
                created_at=datetime.fromisoformat(meta["created_at"]),
                updated_at=datetime.fromisoformat(meta["updated_at"]),
                created_by=meta.get("created_by", "system"),
                version=meta.get("version", 1),
                tags=meta.get("tags", []),
            )
        
        if ent := data.get("entelexis"):
            ctx.entelexis = EntelexisRef(
                purpose_id=ent["purpose_id"],
                purpose_name=ent["purpose_name"],
                state=ent["state"],
                confidence=ent.get("confidence", 0.5),
            )
        
        ctx.domains = [
            DomainRef(d["domain_id"], d["name"], d["type"], d.get("depth", 0))
            for d in data.get("domains", [])
        ]
        ctx.active_domain_id = data.get("active_domain_id")
        
        ctx.ideas = [
            IdeaRef(i["idea_id"], i["title"], i["state"], i.get("parent_id"))
            for i in data.get("ideas", [])
        ]
        ctx.active_idea_id = data.get("active_idea_id")
        
        ctx.projects = [
            ProjectRef(p["project_id"], p["name"], p["status"], p.get("idea_ids", []))
            for p in data.get("projects", [])
        ]
        ctx.active_project_id = data.get("active_project_id")
        
        ctx.contacts = [
            ContactRef(c["contact_id"], c["name"], c["type"], c.get("role", "participant"), c.get("active", True))
            for c in data.get("contacts", [])
        ]
        ctx.active_agent_ids = data.get("active_agent_ids", [])
        
        if dialog := data.get("dialog"):
            ctx.dialog = DialogState(
                turn_count=dialog.get("turn_count", 0),
                last_speaker=dialog.get("last_speaker", "user"),
                topic_stack=dialog.get("topic_stack", []),
                pending_questions=dialog.get("pending_questions", []),
            )
        
        if dial := data.get("dialectical"):
            ctx.dialectical = DialecticalState(
                thesis=dial.get("thesis"),
                antithesis=dial.get("antithesis"),
                synthesis=dial.get("synthesis"),
                mode=dial.get("mode", "exploratory"),
                contradictions=dial.get("contradictions", []),
            )
        
        ctx.knowledge_graph_id = data.get("knowledge_graph_id")
        ctx.commit_hash = data.get("commit_hash")
        ctx.extensions = data.get("extensions", {})
        
        return ctx
    
    @staticmethod
    def to_json(ctx: InceptionContext) -> str:
        """Serialize to JSON string."""
        return json.dumps(ContextSerializer.to_dict(ctx))
    
    @staticmethod
    def from_json(json_str: str) -> InceptionContext:
        """Deserialize from JSON string."""
        return ContextSerializer.from_dict(json.loads(json_str))


# =============================================================================
# Step 203: Context Persistence (LMDB)
# =============================================================================

class ContextStore:
    """LMDB-backed context storage."""
    
    def __init__(self, path: Path, map_size: int = 1024**3):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        self.env = lmdb.open(
            str(self.path),
            map_size=map_size,
            max_dbs=5,
        )
        
        self.contexts_db = self.env.open_db(b"contexts", create=True)
        self.sessions_db = self.env.open_db(b"sessions", create=True)
        self.history_db = self.env.open_db(b"history", create=True)
    
    def save(self, ctx: InceptionContext) -> str:
        """Save a context."""
        data = ContextSerializer.to_json(ctx).encode()
        
        with self.env.begin(write=True) as txn:
            txn.put(ctx.context_id.encode(), data, db=self.contexts_db)
            
            # Index by session
            session_key = f"{ctx.session_id}:{ctx.context_id}".encode()
            txn.put(session_key, ctx.context_id.encode(), db=self.sessions_db)
            
            # Save to history
            history_key = f"{ctx.context_id}:{ctx.metadata.version}".encode()
            txn.put(history_key, data, db=self.history_db)
        
        return ctx.context_id
    
    def load(self, context_id: str) -> Optional[InceptionContext]:
        """Load a context by ID."""
        with self.env.begin(db=self.contexts_db) as txn:
            data = txn.get(context_id.encode())
            if data:
                return ContextSerializer.from_json(data.decode())
        return None
    
    def load_by_session(self, session_id: str) -> list[InceptionContext]:
        """Load all contexts for a session."""
        contexts = []
        prefix = f"{session_id}:".encode()
        
        with self.env.begin(db=self.sessions_db) as txn:
            cursor = txn.cursor()
            cursor.set_range(prefix)
            
            for key, value in cursor:
                if not key.startswith(prefix):
                    break
                context_id = value.decode()
                ctx = self.load(context_id)
                if ctx:
                    contexts.append(ctx)
        
        return contexts
    
    def get_history(self, context_id: str, limit: int = 10) -> list[InceptionContext]:
        """Get version history for a context."""
        history = []
        prefix = f"{context_id}:".encode()
        
        with self.env.begin(db=self.history_db) as txn:
            cursor = txn.cursor()
            cursor.set_range(prefix)
            
            for key, value in cursor:
                if not key.startswith(prefix):
                    break
                ctx = ContextSerializer.from_json(value.decode())
                history.append(ctx)
                if len(history) >= limit:
                    break
        
        return sorted(history, key=lambda c: c.metadata.version, reverse=True)
    
    def delete(self, context_id: str) -> bool:
        """Delete a context."""
        with self.env.begin(write=True) as txn:
            return txn.delete(context_id.encode(), db=self.contexts_db)
    
    def close(self) -> None:
        """Close the store."""
        self.env.close()


# =============================================================================
# Step 204: Context Query API
# =============================================================================

class ContextQuery:
    """Query builder for contexts."""
    
    def __init__(self, store: ContextStore):
        self.store = store
        self._filters: list[callable] = []
    
    def where_state(self, state: ContextState) -> ContextQuery:
        """Filter by state."""
        self._filters.append(lambda c: c.state == state)
        return self
    
    def where_tag(self, tag: str) -> ContextQuery:
        """Filter by tag."""
        self._filters.append(lambda c: tag in c.metadata.tags)
        return self
    
    def where_domain(self, domain_id: str) -> ContextQuery:
        """Filter by domain."""
        self._filters.append(lambda c: any(d.domain_id == domain_id for d in c.domains))
        return self
    
    def where_project(self, project_id: str) -> ContextQuery:
        """Filter by project."""
        self._filters.append(lambda c: any(p.project_id == project_id for p in c.projects))
        return self
    
    def where_agent(self, agent_id: str) -> ContextQuery:
        """Filter by active agent."""
        self._filters.append(lambda c: agent_id in c.active_agent_ids)
        return self
    
    def execute(self, session_id: Optional[str] = None) -> list[InceptionContext]:
        """Execute the query."""
        if session_id:
            contexts = self.store.load_by_session(session_id)
        else:
            # Load all (expensive, would use index in production)
            contexts = []
            with self.store.env.begin(db=self.store.contexts_db) as txn:
                cursor = txn.cursor()
                for key, value in cursor:
                    ctx = ContextSerializer.from_json(value.decode())
                    contexts.append(ctx)
        
        # Apply filters
        for f in self._filters:
            contexts = [c for c in contexts if f(c)]
        
        return contexts


# =============================================================================
# Step 205-209: Resource Discovery and Tracking
# =============================================================================

class EntelexisDiscovery:
    """Discover and link Entelexis purposes from context."""
    
    def discover_from_context(self, ctx: InceptionContext) -> list[EntelexisRef]:
        """Discover purposes from context state."""
        purposes = []
        
        # From active project
        if ctx.active_project_id:
            for p in ctx.projects:
                if p.project_id == ctx.active_project_id:
                    purposes.append(EntelexisRef(
                        purpose_id=f"project:{p.project_id}",
                        purpose_name=f"Complete {p.name}",
                        state="focused",
                        confidence=0.8,
                    ))
        
        # From active idea
        if ctx.active_idea_id:
            for i in ctx.ideas:
                if i.idea_id == ctx.active_idea_id:
                    purposes.append(EntelexisRef(
                        purpose_id=f"idea:{i.idea_id}",
                        purpose_name=f"Develop {i.title}",
                        state="emerging",
                        confidence=0.6,
                    ))
        
        # From dialectical state
        if ctx.dialectical.thesis:
            purposes.append(EntelexisRef(
                purpose_id="dialectical:synthesis",
                purpose_name="Achieve synthesis",
                state="flowing" if ctx.dialectical.synthesis else "focused",
                confidence=0.7,
            ))
        
        return purposes


class DomainTracker:
    """Track domain focus changes."""
    
    def __init__(self):
        self.domain_history: list[tuple[str, datetime]] = []
    
    def track_domain_change(self, ctx: InceptionContext, new_domain_id: str) -> None:
        """Track a domain focus change."""
        self.domain_history.append((new_domain_id, datetime.utcnow()))
        ctx.active_domain_id = new_domain_id
        ctx.touch()
    
    def get_domain_time(self, domain_id: str) -> float:
        """Get time spent in a domain (seconds)."""
        total = 0.0
        in_domain_since = None
        
        for did, ts in self.domain_history:
            if did == domain_id:
                in_domain_since = ts
            elif in_domain_since:
                total += (ts - in_domain_since).total_seconds()
                in_domain_since = None
        
        if in_domain_since:
            total += (datetime.utcnow() - in_domain_since).total_seconds()
        
        return total


class IdeaState(Enum):
    """Lifecycle states for ideas."""
    NASCENT = "nascent"
    DEVELOPING = "developing"
    MATURE = "mature"
    ARCHIVED = "archived"


class IdeaLifecycle:
    """Track idea lifecycle."""
    
    def __init__(self):
        self.transitions: list[tuple[str, IdeaState, datetime]] = []
    
    def transition(self, ctx: InceptionContext, idea_id: str, new_state: IdeaState) -> None:
        """Transition an idea to a new state."""
        for idea in ctx.ideas:
            if idea.idea_id == idea_id:
                idea.state = new_state.value
                self.transitions.append((idea_id, new_state, datetime.utcnow()))
                ctx.touch()
                break
    
    def get_lifecycle(self, idea_id: str) -> list[tuple[IdeaState, datetime]]:
        """Get lifecycle history for an idea."""
        return [(s, ts) for iid, s, ts in self.transitions if iid == idea_id]


class ProjectIdeaLinker:
    """Link projects to ideas to concepts."""
    
    def link_idea_to_project(self, ctx: InceptionContext, idea_id: str, project_id: str) -> bool:
        """Link an idea to a project."""
        for project in ctx.projects:
            if project.project_id == project_id:
                if idea_id not in project.idea_ids:
                    project.idea_ids.append(idea_id)
                    ctx.touch()
                    return True
        return False
    
    def get_project_ideas(self, ctx: InceptionContext, project_id: str) -> list[IdeaRef]:
        """Get all ideas linked to a project."""
        for project in ctx.projects:
            if project.project_id == project_id:
                return [i for i in ctx.ideas if i.idea_id in project.idea_ids]
        return []


class ContactRegistry:
    """Registry for contacts (humans and agents)."""
    
    def register_contact(self, ctx: InceptionContext, contact: ContactRef) -> None:
        """Register a contact in context."""
        existing = next((c for c in ctx.contacts if c.contact_id == contact.contact_id), None)
        if existing:
            # Update
            existing.name = contact.name
            existing.role = contact.role
            existing.active = contact.active
        else:
            ctx.contacts.append(contact)
        ctx.touch()
    
    def activate_agent(self, ctx: InceptionContext, agent_id: str) -> None:
        """Activate an agent in the context."""
        if agent_id not in ctx.active_agent_ids:
            ctx.active_agent_ids.append(agent_id)
            ctx.touch()
    
    def deactivate_agent(self, ctx: InceptionContext, agent_id: str) -> None:
        """Deactivate an agent."""
        if agent_id in ctx.active_agent_ids:
            ctx.active_agent_ids.remove(agent_id)
            ctx.touch()
    
    def get_active_agents(self, ctx: InceptionContext) -> list[ContactRef]:
        """Get all active agents."""
        return [c for c in ctx.contacts 
                if c.type == "agent" and c.contact_id in ctx.active_agent_ids]


# =============================================================================
# Step 210: Context Diff
# =============================================================================

@dataclass
class ContextDiff:
    """Difference between two context versions."""
    from_version: int
    to_version: int
    changes: list[dict[str, Any]]
    
    @property
    def change_count(self) -> int:
        return len(self.changes)


class ContextDiffer:
    """Compute diffs between context versions."""
    
    def diff(self, old: InceptionContext, new: InceptionContext) -> ContextDiff:
        """Compute diff between two contexts."""
        changes = []
        
        # State change
        if old.state != new.state:
            changes.append({
                "field": "state",
                "old": old.state.value,
                "new": new.state.value,
            })
        
        # Domain changes
        old_domains = {d.domain_id for d in old.domains}
        new_domains = {d.domain_id for d in new.domains}
        
        for added in new_domains - old_domains:
            changes.append({"field": "domains", "action": "added", "domain_id": added})
        for removed in old_domains - new_domains:
            changes.append({"field": "domains", "action": "removed", "domain_id": removed})
        
        if old.active_domain_id != new.active_domain_id:
            changes.append({
                "field": "active_domain_id",
                "old": old.active_domain_id,
                "new": new.active_domain_id,
            })
        
        # Idea changes
        old_ideas = {i.idea_id for i in old.ideas}
        new_ideas = {i.idea_id for i in new.ideas}
        
        for added in new_ideas - old_ideas:
            changes.append({"field": "ideas", "action": "added", "idea_id": added})
        for removed in old_ideas - new_ideas:
            changes.append({"field": "ideas", "action": "removed", "idea_id": removed})
        
        # Dialectical changes
        if old.dialectical.thesis != new.dialectical.thesis:
            changes.append({"field": "dialectical.thesis", "old": old.dialectical.thesis, "new": new.dialectical.thesis})
        if old.dialectical.antithesis != new.dialectical.antithesis:
            changes.append({"field": "dialectical.antithesis", "old": old.dialectical.antithesis, "new": new.dialectical.antithesis})
        if old.dialectical.synthesis != new.dialectical.synthesis:
            changes.append({"field": "dialectical.synthesis", "old": old.dialectical.synthesis, "new": new.dialectical.synthesis})
        
        # Dialog changes
        if old.dialog.turn_count != new.dialog.turn_count:
            changes.append({
                "field": "dialog.turn_count",
                "old": old.dialog.turn_count,
                "new": new.dialog.turn_count,
            })
        
        return ContextDiff(
            from_version=old.metadata.version,
            to_version=new.metadata.version,
            changes=changes,
        )


# =============================================================================
# Step 211: Context to Bus Events
# =============================================================================

class ContextEventType(Enum):
    """Types of context events."""
    CREATED = "context_created"
    ACTIVATED = "context_activated"
    SUSPENDED = "context_suspended"
    COMPLETED = "context_completed"
    DOMAIN_CHANGED = "domain_changed"
    IDEA_ADDED = "idea_added"
    IDEA_TRANSITIONED = "idea_transitioned"
    AGENT_JOINED = "agent_joined"
    AGENT_LEFT = "agent_left"
    DIALECTICAL_UPDATE = "dialectical_update"


@dataclass
class ContextEvent:
    """Event for context changes."""
    event_type: ContextEventType
    context_id: str
    session_id: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_bus_format(self) -> dict[str, Any]:
        """Convert to message bus format."""
        return {
            "type": f"inception.context.{self.event_type.value}",
            "context_id": self.context_id,
            "session_id": self.session_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }


class ContextEventEmitter:
    """Emit context events to the bus."""
    
    def __init__(self, bus=None):
        self.bus = bus
        self.event_log: list[ContextEvent] = []
    
    def emit(self, event: ContextEvent) -> None:
        """Emit an event."""
        self.event_log.append(event)
        
        if self.bus:
            # Would call bus.publish(event.to_bus_format())
            pass
    
    def emit_state_change(self, ctx: InceptionContext, old_state: ContextState) -> None:
        """Emit state change event."""
        event_type = {
            ContextState.ACTIVE: ContextEventType.ACTIVATED,
            ContextState.SUSPENDED: ContextEventType.SUSPENDED,
            ContextState.COMPLETED: ContextEventType.COMPLETED,
        }.get(ctx.state, ContextEventType.CREATED)
        
        self.emit(ContextEvent(
            event_type=event_type,
            context_id=ctx.context_id,
            session_id=ctx.session_id,
            payload={"old_state": old_state.value, "new_state": ctx.state.value},
        ))
    
    def emit_domain_change(self, ctx: InceptionContext, old_domain_id: str, new_domain_id: str) -> None:
        """Emit domain change event."""
        self.emit(ContextEvent(
            event_type=ContextEventType.DOMAIN_CHANGED,
            context_id=ctx.context_id,
            session_id=ctx.session_id,
            payload={"old_domain": old_domain_id, "new_domain": new_domain_id},
        ))


# =============================================================================
# Factory Functions
# =============================================================================

def create_context(session_id: str, purpose: str = None) -> InceptionContext:
    """Create a new context."""
    import uuid
    
    ctx = InceptionContext(
        context_id=str(uuid.uuid4())[:8],
        session_id=session_id,
    )
    
    if purpose:
        ctx.entelexis = EntelexisRef(
            purpose_id=f"purpose:{ctx.context_id}",
            purpose_name=purpose,
            state="emerging",
            confidence=0.5,
        )
    
    return ctx


def open_context_store(path: str) -> ContextStore:
    """Open or create a context store."""
    return ContextStore(Path(path))


__all__ = [
    # Context types
    "InceptionContext",
    "ContextState",
    "ContextMetadata",
    
    # Reference types
    "EntelexisRef",
    "DomainRef",
    "IdeaRef",
    "ProjectRef",
    "ContactRef",
    
    # State types
    "DialogState",
    "DialecticalState",
    
    # Serialization
    "ContextSerializer",
    
    # Storage
    "ContextStore",
    "ContextQuery",
    
    # Discovery/Tracking
    "EntelexisDiscovery",
    "DomainTracker",
    "IdeaState",
    "IdeaLifecycle",
    "ProjectIdeaLinker",
    "ContactRegistry",
    
    # Diff
    "ContextDiff",
    "ContextDiffer",
    
    # Events
    "ContextEventType",
    "ContextEvent",
    "ContextEventEmitter",
    
    # Factory
    "create_context",
    "open_context_store",
]
