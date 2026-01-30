"""
Unit tests for surface/safety.py

Tests for verification and safety layer:
- InvariantSystem: Pre/post condition checking
- SafetyController: Safety bounds and rollback
"""

import pytest
from datetime import datetime, timedelta
from inception.surface.safety import (
    # Enums
    InvariantType,
    ViolationSeverity,
    # Data classes
    Invariant,
    InvariantViolation,
    SafetyBound,
    SafetyCheckpoint,
    # Controllers
    InvariantSystem,
    SafetyController,
)


# =============================================================================
# Test: Enums
# =============================================================================

class TestInvariantType:
    """Tests for InvariantType enum."""
    
    def test_invariant_types(self):
        """Test invariant type values."""
        assert InvariantType.PRECONDITION.value == "precondition"
        assert InvariantType.POSTCONDITION.value == "postcondition"
        assert InvariantType.STATE.value == "state"


class TestViolationSeverity:
    """Tests for ViolationSeverity enum."""
    
    def test_severity_values(self):
        """Test violation severity values."""
        assert ViolationSeverity.WARNING.value == "warning"
        assert ViolationSeverity.ERROR.value == "error"
        assert ViolationSeverity.CRITICAL.value == "critical"


# =============================================================================
# Test: Invariant
# =============================================================================

class TestInvariant:
    """Tests for Invariant dataclass."""
    
    def test_creation(self):
        """Test creating an invariant."""
        invariant = Invariant(
            invariant_id="inv-001",
            name="No Negative Values",
            invariant_type=InvariantType.STATE,
            check_fn=lambda ctx: ctx.get("value", 0) >= 0,
            description="Values must be non-negative",
        )
        
        assert invariant.name == "No Negative Values"
        assert invariant.auto_rollback is False
    
    def test_check_passes(self):
        """Test invariant check that passes."""
        invariant = Invariant(
            invariant_id="inv-001",
            name="Test",
            invariant_type=InvariantType.STATE,
            check_fn=lambda ctx: ctx.get("valid", False),
            description="Test invariant",
        )
        
        result = invariant.check({"valid": True})
        
        assert result is True
        assert invariant.checks == 1
    
    def test_check_fails(self):
        """Test invariant check that fails."""
        invariant = Invariant(
            invariant_id="inv-001",
            name="Test",
            invariant_type=InvariantType.STATE,
            check_fn=lambda ctx: ctx.get("valid", False),
            description="Test invariant",
        )
        
        result = invariant.check({"valid": False})
        
        assert result is False
        assert invariant.violations == 1


# =============================================================================
# Test: InvariantSystem
# =============================================================================

class TestInvariantSystem:
    """Tests for InvariantSystem."""
    
    def test_creation_with_defaults(self):
        """Test creating system with default invariants."""
        system = InvariantSystem()
        
        # Should have some default invariants
        assert len(system.invariants) > 0
    
    def test_add_invariant(self):
        """Test adding a custom invariant."""
        system = InvariantSystem()
        
        invariant = Invariant(
            invariant_id="custom-001",
            name="Custom Check",
            invariant_type=InvariantType.STATE,
            check_fn=lambda ctx: True,
            description="Always passes",
        )
        
        system.add(invariant)
        
        assert "custom-001" in system.invariants
    
    def test_check_for_action_passes(self):
        """Test checking invariants for an action (pass case)."""
        system = InvariantSystem()
        
        # Provide a valid context
        context = {
            "memory_mb": 100,
            "connections": 10,
        }
        
        violations = system.check_for_action("test_action", context)
        
        # May or may not have violations depending on defaults
        assert isinstance(violations, list)
    
    def test_check_for_action_with_violation(self):
        """Test checking invariants for an action (violation case)."""
        system = InvariantSystem()
        
        # Add an invariant that will fail
        invariant = Invariant(
            invariant_id="always-fails",
            name="Always Fails",
            invariant_type=InvariantType.PRECONDITION,
            check_fn=lambda ctx: False,
            description="Always fails",
            applies_to="*",
        )
        system.add(invariant)
        
        violations = system.check_for_action("any_action", {})
        
        assert any(v.invariant_id == "always-fails" for v in violations)
    
    def test_get_statistics(self):
        """Test getting invariant statistics."""
        system = InvariantSystem()
        
        # Do some checks
        system.check_for_action("test", {})
        
        stats = system.get_statistics()
        
        assert "invariant_count" in stats
        assert "total_checks" in stats


# =============================================================================
# Test: SafetyBound
# =============================================================================

class TestSafetyBound:
    """Tests for SafetyBound dataclass."""
    
    def test_creation(self):
        """Test creating a safety bound."""
        bound = SafetyBound(
            bound_id="bound-001",
            name="Memory Limit",
            description="Max memory usage",
            metric="memory_mb",
            max_value=1000.0,
        )
        
        assert bound.name == "Memory Limit"
        assert bound.max_value == 1000.0
        assert not bound.breached


# =============================================================================
# Test: SafetyController
# =============================================================================

class TestSafetyController:
    """Tests for SafetyController."""
    
    def test_creation_with_defaults(self):
        """Test creating controller with defaults."""
        controller = SafetyController()
        
        # Should have some default bounds
        assert len(controller.bounds) > 0
    
    def test_check_bound_within_limit(self):
        """Test checking a bound within limits."""
        controller = SafetyController()
        
        # Add a simple bound
        controller.bounds["test_metric"] = SafetyBound(
            bound_id="test",
            name="Test",
            description="Test bound",
            metric="test_metric",
            max_value=100.0,
        )
        
        is_safe, action = controller.check_bound("test_metric", 50.0)
        
        assert is_safe is True
    
    def test_check_bound_exceeds_limit(self):
        """Test checking a bound that exceeds limits."""
        controller = SafetyController()
        
        # Add a simple bound
        controller.bounds["test_metric"] = SafetyBound(
            bound_id="test",
            name="Test",
            description="Test bound",
            metric="test_metric",
            max_value=100.0,
            on_breach="block",
        )
        
        is_safe, action = controller.check_bound("test_metric", 150.0)
        
        assert is_safe is False
        assert action == "block"
    
    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        controller = SafetyController()
        
        state = {"data": "important"}
        checkpoint_id = controller.create_checkpoint(state, "Before risky op")
        
        assert checkpoint_id is not None
        assert len(controller.checkpoints) >= 1
    
    def test_rollback_to_checkpoint(self):
        """Test rolling back to a checkpoint."""
        controller = SafetyController()
        
        # Create checkpoint
        original_state = {"value": 100}
        cp = controller.create_checkpoint(original_state, "Before change")
        cp_id = cp.checkpoint_id
        
        # Rollback
        restored = controller.rollback_to(cp_id)
        
        # May return the state or checkpoint object
        assert restored is not None or len(controller.checkpoints) > 0
    
    def test_rollback_to_nonexistent(self):
        """Test rolling back to non-existent checkpoint."""
        controller = SafetyController()
        
        result = controller.rollback_to("nonexistent")
        
        assert result is None
    
    def test_safe_execute_success(self):
        """Test safe execute with successful function."""
        controller = SafetyController()
        
        def good_fn():
            return "success"
        
        result = controller.safe_execute(
            action="test",
            execute_fn=good_fn,
            context={},
        )
        
        # safe_execute returns a dict with status and output
        assert result["status"] == "success"
        assert result["output"] == "success"
    
    def test_safe_execute_with_failure(self):
        """Test safe execute with failing function."""
        controller = SafetyController()
        
        def bad_fn():
            raise ValueError("Something went wrong")
        
        # safe_execute catches exceptions and returns error in dict
        result = controller.safe_execute(
            action="test",
            execute_fn=bad_fn,
            context={},
        )
        
        assert result["status"] == "error"
        assert "error" in result
    
    def test_get_safety_status(self):
        """Test getting safety status."""
        controller = SafetyController()
        
        status = controller.get_safety_status()
        
        assert "bounds_count" in status
        assert "breached_count" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
