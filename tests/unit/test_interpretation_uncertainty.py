"""
Unit tests for interpretation/uncertainty.py

Tests for epistemic gap handling:
- EpistemicGapType, GapSeverity: Enums
- EpistemicGap: Gap dataclass
- KnowledgeSource: Source dataclass
- EpistemicGapFiller: Gap filler
"""

import pytest

try:
    from inception.interpretation.uncertainty import (
        EpistemicGapType,
        GapSeverity,
        EpistemicGap,
        SourceType,
        KnowledgeSource,
        EpistemicGapFiller,
        SocraticEscalation,
        EpistemicToSocraticBridge,
    )
    HAS_UNCERTAINTY = True
except ImportError:
    HAS_UNCERTAINTY = False


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty module not available")
class TestEpistemicGapType:
    """Tests for EpistemicGapType enum."""
    
    def test_values(self):
        """Test gap type values."""
        assert EpistemicGapType.MISSING_FACT.value == "missing_fact"
        assert EpistemicGapType.AMBIGUOUS_TERM.value == "ambiguous_term"
        assert EpistemicGapType.IMPLICIT_ASSUMPTION.value == "implicit"


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty module not available")
class TestGapSeverity:
    """Tests for GapSeverity enum."""
    
    def test_values(self):
        """Test severity values."""
        assert GapSeverity.MINOR.value == 1
        assert GapSeverity.CRITICAL.value == 4


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty module not available")
class TestEpistemicGap:
    """Tests for EpistemicGap dataclass."""
    
    def test_creation(self):
        """Test creating gap."""
        gap = EpistemicGap(
            id="gap-001",
            gap_type=EpistemicGapType.MISSING_FACT,
            description="Unknown publication date",
        )
        
        assert gap.id == "gap-001"
        assert gap.gap_type == EpistemicGapType.MISSING_FACT
    
    def test_fill(self):
        """Test filling a gap."""
        gap = EpistemicGap(
            id="gap-002",
            gap_type=EpistemicGapType.MISSING_FACT,
            description="Unknown author",
        )
        
        gap.fill("John Doe", "external source", 0.9)
        
        # Check filled_at is set (indicates fill happened)
        assert gap.filled_at is not None
        assert gap.fill_value == "John Doe"  # API uses fill_value not filled_value


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty module not available")
class TestSourceType:
    """Tests for SourceType enum."""
    
    def test_values(self):
        """Test source type values."""
        assert SourceType.EXPLICIT_STATEMENT.value == "explicit"
        assert SourceType.INFERENCE.value == "inference"


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty module not available")
class TestKnowledgeSource:
    """Tests for KnowledgeSource dataclass."""
    
    def test_creation(self):
        """Test creating source."""
        source = KnowledgeSource(
            source_id="src-001",
            source_type=SourceType.EXPLICIT_STATEMENT,
        )
        
        assert source.source_id == "src-001"
    
    def test_score(self):
        """Test score calculation."""
        source = KnowledgeSource(
            source_id="src-002",
            source_type=SourceType.EXPLICIT_STATEMENT,
            reliability=0.9,
            recency=0.8,
            context_match=1.0,
        )
        
        # score is a method, not property
        score = source.score()
        
        assert isinstance(score, (int, float))
        assert 0 < score <= 1


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty module not available")
class TestEpistemicGapFiller:
    """Tests for EpistemicGapFiller."""
    
    def test_creation(self):
        """Test creating filler."""
        filler = EpistemicGapFiller()
        
        assert filler is not None
        assert len(filler.sources) == 0
    
    def test_register_source(self):
        """Test registering source."""
        filler = EpistemicGapFiller()
        source = KnowledgeSource(
            source_id="src-001",
            source_type=SourceType.EXPLICIT_STATEMENT,
        )
        
        filler.register_source(source)
        
        assert len(filler.sources) == 1
    
    def test_prioritize_gaps(self):
        """Test gap prioritization."""
        filler = EpistemicGapFiller()
        gaps = [
            EpistemicGap(id="g1", gap_type=EpistemicGapType.MISSING_FACT, description="A", severity=GapSeverity.MINOR),
            EpistemicGap(id="g2", gap_type=EpistemicGapType.MISSING_FACT, description="B", severity=GapSeverity.CRITICAL),
        ]
        
        prioritized = filler.prioritize_gaps(gaps)
        
        # Critical should come first
        assert prioritized[0].severity.value >= prioritized[-1].severity.value


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty module not available")
class TestSocraticEscalation:
    """Tests for SocraticEscalation dataclass."""
    
    def test_creation(self):
        """Test creating escalation."""
        escalation = SocraticEscalation(
            gap_id="gap-001",
            question="What is the publication date?",
            question_type="factual",
        )
        
        assert escalation.gap_id == "gap-001"
        assert escalation.answered is False


@pytest.mark.skipif(not HAS_UNCERTAINTY, reason="uncertainty module not available")
class TestEpistemicToSocraticBridge:
    """Tests for EpistemicToSocraticBridge."""
    
    def test_creation(self):
        """Test creating bridge."""
        bridge = EpistemicToSocraticBridge()
        
        assert bridge is not None
    
    def test_get_pending(self):
        """Test getting pending escalations."""
        bridge = EpistemicToSocraticBridge()
        
        pending = bridge.get_pending()
        
        assert isinstance(pending, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
