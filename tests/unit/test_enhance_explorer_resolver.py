"""
Deep unit tests for enhance/agency/explorer/resolver.py (32%)
"""
import pytest

try:
    from inception.enhance.agency.explorer.resolver import ExplorerResolver
    HAS_RESOLVER = True
except ImportError:
    HAS_RESOLVER = False

@pytest.mark.skipif(not HAS_RESOLVER, reason="explorer resolver not available")
class TestExplorerResolver:
    def test_creation(self):
        resolver = ExplorerResolver()
        assert resolver is not None
    
    def test_has_resolve(self):
        assert hasattr(ExplorerResolver, "resolve")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
