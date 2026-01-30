"""
REAL tests for analyze/claims.py (now that spaCy is installed)
"""
import pytest
from inception.analyze.claims import ClaimExtractor, Claim, ClaimExtractionResult


class TestClaim:
    def test_creation(self):
        claim = Claim(
            text="The Earth is round",
            subject="Earth",
            predicate="is",
            object="round",
            confidence=0.9,
        )
        assert claim.text == "The Earth is round"
        assert claim.subject == "Earth"


class TestClaimExtractionResult:
    def test_creation(self):
        result = ClaimExtractionResult(claims=[])
        assert result.claims == []


class TestClaimExtractor:
    def test_creation(self):
        extractor = ClaimExtractor()
        assert extractor is not None
    
    def test_extract_simple(self):
        extractor = ClaimExtractor()
        result = extractor.extract("Water boils at 100 degrees Celsius.")
        assert isinstance(result, ClaimExtractionResult)
    
    def test_extract_multiple(self):
        extractor = ClaimExtractor()
        text = "The sun is a star. The moon orbits Earth. Mars is red."
        result = extractor.extract(text)
        assert isinstance(result, ClaimExtractionResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
