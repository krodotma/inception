"""
Unit tests for analyze/claims.py

Tests for claim extraction:
- Claim: Data class
- ClaimExtractionResult: Results
- ClaimExtractor: Main extractor
"""

import pytest

# These modules may have spacy dependency - handle gracefully
try:
    from inception.analyze.claims import (
        Claim,
        ClaimExtractionResult,
        ClaimExtractor,
        extract_claims,
        compute_claim_similarity,
        detect_contradiction,
        HEDGE_WORDS,
        NEGATION_MARKERS,
    )
    HAS_CLAIMS = True
except ImportError:
    HAS_CLAIMS = False


@pytest.mark.skipif(not HAS_CLAIMS, reason="claims module not available")
class TestClaim:
    """Tests for Claim dataclass."""
    
    def test_creation_minimal(self):
        """Test creating a minimal claim."""
        claim = Claim(text="The sky is blue")
        
        assert claim.text == "The sky is blue"
        assert claim.modality == "assertion"
    
    def test_creation_full(self):
        """Test creating a full claim."""
        claim = Claim(
            text="Dogs are mammals",
            subject="Dogs",
            predicate="are",
            object="mammals",
            modality="assertion",
            tense="present",
        )
        
        assert claim.subject == "Dogs"
        assert claim.predicate == "are"
        assert claim.object == "mammals"
    
    def test_spo_tuple(self):
        """Test SPO tuple."""
        claim = Claim(
            text="Dogs are mammals",
            subject="Dogs",
            predicate="are",
            object="mammals",
        )
        
        spo = claim.spo_tuple()
        
        assert spo == ("Dogs", "are", "mammals")
    
    def test_is_hedged_false(self):
        """Test non-hedged claim."""
        claim = Claim(text="X is Y", modality="assertion")
        
        assert claim.is_hedged() is False
    
    def test_is_hedged_true(self):
        """Test hedged claim."""
        claim = Claim(text="X might be Y", modality="possibility")
        
        assert claim.is_hedged() is True
    
    def test_kind(self):
        """Test claim kind."""
        claim = Claim(text="Test")
        
        kind = claim.kind()
        
        assert kind is not None


@pytest.mark.skipif(not HAS_CLAIMS, reason="claims module not available")
class TestClaimExtractionResult:
    """Tests for ClaimExtractionResult."""
    
    def test_creation(self):
        """Test creating result."""
        result = ClaimExtractionResult()
        
        assert result.claims == []
        assert result.claim_count == 0
    
    def test_avg_confidence_empty(self):
        """Test avg confidence with no claims."""
        result = ClaimExtractionResult()
        
        avg = result.avg_confidence()
        
        assert avg == 0.0
    
    def test_avg_confidence_with_claims(self):
        """Test avg confidence calculation."""
        from inception.db.records import Confidence
        
        claims = [
            Claim(text="A", confidence=Confidence(value=0.8)),
            Claim(text="B", confidence=Confidence(value=0.6)),
        ]
        result = ClaimExtractionResult(claims=claims, claim_count=2)
        
        avg = result.avg_confidence()
        
        assert 0.6 <= avg <= 0.8


@pytest.mark.skipif(not HAS_CLAIMS, reason="claims module not available")
class TestClaimExtractor:
    """Tests for ClaimExtractor."""
    
    def test_creation(self):
        """Test creating extractor."""
        extractor = ClaimExtractor()
        
        assert extractor is not None
    
    def test_creation_with_custom_params(self):
        """Test creating with custom params."""
        extractor = ClaimExtractor(min_claim_length=6)
        
        assert extractor.min_claim_length == 6


@pytest.mark.skipif(not HAS_CLAIMS, reason="claims module not available")
class TestClaimFunctions:
    """Tests for module-level functions."""
    
    def test_hedge_words_defined(self):
        """Test hedge words are defined."""
        assert "might" in HEDGE_WORDS
        assert "perhaps" in HEDGE_WORDS
    
    def test_negation_markers_defined(self):
        """Test negation markers are defined."""
        assert "not" in NEGATION_MARKERS
        assert "never" in NEGATION_MARKERS
    
    def test_compute_claim_similarity(self):
        """Test claim similarity computation."""
        c1 = Claim(text="Dogs are mammals")
        c2 = Claim(text="Cats are mammals")
        
        sim = compute_claim_similarity(c1, c2)
        
        assert 0 <= sim <= 1
    
    def test_detect_contradiction(self):
        """Test contradiction detection."""
        c1 = Claim(text="X is true", subject="X", predicate="is", object="true")
        c2 = Claim(text="X is false", subject="X", predicate="is", object="false")
        
        is_contra, conf = detect_contradiction(c1, c2)
        
        assert isinstance(is_contra, bool)
        assert 0 <= conf <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
