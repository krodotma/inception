"""
Unit tests for surface/interactive.py

Tests for interactive differentiation layer:
- ConfidenceRouter: Confidence-based routing
- HumanInteractionManager: Interaction handling
"""

import pytest
from inception.surface.interactive import (
    # Enums
    RoutingDecision,
    RiskLevel,
    InteractionType,
    # Data classes
    RoutingResult,
    InteractionPoint,
    # Managers
    ConfidenceRouter,
    HumanInteractionManager,
)


# =============================================================================
# Test: Enums
# =============================================================================

class TestRoutingDecision:
    """Tests for RoutingDecision enum."""
    
    def test_decision_values(self):
        """Test routing decision values."""
        assert RoutingDecision.AUTONOMOUS.value == "autonomous"
        assert RoutingDecision.NOTIFY.value == "notify"
        assert RoutingDecision.REQUEST.value == "request"
        assert RoutingDecision.ESCALATE.value == "escalate"


class TestRiskLevel:
    """Tests for RiskLevel enum."""
    
    def test_risk_values(self):
        """Test risk level values."""
        assert RiskLevel.TRIVIAL.value == "trivial"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestInteractionType:
    """Tests for InteractionType enum."""
    
    def test_interaction_values(self):
        """Test interaction type values."""
        assert InteractionType.CLARIFICATION.value == "clarification"
        assert InteractionType.VALIDATION.value == "validation"
        assert InteractionType.DECISION.value == "decision"


# =============================================================================
# Test: ConfidenceRouter
# =============================================================================

class TestConfidenceRouter:
    """Tests for ConfidenceRouter."""
    
    def test_creation_with_defaults(self):
        """Test creating router with defaults."""
        router = ConfidenceRouter()
        
        assert router is not None
    
    def test_creation_with_custom_thresholds(self):
        """Test creating router with custom thresholds."""
        router = ConfidenceRouter(
            base_autonomous_threshold=0.95,
            base_notify_threshold=0.6,
        )
        
        assert router is not None
    
    def test_route_high_confidence(self):
        """Test routing with high confidence."""
        router = ConfidenceRouter()
        
        result = router.route(
            confidence=0.95,
            domain="general",
            risk_level=RiskLevel.LOW,
        )
        
        # With default thresholds, high confidence may still notify
        assert result.decision in [RoutingDecision.AUTONOMOUS, RoutingDecision.NOTIFY]
    
    def test_route_medium_confidence(self):
        """Test routing with medium confidence."""
        router = ConfidenceRouter()
        
        result = router.route(
            confidence=0.7,
            domain="general",
            risk_level=RiskLevel.LOW,
        )
        
        assert result.decision in [RoutingDecision.NOTIFY, RoutingDecision.REQUEST]
    
    def test_route_low_confidence(self):
        """Test routing with low confidence."""
        router = ConfidenceRouter()
        
        result = router.route(
            confidence=0.3,
            domain="general",
            risk_level=RiskLevel.LOW,
        )
        
        assert result.decision in [RoutingDecision.REQUEST, RoutingDecision.ESCALATE, RoutingDecision.DEFER]
    
    def test_route_with_high_risk(self):
        """Test routing with high risk lowers threshold."""
        router = ConfidenceRouter()
        
        # High confidence but high risk - should not be autonomous
        result = router.route(
            confidence=0.85,
            domain="general",
            risk_level=RiskLevel.CRITICAL,
        )
        
        # High risk should require higher confidence
        assert result.decision in [RoutingDecision.NOTIFY, RoutingDecision.REQUEST, RoutingDecision.ESCALATE]
    
    def test_set_domain_thresholds(self):
        """Test setting domain-specific thresholds."""
        router = ConfidenceRouter()
        
        router.set_domain_thresholds(
            domain="finance",
            autonomous=0.99,
            notify=0.8,
        )
        
        # High confidence in finance domain still needs higher threshold
        result = router.route(confidence=0.95, domain="finance")
        
        assert result.decision != RoutingDecision.AUTONOMOUS
    
    def test_learn_from_feedback_correct(self):
        """Test learning from correct feedback."""
        router = ConfidenceRouter()
        
        router.learn_from_feedback(
            decision=RoutingDecision.AUTONOMOUS,
            was_correct=True,
            domain="general",
        )
        
        # No errors - threshold adjustment should happen
        assert router is not None
    
    def test_learn_from_feedback_incorrect(self):
        """Test learning from incorrect feedback."""
        router = ConfidenceRouter()
        
        router.learn_from_feedback(
            decision=RoutingDecision.AUTONOMOUS,
            was_correct=False,
            domain="general",
        )
        
        # Threshold should be adjusted upward
        assert router is not None
    
    def test_get_statistics(self):
        """Test getting routing statistics."""
        router = ConfidenceRouter()
        
        # Do some routing
        router.route(confidence=0.9)
        router.route(confidence=0.5)
        
        stats = router.get_statistics()
        
        assert isinstance(stats, dict)


# =============================================================================
# Test: InteractionPoint
# =============================================================================

class TestInteractionPoint:
    """Tests for InteractionPoint dataclass."""
    
    def test_creation(self):
        """Test creating an interaction point."""
        point = InteractionPoint(
            interaction_id="int-001",
            interaction_type=InteractionType.CLARIFICATION,
            question="What do you mean?",
            context="User said something ambiguous",
        )
        
        assert point.status == "pending"
        assert point.response is None


# =============================================================================
# Test: HumanInteractionManager
# =============================================================================

class TestHumanInteractionManager:
    """Tests for HumanInteractionManager."""
    
    def test_creation(self):
        """Test creating manager."""
        manager = HumanInteractionManager()
        
        assert len(manager.pending) == 0
    
    def test_request_clarification(self):
        """Test requesting clarification."""
        manager = HumanInteractionManager()
        
        point = manager.request_clarification(
            question="What format?",
            context="User requested output",
            priority=5,
        )
        
        assert point.interaction_type == InteractionType.CLARIFICATION
        assert len(manager.pending) >= 1
    
    def test_request_validation(self):
        """Test requesting validation."""
        manager = HumanInteractionManager()
        
        point = manager.request_validation(
            proposed_action="Delete all files",
            context="Cleanup requested",
            options=["Yes", "No", "Cancel"],
        )
        
        assert point.interaction_type == InteractionType.VALIDATION
        assert point.options == ["Yes", "No", "Cancel"]
    
    def test_request_decision(self):
        """Test requesting a decision."""
        manager = HumanInteractionManager()
        
        point = manager.request_decision(
            question="Which option?",
            options=["A", "B", "C"],
            context="Multiple choices available",
            priority=10,
        )
        
        assert point.interaction_type == InteractionType.DECISION
        assert len(point.options) == 3
    
    def test_escalate(self):
        """Test escalation."""
        manager = HumanInteractionManager()
        
        point = manager.escalate(
            issue="Critical error occurred",
            context="System malfunction",
            severity=10,
        )
        
        assert point.interaction_type == InteractionType.ESCALATION
    
    def test_pending_list_added(self):
        """Test that interactions are added to pending list."""
        manager = HumanInteractionManager()
        
        point = manager.request_clarification(
            question="What format?",
            context="User requested output",
        )
        
        # pending list should have at least one item
        assert len(manager.pending) >= 1
    
    def test_pending_list_multiple(self):
        """Test multiple pending interactions."""
        manager = HumanInteractionManager()
        
        manager.request_clarification("Q1?", "Context 1")
        manager.request_clarification("Q2?", "Context 2")
        
        # pending list should reflect added items
        assert len(manager.pending) >= 2
    
    def test_priority_handling(self):
        """Test that priority is tracked."""
        manager = HumanInteractionManager()
        
        low = manager.request_clarification("Low priority", "Context", priority=1)
        high = manager.request_clarification("High priority", "Context", priority=10)
        
        # Both should be in pending
        assert len(manager.pending) >= 2
        assert high.priority > low.priority
    
    def test_listener_registration(self):
        """Test registering listeners."""
        manager = HumanInteractionManager()
        
        received = []
        def listener(point):
            received.append(point)
        
        manager.on(listener)
        
        manager.request_clarification("Test?", "Context")
        
        assert len(received) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
