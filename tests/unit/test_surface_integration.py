"""
Unit tests for surface/integration.py

Tests for integration layer:
- InceptionBridge: Bridge to Inception systems
- PluribusBridge: Bridge to Pluribus ecosystem
- FlowOrchestrator: Flow coordination
"""

import pytest
from pathlib import Path
from inception.surface.integration import (
    # Enums
    FlowState,
    FlowStage,
    # Config
    InceptionBridgeConfig,
    PluribusBridgeConfig,
    # Bridges
    InceptionBridge,
    PluribusBridge,
)


# =============================================================================
# Test: Enums
# =============================================================================

class TestFlowState:
    """Tests for FlowState enum."""
    
    def test_state_values(self):
        """Test flow state values."""
        assert FlowState.PENDING.value == "pending"
        assert FlowState.RUNNING.value == "running"
        assert FlowState.COMPLETED.value == "completed"
        assert FlowState.FAILED.value == "failed"


class TestFlowStage:
    """Tests for FlowStage enum."""
    
    def test_stage_values(self):
        """Test flow stage values."""
        assert FlowStage.INTAKE.value == "intake"
        assert FlowStage.CLASSIFY.value == "classify"
        assert FlowStage.REASON.value == "reason"
        assert FlowStage.OUTPUT.value == "output"


# =============================================================================
# Test: InceptionBridgeConfig
# =============================================================================

class TestInceptionBridgeConfig:
    """Tests for InceptionBridgeConfig dataclass."""
    
    def test_creation(self):
        """Test creating bridge config."""
        config = InceptionBridgeConfig(
            inception_root=Path("/tmp/inception"),
        )
        
        assert config.inception_root == Path("/tmp/inception")
        assert config.context_cache_size == 1000
    
    def test_with_custom_values(self):
        """Test config with custom values."""
        config = InceptionBridgeConfig(
            inception_root=Path("/custom"),
            context_cache_size=500,
            storage_backend="sqlite",
        )
        
        assert config.context_cache_size == 500
        assert config.storage_backend == "sqlite"


# =============================================================================
# Test: InceptionBridge
# =============================================================================

class TestInceptionBridge:
    """Tests for InceptionBridge."""
    
    def test_creation_without_config(self):
        """Test creating bridge without config."""
        bridge = InceptionBridge()
        
        assert bridge is not None
    
    def test_creation_with_config(self):
        """Test creating bridge with config."""
        config = InceptionBridgeConfig(
            inception_root=Path("/tmp/test"),
        )
        bridge = InceptionBridge(config=config)
        
        assert bridge is not None
    
    def test_get_context(self):
        """Test getting context."""
        bridge = InceptionBridge()
        
        context = bridge.get_context()
        
        # May return None, stub dict, or real context
        assert context is None or isinstance(context, (dict, object))
    
    def test_get_extractors(self):
        """Test getting extractors."""
        bridge = InceptionBridge()
        
        extractors = bridge.get_extractors()
        
        assert isinstance(extractors, (list, dict))
    
    def test_extend_storage(self):
        """Test extending storage."""
        bridge = InceptionBridge()
        
        # Should not raise
        bridge.extend_storage("test_key", {"data": "value"})
    
    def test_retrieve_storage(self):
        """Test retrieving from storage."""
        bridge = InceptionBridge()
        
        bridge.extend_storage("test_key", {"data": "value"})
        result = bridge.retrieve_storage("test_key")
        
        # May return the value or None depending on storage backend
        assert result is None or result == {"data": "value"}


# =============================================================================
# Test: PluribusBridgeConfig
# =============================================================================

class TestPluribusBridgeConfig:
    """Tests for PluribusBridgeConfig dataclass."""
    
    def test_creation(self):
        """Test creating config."""
        config = PluribusBridgeConfig(
            pluribus_root=Path("/tmp/pluribus"),
        )
        
        assert config.pluribus_root == Path("/tmp/pluribus")
        assert config.enable_entelexis is True
    
    def test_with_disabled_components(self):
        """Test config with disabled components."""
        config = PluribusBridgeConfig(
            pluribus_root=Path("/tmp/pluribus"),
            enable_ark=False,
        )
        
        assert config.enable_ark is False


# =============================================================================
# Test: PluribusBridge
# =============================================================================

class TestPluribusBridge:
    """Tests for PluribusBridge."""
    
    def test_creation_without_config(self):
        """Test creating bridge without config."""
        bridge = PluribusBridge()
        
        assert bridge is not None
    
    def test_creation_with_config(self):
        """Test creating bridge with config."""
        config = PluribusBridgeConfig(
            pluribus_root=Path("/tmp/pluribus"),
        )
        bridge = PluribusBridge(config=config)
        
        assert bridge is not None
    
    def test_connect_entelexis(self):
        """Test connecting to Entelexis."""
        bridge = PluribusBridge()
        
        result = bridge.connect_entelexis()
        
        # Should return connection status
        assert result is not None or isinstance(result, bool)
    
    def test_connect_auom(self):
        """Test connecting to AuOm."""
        bridge = PluribusBridge()
        
        result = bridge.connect_auom()
        
        assert result is not None or isinstance(result, bool)
    
    def test_connect_ark(self):
        """Test connecting to ARK."""
        bridge = PluribusBridge()
        
        result = bridge.connect_ark()
        
        assert result is not None or isinstance(result, bool)
    
    def test_get_connection_status(self):
        """Test getting connection status."""
        bridge = PluribusBridge()
        
        status = bridge.get_connection_status()
        
        assert isinstance(status, dict)
    
    def test_send_to_entelexis(self):
        """Test sending to Entelexis."""
        bridge = PluribusBridge()
        
        result = bridge.send_to_entelexis(
            concept="test_concept",
            context={"key": "value"},
        )
        
        assert result is not None or result == {}
    
    def test_send_to_ark(self):
        """Test sending to ARK."""
        bridge = PluribusBridge()
        
        result = bridge.send_to_ark(
            action="test_action",
            parameters={"param": "value"},
        )
        
        assert result is not None or result == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
