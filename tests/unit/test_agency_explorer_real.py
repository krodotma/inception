"""Tests for enhance/agency/explorer/* modules"""
import pytest

try:
    from inception.enhance.agency.explorer.resolver import GapResolver
    HAS_RESOLVER = True
except ImportError:
    HAS_RESOLVER = False

try:
    from inception.enhance.agency.validator.sources import SourceValidator
    HAS_VALIDATOR = True
except ImportError:
    HAS_VALIDATOR = False


@pytest.mark.skipif(not HAS_RESOLVER, reason="GapResolver not available")
class TestGapResolver:
    def test_creation(self):
        resolver = GapResolver()
        assert resolver is not None


@pytest.mark.skipif(not HAS_VALIDATOR, reason="SourceValidator not available")
class TestSourceValidator:
    def test_creation(self):
        validator = SourceValidator()
        assert validator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
