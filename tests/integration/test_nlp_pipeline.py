"""
Integration tests for spaCy NLP pipeline.
Tests entity extraction, claim analysis, and procedure detection.
"""
import pytest

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        HAS_SPACY = True
    except OSError:
        HAS_SPACY = False
except ImportError:
    HAS_SPACY = False

try:
    from inception.analyze.entities import EntityExtractor, Entity
    HAS_ENTITIES = True
except ImportError:
    HAS_ENTITIES = False

try:
    from inception.analyze.claims import ClaimExtractor, Claim
    HAS_CLAIMS = True
except ImportError:
    HAS_CLAIMS = False

try:
    from inception.analyze.procedures import ProcedureExtractor, Procedure
    HAS_PROCEDURES = True
except ImportError:
    HAS_PROCEDURES = False


@pytest.mark.skipif(not HAS_SPACY, reason="spaCy not available")
class TestSpacyIntegration:
    """Test spaCy model loading and basic NLP."""
    
    def test_spacy_load_model(self):
        """Verify en_core_web_sm model loads."""
        nlp = spacy.load("en_core_web_sm")
        assert nlp is not None
    
    def test_spacy_tokenize(self):
        """Test tokenization."""
        nlp = spacy.load("en_core_web_sm")
        doc = nlp("Hello world, this is a test.")
        assert len(list(doc)) > 0
    
    def test_spacy_ner(self):
        """Test named entity recognition."""
        nlp = spacy.load("en_core_web_sm")
        doc = nlp("Apple Inc. was founded by Steve Jobs in California.")
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        assert len(entities) > 0
    
    def test_spacy_pos_tagging(self):
        """Test POS tagging."""
        nlp = spacy.load("en_core_web_sm")
        doc = nlp("The quick brown fox jumps over the lazy dog.")
        pos_tags = [(token.text, token.pos_) for token in doc]
        assert len(pos_tags) > 0


@pytest.mark.skipif(not HAS_ENTITIES or not HAS_SPACY, reason="EntityExtractor or spaCy not available")
class TestEntityExtractorIntegration:
    """Test EntityExtractor with real spaCy."""
    
    def test_extractor_creation(self):
        """Create entity extractor."""
        extractor = EntityExtractor()
        assert extractor is not None
    
    def test_extract_entities(self):
        """Extract entities from text."""
        extractor = EntityExtractor()
        result = extractor.extract("Apple Inc. is located in Cupertino, California.")
        assert result is not None


@pytest.mark.skipif(not HAS_CLAIMS or not HAS_SPACY, reason="ClaimExtractor or spaCy not available")
class TestClaimExtractorIntegration:
    """Test ClaimExtractor with real spaCy."""
    
    def test_extractor_creation(self):
        """Create claim extractor."""
        extractor = ClaimExtractor()
        assert extractor is not None
    
    def test_extract_claims(self):
        """Extract claims from text."""
        extractor = ClaimExtractor()
        result = extractor.extract("The Earth revolves around the Sun once per year.")
        assert result is not None


@pytest.mark.skipif(not HAS_PROCEDURES or not HAS_SPACY, reason="ProcedureExtractor or spaCy not available")
class TestProcedureExtractorIntegration:
    """Test ProcedureExtractor with real spaCy."""
    
    def test_extractor_creation(self):
        """Create procedure extractor."""
        extractor = ProcedureExtractor()
        assert extractor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
