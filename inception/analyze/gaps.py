"""
Gap detection and uncertainty modeling module.

Detects and represents gaps in knowledge (both aleatoric and epistemic).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from inception.db.keys import NodeKind
from inception.db.records import Confidence


class GapType(str, Enum):
    """Types of knowledge gaps."""
    
    # Aleatoric uncertainty (inherent noise/randomness)
    AMBIGUOUS_REFERENCE = "ambiguous_reference"  # Unclear pronoun/reference
    INAUDIBLE = "inaudible"  # Couldn't hear/transcribe
    ILLEGIBLE = "illegible"  # Couldn't read/OCR
    UNCLEAR_QUANTITY = "unclear_quantity"  # Vague amounts
    
    # Epistemic uncertainty (missing information)
    MISSING_CONTEXT = "missing_context"  # Needs external info
    INCOMPLETE_PROCEDURE = "incomplete_procedure"  # Steps missing
    UNDEFINED_TERM = "undefined_term"  # Term not explained
    ASSUMED_KNOWLEDGE = "assumed_knowledge"  # Prerequisites not stated
    TEMPORAL_GAP = "temporal_gap"  # Time period unclear
    
    # Contradictions and conflicts
    CONTRADICTION = "contradiction"  # Conflicting claims
    OUTDATED = "outdated"  # Information may be stale
    
    # Recording/extraction issues
    TRUNCATED = "truncated"  # Cut off mid-sentence
    PARSING_FAILURE = "parsing_failure"  # Couldn't parse structure


@dataclass
class Gap:
    """A knowledge gap or uncertainty in the extracted content."""
    
    gap_type: GapType
    description: str
    
    # Location
    start_ms: int | None = None
    end_ms: int | None = None
    start_char: int | None = None
    end_char: int | None = None
    
    # Context
    context_text: str | None = None
    surrounding_span_nids: list[int] = field(default_factory=list)
    
    # Related entities
    related_entity_text: str | None = None
    related_claim_text: str | None = None
    
    # Severity and confidence
    severity: str = "minor"  # minor, moderate, major, critical
    confidence: float = 1.0  # Confidence that this IS a gap
    
    # Resolution
    resolved: bool = False
    resolution_text: str | None = None
    resolution_source: str | None = None
    
    @property
    def kind(self) -> NodeKind:
        return NodeKind.GAP
    
    @property
    def is_aleatoric(self) -> bool:
        """Check if this is an aleatoric (inherent noise) gap."""
        aleatoric_types = {
            GapType.AMBIGUOUS_REFERENCE,
            GapType.INAUDIBLE,
            GapType.ILLEGIBLE,
            GapType.UNCLEAR_QUANTITY,
        }
        return self.gap_type in aleatoric_types
    
    @property
    def is_epistemic(self) -> bool:
        """Check if this is an epistemic (missing info) gap."""
        epistemic_types = {
            GapType.MISSING_CONTEXT,
            GapType.INCOMPLETE_PROCEDURE,
            GapType.UNDEFINED_TERM,
            GapType.ASSUMED_KNOWLEDGE,
            GapType.TEMPORAL_GAP,
        }
        return self.gap_type in epistemic_types


@dataclass
class GapDetectionResult:
    """Result of gap detection analysis."""
    
    gaps: list[Gap] = field(default_factory=list)
    
    # Statistics
    aleatoric_count: int = 0
    epistemic_count: int = 0
    
    @property
    def total_count(self) -> int:
        return len(self.gaps)
    
    @property
    def severity_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {"minor": 0, "moderate": 0, "major": 0, "critical": 0}
        for gap in self.gaps:
            dist[gap.severity] = dist.get(gap.severity, 0) + 1
        return dist
    
    def get_by_type(self, gap_type: GapType) -> list[Gap]:
        """Get gaps of a specific type."""
        return [g for g in self.gaps if g.gap_type == gap_type]
    
    def get_unresolved(self) -> list[Gap]:
        """Get unresolved gaps."""
        return [g for g in self.gaps if not g.resolved]


class GapDetector:
    """
    Gap detector for identifying knowledge uncertainties.
    """
    
    def __init__(self):
        """Initialize the detector."""
        self.undefined_term_patterns = [
            "this", "that", "it", "they", "those",
            "the thing", "the stuff", "whatever",
        ]
        
        self.vague_quantity_patterns = [
            "some", "many", "few", "several", "a lot",
            "a bit", "a little", "various", "multiple",
        ]
    
    def detect(
        self,
        text: str,
        transcript_confidence: float = 1.0,
        ocr_confidence: float = 1.0,
    ) -> GapDetectionResult:
        """
        Detect gaps in text content.
        
        Args:
            text: Input text
            transcript_confidence: Confidence of transcription
            ocr_confidence: Confidence of OCR
        
        Returns:
            GapDetectionResult with detected gaps
        """
        gaps = []
        
        # Check for transcription quality issues
        if transcript_confidence < 0.7:
            gaps.append(Gap(
                gap_type=GapType.INAUDIBLE,
                description="Low transcription confidence indicates potential inaudible content",
                severity="moderate",
                confidence=1.0 - transcript_confidence,
            ))
        
        # Check for OCR quality issues
        if ocr_confidence < 0.7:
            gaps.append(Gap(
                gap_type=GapType.ILLEGIBLE,
                description="Low OCR confidence indicates potential illegible content",
                severity="moderate",
                confidence=1.0 - ocr_confidence,
            ))
        
        # Detect ambiguous references
        ambiguous_gaps = self._detect_ambiguous_references(text)
        gaps.extend(ambiguous_gaps)
        
        # Detect vague quantities
        vague_gaps = self._detect_vague_quantities(text)
        gaps.extend(vague_gaps)
        
        # Detect undefined terms
        undefined_gaps = self._detect_undefined_terms(text)
        gaps.extend(undefined_gaps)
        
        # Detect truncated content
        if text and not text.rstrip().endswith((".", "!", "?", '"', "'")):
            gaps.append(Gap(
                gap_type=GapType.TRUNCATED,
                description="Content appears to be cut off",
                context_text=text[-50:] if len(text) > 50 else text,
                severity="minor",
            ))
        
        # Count by type
        aleatoric_count = sum(1 for g in gaps if g.is_aleatoric)
        epistemic_count = sum(1 for g in gaps if g.is_epistemic)
        
        return GapDetectionResult(
            gaps=gaps,
            aleatoric_count=aleatoric_count,
            epistemic_count=epistemic_count,
        )
    
    def _detect_ambiguous_references(self, text: str) -> list[Gap]:
        """Detect ambiguous pronoun references."""
        import re
        
        gaps = []
        
        # Pattern for sentences starting with pronouns
        sentences = text.split(".")
        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if not sent:
                continue
            
            first_word = sent.split()[0].lower() if sent.split() else ""
            
            if first_word in ("it", "this", "that", "they", "these", "those"):
                # Check if previous sentence exists to provide context
                if i == 0:
                    gaps.append(Gap(
                        gap_type=GapType.AMBIGUOUS_REFERENCE,
                        description=f"Ambiguous reference '{first_word}' at start without context",
                        context_text=sent[:100],
                        severity="minor",
                    ))
        
        return gaps
    
    def _detect_vague_quantities(self, text: str) -> list[Gap]:
        """Detect vague quantity expressions."""
        import re
        
        gaps = []
        
        for pattern in self.vague_quantity_patterns:
            matches = list(re.finditer(rf"\b{pattern}\b", text.lower()))
            for match in matches:
                # Only flag if in potentially important context
                context_start = max(0, match.start() - 30)
                context_end = min(len(text), match.end() + 30)
                context = text[context_start:context_end]
                
                gaps.append(Gap(
                    gap_type=GapType.UNCLEAR_QUANTITY,
                    description=f"Vague quantity '{pattern}'",
                    context_text=context,
                    start_char=match.start(),
                    end_char=match.end(),
                    severity="minor",
                ))
        
        # Limit to top 5 to avoid noise
        return gaps[:5]
    
    def _detect_undefined_terms(self, text: str) -> list[Gap]:
        """Detect potentially undefined technical terms."""
        import re
        
        gaps = []
        
        # Look for quoted terms that might need definition
        quoted = re.findall(r'"([^"]+)"', text)
        for term in quoted[:3]:  # Limit
            if len(term.split()) <= 3:  # Short terms
                gaps.append(Gap(
                    gap_type=GapType.UNDEFINED_TERM,
                    description=f"Term '{term}' may need definition",
                    related_entity_text=term,
                    severity="minor",
                ))
        
        return gaps


def detect_gaps(
    text: str,
    transcript_confidence: float = 1.0,
    ocr_confidence: float = 1.0,
) -> GapDetectionResult:
    """
    Convenience function to detect gaps in text.
    
    Args:
        text: Input text
        transcript_confidence: Optional transcription confidence
        ocr_confidence: Optional OCR confidence
    
    Returns:
        GapDetectionResult
    """
    detector = GapDetector()
    return detector.detect(text, transcript_confidence, ocr_confidence)


def create_gap_node(gap: Gap) -> dict:
    """
    Convert a Gap to a node payload for storage.
    
    Args:
        gap: Gap to convert
    
    Returns:
        Node payload dictionary
    """
    return {
        "gap_type": gap.gap_type.value,
        "description": gap.description,
        "context": gap.context_text,
        "severity": gap.severity,
        "is_aleatoric": gap.is_aleatoric,
        "is_epistemic": gap.is_epistemic,
        "resolved": gap.resolved,
        "resolution": gap.resolution_text,
    }
