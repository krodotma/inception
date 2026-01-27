"""
Claim extraction and analysis module.

Extracts factual claims from text using dependency parsing
and semantic analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import spacy
from spacy.tokens import Doc, Span as SpacySpan

from inception.db.keys import NodeKind
from inception.db.records import Confidence


@dataclass
class Claim:
    """A factual claim extracted from text."""
    
    text: str
    
    # Decomposition
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    
    # Modality
    modality: str = "assertion"  # assertion, possibility, necessity, negation
    tense: str = "present"  # past, present, future
    
    # Scope
    temporal_scope: str | None = None
    spatial_scope: str | None = None
    
    # Qualifiers
    hedges: list[str] = field(default_factory=list)
    evidentials: list[str] = field(default_factory=list)
    
    # Source position
    start_char: int = 0
    end_char: int = 0
    sentence_idx: int = 0
    
    # Confidence
    confidence: Confidence = field(default_factory=Confidence)
    
    # Linking
    source_span_nid: int | None = None
    supporting_evidence: list[int] = field(default_factory=list)
    
    @property
    def kind(self) -> NodeKind:
        return NodeKind.CLAIM
    
    @property
    def is_hedged(self) -> bool:
        return len(self.hedges) > 0
    
    @property
    def spo_tuple(self) -> tuple[str | None, str | None, str | None]:
        return (self.subject, self.predicate, self.object)


@dataclass
class ClaimExtractionResult:
    """Result of claim extraction from text."""
    
    claims: list[Claim] = field(default_factory=list)
    
    # Statistics
    claim_count: int = 0
    hedged_count: int = 0
    negated_count: int = 0
    
    @property
    def avg_confidence(self) -> float:
        if not self.claims:
            return 0.0
        return sum(c.confidence.combined for c in self.claims) / len(self.claims)


# Hedge words that indicate uncertainty
HEDGE_WORDS = {
    "might", "may", "could", "possibly", "perhaps", "probably",
    "likely", "unlikely", "appears", "seems", "suggests",
    "approximately", "about", "roughly", "around",
    "generally", "typically", "usually", "often",
    "in some cases", "sometimes", "occasionally",
}

# Evidential markers
EVIDENTIALS = {
    "according to", "reportedly", "allegedly", "supposedly",
    "claims", "states", "argues", "suggests", "indicates",
    "research shows", "studies suggest", "evidence indicates",
}

# Negation markers
NEGATION_MARKERS = {"not", "n't", "never", "no", "none", "neither", "nor"}


class ClaimExtractor:
    """
    Claim extractor using dependency parsing.
    
    Extracts Subject-Predicate-Object triples and analyzes
    claim modality and hedging.
    """
    
    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        min_claim_length: int = 4,
    ):
        """
        Initialize the extractor.
        
        Args:
            model_name: spaCy model name
            min_claim_length: Minimum word count for a claim
        """
        self.model_name = model_name
        self.min_claim_length = min_claim_length
        self._nlp = None
    
    def _get_nlp(self):
        """Lazy-load spaCy model."""
        if self._nlp is None:
            self._nlp = spacy.load(self.model_name)
        return self._nlp
    
    def extract(self, text: str) -> ClaimExtractionResult:
        """
        Extract claims from text.
        
        Args:
            text: Input text
        
        Returns:
            ClaimExtractionResult with extracted claims
        """
        nlp = self._get_nlp()
        doc = nlp(text)
        
        claims = []
        hedged_count = 0
        negated_count = 0
        
        for sent_idx, sent in enumerate(doc.sents):
            # Try to extract SPO from sentence
            claim = self._extract_claim_from_sent(sent, sent_idx)
            if claim is not None:
                claims.append(claim)
                
                if claim.is_hedged:
                    hedged_count += 1
                if claim.modality == "negation":
                    negated_count += 1
        
        return ClaimExtractionResult(
            claims=claims,
            claim_count=len(claims),
            hedged_count=hedged_count,
            negated_count=negated_count,
        )
    
    def _extract_claim_from_sent(
        self,
        sent: SpacySpan,
        sent_idx: int,
    ) -> Claim | None:
        """Extract a claim from a sentence."""
        # Skip short sentences
        if len(sent) < self.min_claim_length:
            return None
        
        # Find main verb (ROOT)
        root = None
        for token in sent:
            if token.dep_ == "ROOT":
                root = token
                break
        
        if root is None or root.pos_ != "VERB":
            return None
        
        # Find subject and object
        subject = self._find_subject(root)
        obj = self._find_object(root)
        
        # Build predicate including auxiliaries
        predicate = self._build_predicate(root)
        
        # Analyze modality
        modality, hedges = self._analyze_modality(sent, root)
        
        # Detect negation
        is_negated = any(
            child.dep_ == "neg" for child in root.children
        )
        if is_negated:
            modality = "negation"
        
        # Confidence based on hedging and structure
        confidence = Confidence(
            aleatoric=1.0 if not hedges else 0.7,
            epistemic=1.0 if subject and obj else 0.8,
        )
        
        return Claim(
            text=sent.text.strip(),
            subject=subject,
            predicate=predicate,
            object=obj,
            modality=modality,
            hedges=hedges,
            start_char=sent.start_char,
            end_char=sent.end_char,
            sentence_idx=sent_idx,
            confidence=confidence,
        )
    
    def _find_subject(self, root) -> str | None:
        """Find the subject of a verb."""
        for child in root.children:
            if child.dep_ in ("nsubj", "nsubjpass"):
                # Include compound modifiers
                subject_tokens = [child]
                for sub_child in child.subtree:
                    if sub_child.dep_ in ("compound", "amod", "det"):
                        subject_tokens.append(sub_child)
                
                subject_tokens.sort(key=lambda t: t.i)
                return " ".join(t.text for t in subject_tokens)
        
        return None
    
    def _find_object(self, root) -> str | None:
        """Find the object of a verb."""
        for child in root.children:
            if child.dep_ in ("dobj", "attr", "pobj"):
                # Include modifiers
                obj_tokens = list(child.subtree)
                obj_tokens.sort(key=lambda t: t.i)
                return " ".join(t.text for t in obj_tokens)
        
        # Check for prepositional phrases
        for child in root.children:
            if child.dep_ == "prep":
                for pobj in child.children:
                    if pobj.dep_ == "pobj":
                        prep_tokens = list(pobj.subtree)
                        prep_tokens.sort(key=lambda t: t.i)
                        return child.text + " " + " ".join(t.text for t in prep_tokens)
        
        return None
    
    def _build_predicate(self, root) -> str:
        """Build predicate including auxiliaries."""
        predicate_parts = []
        
        # Get auxiliaries
        for child in root.children:
            if child.dep_ == "aux":
                predicate_parts.append(child.text)
        
        predicate_parts.append(root.text)
        
        return " ".join(predicate_parts)
    
    def _analyze_modality(
        self,
        sent: SpacySpan,
        root,
    ) -> tuple[str, list[str]]:
        """Analyze the modality and hedging of a sentence."""
        sent_lower = sent.text.lower()
        
        hedges = []
        modality = "assertion"
        
        # Check for hedge words
        for hedge in HEDGE_WORDS:
            if hedge in sent_lower:
                hedges.append(hedge)
                modality = "possibility"
        
        # Check modal verbs
        for child in root.children:
            if child.dep_ == "aux" and child.text.lower() in ("might", "may", "could"):
                modality = "possibility"
            elif child.dep_ == "aux" and child.text.lower() in ("must", "should"):
                modality = "necessity"
        
        return modality, hedges


def extract_claims(text: str) -> ClaimExtractionResult:
    """
    Convenience function to extract claims from text.
    
    Args:
        text: Input text
    
    Returns:
        ClaimExtractionResult
    """
    extractor = ClaimExtractor()
    return extractor.extract(text)


def compute_claim_similarity(claim1: Claim, claim2: Claim) -> float:
    """
    Compute semantic similarity between two claims.
    
    Args:
        claim1: First claim
        claim2: Second claim
    
    Returns:
        Similarity score (0-1)
    """
    # Simple word overlap for now
    words1 = set(claim1.text.lower().split())
    words2 = set(claim2.text.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


def detect_contradiction(claim1: Claim, claim2: Claim) -> tuple[bool, float]:
    """
    Detect if two claims contradict each other.
    
    Args:
        claim1: First claim
        claim2: Second claim
    
    Returns:
        Tuple of (is_contradiction, confidence)
    """
    # Simple heuristic: same subject/object but different modality
    if claim1.subject and claim2.subject:
        if claim1.subject.lower() == claim2.subject.lower():
            if claim1.modality == "negation" and claim2.modality == "assertion":
                return True, 0.8
            if claim1.modality == "assertion" and claim2.modality == "negation":
                return True, 0.8
    
    return False, 0.0
