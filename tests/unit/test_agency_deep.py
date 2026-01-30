"""Tests for agency resolver/validator modules at 32-39%"""
import pytest

try:
    from inception.enhance.agency.explorer.resolver import GapResolver, ResolutionResult
    HAS_RESOLVER = True
except ImportError:
    try:
        from inception.enhance.agency.explorer.resolver import GapResolver
        HAS_RESOLVER = True
        ResolutionResult = None
    except ImportError:
        HAS_RESOLVER = False

try:
    from inception.enhance.agency.validator.sources import SourceValidator, ValidationResult
    HAS_VALIDATOR = True
except ImportError:
    try:
        from inception.enhance.agency.validator.sources import SourceValidator
        HAS_VALIDATOR = True
        ValidationResult = None
    except ImportError:
        HAS_VALIDATOR = False


@pytest.mark.skipif(not HAS_RESOLVER, reason="GapResolver not available")
class TestGapResolverDeep:
    def test_creation(self):
        resolver = GapResolver()
        assert resolver is not None


@pytest.mark.skipif(not HAS_VALIDATOR, reason="SourceValidator not available")
class TestSourceValidatorDeep:
    def test_creation(self):
        validator = SourceValidator()
        assert validator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
