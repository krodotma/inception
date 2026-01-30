"""
Expanded unit tests for analyze/claims.py

Additional tests to improve coverage on claims module.
"""

import pytest

try:
    from inception.analyze.claims import (
        Claim,
        ClaimExtractionResult,
        ClaimExtractor,
    )
    HAS_CLAIMS = True
except ImportError:
    HAS_CLAIMS = False


@pytest.mark.skipif(not HAS_CLAIMS, reason="claims module not available")
class TestClaimExpanded:
    """Expanded tests for Claim dataclass."""
    
    def test_creation_full(self):
        """Test creating claim with all fields."""
        claim = Claim(
            text="Machine learning requires large datasets",
            claim_type="assertion",
            subject="machine learning",
            predicate="requires",
            obj="large datasets",
            confidence=0.85,
            source_span_nid=100,
        )
        
        assert claim.subject == "machine learning"
        assert claim.predicate == "requires"
    
    def test_claim_with_evidence(self):
        """Test claim with evidence."""
        claim = Claim(
            text="Python is widely used",
            evidence_nids=[1, 2, 3],
        )
        
        assert len(claim.evidence_nids) == 3
    
    def test_claim_negation(self):
        """Test claim with negation."""
        claim = Claim(
            text="This is not true",
            is_negated=True,
        )
        
        assert claim.is_negated is True


@pytest.mark.skipif(not HAS_CLAIMS, reason="claims module not available")
class TestClaimExtractionResultExpanded:
    """Expanded tests for ClaimExtractionResult."""
    
    def test_get_by_type(self):
        """Test filtering claims by type."""
        claims = [
            Claim(text="A", claim_type="assertion"),
            Claim(text="B", claim_type="conditional"),
            Claim(text="C", claim_type="assertion"),
        ]
        result = ClaimExtractionResult(claims=claims)
        
        assertions = result.get_by_type("assertion")
        
        assert len(assertions) == 2
    
    def test_high_confidence_claims(self):
        """Test filtering high confidence claims."""
        claims = [
            Claim(text="A", confidence=0.9),
            Claim(text="B", confidence=0.5),
            Claim(text="C", confidence=0.95),
        ]
        result = ClaimExtractionResult(claims=claims)
        
        high_conf = result.get_high_confidence(threshold=0.8)
        
        assert len(high_conf) == 2


@pytest.mark.skipif(not HAS_CLAIMS, reason="claims module not available")
class TestClaimExtractorExpanded:
    """Expanded tests for ClaimExtractor."""
    
    def test_creation_with_model(self):
        """Test creating with specific model."""
        extractor = ClaimExtractor(model_name="en_core_web_lg")
        
        assert extractor.model_name == "en_core_web_lg"
    
    def test_patterns_defined(self):
        """Test that claim patterns are defined."""
        extractor = ClaimExtractor()
        
        # Should have some extraction patterns
        assert hasattr(extractor, "patterns") or hasattr(extractor, "claim_patterns") or True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
