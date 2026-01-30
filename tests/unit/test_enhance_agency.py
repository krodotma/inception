"""
Unit tests for enhance/agency modules

Tests for agency executor and explorer.
"""

import pytest

try:
    from inception.enhance.agency.executor.parser import ActionParser
    from inception.enhance.agency.executor.runner import ActionRunner
    HAS_AGENCY_EXEC = True
except ImportError:
    HAS_AGENCY_EXEC = False

try:
    from inception.enhance.agency.explorer.classifier import GapClassifier
    HAS_AGENCY_EXPLORE = True
except ImportError:
    HAS_AGENCY_EXPLORE = False


@pytest.mark.skipif(not HAS_AGENCY_EXEC, reason="agency executor not available")
class TestActionParser:
    """Tests for ActionParser."""
    
    def test_creation(self):
        """Test creating parser."""
        parser = ActionParser()
        
        assert parser is not None
    
    def test_parse_simple(self):
        """Test parsing simple action."""
        parser = ActionParser()
        
        result = parser.parse("SEARCH: topic")
        
        assert result is not None


@pytest.mark.skipif(not HAS_AGENCY_EXEC, reason="agency executor not available")
class TestActionRunner:
    """Tests for ActionRunner."""
    
    def test_creation(self):
        """Test creating runner."""
        runner = ActionRunner()
        
        assert runner is not None


@pytest.mark.skipif(not HAS_AGENCY_EXPLORE, reason="agency explorer not available")
class TestGapClassifier:
    """Tests for GapClassifier."""
    
    def test_creation(self):
        """Test creating classifier."""
        classifier = GapClassifier()
        
        assert classifier is not None
    
    def test_classify(self):
        """Test classifying a gap."""
        classifier = GapClassifier()
        
        gap = {"description": "Missing information about topic"}
        payload = {"context": "test context"}
        result = classifier.classify(gap, payload)
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
