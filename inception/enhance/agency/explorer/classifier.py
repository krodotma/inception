"""
Gap classifier for identifying knowledge gaps.

Taxonomy designed by OPUS-1:
- undefined_term: Term used without definition
- missing_context: Assumed knowledge not explained
- incomplete_procedure: Steps missing from instructions
- unresolved_reference: External citation without content
- contradiction: Conflicting claims needing resolution
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class GapType(Enum):
    """Types of knowledge gaps."""
    
    UNDEFINED_TERM = auto()      # Term used but never defined
    MISSING_CONTEXT = auto()     # Background knowledge assumed
    INCOMPLETE_PROCEDURE = auto() # Procedure with missing steps
    UNRESOLVED_REFERENCE = auto() # External reference not resolved
    CONTRADICTION = auto()        # Conflicting information
    UNKNOWN = auto()              # Unclassified gap


@dataclass
class ClassifiedGap:
    """A classified knowledge gap with metadata."""
    
    nid: int                     # Node ID in graph
    gap_type: GapType
    term: str                    # The gap term or concept
    context: str                 # Surrounding context
    confidence: float            # Classification confidence (0-1)
    suggested_queries: list[str] # Search queries to resolve
    
    @property
    def priority(self) -> int:
        """Priority for resolution (higher = more important)."""
        priority_map = {
            GapType.UNDEFINED_TERM: 5,
            GapType.MISSING_CONTEXT: 4,
            GapType.INCOMPLETE_PROCEDURE: 4,
            GapType.UNRESOLVED_REFERENCE: 3,
            GapType.CONTRADICTION: 5,
            GapType.UNKNOWN: 1,
        }
        return priority_map.get(self.gap_type, 1)


class GapClassifier:
    """
    Classifies knowledge gaps by type.
    
    Uses pattern matching and optional LLM for complex cases.
    """
    
    def __init__(self, use_llm: bool = False):
        """
        Initialize the gap classifier.
        
        Args:
            use_llm: Use LLM for complex classification
        """
        self.use_llm = use_llm
        self._llm = None
    
    def classify(
        self,
        nid: int,
        payload: dict[str, Any],
    ) -> ClassifiedGap:
        """
        Classify a gap node.
        
        Args:
            nid: Node ID
            payload: Node payload from the graph
        
        Returns:
            Classified gap with metadata
        """
        term = payload.get("term", payload.get("text", ""))
        context = payload.get("context", "")
        gap_subtype = payload.get("subtype", "")
        
        # Classify based on subtype or patterns
        gap_type = self._determine_type(term, context, gap_subtype)
        
        # Generate search queries
        queries = self._generate_queries(term, gap_type)
        
        # Calculate confidence
        confidence = self._calculate_confidence(gap_type, term, context)
        
        return ClassifiedGap(
            nid=nid,
            gap_type=gap_type,
            term=term,
            context=context,
            confidence=confidence,
            suggested_queries=queries,
        )
    
    def _determine_type(
        self,
        term: str,
        context: str,
        subtype: str,
    ) -> GapType:
        """Determine gap type from term and context."""
        term_lower = term.lower()
        context_lower = context.lower()
        
        # Check explicit subtype first
        subtype_map = {
            "undefined": GapType.UNDEFINED_TERM,
            "missing": GapType.MISSING_CONTEXT,
            "incomplete": GapType.INCOMPLETE_PROCEDURE,
            "reference": GapType.UNRESOLVED_REFERENCE,
            "contradiction": GapType.CONTRADICTION,
        }
        for key, gap_type in subtype_map.items():
            if key in subtype.lower():
                return gap_type
        
        # Pattern matching
        if any(phrase in context_lower for phrase in [
            "not defined", "undefined", "what is", "unknown term"
        ]):
            return GapType.UNDEFINED_TERM
        
        if any(phrase in context_lower for phrase in [
            "assumed", "prerequisite", "background", "prior knowledge"
        ]):
            return GapType.MISSING_CONTEXT
        
        if any(phrase in context_lower for phrase in [
            "step", "procedure", "how to", "incomplete"
        ]):
            return GapType.INCOMPLETE_PROCEDURE
        
        if any(phrase in context_lower for phrase in [
            "reference", "citation", "source", "according to"
        ]):
            return GapType.UNRESOLVED_REFERENCE
        
        if any(phrase in context_lower for phrase in [
            "contradicts", "conflicts", "disagrees", "versus"
        ]):
            return GapType.CONTRADICTION
        
        return GapType.UNKNOWN
    
    def _generate_queries(
        self,
        term: str,
        gap_type: GapType,
    ) -> list[str]:
        """Generate search queries for gap resolution."""
        queries = []
        
        if gap_type == GapType.UNDEFINED_TERM:
            queries = [
                f"{term} definition",
                f"what is {term}",
                f"{term} meaning explained",
            ]
        elif gap_type == GapType.MISSING_CONTEXT:
            queries = [
                f"{term} background",
                f"{term} fundamentals",
                f"{term} introduction",
            ]
        elif gap_type == GapType.INCOMPLETE_PROCEDURE:
            queries = [
                f"how to {term}",
                f"{term} step by step",
                f"{term} tutorial",
            ]
        elif gap_type == GapType.UNRESOLVED_REFERENCE:
            queries = [
                f'"{term}" source',
                f"{term} original paper",
                f"{term} primary source",
            ]
        elif gap_type == GapType.CONTRADICTION:
            queries = [
                f"{term} authoritative source",
                f"{term} official documentation",
                f"{term} definitive answer",
            ]
        else:
            queries = [
                f"{term}",
                f"{term} explanation",
            ]
        
        return queries[:3]  # Return top 3
    
    def _calculate_confidence(
        self,
        gap_type: GapType,
        term: str,
        context: str,
    ) -> float:
        """Calculate classification confidence."""
        if gap_type == GapType.UNKNOWN:
            return 0.3
        
        # Higher confidence if we have good context
        if len(context) > 50:
            return 0.8
        elif len(context) > 20:
            return 0.6
        else:
            return 0.5
