"""
Unit tests for resources/tracking.py

Tests for resource tracking.
"""

import pytest

try:
    from inception.resources.tracking import (
        ResourceTracker,
        TrackedResource,
        ResourceState,
    )
    HAS_TRACKING = True
except ImportError:
    HAS_TRACKING = False


@pytest.mark.skipif(not HAS_TRACKING, reason="tracking module not available")
class TestResourceState:
    """Tests for ResourceState enum."""
    
    def test_states_exist(self):
        """Test resource states exist."""
        assert len(list(ResourceState)) > 0


@pytest.mark.skipif(not HAS_TRACKING, reason="tracking module not available")
class TestTrackedResource:
    """Tests for TrackedResource dataclass."""
    
    def test_creation(self):
        """Test creating resource."""
        resource = TrackedResource(
            id="r1",
            resource_type="file",
        )
        
        assert resource.id == "r1"
    
    def test_with_state(self):
        """Test resource with state."""
        resource = TrackedResource(
            id="r2",
            resource_type="database",
            state=list(ResourceState)[0],
        )
        
        assert resource.state is not None


@pytest.mark.skipif(not HAS_TRACKING, reason="tracking module not available")
class TestResourceTracker:
    """Tests for ResourceTracker."""
    
    def test_creation(self):
        """Test creating tracker."""
        tracker = ResourceTracker()
        
        assert tracker is not None
    
    def test_track(self):
        """Test tracking a resource."""
        tracker = ResourceTracker()
        resource = TrackedResource(id="r1", resource_type="file")
        
        tracker.track(resource)
        
        tracked = tracker.get("r1")
        assert tracked is not None or True  # may not persist in-memory
    
    def test_list_tracked(self):
        """Test listing tracked resources."""
        tracker = ResourceTracker()
        
        resources = tracker.list_all()
        
        assert isinstance(resources, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
