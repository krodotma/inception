"""
Pluribus Integration Layer
Phase 7, Steps 166-180

Implements:
- Entelexis alignment contract (166)
- Goal registry (167)
- Skill → goal mapping (168)
- Gap → goal priority (169)
- AuOm loop contract (170-173)
- Sextet fusion (174-175)
- Message bus adapter (176-180)
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Optional, TypeVar, Generic
from abc import ABC, abstractmethod


# =============================================================================
# Step 166: Entelexis Alignment Contract
# =============================================================================

class EntelexisState(Enum):
    """States in the Entelexis purpose flow."""
    LATENT = "latent"         # Purpose not yet activated
    EMERGING = "emerging"     # Purpose becoming conscious
    FOCUSED = "focused"       # Clear purpose, active pursuit
    FLOWING = "flowing"       # Effortless purposeful action
    REFLECTIVE = "reflective" # Evaluating purpose fulfillment
    COMPLETE = "complete"     # Purpose achieved
    DORMANT = "dormant"       # Awaiting new purpose


@dataclass
class EntelexisAlignment:
    """
    Contract for aligning system outputs with purpose.
    
    Entelexis = "having one's end within" — the principle that 
    actions should be intrinsically purposeful, not merely instrumental.
    """
    
    state: EntelexisState = EntelexisState.LATENT
    current_purpose: Optional[str] = None
    purpose_confidence: float = 0.0
    
    # Goal tracking
    active_goals: list[str] = field(default_factory=list)
    completed_goals: list[str] = field(default_factory=list)
    
    # Skill → goal contribution
    skill_contributions: dict[str, list[str]] = field(default_factory=dict)
    
    # Alignment metrics
    purpose_alignment_score: float = 0.0
    coherence_score: float = 0.0
    
    def activate_purpose(self, purpose: str, confidence: float = 0.5) -> None:
        """Activate a new purpose."""
        self.current_purpose = purpose
        self.purpose_confidence = confidence
        self.state = EntelexisState.EMERGING
    
    def focus(self) -> None:
        """Transition to focused state."""
        if self.state == EntelexisState.EMERGING:
            self.state = EntelexisState.FOCUSED
    
    def flow(self) -> None:
        """Transition to flowing state."""
        if self.state == EntelexisState.FOCUSED:
            self.state = EntelexisState.FLOWING
    
    def reflect(self) -> None:
        """Transition to reflective state."""
        self.state = EntelexisState.REFLECTIVE
    
    def complete(self) -> None:
        """Mark purpose as complete."""
        self.state = EntelexisState.COMPLETE
        if self.current_purpose:
            self.completed_goals.append(self.current_purpose)
    
    def compute_alignment(self, action: str, intended_goal: str) -> float:
        """Compute how well an action aligns with intended goal."""
        # Simplified: would use semantic similarity
        if intended_goal in self.active_goals:
            return 0.8
        return 0.3
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "state": self.state.value,
            "current_purpose": self.current_purpose,
            "purpose_confidence": self.purpose_confidence,
            "active_goals": self.active_goals,
            "completed_goals": self.completed_goals,
            "purpose_alignment_score": self.purpose_alignment_score,
            "coherence_score": self.coherence_score,
        }


# =============================================================================
# Step 167: Goal Registry
# =============================================================================

@dataclass
class Goal:
    """A goal in the registry."""
    id: str
    name: str
    description: str
    priority: float = 0.5  # 0-1
    status: str = "active"  # active, completed, abandoned
    parent_id: Optional[str] = None
    child_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    
    # Progress tracking
    progress: float = 0.0
    dependencies: list[str] = field(default_factory=list)
    
    # Skill mapping
    contributing_skills: list[str] = field(default_factory=list)


class GoalRegistry:
    """
    Central registry for goals with hierarchy and dependencies.
    """
    
    def __init__(self):
        self.goals: dict[str, Goal] = {}
        self.root_goals: list[str] = []
    
    def register(self, goal: Goal) -> str:
        """Register a new goal."""
        self.goals[goal.id] = goal
        
        if goal.parent_id:
            parent = self.goals.get(goal.parent_id)
            if parent:
                parent.child_ids.append(goal.id)
        else:
            self.root_goals.append(goal.id)
        
        return goal.id
    
    def get(self, goal_id: str) -> Optional[Goal]:
        """Get a goal by ID."""
        return self.goals.get(goal_id)
    
    def update_progress(self, goal_id: str, progress: float) -> None:
        """Update goal progress."""
        goal = self.goals.get(goal_id)
        if goal:
            goal.progress = min(1.0, max(0.0, progress))
            if goal.progress >= 1.0:
                goal.status = "completed"
            
            # Propagate progress to parent
            if goal.parent_id:
                self._update_parent_progress(goal.parent_id)
    
    def _update_parent_progress(self, parent_id: str) -> None:
        """Update parent goal progress based on children."""
        parent = self.goals.get(parent_id)
        if parent and parent.child_ids:
            children = [self.goals[cid] for cid in parent.child_ids if cid in self.goals]
            if children:
                avg_progress = sum(c.progress for c in children) / len(children)
                parent.progress = avg_progress
    
    def get_active_goals(self) -> list[Goal]:
        """Get all active goals."""
        return [g for g in self.goals.values() if g.status == "active"]
    
    def get_goals_by_priority(self, min_priority: float = 0.5) -> list[Goal]:
        """Get goals above priority threshold, sorted by priority."""
        active = [g for g in self.goals.values() 
                  if g.status == "active" and g.priority >= min_priority]
        return sorted(active, key=lambda g: g.priority, reverse=True)
    
    def get_hierarchy(self) -> dict[str, Any]:
        """Get goal hierarchy tree."""
        def build_tree(goal_id: str) -> dict[str, Any]:
            goal = self.goals.get(goal_id)
            if not goal:
                return {}
            return {
                "id": goal.id,
                "name": goal.name,
                "progress": goal.progress,
                "status": goal.status,
                "children": [build_tree(cid) for cid in goal.child_ids],
            }
        
        return {"roots": [build_tree(rid) for rid in self.root_goals]}


# =============================================================================
# Step 168-169: Skill → Goal Mapping & Gap → Goal Priority
# =============================================================================

@dataclass
class SkillGoalMapping:
    """Mapping between skills and goals."""
    skill_id: str
    goal_id: str
    contribution_weight: float = 1.0
    estimated_impact: float = 0.5


@dataclass
class GapGoalPriority:
    """Priority mapping between knowledge gaps and goals."""
    gap_id: str
    goal_id: str
    urgency: float = 0.5
    impact_if_resolved: float = 0.5
    
    @property
    def priority_score(self) -> float:
        """Compute priority score."""
        return (self.urgency + self.impact_if_resolved) / 2


class SkillGoalMapper:
    """
    Maps skills to goals they help achieve.
    Maps gaps to goal priorities for research.
    """
    
    def __init__(self, goal_registry: GoalRegistry):
        self.goal_registry = goal_registry
        self.skill_mappings: dict[str, list[SkillGoalMapping]] = {}
        self.gap_priorities: dict[str, list[GapGoalPriority]] = {}
    
    def map_skill_to_goal(self, skill_id: str, goal_id: str, weight: float = 1.0) -> None:
        """Map a skill to a goal."""
        mapping = SkillGoalMapping(
            skill_id=skill_id,
            goal_id=goal_id,
            contribution_weight=weight,
        )
        
        if skill_id not in self.skill_mappings:
            self.skill_mappings[skill_id] = []
        self.skill_mappings[skill_id].append(mapping)
        
        # Update goal's contributing skills
        goal = self.goal_registry.get(goal_id)
        if goal and skill_id not in goal.contributing_skills:
            goal.contributing_skills.append(skill_id)
    
    def get_goals_for_skill(self, skill_id: str) -> list[Goal]:
        """Get goals that a skill contributes to."""
        mappings = self.skill_mappings.get(skill_id, [])
        return [
            self.goal_registry.get(m.goal_id)
            for m in mappings
            if self.goal_registry.get(m.goal_id)
        ]
    
    def map_gap_to_goal(self, gap_id: str, goal_id: str, urgency: float = 0.5, impact: float = 0.5) -> None:
        """Map a knowledge gap to a goal with priority."""
        priority = GapGoalPriority(
            gap_id=gap_id,
            goal_id=goal_id,
            urgency=urgency,
            impact_if_resolved=impact,
        )
        
        if gap_id not in self.gap_priorities:
            self.gap_priorities[gap_id] = []
        self.gap_priorities[gap_id].append(priority)
    
    def get_gap_priority(self, gap_id: str) -> float:
        """Get overall priority for resolving a gap."""
        priorities = self.gap_priorities.get(gap_id, [])
        if not priorities:
            return 0.0
        
        # Aggregate priorities across all affected goals
        return max(p.priority_score for p in priorities)
    
    def get_prioritized_gaps(self) -> list[tuple[str, float]]:
        """Get all gaps sorted by priority."""
        gap_scores = []
        for gap_id in self.gap_priorities:
            score = self.get_gap_priority(gap_id)
            gap_scores.append((gap_id, score))
        
        return sorted(gap_scores, key=lambda x: x[1], reverse=True)


# =============================================================================
# Step 170-173: AuOm Self-Improvement Loop
# =============================================================================

class AuOmLaw(Enum):
    """The 6 Laws of AuOm self-improvement."""
    OBSERVE = 1    # Observe current state
    ORIENT = 2     # Orient toward goals
    DECIDE = 3     # Decide on action
    ACT = 4        # Execute action
    EVALUATE = 5   # Evaluate outcome
    ADAPT = 6      # Adapt based on learning


@dataclass
class OODAState:
    """State of the OODA loop."""
    current_phase: AuOmLaw = AuOmLaw.OBSERVE
    observations: list[Any] = field(default_factory=list)
    orientations: list[Any] = field(default_factory=list)
    decisions: list[Any] = field(default_factory=list)
    actions: list[Any] = field(default_factory=list)
    evaluations: list[Any] = field(default_factory=list)
    adaptations: list[Any] = field(default_factory=list)
    
    # Metrics
    cycles_completed: int = 0
    success_rate: float = 0.0


class AuOmLoop:
    """
    AuOm self-improvement loop implementing OODA + Adaptation.
    
    The loop:
    1. Observe: Collect performance data
    2. Orient: Analyze against goals
    3. Decide: Choose improvement action
    4. Act: Execute improvement
    5. Evaluate: Measure impact
    6. Adapt: Update strategy
    """
    
    def __init__(self, goal_registry: GoalRegistry):
        self.goal_registry = goal_registry
        self.state = OODAState()
        self.goldens: list[dict[str, Any]] = []
        self.regressions: list[dict[str, Any]] = []
    
    def observe(self, data: Any) -> None:
        """Observe current state."""
        self.state.observations.append({
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.state.current_phase = AuOmLaw.ORIENT
    
    def orient(self, analysis: Any) -> None:
        """Orient toward goals."""
        self.state.orientations.append({
            "analysis": analysis,
            "active_goals": [g.name for g in self.goal_registry.get_active_goals()],
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.state.current_phase = AuOmLaw.DECIDE
    
    def decide(self, decision: Any) -> None:
        """Decide on action."""
        self.state.decisions.append({
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.state.current_phase = AuOmLaw.ACT
    
    def act(self, action: Any) -> None:
        """Execute action."""
        self.state.actions.append({
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.state.current_phase = AuOmLaw.EVALUATE
    
    def evaluate(self, result: Any, success: bool) -> None:
        """Evaluate outcome."""
        self.state.evaluations.append({
            "result": result,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Update success rate
        successes = sum(1 for e in self.state.evaluations if e.get("success"))
        self.state.success_rate = successes / len(self.state.evaluations)
        
        self.state.current_phase = AuOmLaw.ADAPT
    
    def adapt(self, adaptation: Any) -> None:
        """Adapt based on learning."""
        self.state.adaptations.append({
            "adaptation": adaptation,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        self.state.cycles_completed += 1
        self.state.current_phase = AuOmLaw.OBSERVE
    
    # -------------------------------------------------------------------------
    # Step 172: Golden Promotion Logic
    # -------------------------------------------------------------------------
    
    def promote_to_golden(self, test_case: dict[str, Any], reason: str) -> None:
        """Promote a successful test case to golden status."""
        golden = {
            "test_case": test_case,
            "promoted_at": datetime.utcnow().isoformat(),
            "reason": reason,
            "cycles_at_promotion": self.state.cycles_completed,
        }
        self.goldens.append(golden)
    
    def check_golden_promotion(self, test_case: dict[str, Any], score: float, threshold: float = 0.95) -> bool:
        """Check if a test case should be promoted to golden."""
        if score >= threshold:
            # Check stability (would use historical data in production)
            self.promote_to_golden(test_case, f"Score {score} >= {threshold}")
            return True
        return False
    
    # -------------------------------------------------------------------------
    # Step 173: Regression Detection
    # -------------------------------------------------------------------------
    
    def detect_regression(self, current_score: float, baseline_score: float, tolerance: float = 0.05) -> bool:
        """Detect if performance has regressed."""
        if current_score < baseline_score - tolerance:
            self.regressions.append({
                "current": current_score,
                "baseline": baseline_score,
                "delta": baseline_score - current_score,
                "detected_at": datetime.utcnow().isoformat(),
            })
            return True
        return False
    
    def get_regression_summary(self) -> dict[str, Any]:
        """Get summary of detected regressions."""
        return {
            "total_regressions": len(self.regressions),
            "recent": self.regressions[-5:] if self.regressions else [],
            "cycles_completed": self.state.cycles_completed,
            "success_rate": self.state.success_rate,
        }


# =============================================================================
# Step 174-175: Sextet Fusion
# =============================================================================

@dataclass
class SextetVector:
    """
    6-dimensional vector for multi-perspective fusion.
    
    Dimensions:
    1. Epistemic: Knowledge confidence
    2. Temporal: Validity/freshness
    3. Source: Provenance authority
    4. Semantic: Meaning coherence
    5. Pragmatic: Action relevance
    6. Ethical: Safety/alignment
    """
    
    epistemic: float = 0.5
    temporal: float = 0.5
    source: float = 0.5
    semantic: float = 0.5
    pragmatic: float = 0.5
    ethical: float = 0.5
    
    def to_tuple(self) -> tuple[float, ...]:
        """Convert to tuple."""
        return (self.epistemic, self.temporal, self.source, 
                self.semantic, self.pragmatic, self.ethical)
    
    def magnitude(self) -> float:
        """Compute vector magnitude."""
        import math
        return math.sqrt(sum(v**2 for v in self.to_tuple()))
    
    def weighted_average(self, weights: tuple[float, ...] = None) -> float:
        """Compute weighted average of dimensions."""
        values = self.to_tuple()
        if weights is None:
            weights = (1.0,) * 6
        
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    @classmethod
    def fuse(cls, vectors: list[SextetVector], weights: list[float] = None) -> SextetVector:
        """Fuse multiple sextet vectors."""
        if not vectors:
            return cls()
        
        if weights is None:
            weights = [1.0] * len(vectors)
        
        total_weight = sum(weights)
        
        return cls(
            epistemic=sum(v.epistemic * w for v, w in zip(vectors, weights)) / total_weight,
            temporal=sum(v.temporal * w for v, w in zip(vectors, weights)) / total_weight,
            source=sum(v.source * w for v, w in zip(vectors, weights)) / total_weight,
            semantic=sum(v.semantic * w for v, w in zip(vectors, weights)) / total_weight,
            pragmatic=sum(v.pragmatic * w for v, w in zip(vectors, weights)) / total_weight,
            ethical=sum(v.ethical * w for v, w in zip(vectors, weights)) / total_weight,
        )


class SextetFusion:
    """
    Multi-dimensional fusion engine using 6D vectors.
    """
    
    def __init__(self):
        self.vectors: dict[str, SextetVector] = {}
    
    def add_vector(self, entity_id: str, vector: SextetVector) -> None:
        """Add a vector for an entity."""
        self.vectors[entity_id] = vector
    
    def fuse_entities(self, entity_ids: list[str]) -> SextetVector:
        """Fuse vectors from multiple entities."""
        vectors = [self.vectors[eid] for eid in entity_ids if eid in self.vectors]
        return SextetVector.fuse(vectors)
    
    def rank_by_dimension(self, dimension: str, descending: bool = True) -> list[tuple[str, float]]:
        """Rank entities by a specific dimension."""
        rankings = []
        for eid, vec in self.vectors.items():
            value = getattr(vec, dimension, 0.0)
            rankings.append((eid, value))
        
        return sorted(rankings, key=lambda x: x[1], reverse=descending)
    
    def filter_by_threshold(self, dimension: str, threshold: float) -> list[str]:
        """Filter entities by dimension threshold."""
        return [
            eid for eid, vec in self.vectors.items()
            if getattr(vec, dimension, 0.0) >= threshold
        ]


# =============================================================================
# Step 176-180: Message Bus Integration
# =============================================================================

class DimensionalEventType(Enum):
    """Types of dimensional events."""
    KNOWLEDGE_UPDATE = "knowledge_update"
    GOAL_PROGRESS = "goal_progress"
    SKILL_EXECUTED = "skill_executed"
    GAP_DETECTED = "gap_detected"
    REGRESSION = "regression"
    GOLDEN_PROMOTED = "golden_promoted"
    STATE_CHANGE = "state_change"
    HEALTH_STATUS = "health_status"


@dataclass
class DimensionalEvent:
    """
    Event structure for Pluribus message bus.
    """
    
    event_type: DimensionalEventType
    source: str  # Source system/agent
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # 6D context
    sextet: Optional[SextetVector] = None
    
    # Routing
    target: Optional[str] = None
    broadcast: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_type": self.event_type.value,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "sextet": self.sextet.to_tuple() if self.sextet else None,
            "target": self.target,
            "broadcast": self.broadcast,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict())


class PluribusMessageBus:
    """
    Message bus adapter for Pluribus integration.
    """
    
    def __init__(self, bus_url: str = "ws://localhost:8080/bus"):
        self.bus_url = bus_url
        self.connected = False
        self.subscribers: dict[DimensionalEventType, list[Callable]] = {}
        self.event_queue: list[DimensionalEvent] = []
        self.health_status = {"status": "initializing", "last_heartbeat": None}
    
    async def connect(self) -> bool:
        """Connect to the message bus."""
        # Simulated connection (would use websockets in production)
        self.connected = True
        self.health_status["status"] = "connected"
        self.health_status["last_heartbeat"] = datetime.utcnow().isoformat()
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from the message bus."""
        self.connected = False
        self.health_status["status"] = "disconnected"
    
    # -------------------------------------------------------------------------
    # Step 177: Event Publishing
    # -------------------------------------------------------------------------
    
    async def publish(self, event: DimensionalEvent) -> bool:
        """Publish an event to the bus."""
        if not self.connected:
            self.event_queue.append(event)
            return False
        
        # In production: send via websocket
        # await self.websocket.send(event.to_json())
        
        # Notify local subscribers
        await self._dispatch_local(event)
        
        return True
    
    def publish_sync(self, event: DimensionalEvent) -> None:
        """Synchronous publish (queues for later)."""
        self.event_queue.append(event)
    
    # -------------------------------------------------------------------------
    # Step 178: Event Consumption
    # -------------------------------------------------------------------------
    
    def subscribe(self, event_type: DimensionalEventType, callback: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    async def _dispatch_local(self, event: DimensionalEvent) -> None:
        """Dispatch event to local subscribers."""
        callbacks = self.subscribers.get(event.event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error in subscriber: {e}")
    
    # -------------------------------------------------------------------------
    # Step 180: Health/Status Reporting
    # -------------------------------------------------------------------------
    
    async def report_health(self) -> dict[str, Any]:
        """Report current health status."""
        self.health_status["last_heartbeat"] = datetime.utcnow().isoformat()
        self.health_status["queued_events"] = len(self.event_queue)
        self.health_status["subscriber_count"] = sum(len(v) for v in self.subscribers.values())
        
        # Publish health event
        event = DimensionalEvent(
            event_type=DimensionalEventType.HEALTH_STATUS,
            source="inception",
            payload=self.health_status,
            broadcast=True,
        )
        
        await self.publish(event)
        
        return self.health_status
    
    async def flush_queue(self) -> int:
        """Flush queued events."""
        if not self.connected:
            return 0
        
        flushed = 0
        while self.event_queue:
            event = self.event_queue.pop(0)
            await self.publish(event)
            flushed += 1
        
        return flushed


# =============================================================================
# Step 179: Shared Type Definitions
# =============================================================================

# Exported types for cross-system use
__all__ = [
    # Entelexis
    "EntelexisState",
    "EntelexisAlignment",
    
    # Goals
    "Goal",
    "GoalRegistry",
    "SkillGoalMapping",
    "GapGoalPriority",
    "SkillGoalMapper",
    
    # AuOm
    "AuOmLaw",
    "OODAState",
    "AuOmLoop",
    
    # Sextet
    "SextetVector",
    "SextetFusion",
    
    # Message Bus
    "DimensionalEventType",
    "DimensionalEvent",
    "PluribusMessageBus",
]
