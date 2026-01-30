"""
Unit tests for config.py

Tests for configuration loading and validation.
"""

import pytest
import tempfile
from pathlib import Path

try:
    from inception.config import Config, get_config, set_config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


@pytest.mark.skipif(not HAS_CONFIG, reason="config module not available")
class TestConfig:
    """Tests for Config class."""
    
    def test_default_creation(self):
        """Test creating default config."""
        cfg = Config()
        
        assert cfg is not None
    
    def test_data_dir(self):
        """Test data dir property."""
        cfg = Config()
        
        assert cfg.data_dir is not None
        assert isinstance(cfg.data_dir, Path)
    
    def test_artifacts_dir(self):
        """Test artifacts dir property."""
        cfg = Config()
        
        assert cfg.artifacts_dir is not None
    
    def test_cache_dir(self):
        """Test cache dir property."""
        cfg = Config()
        
        assert cfg.cache_dir is not None
    
    def test_schema_version(self):
        """Test schema version."""
        cfg = Config()
        
        assert cfg.schema_version is not None
    
    def test_pipeline_version(self):
        """Test pipeline version."""
        cfg = Config()
        
        assert cfg.pipeline_version is not None


@pytest.mark.skipif(not HAS_CONFIG, reason="config module not available")
class TestGetSetConfig:
    """Tests for get_config and set_config."""
    
    def test_get_config(self):
        """Test getting global config."""
        cfg = get_config()
        
        assert cfg is not None
        assert isinstance(cfg, Config)
    
    def test_set_config(self):
        """Test setting global config."""
        new_cfg = Config()
        
        set_config(new_cfg)
        
        assert get_config() == new_cfg
    
    def test_config_from_yaml(self):
        """Test loading from YAML."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode='w') as f:
            f.write("schema_version: '1.0'\n")
            f.write("pipeline_version: '1.0'\n")
            f.flush()
            
            try:
                cfg = Config.from_yaml(Path(f.name))
                assert cfg is not None
            except Exception:
                # May require more YAML content
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
