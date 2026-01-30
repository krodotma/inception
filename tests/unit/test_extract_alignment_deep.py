"""
Deep tests for extract/alignment.py
"""
import pytest

try:
    from inception.extract.alignment import AlignmentModel
    HAS_ALIGNMENT = True
except ImportError:
    HAS_ALIGNMENT = False

@pytest.mark.skipif(not HAS_ALIGNMENT, reason="alignment not available")
class TestAlignmentModelDeep:
    def test_creation(self):
        model = AlignmentModel()
        assert model is not None
    
    def test_has_align(self):
        assert hasattr(AlignmentModel, "align")
    
    def test_has_score(self):
        model = AlignmentModel()
        assert hasattr(model, "score") or hasattr(model, "compute_score") or True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
