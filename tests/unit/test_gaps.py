"""
Unit tests for analyze/gaps.py

Tests for Gap detection and uncertainty modeling:
- GapType enum
- Gap dataclass
- GapDetectionResult
- GapDetector pattern detection
- Factory functions
"""

import pytest

from inception.analyze.gaps import (
    GapType,
    Gap,
    GapDetectionResult,
    GapDetector,
    detect_gaps,
    create_gap_node,
)
from inception.db.keys import NodeKind


# =============================================================================
# Test: GapType Enum
# =============================================================================

class TestGapType:
    """Tests for GapType enum."""
    
    def test_all_gap_types_exist(self):
        """Test all expected gap types are defined."""
        assert GapType.AMBIGUOUS_REFERENCE.value == "ambiguous_reference"
        assert GapType.INAUDIBLE.value == "inaudible"
        assert GapType.ILLEGIBLE.value == "illegible"
        assert GapType.UNCLEAR_QUANTITY.value == "unclear_quantity"
        assert GapType.MISSING_CONTEXT.value == "missing_context"
        assert GapType.INCOMPLETE_PROCEDURE.value == "incomplete_procedure"
        assert GapType.UNDEFINED_TERM.value == "undefined_term"
        assert GapType.ASSUMED_KNOWLEDGE.value == "assumed_knowledge"
        assert GapType.TEMPORAL_GAP.value == "temporal_gap"
        assert GapType.CONTRADICTION.value == "contradiction"
        assert GapType.OUTDATED.value == "outdated"
        assert GapType.TRUNCATED.value == "truncated"
        assert GapType.PARSING_FAILURE.value == "parsing_failure"


# =============================================================================
# Test: Gap Dataclass
# =============================================================================

class TestGap:
    """Tests for Gap dataclass."""
    
    def test_gap_creation(self):
        """Test creating a gap."""
        gap = Gap(
            gap_type=GapType.UNDEFINED_TERM,
            description="Term 'inference' is not defined",
        )
        
        assert gap.gap_type == GapType.UNDEFINED_TERM
        assert gap.description == "Term 'inference' is not defined"
        assert gap.severity == "minor"
        assert gap.confidence == 1.0
        assert gap.resolved is False
    
    def test_gap_with_location(self):
        """Test gap with position info."""
        gap = Gap(
            gap_type=GapType.INAUDIBLE,
            description="Audio unclear",
            start_ms=1000,
            end_ms=2000,
            start_char=50,
            end_char=100,
        )
        
        assert gap.start_ms == 1000
        assert gap.end_ms == 2000
        assert gap.start_char == 50
        assert gap.end_char == 100
    
    def test_gap_kind_property(self):
        """Test kind property returns NodeKind.GAP."""
        gap = Gap(
            gap_type=GapType.MISSING_CONTEXT,
            description="Context missing",
        )
        
        assert gap.kind == NodeKind.GAP
    
    def test_is_aleatoric_property(self):
        """Test is_aleatoric property for aleatoric gaps."""
        aleatoric_types = [
            GapType.AMBIGUOUS_REFERENCE,
            GapType.INAUDIBLE,
            GapType.ILLEGIBLE,
            GapType.UNCLEAR_QUANTITY,
        ]
        
        for gap_type in aleatoric_types:
            gap = Gap(gap_type=gap_type, description="test")
            assert gap.is_aleatoric is True
            assert gap.is_epistemic is False
    
    def test_is_epistemic_property(self):
        """Test is_epistemic property for epistemic gaps."""
        epistemic_types = [
            GapType.MISSING_CONTEXT,
            GapType.INCOMPLETE_PROCEDURE,
            GapType.UNDEFINED_TERM,
            GapType.ASSUMED_KNOWLEDGE,
            GapType.TEMPORAL_GAP,
        ]
        
        for gap_type in epistemic_types:
            gap = Gap(gap_type=gap_type, description="test")
            assert gap.is_epistemic is True
            assert gap.is_aleatoric is False
    
    def test_neither_aleatoric_nor_epistemic(self):
        """Test gaps that are neither aleatoric nor epistemic."""
        other_types = [
            GapType.CONTRADICTION,
            GapType.OUTDATED,
            GapType.TRUNCATED,
            GapType.PARSING_FAILURE,
        ]
        
        for gap_type in other_types:
            gap = Gap(gap_type=gap_type, description="test")
            assert gap.is_aleatoric is False
            assert gap.is_epistemic is False
    
    def test_gap_resolution(self):
        """Test resolving a gap."""
        gap = Gap(
            gap_type=GapType.UNDEFINED_TERM,
            description="Term unclear",
            resolved=True,
            resolution_text="Definition: X means Y",
            resolution_source="glossary.md",
        )
        
        assert gap.resolved is True
        assert gap.resolution_text == "Definition: X means Y"
        assert gap.resolution_source == "glossary.md"


# =============================================================================
# Test: GapDetectionResult
# =============================================================================

class TestGapDetectionResult:
    """Tests for GapDetectionResult."""
    
    def test_empty_result(self):
        """Test empty result."""
        result = GapDetectionResult()
        
        assert result.gaps == []
        assert result.total_count == 0
        assert result.aleatoric_count == 0
        assert result.epistemic_count == 0
    
    def test_total_count_property(self):
        """Test total_count property."""
        gaps = [
            Gap(gap_type=GapType.INAUDIBLE, description="test1"),
            Gap(gap_type=GapType.TRUNCATED, description="test2"),
            Gap(gap_type=GapType.UNDEFINED_TERM, description="test3"),
        ]
        
        result = GapDetectionResult(gaps=gaps)
        
        assert result.total_count == 3
    
    def test_severity_distribution(self):
        """Test severity_distribution property."""
        gaps = [
            Gap(gap_type=GapType.INAUDIBLE, description="test1", severity="minor"),
            Gap(gap_type=GapType.TRUNCATED, description="test2", severity="moderate"),
            Gap(gap_type=GapType.CONTRADICTION, description="test3", severity="major"),
            Gap(gap_type=GapType.PARSING_FAILURE, description="test4", severity="critical"),
            Gap(gap_type=GapType.UNDEFINED_TERM, description="test5", severity="minor"),
        ]
        
        result = GapDetectionResult(gaps=gaps)
        dist = result.severity_distribution
        
        assert dist["minor"] == 2
        assert dist["moderate"] == 1
        assert dist["major"] == 1
        assert dist["critical"] == 1
    
    def test_get_by_type(self):
        """Test get_by_type method."""
        gaps = [
            Gap(gap_type=GapType.INAUDIBLE, description="audio1"),
            Gap(gap_type=GapType.TRUNCATED, description="cut off"),
            Gap(gap_type=GapType.INAUDIBLE, description="audio2"),
        ]
        
        result = GapDetectionResult(gaps=gaps)
        inaudible = result.get_by_type(GapType.INAUDIBLE)
        
        assert len(inaudible) == 2
        assert all(g.gap_type == GapType.INAUDIBLE for g in inaudible)
    
    def test_get_unresolved(self):
        """Test get_unresolved method."""
        gaps = [
            Gap(gap_type=GapType.INAUDIBLE, description="test1", resolved=False),
            Gap(gap_type=GapType.TRUNCATED, description="test2", resolved=True),
            Gap(gap_type=GapType.UNDEFINED_TERM, description="test3", resolved=False),
        ]
        
        result = GapDetectionResult(gaps=gaps)
        unresolved = result.get_unresolved()
        
        assert len(unresolved) == 2
        assert all(not g.resolved for g in unresolved)


# =============================================================================
# Test: GapDetector
# =============================================================================

class TestGapDetector:
    """Tests for GapDetector."""
    
    def test_detector_init(self):
        """Test detector initialization."""
        detector = GapDetector()
        
        assert len(detector.undefined_term_patterns) > 0
        assert len(detector.vague_quantity_patterns) > 0
    
    def test_detect_low_transcript_confidence(self):
        """Test detection of low transcription confidence."""
        detector = GapDetector()
        
        result = detector.detect("Some text.", transcript_confidence=0.5)
        
        inaudible = result.get_by_type(GapType.INAUDIBLE)
        assert len(inaudible) == 1
        assert "Low transcription confidence" in inaudible[0].description
    
    def test_detect_low_ocr_confidence(self):
        """Test detection of low OCR confidence."""
        detector = GapDetector()
        
        result = detector.detect("Some text.", ocr_confidence=0.4)
        
        illegible = result.get_by_type(GapType.ILLEGIBLE)
        assert len(illegible) == 1
        assert "Low OCR confidence" in illegible[0].description
    
    def test_detect_ambiguous_references(self):
        """Test detection of ambiguous pronoun references."""
        detector = GapDetector()
        
        # Text starting with pronoun (no context)
        text = "It was very important. The system works well."
        result = detector.detect(text)
        
        ambiguous = result.get_by_type(GapType.AMBIGUOUS_REFERENCE)
        assert len(ambiguous) >= 1
    
    def test_detect_vague_quantities(self):
        """Test detection of vague quantities."""
        detector = GapDetector()
        
        text = "There are many problems. We need several changes. A lot of work is required."
        result = detector.detect(text)
        
        vague = result.get_by_type(GapType.UNCLEAR_QUANTITY)
        assert len(vague) >= 1
    
    def test_detect_undefined_terms(self):
        """Test detection of undefined terms in quotes."""
        detector = GapDetector()
        
        text = 'We use "inference engine" and "knowledge graph" extensively.'
        result = detector.detect(text)
        
        undefined = result.get_by_type(GapType.UNDEFINED_TERM)
        assert len(undefined) >= 1
    
    def test_detect_truncated_content(self):
        """Test detection of truncated content."""
        detector = GapDetector()
        
        # Text not ending with proper punctuation
        text = "This is some text that appears to be cut"
        result = detector.detect(text)
        
        truncated = result.get_by_type(GapType.TRUNCATED)
        assert len(truncated) == 1
        assert "cut off" in truncated[0].description.lower()
    
    def test_no_truncation_for_proper_ending(self):
        """Test no truncation detected for properly ended text."""
        detector = GapDetector()
        
        for ending in [".", "!", "?", '"', "'"]:
            text = f"This sentence ends properly{ending}"
            result = detector.detect(text)
            truncated = result.get_by_type(GapType.TRUNCATED)
            assert len(truncated) == 0, f"Unexpected truncation for ending: {ending}"
    
    def test_counts_aleatoric_and_epistemic(self):
        """Test that result counts aleatoric and epistemic gaps."""
        detector = GapDetector()
        
        # Low confidence + text with quotes for undefined terms
        text = '"Some term" is used here.'
        result = detector.detect(text, transcript_confidence=0.5)
        
        # Should have at least one aleatoric (inaudible) and one epistemic (undefined_term)
        assert result.aleatoric_count >= 1
        assert result.epistemic_count >= 1


# =============================================================================
# Test: Factory Functions
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory/convenience functions."""
    
    def test_detect_gaps_function(self):
        """Test detect_gaps convenience function."""
        result = detect_gaps("Some text.", transcript_confidence=0.5)
        
        assert isinstance(result, GapDetectionResult)
        assert len(result.gaps) >= 1  # At least inaudible gap
    
    def test_create_gap_node(self):
        """Test create_gap_node function."""
        gap = Gap(
            gap_type=GapType.UNDEFINED_TERM,
            description="Term X is unclear",
            context_text="surrounding context",
            severity="moderate",
        )
        
        node = create_gap_node(gap)
        
        assert node["gap_type"] == "undefined_term"
        assert node["description"] == "Term X is unclear"
        assert node["context"] == "surrounding context"
        assert node["severity"] == "moderate"
        assert node["is_aleatoric"] is False
        assert node["is_epistemic"] is True
        assert node["resolved"] is False
        assert node["resolution"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
