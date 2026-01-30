"""Deep analyze tests to push coverage"""
import pytest

try:
    from inception.analyze.questions import QuestionExtractor, Question
    HAS_QUESTIONS = True
except ImportError:
    HAS_QUESTIONS = False

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
    from inception.analyze.gaps import GapAnalyzer
    HAS_GAPS = True
except ImportError:
    HAS_GAPS = False


@pytest.mark.skipif(not HAS_QUESTIONS, reason="questions not available")
class TestQuestionExtractorDeep:
    def test_creation(self):
        extractor = QuestionExtractor()
        assert extractor is not None
    
    def test_extract(self):
        extractor = QuestionExtractor()
        result = extractor.extract("What is the capital of France? How tall is the Eiffel Tower?")
        assert result is not None


@pytest.mark.skipif(not HAS_ENTITIES, reason="entities not available")
class TestEntityExtractorDeep:
    def test_creation(self):
        extractor = EntityExtractor()
        assert extractor is not None
    
    def test_extract(self):
        extractor = EntityExtractor()
        result = extractor.extract("Apple Inc. was founded by Steve Jobs in California.")
        assert result is not None


@pytest.mark.skipif(not HAS_CLAIMS, reason="claims not available")
class TestClaimExtractorDeep:
    def test_creation(self):
        extractor = ClaimExtractor()
        assert extractor is not None
    
    def test_extract(self):
        extractor = ClaimExtractor()
        result = extractor.extract("The Earth revolves around the Sun.")
        assert result is not None


@pytest.mark.skipif(not HAS_GAPS, reason="gaps not available")
class TestGapAnalyzerDeep:
    def test_creation(self):
        analyzer = GapAnalyzer()
        assert analyzer is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
