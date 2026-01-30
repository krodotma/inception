"""
Deep tests for enhance/agency/explorer/classifier.py (89%)
"""
import pytest

try:
    from inception.enhance.agency.explorer.classifier import GapClassifier
    HAS_CLASSIFIER = True
except ImportError:
    HAS_CLASSIFIER = False

@pytest.mark.skipif(not HAS_CLASSIFIER, reason="gap classifier not available")
class TestGapClassifierDeep:
    def test_creation(self):
        classifier = GapClassifier()
        assert classifier is not None
    
    def test_has_classify(self):
        assert hasattr(GapClassifier, "classify")
    
    def test_classify_gap(self):
        classifier = GapClassifier()
        gap = {"id": "g1", "description": "Missing info"}
        payload = {"context": "test"}
        result = classifier.classify(gap, payload)
        assert result is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
