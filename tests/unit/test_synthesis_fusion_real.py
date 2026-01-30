"""Tests for enhance/synthesis/fusion/* modules"""
import pytest

try:
    from inception.enhance.synthesis.fusion.matcher import FusionMatcher
    HAS_MATCHER = True
except ImportError:
    HAS_MATCHER = False

try:
    from inception.enhance.synthesis.fusion.resolver import ConflictResolver
    HAS_RESOLVER = True
except ImportError:
    HAS_RESOLVER = False

try:
    from inception.enhance.synthesis.fusion.sources import SourceFusion
    HAS_SOURCES = True
except ImportError:
    HAS_SOURCES = False

try:
    from inception.enhance.synthesis.fusion.uncertainty import UncertaintyFusion
    HAS_UNCERTAINTY = True
except ImportError:
    HAS_UNCERTAINTY = False


@pytest.mark.skipif(not HAS_MATCHER, reason="FusionMatcher not available")
class TestFusionMatcher:
    def test_creation(self):
        matcher = FusionMatcher()
        assert matcher is not None


@pytest.mark.skipif(not HAS_RESOLVER, reason="ConflictResolver not available")
class TestConflictResolver:
    def test_creation(self):
        resolver = ConflictResolver()
        assert resolver is not None


@pytest.mark.skipif(not HAS_SOURCES, reason="SourceFusion not available")
class TestSourceFusion:
    def test_creation(self):
        fusion = SourceFusion()
        assert fusion is not None


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="UncertaintyFusion not available")
class TestUncertaintyFusion:
    def test_creation(self):
        fusion = UncertaintyFusion()
        assert fusion is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
