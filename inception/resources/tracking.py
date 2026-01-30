"""
Resource Tracking System
Phase 11, Steps 241-260

Implements:
- Resource base type (241)
- Domain resource tracking (242)
- Idea resource lifecycle (243)
- Project resource management (244)
- Contact registry (humans + agents) (245)
- Agent registry and state tracking (246)
- Resource → concept linking (247)
- Resource dependency graph (248)
- Resource conflict detection (249)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional, TypeVar, Generic
from abc import ABC, abstractmethod


# =============================================================================
# Step 241: Resource Base Type
# =============================================================================

class ResourceType(Enum):
    """Types of resources."""
    DOMAIN = "domain"
    IDEA = "idea"
    PROJECT = "project"
    CONTACT = "contact"
    AGENT = "agent"
    DOCUMENT = "document"
    CONCEPT = "concept"


class ResourceState(Enum):
    """States of a resource."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class ResourceMetadata:
    """Metadata for resources."""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    version: int = 1
    tags: list[str] = field(default_factory=list)
    custom: dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource(ABC):
    """
    Base class for all tracked resources.
    """
    id: str
    name: str
    resource_type: ResourceType
    state: ResourceState = ResourceState.DRAFT
    metadata: ResourceMetadata = field(default_factory=ResourceMetadata)
    
    # Relationships
    parent_id: Optional[str] = None
    child_ids: list[str] = field(default_factory=list)
    linked_concept_ids: list[str] = field(default_factory=list)
    dependency_ids: list[str] = field(default_factory=list)
    
    def touch(self) -> None:
        """Update modification timestamp."""
        self.metadata.updated_at = datetime.utcnow()
        self.metadata.version += 1
    
    def activate(self) -> None:
        """Activate the resource."""
        self.state = ResourceState.ACTIVE
        self.touch()
    
    def pause(self) -> None:
        """Pause the resource."""
        self.state = ResourceState.PAUSED
        self.touch()
    
    def complete(self) -> None:
        """Mark resource as completed."""
        self.state = ResourceState.COMPLETED
        self.touch()
    
    def archive(self) -> None:
        """Archive the resource."""
        self.state = ResourceState.ARCHIVED
        self.touch()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag."""
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.touch()
    
    def link_concept(self, concept_id: str) -> None:
        """Link to a concept."""
        if concept_id not in self.linked_concept_ids:
            self.linked_concept_ids.append(concept_id)
            self.touch()
    
    def add_dependency(self, resource_id: str) -> None:
        """Add a dependency on another resource."""
        if resource_id not in self.dependency_ids:
            self.dependency_ids.append(resource_id)
            self.touch()


# =============================================================================
# Step 242: Domain Resource Tracking
# =============================================================================

class DomainType(Enum):
    """Types of domains."""
    SUBJECT = "subject"       # Subject area (e.g., "Machine Learning")
    PROCESS = "process"       # Process domain (e.g., "Software Development")
    TECHNOLOGY = "technology" # Technology domain (e.g., "Python")
    INDUSTRY = "industry"     # Industry domain (e.g., "Finance")
    CUSTOM = "custom"


@dataclass
class Domain(Resource):
    """A domain of knowledge or activity."""
    domain_type: DomainType = DomainType.SUBJECT
    depth: int = 0  # 0 = root domain
    
    # Domain-specific
    description: str = ""
    expertise_level: float = 0.0  # 0-1
    relevance_score: float = 0.5  # 0-1
    
    # Sub-domains
    subdomain_ids: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.resource_type = ResourceType.DOMAIN


class DomainRegistry:
    """Registry for tracking domains."""
    
    def __init__(self):
        self.domains: dict[str, Domain] = {}
        self.domain_tree: dict[str, list[str]] = {}  # parent_id -> child_ids
    
    def register(self, domain: Domain) -> str:
        """Register a domain."""
        self.domains[domain.id] = domain
        
        if domain.parent_id:
            if domain.parent_id not in self.domain_tree:
                self.domain_tree[domain.parent_id] = []
            self.domain_tree[domain.parent_id].append(domain.id)
            
            # Update parent
            if domain.parent_id in self.domains:
                self.domains[domain.parent_id].subdomain_ids.append(domain.id)
        
        return domain.id
    
    def get_root_domains(self) -> list[Domain]:
        """Get all root-level domains."""
        return [d for d in self.domains.values() if d.parent_id is None]
    
    def get_subdomains(self, domain_id: str) -> list[Domain]:
        """Get subdomains of a domain."""
        return [
            self.domains[sid]
            for sid in self.domain_tree.get(domain_id, [])
        ]
    
    def get_domain_path(self, domain_id: str) -> list[Domain]:
        """Get path from root to domain."""
        path = []
        current_id = domain_id
        
        while current_id:
            domain = self.domains.get(current_id)
            if domain:
                path.append(domain)
                current_id = domain.parent_id
            else:
                break
        
        return list(reversed(path))


# =============================================================================
# Step 243: Idea Resource Lifecycle
# =============================================================================

class IdeaState(Enum):
    """Lifecycle states for ideas."""
    NASCENT = "nascent"         # Just captured
    DEVELOPING = "developing"   # Being explored
    MATURE = "mature"           # Fully developed
    VALIDATED = "validated"     # Tested/proven
    IMPLEMENTED = "implemented" # Built into something
    ARCHIVED = "archived"       # No longer active


@dataclass
class Idea(Resource):
    """An idea being tracked through its lifecycle."""
    idea_state: IdeaState = IdeaState.NASCENT
    
    # Idea content
    title: str = ""
    description: str = ""
    hypothesis: Optional[str] = None
    
    # Relationships
    related_idea_ids: list[str] = field(default_factory=list)
    project_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)
    
    # Metrics
    novelty_score: float = 0.5
    feasibility_score: float = 0.5
    impact_score: float = 0.5
    
    # History
    state_history: list[tuple[IdeaState, datetime]] = field(default_factory=list)
    
    def __post_init__(self):
        self.resource_type = ResourceType.IDEA
        self.state_history.append((self.idea_state, datetime.utcnow()))
    
    def transition_to(self, new_state: IdeaState) -> None:
        """Transition to a new state."""
        self.idea_state = new_state
        self.state_history.append((new_state, datetime.utcnow()))
        self.touch()
    
    @property
    def priority_score(self) -> float:
        """Calculate priority based on metrics."""
        return (self.novelty_score + self.feasibility_score + self.impact_score) / 3


class IdeaTracker:
    """Tracker for idea lifecycle."""
    
    def __init__(self):
        self.ideas: dict[str, Idea] = {}
        self.by_state: dict[IdeaState, list[str]] = {s: [] for s in IdeaState}
    
    def register(self, idea: Idea) -> str:
        """Register an idea."""
        self.ideas[idea.id] = idea
        self.by_state[idea.idea_state].append(idea.id)
        return idea.id
    
    def transition(self, idea_id: str, new_state: IdeaState) -> bool:
        """Transition an idea to a new state."""
        idea = self.ideas.get(idea_id)
        if not idea:
            return False
        
        # Remove from old state list
        old_state = idea.idea_state
        if idea_id in self.by_state[old_state]:
            self.by_state[old_state].remove(idea_id)
        
        # Update state
        idea.transition_to(new_state)
        self.by_state[new_state].append(idea_id)
        
        return True
    
    def get_by_state(self, state: IdeaState) -> list[Idea]:
        """Get ideas in a specific state."""
        return [self.ideas[iid] for iid in self.by_state.get(state, [])]
    
    def get_priority_ranked(self, limit: int = 10) -> list[Idea]:
        """Get ideas ranked by priority."""
        active_ideas = [i for i in self.ideas.values() 
                       if i.idea_state not in [IdeaState.ARCHIVED, IdeaState.IMPLEMENTED]]
        return sorted(active_ideas, key=lambda i: i.priority_score, reverse=True)[:limit]


# =============================================================================
# Step 244: Project Resource Management
# =============================================================================

class ProjectStatus(Enum):
    """Project statuses."""
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Milestone:
    """A project milestone."""
    id: str
    name: str
    description: str
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    completed: bool = False


@dataclass
class Project(Resource):
    """A project resource."""
    status: ProjectStatus = ProjectStatus.PLANNING
    
    # Project content
    description: str = ""
    goal: str = ""
    
    # Timeline
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    
    # Milestones
    milestones: list[Milestone] = field(default_factory=list)
    
    # Relationships
    idea_ids: list[str] = field(default_factory=list)
    team_member_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)
    
    # Metrics
    progress: float = 0.0  # 0-1
    health: str = "green"  # 'green', 'yellow', 'red'
    
    def __post_init__(self):
        self.resource_type = ResourceType.PROJECT
    
    def add_milestone(self, name: str, description: str, due_date: datetime = None) -> Milestone:
        """Add a milestone."""
        milestone = Milestone(
            id=f"{self.id}_m{len(self.milestones)}",
            name=name,
            description=description,
            due_date=due_date,
        )
        self.milestones.append(milestone)
        self.touch()
        return milestone
    
    def complete_milestone(self, milestone_id: str) -> bool:
        """Mark a milestone as completed."""
        for m in self.milestones:
            if m.id == milestone_id:
                m.completed = True
                m.completed_date = datetime.utcnow()
                self._update_progress()
                return True
        return False
    
    def _update_progress(self) -> None:
        """Update progress based on milestones."""
        if self.milestones:
            completed = sum(1 for m in self.milestones if m.completed)
            self.progress = completed / len(self.milestones)
        self.touch()
    
    def link_idea(self, idea_id: str) -> None:
        """Link an idea to this project."""
        if idea_id not in self.idea_ids:
            self.idea_ids.append(idea_id)
            self.touch()


class ProjectManager:
    """Manager for projects."""
    
    def __init__(self):
        self.projects: dict[str, Project] = {}
    
    def create(self, name: str, goal: str, description: str = "") -> Project:
        """Create a new project."""
        project = Project(
            id=hashlib.md5(f"{name}{datetime.utcnow()}".encode()).hexdigest()[:8],
            name=name,
            resource_type=ResourceType.PROJECT,
            description=description,
            goal=goal,
        )
        self.projects[project.id] = project
        return project
    
    def get_active(self) -> list[Project]:
        """Get active projects."""
        return [p for p in self.projects.values() if p.status == ProjectStatus.ACTIVE]
    
    def get_by_status(self, status: ProjectStatus) -> list[Project]:
        """Get projects by status."""
        return [p for p in self.projects.values() if p.status == status]
    
    def get_health_report(self) -> dict[str, Any]:
        """Get health report for all projects."""
        return {
            "total": len(self.projects),
            "by_status": {s.value: len(self.get_by_status(s)) for s in ProjectStatus},
            "by_health": {
                "green": sum(1 for p in self.projects.values() if p.health == "green"),
                "yellow": sum(1 for p in self.projects.values() if p.health == "yellow"),
                "red": sum(1 for p in self.projects.values() if p.health == "red"),
            },
        }


# =============================================================================
# Step 245-246: Contact and Agent Registry
# =============================================================================

class ContactType(Enum):
    """Types of contacts."""
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class AgentState(Enum):
    """States of an agent."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class Contact(Resource):
    """A contact (human or agent)."""
    contact_type: ContactType = ContactType.HUMAN
    
    # Identity
    email: Optional[str] = None
    handle: Optional[str] = None
    
    # Relationship
    role: str = "participant"
    organization: Optional[str] = None
    
    # Interaction
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    
    def __post_init__(self):
        self.resource_type = ResourceType.CONTACT
    
    def record_interaction(self) -> None:
        """Record an interaction."""
        self.last_interaction = datetime.utcnow()
        self.interaction_count += 1
        self.touch()


@dataclass
class Agent(Resource):
    """An AI agent."""
    agent_type: str = "generic"  # 'reasoner', 'extractor', 'validator', etc.
    agent_state: AgentState = AgentState.IDLE
    
    # Capabilities
    capabilities: list[str] = field(default_factory=list)
    persona: Optional[str] = None
    
    # State
    current_task: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    
    # Metrics
    tasks_completed: int = 0
    success_rate: float = 1.0
    avg_latency_ms: float = 0.0
    
    def __post_init__(self):
        self.resource_type = ResourceType.AGENT
    
    def activate(self, task: str = None) -> None:
        """Activate the agent."""
        self.agent_state = AgentState.ACTIVE
        self.current_task = task
        self.touch()
    
    def complete_task(self, success: bool = True) -> None:
        """Complete current task."""
        self.tasks_completed += 1
        if not success:
            self.success_rate = (self.success_rate * (self.tasks_completed - 1) + 0) / self.tasks_completed
        self.current_task = None
        self.agent_state = AgentState.IDLE
        self.touch()
    
    def heartbeat(self) -> None:
        """Record heartbeat."""
        self.last_heartbeat = datetime.utcnow()


class ContactRegistry:
    """Registry for contacts (humans and agents)."""
    
    def __init__(self):
        self.contacts: dict[str, Contact] = {}
        self.agents: dict[str, Agent] = {}
    
    def register_contact(self, contact: Contact) -> str:
        """Register a contact."""
        self.contacts[contact.id] = contact
        return contact.id
    
    def register_agent(self, agent: Agent) -> str:
        """Register an agent."""
        self.agents[agent.id] = agent
        return agent.id
    
    def get_humans(self) -> list[Contact]:
        """Get all human contacts."""
        return [c for c in self.contacts.values() if c.contact_type == ContactType.HUMAN]
    
    def get_active_agents(self) -> list[Agent]:
        """Get active agents."""
        return [a for a in self.agents.values() if a.agent_state == AgentState.ACTIVE]
    
    def get_available_agents(self, capability: str = None) -> list[Agent]:
        """Get available agents, optionally filtered by capability."""
        available = [a for a in self.agents.values() if a.agent_state == AgentState.IDLE]
        if capability:
            available = [a for a in available if capability in a.capabilities]
        return available
    
    def get_agent_stats(self) -> dict[str, Any]:
        """Get agent statistics."""
        return {
            "total": len(self.agents),
            "by_state": {s.value: sum(1 for a in self.agents.values() if a.agent_state == s) for s in AgentState},
            "avg_success_rate": sum(a.success_rate for a in self.agents.values()) / len(self.agents) if self.agents else 0,
        }


# =============================================================================
# Step 247-248: Resource Linking and Dependency Graph
# =============================================================================

@dataclass
class ResourceLink:
    """A link between resources."""
    from_id: str
    to_id: str
    link_type: str  # 'depends_on', 'derives_from', 'relates_to', 'implements'
    strength: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)


class ResourceGraph:
    """Graph of resource relationships and dependencies."""
    
    def __init__(self):
        self.resources: dict[str, Resource] = {}
        self.links: list[ResourceLink] = []
        self.adjacency: dict[str, list[str]] = {}
        self.reverse_adjacency: dict[str, list[str]] = {}
    
    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the graph."""
        self.resources[resource.id] = resource
        self.adjacency[resource.id] = []
        self.reverse_adjacency[resource.id] = []
    
    def add_link(self, from_id: str, to_id: str, link_type: str, strength: float = 1.0) -> ResourceLink:
        """Add a link between resources."""
        link = ResourceLink(
            from_id=from_id,
            to_id=to_id,
            link_type=link_type,
            strength=strength,
        )
        self.links.append(link)
        
        if from_id in self.adjacency:
            self.adjacency[from_id].append(to_id)
        if to_id in self.reverse_adjacency:
            self.reverse_adjacency[to_id].append(from_id)
        
        return link
    
    def get_dependencies(self, resource_id: str) -> list[Resource]:
        """Get resources that this resource depends on."""
        dep_ids = self.adjacency.get(resource_id, [])
        return [self.resources[rid] for rid in dep_ids if rid in self.resources]
    
    def get_dependents(self, resource_id: str) -> list[Resource]:
        """Get resources that depend on this resource."""
        dep_ids = self.reverse_adjacency.get(resource_id, [])
        return [self.resources[rid] for rid in dep_ids if rid in self.resources]
    
    def get_all_dependencies(self, resource_id: str) -> list[Resource]:
        """Get all transitive dependencies."""
        visited = set()
        result = []
        
        def dfs(rid: str):
            if rid in visited:
                return
            visited.add(rid)
            
            for dep_id in self.adjacency.get(rid, []):
                if dep_id in self.resources:
                    result.append(self.resources[dep_id])
                    dfs(dep_id)
        
        dfs(resource_id)
        return result
    
    def topological_sort(self) -> list[str]:
        """Topological sort of resources by dependencies."""
        in_degree = {rid: 0 for rid in self.resources}
        
        for link in self.links:
            if link.to_id in in_degree:
                in_degree[link.to_id] += 1
        
        queue = [rid for rid, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            rid = queue.pop(0)
            result.append(rid)
            
            for dep_id in self.adjacency.get(rid, []):
                if dep_id in in_degree:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        queue.append(dep_id)
        
        return result


# =============================================================================
# Step 249: Resource Conflict Detection
# =============================================================================

class ConflictType(Enum):
    """Types of resource conflicts."""
    VERSION = "version"         # Version conflict
    DEPENDENCY = "dependency"   # Dependency conflict
    STATE = "state"             # State conflict
    OWNERSHIP = "ownership"     # Ownership conflict
    SCHEDULE = "schedule"       # Schedule conflict


@dataclass
class ResourceConflict:
    """A detected conflict between resources."""
    id: str
    conflict_type: ConflictType
    resource_ids: list[str]
    description: str
    severity: str = "warning"  # 'info', 'warning', 'error', 'critical'
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution: Optional[str] = None


class ConflictDetector:
    """Detect conflicts between resources."""
    
    def __init__(self, graph: ResourceGraph):
        self.graph = graph
        self.conflicts: list[ResourceConflict] = []
    
    def detect_all(self) -> list[ResourceConflict]:
        """Detect all conflicts."""
        conflicts = []
        
        conflicts.extend(self._detect_circular_dependencies())
        conflicts.extend(self._detect_state_conflicts())
        conflicts.extend(self._detect_schedule_conflicts())
        
        self.conflicts.extend(conflicts)
        return conflicts
    
    def _detect_circular_dependencies(self) -> list[ResourceConflict]:
        """Detect circular dependencies."""
        conflicts = []
        visited = set()
        rec_stack = set()
        
        def dfs(rid: str, path: list[str]) -> bool:
            visited.add(rid)
            rec_stack.add(rid)
            path.append(rid)
            
            for dep_id in self.graph.adjacency.get(rid, []):
                if dep_id not in visited:
                    if dfs(dep_id, path):
                        return True
                elif dep_id in rec_stack:
                    # Cycle found
                    cycle_start = path.index(dep_id)
                    cycle = path[cycle_start:] + [dep_id]
                    
                    conflicts.append(ResourceConflict(
                        id=f"conflict_cycle_{rid}",
                        conflict_type=ConflictType.DEPENDENCY,
                        resource_ids=cycle,
                        description=f"Circular dependency detected: {' -> '.join(cycle)}",
                        severity="error",
                    ))
                    return True
            
            path.pop()
            rec_stack.remove(rid)
            return False
        
        for rid in self.graph.resources:
            if rid not in visited:
                dfs(rid, [])
        
        return conflicts
    
    def _detect_state_conflicts(self) -> list[ResourceConflict]:
        """Detect state conflicts (e.g., active resource depending on archived)."""
        conflicts = []
        
        for rid, resource in self.graph.resources.items():
            if resource.state == ResourceState.ACTIVE:
                for dep in self.graph.get_dependencies(rid):
                    if dep.state in [ResourceState.ARCHIVED, ResourceState.DELETED]:
                        conflicts.append(ResourceConflict(
                            id=f"conflict_state_{rid}_{dep.id}",
                            conflict_type=ConflictType.STATE,
                            resource_ids=[rid, dep.id],
                            description=f"Active resource '{resource.name}' depends on archived '{dep.name}'",
                            severity="warning",
                        ))
        
        return conflicts
    
    def _detect_schedule_conflicts(self) -> list[ResourceConflict]:
        """Detect schedule conflicts for projects."""
        conflicts = []
        projects = [r for r in self.graph.resources.values() if r.resource_type == ResourceType.PROJECT]
        
        for project in projects:
            if hasattr(project, 'target_date') and project.target_date:
                for dep in self.graph.get_dependencies(project.id):
                    if hasattr(dep, 'target_date') and dep.target_date:
                        if dep.target_date > project.target_date:
                            conflicts.append(ResourceConflict(
                                id=f"conflict_schedule_{project.id}_{dep.id}",
                                conflict_type=ConflictType.SCHEDULE,
                                resource_ids=[project.id, dep.id],
                                description=f"'{project.name}' target date before dependency '{dep.name}'",
                                severity="warning",
                            ))
        
        return conflicts
    
    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """Mark a conflict as resolved."""
        for conflict in self.conflicts:
            if conflict.id == conflict_id:
                conflict.resolved = True
                conflict.resolution = resolution
                return True
        return False


# =============================================================================
# Factory Functions
# =============================================================================

def create_domain(name: str, domain_type: DomainType = DomainType.SUBJECT) -> Domain:
    """Create a new domain."""
    return Domain(
        id=hashlib.md5(f"domain_{name}".encode()).hexdigest()[:8],
        name=name,
        resource_type=ResourceType.DOMAIN,
        domain_type=domain_type,
    )


def create_idea(title: str, description: str = "") -> Idea:
    """Create a new idea."""
    return Idea(
        id=hashlib.md5(f"idea_{title}".encode()).hexdigest()[:8],
        name=title,
        resource_type=ResourceType.IDEA,
        title=title,
        description=description,
    )


def create_agent(name: str, agent_type: str, capabilities: list[str] = None) -> Agent:
    """Create a new agent."""
    return Agent(
        id=hashlib.md5(f"agent_{name}".encode()).hexdigest()[:8],
        name=name,
        resource_type=ResourceType.AGENT,
        agent_type=agent_type,
        capabilities=capabilities or [],
    )


__all__ = [
    # Base types
    "ResourceType",
    "ResourceState",
    "ResourceMetadata",
    "Resource",
    
    # Domain
    "DomainType",
    "Domain",
    "DomainRegistry",
    
    # Idea
    "IdeaState",
    "Idea",
    "IdeaTracker",
    
    # Project
    "ProjectStatus",
    "Milestone",
    "Project",
    "ProjectManager",
    
    # Contact/Agent
    "ContactType",
    "AgentState",
    "Contact",
    "Agent",
    "ContactRegistry",
    
    # Graph
    "ResourceLink",
    "ResourceGraph",
    
    # Conflict
    "ConflictType",
    "ResourceConflict",
    "ConflictDetector",
    
    # Factory
    "create_domain",
    "create_idea",
    "create_agent",
]
