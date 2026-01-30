"""
Context-Aware Skill Execution — Phase 4

Implements InceptionContext threading through skill execution pipeline.
Skills receive context, execute, and return updated context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field


# =============================================================================
# INCEPTION CONTEXT (Step 96 — ALREADY DEFINED, imported here)
# =============================================================================

# InceptionContext is defined in taxonomic_types.py
# This module provides execution infrastructure around it


# =============================================================================
# SKILL RESULT
# =============================================================================

class SkillStatus(str, Enum):
    """Execution status of a skill."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"  # Partial success with gaps
    FAILED = "failed"
    SKIPPED = "skipped"


T = TypeVar("T")


@dataclass
class SkillResult(Generic[T]):
    """
    Result of a skill execution.
    
    Contains the output, updated context, and execution metadata.
    """
    
    skill_name: str
    status: SkillStatus
    output: T | None = None
    error: str | None = None
    
    # Context updates
    context_updates: dict[str, Any] = field(default_factory=dict)
    
    # Tracking
    execution_time_ms: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    # Learning signals
    epistemic_gaps_found: list[str] = field(default_factory=list)
    aleatoric_expansions: list[str] = field(default_factory=list)
    
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status in (SkillStatus.SUCCESS, SkillStatus.PARTIAL)


# =============================================================================
# SKILL DEFINITION
# =============================================================================

@dataclass
class SkillDefinition:
    """
    Definition of a skill that can be executed.
    
    Skills are invoked with context and return results with context updates.
    """
    
    name: str
    description: str
    category: str  # e.g., "extraction", "synthesis", "verification"
    
    # Execution
    handler: Callable[..., Any] | None = None
    
    # Context requirements
    required_context_fields: list[str] = field(default_factory=list)
    optional_context_fields: list[str] = field(default_factory=list)
    
    # Output specification
    output_type: str = "any"
    updates_context: bool = True
    
    # Entelexis alignment
    entelexis_phase: str = "potential"  # "potential", "developing", "actualized"
    
    # Metadata
    version: str = "1.0.0"
    author: str = "system"


# =============================================================================
# SKILL REGISTRY
# =============================================================================

class SkillRegistry:
    """
    Registry of available skills.
    
    Skills are registered by name and can be looked up for execution.
    """
    
    def __init__(self):
        self._skills: dict[str, SkillDefinition] = {}
        self._handlers: dict[str, Callable] = {}
    
    def register(
        self,
        skill: SkillDefinition,
        handler: Callable | None = None,
    ) -> None:
        """Register a skill definition."""
        self._skills[skill.name] = skill
        if handler:
            self._handlers[skill.name] = handler
        elif skill.handler:
            self._handlers[skill.name] = skill.handler
    
    def get(self, name: str) -> SkillDefinition | None:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def get_handler(self, name: str) -> Callable | None:
        """Get a skill's handler function."""
        return self._handlers.get(name)
    
    def list_skills(self, category: str | None = None) -> list[SkillDefinition]:
        """List all registered skills, optionally filtered by category."""
        if category is None:
            return list(self._skills.values())
        return [s for s in self._skills.values() if s.category == category]
    
    def list_categories(self) -> list[str]:
        """List all skill categories."""
        return list(set(s.category for s in self._skills.values()))


# Global registry
SKILL_REGISTRY = SkillRegistry()


# =============================================================================
# CONTEXT PROPAGATION (Step 97)
# =============================================================================

@dataclass
class ContextUpdate:
    """An update to apply to the context."""
    
    field: str
    operation: str  # "set", "append", "increment", "merge"
    value: Any
    source_skill: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ContextPropagator:
    """
    Propagates context through skill execution pipeline.
    
    Handles context serialization, updates, and versioning.
    """
    
    def __init__(self):
        self._updates: list[ContextUpdate] = []
    
    def record_update(self, update: ContextUpdate) -> None:
        """Record a context update."""
        self._updates.append(update)
    
    def apply_updates(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply all recorded updates to a context dict."""
        result = context.copy()
        
        for update in self._updates:
            if update.operation == "set":
                result[update.field] = update.value
            elif update.operation == "append":
                if update.field not in result:
                    result[update.field] = []
                result[update.field].append(update.value)
            elif update.operation == "increment":
                if update.field not in result:
                    result[update.field] = 0
                result[update.field] += update.value
            elif update.operation == "merge":
                if update.field not in result:
                    result[update.field] = {}
                result[update.field].update(update.value)
        
        return result
    
    def get_updates_since(self, timestamp: datetime) -> list[ContextUpdate]:
        """Get updates since a specific timestamp."""
        return [u for u in self._updates if u.timestamp >= timestamp]
    
    def clear(self) -> None:
        """Clear all recorded updates."""
        self._updates = []


# =============================================================================
# ENTELEXIS TRACKING (Step 98)
# =============================================================================

@dataclass
class EntelexisProgress:
    """Tracks progress of purpose actualization."""
    
    potential_id: str
    phase: str  # "potential", "developing", "actualized"
    progress: float  # 0.0 to 1.0
    blockers: list[str] = field(default_factory=list)
    milestones_reached: list[str] = field(default_factory=list)


class EntelexisTracker:
    """
    Tracks Entelexis (purpose actualization) through skill execution.
    
    Monitors how execution moves toward intended outcomes.
    """
    
    def __init__(self):
        self._potentials: dict[str, EntelexisProgress] = {}
    
    def register_potential(
        self,
        potential_id: str,
        description: str,
    ) -> EntelexisProgress:
        """Register a new potential to be actualized."""
        progress = EntelexisProgress(
            potential_id=potential_id,
            phase="potential",
            progress=0.0,
        )
        self._potentials[potential_id] = progress
        return progress
    
    def update_progress(
        self,
        potential_id: str,
        delta: float,
        milestone: str | None = None,
    ) -> EntelexisProgress | None:
        """Update progress toward actualization."""
        if potential_id not in self._potentials:
            return None
        
        progress = self._potentials[potential_id]
        progress.progress = min(1.0, progress.progress + delta)
        
        # Update phase based on progress
        if progress.progress >= 1.0:
            progress.phase = "actualized"
        elif progress.progress > 0.0:
            progress.phase = "developing"
        
        if milestone:
            progress.milestones_reached.append(milestone)
        
        return progress
    
    def add_blocker(self, potential_id: str, blocker: str) -> None:
        """Add a blocker to a potential."""
        if potential_id in self._potentials:
            self._potentials[potential_id].blockers.append(blocker)
    
    def remove_blocker(self, potential_id: str, blocker: str) -> None:
        """Remove a blocker from a potential."""
        if potential_id in self._potentials:
            blockers = self._potentials[potential_id].blockers
            if blocker in blockers:
                blockers.remove(blocker)
    
    def get_blocked(self) -> list[EntelexisProgress]:
        """Get all blocked potentials."""
        return [p for p in self._potentials.values() if p.blockers]
    
    def get_actualized(self) -> list[EntelexisProgress]:
        """Get all actualized potentials."""
        return [p for p in self._potentials.values() if p.phase == "actualized"]


# =============================================================================
# RESOURCE TRACKING (Steps 99-101)
# =============================================================================

@dataclass
class ResourceReference:
    """Reference to a resource (domain/idea/project/contact)."""
    
    resource_type: str  # "domain", "idea", "project", "contact"
    nid: int
    name: str
    relevance: float = 1.0


class ResourceTracker:
    """
    Tracks active resources (domains, ideas, projects, contacts, KG refs).
    
    Steps 99-101: domain/idea/project tracking + agent state + KG/HyperKG refs.
    """
    
    def __init__(self):
        self._domains: dict[int, ResourceReference] = {}
        self._ideas: dict[int, ResourceReference] = {}
        self._projects: dict[int, ResourceReference] = {}
        self._contacts: dict[int, ResourceReference] = {}
        self._kg_refs: dict[str, Any] = {}  # Knowledge graph references
        self._agent_states: dict[str, str] = {}  # agent_id -> state
    
    def add_domain(self, nid: int, name: str, relevance: float = 1.0) -> None:
        """Add an active domain."""
        self._domains[nid] = ResourceReference(
            resource_type="domain",
            nid=nid,
            name=name,
            relevance=relevance,
        )
    
    def add_idea(self, nid: int, name: str, relevance: float = 1.0) -> None:
        """Add an active idea."""
        self._ideas[nid] = ResourceReference(
            resource_type="idea",
            nid=nid,
            name=name,
            relevance=relevance,
        )
    
    def add_project(self, nid: int, name: str, relevance: float = 1.0) -> None:
        """Add an active project."""
        self._projects[nid] = ResourceReference(
            resource_type="project",
            nid=nid,
            name=name,
            relevance=relevance,
        )
    
    def add_contact(self, nid: int, name: str, relevance: float = 1.0) -> None:
        """Add an active contact."""
        self._contacts[nid] = ResourceReference(
            resource_type="contact",
            nid=nid,
            name=name,
            relevance=relevance,
        )
    
    def add_kg_ref(self, ref_id: str, ref_data: Any) -> None:
        """Add a knowledge graph reference."""
        self._kg_refs[ref_id] = ref_data
    
    def set_agent_state(self, agent_id: str, state: str) -> None:
        """Set an agent's current state."""
        self._agent_states[agent_id] = state
    
    def get_all_resources(self) -> dict[str, list[ResourceReference]]:
        """Get all active resources by type."""
        return {
            "domains": list(self._domains.values()),
            "ideas": list(self._ideas.values()),
            "projects": list(self._projects.values()),
            "contacts": list(self._contacts.values()),
        }
    
    def get_most_relevant(self, resource_type: str, n: int = 3) -> list[ResourceReference]:
        """Get the n most relevant resources of a type."""
        resources = {
            "domain": self._domains,
            "idea": self._ideas,
            "project": self._projects,
            "contact": self._contacts,
        }.get(resource_type, {})
        
        sorted_refs = sorted(resources.values(), key=lambda r: -r.relevance)
        return sorted_refs[:n]


# =============================================================================
# SKILL EXECUTOR (Steps 102-110)
# =============================================================================

class SkillExecutor:
    """
    Executes skills with context awareness.
    
    Manages context propagation, entelexis tracking, and resource management.
    """
    
    def __init__(
        self,
        registry: SkillRegistry | None = None,
    ):
        self.registry = registry or SKILL_REGISTRY
        self.propagator = ContextPropagator()
        self.entelexis = EntelexisTracker()
        self.resources = ResourceTracker()
        self._execution_history: list[SkillResult] = []
    
    def execute(
        self,
        skill_name: str,
        context: dict[str, Any],
        **kwargs,
    ) -> SkillResult:
        """
        Execute a skill with the given context.
        
        Args:
            skill_name: Name of the skill to execute
            context: Current context dict
            **kwargs: Additional arguments for the skill
        
        Returns:
            SkillResult with output and context updates
        """
        skill = self.registry.get(skill_name)
        if skill is None:
            return SkillResult(
                skill_name=skill_name,
                status=SkillStatus.FAILED,
                error=f"Skill not found: {skill_name}",
            )
        
        handler = self.registry.get_handler(skill_name)
        if handler is None:
            return SkillResult(
                skill_name=skill_name,
                status=SkillStatus.FAILED,
                error=f"No handler for skill: {skill_name}",
            )
        
        # Check required context fields
        for field_name in skill.required_context_fields:
            if field_name not in context:
                return SkillResult(
                    skill_name=skill_name,
                    status=SkillStatus.FAILED,
                    error=f"Missing required context field: {field_name}",
                )
        
        # Execute
        start_time = datetime.utcnow()
        try:
            output = handler(context=context, **kwargs)
            end_time = datetime.utcnow()
            
            result = SkillResult(
                skill_name=skill_name,
                status=SkillStatus.SUCCESS,
                output=output,
                started_at=start_time,
                completed_at=end_time,
                execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            result = SkillResult(
                skill_name=skill_name,
                status=SkillStatus.FAILED,
                error=str(e),
                started_at=start_time,
                completed_at=end_time,
                execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            )
        
        self._execution_history.append(result)
        return result
    
    def chain(
        self,
        skill_names: list[str],
        initial_context: dict[str, Any],
        **kwargs,
    ) -> list[SkillResult]:
        """
        Execute a chain of skills, passing context through.
        
        Each skill receives the updated context from the previous skill.
        """
        results = []
        context = initial_context.copy()
        
        for skill_name in skill_names:
            result = self.execute(skill_name, context, **kwargs)
            results.append(result)
            
            # Stop chain on failure
            if not result.is_success():
                break
            
            # Update context for next skill
            if result.context_updates:
                context = self.propagator.apply_updates(context)
        
        return results
    
    def get_history(self, n: int | None = None) -> list[SkillResult]:
        """Get execution history, optionally limited to last n entries."""
        if n is None:
            return self._execution_history
        return self._execution_history[-n:]


# =============================================================================
# SKILL DECORATOR
# =============================================================================

def skill(
    name: str,
    description: str,
    category: str = "general",
    required_context: list[str] | None = None,
    optional_context: list[str] | None = None,
) -> Callable:
    """
    Decorator to register a function as a skill.
    
    Usage:
        @skill("extract_claims", "Extract claims from text", "extraction")
        def extract_claims(context: dict, text: str) -> list[str]:
            ...
    """
    def decorator(func: Callable) -> Callable:
        skill_def = SkillDefinition(
            name=name,
            description=description,
            category=category,
            required_context_fields=required_context or [],
            optional_context_fields=optional_context or [],
            handler=func,
        )
        SKILL_REGISTRY.register(skill_def, func)
        return func
    return decorator


# =============================================================================
# BUILT-IN SKILLS
# =============================================================================

@skill("echo", "Echo the input", "utility")
def echo_skill(context: dict[str, Any], message: str) -> str:
    """Simple echo skill for testing."""
    return f"Echo: {message}"


@skill("context_dump", "Dump current context", "utility")
def context_dump_skill(context: dict[str, Any]) -> dict[str, Any]:
    """Dump the current context for debugging."""
    return {
        "context_keys": list(context.keys()),
        "context_size": len(str(context)),
    }


@skill(
    "extract_intent",
    "Extract user intent from prompt",
    "interpretation",
    required_context=["prompt"],
)
def extract_intent_skill(context: dict[str, Any]) -> dict[str, Any]:
    """Extract intent from a prompt."""
    prompt = context.get("prompt", "")
    
    # Simple intent detection
    intent = "query"
    if any(word in prompt.lower() for word in ["create", "make", "build", "generate"]):
        intent = "create"
    elif any(word in prompt.lower() for word in ["explain", "describe", "what is"]):
        intent = "explain"
    elif any(word in prompt.lower() for word in ["fix", "debug", "solve", "resolve"]):
        intent = "fix"
    elif any(word in prompt.lower() for word in ["compare", "difference", "vs"]):
        intent = "compare"
    
    return {
        "intent": intent,
        "prompt": prompt,
        "confidence": 0.7,
    }
