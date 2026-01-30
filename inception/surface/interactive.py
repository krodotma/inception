"""
ENTELECHEIA+ Interactive Differentiation Layer

Implements confidence-based routing between autonomous execution
and human interaction points.

Confidence-Based Routing:
- High confidence (≥0.9): Autonomous execution
- Medium confidence (0.5-0.9): Execute with notification
- Low confidence (<0.5): Request human input

Human Interaction Points:
- Clarification requests
- Validation checkpoints
- Decision escalation
- Feedback collection

Autonomy Boundaries:
- Learned thresholds
- Domain-specific limits
- Risk-based adjustment

Phase 6: Steps 181-210
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import math


# =============================================================================
# ROUTING MODES
# =============================================================================

class RoutingDecision(str, Enum):
    """Decision types for confidence-based routing."""
    
    AUTONOMOUS = "autonomous"       # Execute without human input
    NOTIFY = "notify"               # Execute and notify human
    REQUEST = "request"             # Request human input first
    ESCALATE = "escalate"           # Escalate to higher authority
    DEFER = "defer"                 # Defer execution


class RiskLevel(str, Enum):
    """Risk levels for actions."""
    
    TRIVIAL = "trivial"     # No risk
    LOW = "low"             # Easily reversible
    MEDIUM = "medium"       # May need cleanup
    HIGH = "high"           # Significant impact
    CRITICAL = "critical"   # Irreversible/dangerous


# =============================================================================
# CONFIDENCE ROUTER (Steps 181-190)
# =============================================================================

@dataclass
class RoutingResult:
    """Result of confidence-based routing decision."""
    
    decision: RoutingDecision
    confidence: float
    threshold_used: float
    risk_level: RiskLevel
    explanation: str
    
    # If request/escalate, what to ask
    question: str | None = None
    options: list[str] | None = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConfidenceRouter:
    """
    Routes actions based on confidence levels.
    
    Implements learned thresholds and risk-based adjustment.
    """
    
    def __init__(
        self,
        base_autonomous_threshold: float = 0.9,
        base_notify_threshold: float = 0.5,
    ):
        # Base thresholds (can be adjusted via learning)
        self.autonomous_threshold = base_autonomous_threshold
        self.notify_threshold = base_notify_threshold
        
        # Domain-specific thresholds
        self.domain_thresholds: dict[str, dict[str, float]] = {}
        
        # Risk adjustments
        self.risk_adjustments = {
            RiskLevel.TRIVIAL: 0.0,    # No adjustment
            RiskLevel.LOW: 0.05,       # Slightly higher threshold
            RiskLevel.MEDIUM: 0.15,    # Moderately higher
            RiskLevel.HIGH: 0.25,      # Significantly higher
            RiskLevel.CRITICAL: 0.40,  # Very conservative
        }
        
        # Learning state
        self._decision_history: list[dict[str, Any]] = []
        self._feedback_counts = {
            "autonomous_correct": 0,
            "autonomous_incorrect": 0,
            "should_have_auto": 0,  # Asked but could have auto
        }
    
    def route(
        self,
        confidence: float,
        domain: str = "general",
        risk_level: RiskLevel = RiskLevel.LOW,
        action_description: str = "",
    ) -> RoutingResult:
        """
        Route an action based on confidence and risk.
        """
        # Get domain-specific thresholds or use base
        thresholds = self.domain_thresholds.get(domain, {
            "autonomous": self.autonomous_threshold,
            "notify": self.notify_threshold,
        })
        
        auto_threshold = thresholds.get("autonomous", self.autonomous_threshold)
        notify_threshold = thresholds.get("notify", self.notify_threshold)
        
        # Apply risk adjustment
        adjustment = self.risk_adjustments.get(risk_level, 0.0)
        adjusted_auto_threshold = min(0.99, auto_threshold + adjustment)
        adjusted_notify_threshold = min(adjusted_auto_threshold, notify_threshold + adjustment * 0.5)
        
        # Make decision
        if confidence >= adjusted_auto_threshold:
            decision = RoutingDecision.AUTONOMOUS
            explanation = f"Confidence {confidence:.2f} ≥ threshold {adjusted_auto_threshold:.2f}"
        elif confidence >= adjusted_notify_threshold:
            decision = RoutingDecision.NOTIFY
            explanation = f"Confidence {confidence:.2f} ≥ notify threshold {adjusted_notify_threshold:.2f}"
        elif risk_level == RiskLevel.CRITICAL:
            decision = RoutingDecision.ESCALATE
            explanation = f"Critical risk level requires escalation"
        else:
            decision = RoutingDecision.REQUEST
            explanation = f"Confidence {confidence:.2f} < threshold {adjusted_notify_threshold:.2f}"
        
        result = RoutingResult(
            decision=decision,
            confidence=confidence,
            threshold_used=adjusted_auto_threshold,
            risk_level=risk_level,
            explanation=explanation,
        )
        
        # Store for learning
        self._decision_history.append({
            "confidence": confidence,
            "domain": domain,
            "risk_level": risk_level.value,
            "decision": decision.value,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return result
    
    def learn_from_feedback(
        self,
        decision: RoutingDecision,
        was_correct: bool,
        domain: str = "general",
    ) -> None:
        """
        Update thresholds based on feedback.
        """
        learning_rate = 0.01
        
        if decision == RoutingDecision.AUTONOMOUS:
            if was_correct:
                self._feedback_counts["autonomous_correct"] += 1
            else:
                self._feedback_counts["autonomous_incorrect"] += 1
                # Raise threshold if we were wrong to auto-execute
                if domain in self.domain_thresholds:
                    self.domain_thresholds[domain]["autonomous"] = min(
                        0.99,
                        self.domain_thresholds[domain]["autonomous"] + learning_rate
                    )
                else:
                    self.autonomous_threshold = min(
                        0.99,
                        self.autonomous_threshold + learning_rate
                    )
        
        elif decision in (RoutingDecision.REQUEST, RoutingDecision.NOTIFY):
            if not was_correct:  # We asked but should have auto-executed
                self._feedback_counts["should_have_auto"] += 1
                # Lower threshold slightly
                if domain in self.domain_thresholds:
                    self.domain_thresholds[domain]["autonomous"] = max(
                        0.5,
                        self.domain_thresholds[domain]["autonomous"] - learning_rate
                    )
                else:
                    self.autonomous_threshold = max(
                        0.5,
                        self.autonomous_threshold - learning_rate
                    )
    
    def set_domain_thresholds(
        self,
        domain: str,
        autonomous: float,
        notify: float,
    ) -> None:
        """Set domain-specific thresholds."""
        self.domain_thresholds[domain] = {
            "autonomous": autonomous,
            "notify": notify,
        }
    
    def get_statistics(self) -> dict[str, Any]:
        """Get routing statistics."""
        total_decisions = len(self._decision_history)
        
        decision_counts = {}
        for entry in self._decision_history:
            d = entry["decision"]
            decision_counts[d] = decision_counts.get(d, 0) + 1
        
        return {
            "total_decisions": total_decisions,
            "decision_distribution": decision_counts,
            "current_autonomous_threshold": self.autonomous_threshold,
            "current_notify_threshold": self.notify_threshold,
            "feedback_counts": self._feedback_counts,
            "domain_thresholds": self.domain_thresholds,
        }


# =============================================================================
# HUMAN INTERACTION POINTS (Steps 191-200)
# =============================================================================

class InteractionType(str, Enum):
    """Types of human interaction."""
    
    CLARIFICATION = "clarification"   # Need more info
    VALIDATION = "validation"         # Confirm correctness
    DECISION = "decision"             # Make a choice
    ESCALATION = "escalation"         # Authority needed
    FEEDBACK = "feedback"             # Post-action review


@dataclass
class InteractionPoint:
    """A point requiring human interaction."""
    
    interaction_id: str
    interaction_type: InteractionType
    
    # What we're asking
    question: str
    context: str
    
    # Options (if applicable)
    options: list[str] | None = None
    default_option: str | None = None
    
    # Priority/urgency
    priority: int = 0  # Higher = more urgent
    timeout_seconds: float | None = None
    
    # State
    status: str = "pending"  # pending, answered, timeout, cancelled
    response: Any = None
    responded_at: datetime | None = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)


class HumanInteractionManager:
    """
    Manages human interaction points.
    
    Collects questions, prioritizes them, and handles responses.
    """
    
    def __init__(self):
        self.pending: list[InteractionPoint] = []
        self.completed: list[InteractionPoint] = []
        
        self._counter = 0
        self._listeners: list[Callable[[InteractionPoint], None]] = []
    
    def request_clarification(
        self,
        question: str,
        context: str,
        priority: int = 0,
    ) -> InteractionPoint:
        """Request clarification from human."""
        self._counter += 1
        
        interaction = InteractionPoint(
            interaction_id=f"clarify_{self._counter}",
            interaction_type=InteractionType.CLARIFICATION,
            question=question,
            context=context,
            priority=priority,
        )
        
        self.pending.append(interaction)
        self._notify(interaction)
        
        return interaction
    
    def request_validation(
        self,
        proposed_action: str,
        context: str,
        options: list[str] | None = None,
    ) -> InteractionPoint:
        """Request validation for a proposed action."""
        self._counter += 1
        
        if options is None:
            options = ["approve", "reject", "modify"]
        
        interaction = InteractionPoint(
            interaction_id=f"validate_{self._counter}",
            interaction_type=InteractionType.VALIDATION,
            question=f"Validate: {proposed_action}",
            context=context,
            options=options,
            default_option="approve",
        )
        
        self.pending.append(interaction)
        self._notify(interaction)
        
        return interaction
    
    def request_decision(
        self,
        question: str,
        options: list[str],
        context: str,
        priority: int = 5,
    ) -> InteractionPoint:
        """Request a decision from human."""
        self._counter += 1
        
        interaction = InteractionPoint(
            interaction_id=f"decision_{self._counter}",
            interaction_type=InteractionType.DECISION,
            question=question,
            context=context,
            options=options,
            priority=priority,
        )
        
        self.pending.append(interaction)
        self._notify(interaction)
        
        return interaction
    
    def escalate(
        self,
        issue: str,
        context: str,
        severity: int = 10,
    ) -> InteractionPoint:
        """Escalate an issue to human authority."""
        self._counter += 1
        
        interaction = InteractionPoint(
            interaction_id=f"escalate_{self._counter}",
            interaction_type=InteractionType.ESCALATION,
            question=f"ESCALATION: {issue}",
            context=context,
            priority=severity,
            timeout_seconds=300.0,  # 5 minutes for escalations
        )
        
        self.pending.append(interaction)
        self._notify(interaction)
        
        return interaction
    
    def provide_response(
        self,
        interaction_id: str,
        response: Any,
    ) -> bool:
        """Provide a response to a pending interaction."""
        for i, interaction in enumerate(self.pending):
            if interaction.interaction_id == interaction_id:
                interaction.status = "answered"
                interaction.response = response
                interaction.responded_at = datetime.utcnow()
                
                # Move to completed
                self.completed.append(interaction)
                self.pending.pop(i)
                
                return True
        
        return False
    
    def get_pending_by_priority(self) -> list[InteractionPoint]:
        """Get pending interactions sorted by priority."""
        return sorted(self.pending, key=lambda x: -x.priority)
    
    def on(self, listener: Callable[[InteractionPoint], None]) -> None:
        """Register listener for new interactions."""
        self._listeners.append(listener)
    
    def _notify(self, interaction: InteractionPoint) -> None:
        """Notify listeners of new interaction."""
        for listener in self._listeners:
            try:
                listener(interaction)
            except Exception:
                pass


# =============================================================================
# AUTONOMY BOUNDARIES (Steps 201-210)
# =============================================================================

@dataclass
class AutonomyBoundary:
    """
    Defines a boundary for autonomous action.
    """
    
    boundary_id: str
    name: str
    description: str
    
    # Scope
    domain: str
    action_pattern: str  # Regex pattern for matching actions
    
    # Limits
    max_confidence_for_request: float  # Below this, always request
    min_confidence_for_auto: float     # Above this, can auto
    max_risk_level: RiskLevel          # Max risk we'll auto-execute
    
    # Behavior
    require_audit_trail: bool = True
    allow_batch_approval: bool = False
    
    # Learning
    is_learnable: bool = True
    adjustment_rate: float = 0.01


class AutonomyController:
    """
    Controls autonomous behavior within defined boundaries.
    
    Ensures the system operates within safe limits and
    learns appropriate autonomy levels over time.
    """
    
    def __init__(self):
        self.boundaries: dict[str, AutonomyBoundary] = {}
        self.router = ConfidenceRouter()
        self.interaction_manager = HumanInteractionManager()
        
        # Audit trail
        self._audit_log: list[dict[str, Any]] = []
        
        # Initialize default boundaries
        self._init_default_boundaries()
    
    def _init_default_boundaries(self) -> None:
        """Set up default autonomy boundaries."""
        defaults = [
            AutonomyBoundary(
                boundary_id="file_read",
                name="File Reading",
                description="Read files from disk",
                domain="filesystem",
                action_pattern=r"read_.*|view_.*|list_.*",
                max_confidence_for_request=0.3,
                min_confidence_for_auto=0.7,
                max_risk_level=RiskLevel.LOW,
            ),
            AutonomyBoundary(
                boundary_id="file_write",
                name="File Writing",
                description="Write/modify files",
                domain="filesystem",
                action_pattern=r"write_.*|create_.*|modify_.*",
                max_confidence_for_request=0.5,
                min_confidence_for_auto=0.9,
                max_risk_level=RiskLevel.MEDIUM,
            ),
            AutonomyBoundary(
                boundary_id="file_delete",
                name="File Deletion",
                description="Delete files",
                domain="filesystem",
                action_pattern=r"delete_.*|remove_.*",
                max_confidence_for_request=0.7,
                min_confidence_for_auto=0.95,
                max_risk_level=RiskLevel.HIGH,
            ),
            AutonomyBoundary(
                boundary_id="network",
                name="Network Operations",
                description="Network requests",
                domain="network",
                action_pattern=r"fetch_.*|request_.*|connect_.*",
                max_confidence_for_request=0.5,
                min_confidence_for_auto=0.85,
                max_risk_level=RiskLevel.MEDIUM,
            ),
        ]
        
        for boundary in defaults:
            self.boundaries[boundary.boundary_id] = boundary
    
    def check_action(
        self,
        action: str,
        confidence: float,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> RoutingResult:
        """
        Check if an action can proceed autonomously.
        """
        import re
        
        # Find matching boundary
        matching_boundary = None
        for boundary in self.boundaries.values():
            if re.match(boundary.action_pattern, action):
                matching_boundary = boundary
                break
        
        if matching_boundary:
            # Check risk level
            if risk_level.value > matching_boundary.max_risk_level.value:
                return RoutingResult(
                    decision=RoutingDecision.ESCALATE,
                    confidence=confidence,
                    threshold_used=1.0,
                    risk_level=risk_level,
                    explanation=f"Risk level {risk_level.value} exceeds boundary max {matching_boundary.max_risk_level.value}",
                )
            
            # Use boundary thresholds
            self.router.set_domain_thresholds(
                matching_boundary.domain,
                matching_boundary.min_confidence_for_auto,
                matching_boundary.max_confidence_for_request,
            )
        
        # Route through confidence router
        domain = matching_boundary.domain if matching_boundary else "general"
        result = self.router.route(confidence, domain, risk_level, action)
        
        # Audit
        if matching_boundary and matching_boundary.require_audit_trail:
            self._audit(action, result, matching_boundary)
        
        return result
    
    def _audit(
        self,
        action: str,
        result: RoutingResult,
        boundary: AutonomyBoundary,
    ) -> None:
        """Record action in audit log."""
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "boundary_id": boundary.boundary_id,
            "decision": result.decision.value,
            "confidence": result.confidence,
            "risk_level": result.risk_level.value,
        })
        
        # Keep log bounded
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-10000:]
    
    def add_boundary(self, boundary: AutonomyBoundary) -> None:
        """Add a custom boundary."""
        self.boundaries[boundary.boundary_id] = boundary
    
    def get_audit_log(
        self,
        limit: int = 100,
        action_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent audit log entries."""
        import re
        
        entries = self._audit_log[-limit:]
        
        if action_filter:
            entries = [
                e for e in entries
                if re.match(action_filter, e["action"])
            ]
        
        return entries
    
    def process_action(
        self,
        action: str,
        confidence: float,
        risk_level: RiskLevel,
        execute_fn: Callable[[], Any],
    ) -> dict[str, Any]:
        """
        Full action processing: check, route, and execute or interact.
        
        Returns result of action or interaction request.
        """
        # Check action
        routing = self.check_action(action, confidence, risk_level)
        
        result = {
            "action": action,
            "routing": routing.decision.value,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if routing.decision == RoutingDecision.AUTONOMOUS:
            # Execute directly
            try:
                output = execute_fn()
                result["status"] = "completed"
                result["output"] = output
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
        
        elif routing.decision == RoutingDecision.NOTIFY:
            # Execute and notify
            try:
                output = execute_fn()
                result["status"] = "completed_with_notification"
                result["output"] = output
                result["notification"] = f"Executed: {action}"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
        
        elif routing.decision == RoutingDecision.REQUEST:
            # Request human input
            interaction = self.interaction_manager.request_validation(
                proposed_action=action,
                context=f"Confidence: {confidence:.2f}, Risk: {risk_level.value}",
            )
            result["status"] = "awaiting_input"
            result["interaction_id"] = interaction.interaction_id
        
        elif routing.decision == RoutingDecision.ESCALATE:
            # Escalate
            interaction = self.interaction_manager.escalate(
                issue=action,
                context=routing.explanation,
            )
            result["status"] = "escalated"
            result["interaction_id"] = interaction.interaction_id
        
        else:
            result["status"] = "deferred"
        
        return result
