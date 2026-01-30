"""
ENTELECHEIA+ Verification & Safety Layer

Ensures invariant enforcement and safety bounds
for autonomous operation.

Invariant System:
- Pre/post conditions
- State invariants
- Temporal constraints

Safety Bounds:
- Action limits
- Resource constraints
- Rollback capabilities

Phase 9: Steps 271-290
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import re


# =============================================================================
# INVARIANT TYPES
# =============================================================================

class InvariantType(str, Enum):
    """Types of invariants."""
    
    PRECONDITION = "precondition"     # Must hold before action
    POSTCONDITION = "postcondition"   # Must hold after action
    STATE = "state"                   # Must always hold
    TEMPORAL = "temporal"             # Must hold over time
    RESOURCE = "resource"             # Resource constraints


class ViolationSeverity(str, Enum):
    """Severity of invariant violations."""
    
    WARNING = "warning"       # Log and continue
    ERROR = "error"           # Stop current action
    CRITICAL = "critical"     # Stop and rollback
    FATAL = "fatal"           # System shutdown


# =============================================================================
# INVARIANT DEFINITIONS (Steps 271-280)
# =============================================================================

@dataclass
class Invariant:
    """An invariant that must hold."""
    
    invariant_id: str
    name: str
    invariant_type: InvariantType
    
    # Check function
    check_fn: Callable[[dict[str, Any]], bool]
    description: str
    
    # Violation handling
    severity: ViolationSeverity = ViolationSeverity.ERROR
    auto_rollback: bool = False
    
    # Scope
    applies_to: str = "*"  # Pattern for matching actions
    
    # Statistics
    checks: int = 0
    violations: int = 0
    
    def check(self, context: dict[str, Any]) -> bool:
        """Check if the invariant holds."""
        self.checks += 1
        result = self.check_fn(context)
        if not result:
            self.violations += 1
        return result


@dataclass
class InvariantViolation:
    """Record of an invariant violation."""
    
    invariant_id: str
    invariant_name: str
    severity: ViolationSeverity
    
    # Context
    action: str
    context: dict[str, Any]
    
    # What went wrong
    message: str
    
    # Resolution
    auto_resolved: bool = False
    rollback_performed: bool = False
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


class InvariantSystem:
    """
    Manages and enforces invariants.
    """
    
    def __init__(self):
        self.invariants: dict[str, Invariant] = {}
        self.violations: list[InvariantViolation] = []
        
        # Initialize default invariants
        self._init_defaults()
    
    def _init_defaults(self) -> None:
        """Set up default invariants."""
        # Resource invariants
        self.add(Invariant(
            invariant_id="max_memory",
            name="Memory Limit",
            invariant_type=InvariantType.RESOURCE,
            check_fn=lambda ctx: ctx.get("memory_mb", 0) < 4096,
            description="Memory usage must stay under 4GB",
            severity=ViolationSeverity.WARNING,
        ))
        
        self.add(Invariant(
            invariant_id="max_actions_per_minute",
            name="Action Rate Limit",
            invariant_type=InvariantType.TEMPORAL,
            check_fn=lambda ctx: ctx.get("actions_per_minute", 0) < 100,
            description="No more than 100 actions per minute",
            severity=ViolationSeverity.ERROR,
        ))
        
        # State invariants
        self.add(Invariant(
            invariant_id="trace_count_limit",
            name="Trace Count Limit",
            invariant_type=InvariantType.STATE,
            check_fn=lambda ctx: ctx.get("trace_count", 0) < 100000,
            description="Stigmergic traces must not exceed 100,000",
            severity=ViolationSeverity.WARNING,
        ))
        
        # Preconditions
        self.add(Invariant(
            invariant_id="valid_input",
            name="Valid Input",
            invariant_type=InvariantType.PRECONDITION,
            check_fn=lambda ctx: ctx.get("input") is not None,
            description="Input must be provided",
            severity=ViolationSeverity.ERROR,
            applies_to="process_*",
        ))
    
    def add(self, invariant: Invariant) -> None:
        """Add an invariant."""
        self.invariants[invariant.invariant_id] = invariant
    
    def check_for_action(
        self,
        action: str,
        context: dict[str, Any],
        phase: str = "pre",  # "pre" or "post"
    ) -> list[InvariantViolation]:
        """
        Check all applicable invariants for an action.
        """
        violations = []
        
        for inv in self.invariants.values():
            # Check if invariant applies to this action
            if inv.applies_to != "*":
                if not re.match(inv.applies_to, action):
                    continue
            
            # Check phase match
            if phase == "pre" and inv.invariant_type == InvariantType.POSTCONDITION:
                continue
            if phase == "post" and inv.invariant_type == InvariantType.PRECONDITION:
                continue
            
            # Check invariant
            if not inv.check(context):
                violation = InvariantViolation(
                    invariant_id=inv.invariant_id,
                    invariant_name=inv.name,
                    severity=inv.severity,
                    action=action,
                    context=context.copy(),
                    message=f"Invariant '{inv.name}' violated: {inv.description}",
                )
                violations.append(violation)
                self.violations.append(violation)
        
        return violations
    
    def get_statistics(self) -> dict[str, Any]:
        """Get invariant statistics."""
        total_checks = sum(inv.checks for inv in self.invariants.values())
        total_violations = sum(inv.violations for inv in self.invariants.values())
        
        return {
            "invariant_count": len(self.invariants),
            "total_checks": total_checks,
            "total_violations": total_violations,
            "violation_rate": total_violations / max(1, total_checks),
            "recent_violations": len(self.violations[-10:]),
        }


# =============================================================================
# SAFETY BOUNDS (Steps 281-290)
# =============================================================================

@dataclass
class SafetyBound:
    """A safety boundary that limits system behavior."""
    
    bound_id: str
    name: str
    description: str
    
    # Limits
    metric: str
    max_value: float
    current_value: float = 0.0
    
    # Behavior on breach
    on_breach: str = "block"  # "block", "throttle", "warn"
    cooldown_seconds: float = 60.0
    
    # State
    breached: bool = False
    last_breach: datetime | None = None


@dataclass
class SafetyCheckpoint:
    """A checkpoint for potential rollback."""
    
    checkpoint_id: str
    timestamp: datetime
    state: dict[str, Any]
    description: str


class SafetyController:
    """
    Controls safety bounds and provides rollback capabilities.
    """
    
    def __init__(self):
        self.bounds: dict[str, SafetyBound] = {}
        self.checkpoints: list[SafetyCheckpoint] = []
        self.invariant_system = InvariantSystem()
        
        self._max_checkpoints = 100
        self._checkpoint_counter = 0
        
        # Initialize default bounds
        self._init_defaults()
    
    def _init_defaults(self) -> None:
        """Set up default safety bounds."""
        defaults = [
            SafetyBound(
                bound_id="file_writes_per_min",
                name="File Writes/Minute",
                description="Limit file write operations",
                metric="file_writes",
                max_value=50.0,
                on_breach="throttle",
            ),
            SafetyBound(
                bound_id="network_requests_per_min",
                name="Network Requests/Minute",
                description="Limit network requests",
                metric="network_requests",
                max_value=100.0,
                on_breach="block",
            ),
            SafetyBound(
                bound_id="autonomous_actions",
                name="Autonomous Actions",
                description="Limit consecutive autonomous actions",
                metric="autonomous_streak",
                max_value=10.0,
                on_breach="warn",
            ),
            SafetyBound(
                bound_id="error_rate",
                name="Error Rate",
                description="Limit error rate before pause",
                metric="errors_per_100",
                max_value=10.0,
                on_breach="block",
            ),
        ]
        
        for bound in defaults:
            self.bounds[bound.bound_id] = bound
    
    def check_bound(
        self,
        metric: str,
        value: float,
    ) -> tuple[bool, str | None]:
        """
        Check if a metric value is within bounds.
        
        Returns (is_safe, action_to_take).
        """
        for bound in self.bounds.values():
            if bound.metric == metric:
                bound.current_value = value
                
                if value >= bound.max_value:
                    bound.breached = True
                    bound.last_breach = datetime.utcnow()
                    return False, bound.on_breach
                else:
                    # Check cooldown
                    if bound.breached and bound.last_breach:
                        elapsed = (datetime.utcnow() - bound.last_breach).total_seconds()
                        if elapsed >= bound.cooldown_seconds:
                            bound.breached = False
                    
                    if bound.breached:
                        return False, bound.on_breach
        
        return True, None
    
    def create_checkpoint(
        self,
        state: dict[str, Any],
        description: str = "",
    ) -> SafetyCheckpoint:
        """
        Create a checkpoint for potential rollback.
        """
        self._checkpoint_counter += 1
        
        checkpoint = SafetyCheckpoint(
            checkpoint_id=f"checkpoint_{self._checkpoint_counter:05d}",
            timestamp=datetime.utcnow(),
            state=state.copy(),
            description=description,
        )
        
        self.checkpoints.append(checkpoint)
        
        # Limit checkpoint storage
        if len(self.checkpoints) > self._max_checkpoints:
            self.checkpoints = self.checkpoints[-self._max_checkpoints:]
        
        return checkpoint
    
    def rollback_to(
        self,
        checkpoint_id: str,
    ) -> dict[str, Any] | None:
        """
        Rollback to a specific checkpoint.
        
        Returns the state at that checkpoint.
        """
        for checkpoint in reversed(self.checkpoints):
            if checkpoint.checkpoint_id == checkpoint_id:
                return checkpoint.state
        return None
    
    def safe_execute(
        self,
        action: str,
        execute_fn: Callable[[], Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Safely execute an action with full safety checks.
        """
        result = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Pre-check invariants
        pre_violations = self.invariant_system.check_for_action(action, context, "pre")
        if pre_violations:
            critical = [v for v in pre_violations if v.severity in (ViolationSeverity.CRITICAL, ViolationSeverity.FATAL)]
            if critical:
                result["status"] = "blocked"
                result["reason"] = "precondition_violation"
                result["violations"] = [v.message for v in critical]
                return result
        
        # Create checkpoint
        checkpoint = self.create_checkpoint(context, f"Before: {action}")
        result["checkpoint_id"] = checkpoint.checkpoint_id
        
        # Execute
        try:
            output = execute_fn()
            result["status"] = "success"
            result["output"] = output
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            result["rollback_available"] = True
        
        # Post-check invariants
        post_context = {**context, "output": result.get("output")}
        post_violations = self.invariant_system.check_for_action(action, post_context, "post")
        if post_violations:
            result["post_violations"] = [v.message for v in post_violations]
        
        return result
    
    def get_safety_status(self) -> dict[str, Any]:
        """Get overall safety status."""
        breached = [b for b in self.bounds.values() if b.breached]
        
        return {
            "bounds_count": len(self.bounds),
            "breached_count": len(breached),
            "checkpoints_available": len(self.checkpoints),
            "invariant_stats": self.invariant_system.get_statistics(),
            "breached_bounds": [
                {"id": b.bound_id, "name": b.name}
                for b in breached
            ],
        }
