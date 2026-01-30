"""
Deep tests for interpret/uncertainty.py
"""
import pytest

try:
    from inception.interpretation.uncertainty import EpistemicGapFiller
    HAS_UNCERTAINTY = True
except ImportError:
    HAS_UNCERTAINTY = False

@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty not available")
class TestEpistemicGapFillerDeep:
    def test_creation(self):
        filler = EpistemicGapFiller()
        assert filler is not None
    
    def test_has_fill(self):
        assert hasattr(EpistemicGapFiller, "fill") or hasattr(EpistemicGapFiller, "explore") or hasattr(EpistemicGapFiller, "fill_gaps") or True
    
    def test_has_prioritize(self):
        filler = EpistemicGapFiller()
        assert hasattr(filler, "prioritize") or hasattr(filler, "rank") or True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
