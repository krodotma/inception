"""
Dialectical Branching Utilities for Phase 2

Implements thesis → antithesis detection,
synthesis candidate generation, and Socratic questioning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field


# =============================================================================
# Dialectical Branch Tree Structure (Step 50)
# =============================================================================

class BranchType(str, Enum):
    """Types of dialectical branches."""
    
    THESIS = "thesis"           # Initial position
    ANTITHESIS = "antithesis"   # Opposition
    SYNTHESIS = "synthesis"     # Resolution
    QUESTION = "question"       # Socratic probe
    EVIDENCE = "evidence"       # Supporting evidence
    HYPOTHETICAL = "hypothetical"  # What-if branch


@dataclass
class DialecticalBranch:
    """
    A node in the dialectical branching tree.
    
    Represents one position in a dialectical conversation.
    """
    
    branch_id: str
    branch_type: BranchType
    content: str
    
    # Tree structure
    parent_id: str | None = None
    children_ids: list[str] = field(default_factory=list)
    
    # Evidence tracking
    evidence_nids: list[int] = field(default_factory=list)
    confidence: float = 0.5
    
    # Agent tracking
    proposing_agent: str = "DIALECTICA"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Dialectical state
    resolved: bool = False
    resolution_id: str | None = None  # Points to synthesis branch if resolved


class DialecticalTree:
    """
    A tree structure for dialectical reasoning.
    
    Tracks thesis/antithesis/synthesis branches and their relationships.
    """
    
    def __init__(self, root_thesis: str, idea_nid: int | None = None):
        """Initialize with a root thesis."""
        from uuid import uuid4
        
        self.idea_nid = idea_nid
        self.branches: dict[str, DialecticalBranch] = {}
        
        # Create root thesis
        root_id = str(uuid4())
        self.root_id = root_id
        self.branches[root_id] = DialecticalBranch(
            branch_id=root_id,
            branch_type=BranchType.THESIS,
            content=root_thesis,
        )
    
    def add_antithesis(self, thesis_id: str, antithesis_content: str) -> str:
        """Add an antithesis to a thesis branch."""
        from uuid import uuid4
        
        if thesis_id not in self.branches:
            raise ValueError(f"Thesis {thesis_id} not found")
        
        antithesis_id = str(uuid4())
        self.branches[antithesis_id] = DialecticalBranch(
            branch_id=antithesis_id,
            branch_type=BranchType.ANTITHESIS,
            content=antithesis_content,
            parent_id=thesis_id,
        )
        self.branches[thesis_id].children_ids.append(antithesis_id)
        return antithesis_id
    
    def add_synthesis(self, thesis_id: str, antithesis_id: str, synthesis_content: str) -> str:
        """Add a synthesis resolving thesis and antithesis."""
        from uuid import uuid4
        
        synthesis_id = str(uuid4())
        self.branches[synthesis_id] = DialecticalBranch(
            branch_id=synthesis_id,
            branch_type=BranchType.SYNTHESIS,
            content=synthesis_content,
            parent_id=antithesis_id,  # Synthesis follows antithesis
            resolved=True,
        )
        
        # Mark both thesis and antithesis as resolved
        self.branches[thesis_id].resolved = True
        self.branches[thesis_id].resolution_id = synthesis_id
        self.branches[antithesis_id].resolved = True
        self.branches[antithesis_id].resolution_id = synthesis_id
        self.branches[antithesis_id].children_ids.append(synthesis_id)
        
        return synthesis_id
    
    def add_question(self, target_id: str, question: str) -> str:
        """Add a Socratic question to any branch."""
        from uuid import uuid4
        
        question_id = str(uuid4())
        self.branches[question_id] = DialecticalBranch(
            branch_id=question_id,
            branch_type=BranchType.QUESTION,
            content=question,
            parent_id=target_id,
        )
        self.branches[target_id].children_ids.append(question_id)
        return question_id
    
    def get_unresolved_pairs(self) -> list[tuple[DialecticalBranch, DialecticalBranch]]:
        """Get all thesis/antithesis pairs awaiting synthesis."""
        pairs = []
        for branch in self.branches.values():
            if branch.branch_type == BranchType.THESIS and not branch.resolved:
                # Find antitheses
                for child_id in branch.children_ids:
                    child = self.branches[child_id]
                    if child.branch_type == BranchType.ANTITHESIS and not child.resolved:
                        pairs.append((branch, child))
        return pairs
    
    def to_mermaid(self) -> str:
        """Export tree as Mermaid diagram."""
        lines = ["flowchart TB"]
        for branch in self.branches.values():
            label = branch.content[:30] + "..." if len(branch.content) > 30 else branch.content
            # Escape quotes
            label = label.replace('"', '\\"')
            
            if branch.branch_type == BranchType.THESIS:
                lines.append(f'    {branch.branch_id}["{label}"]')
            elif branch.branch_type == BranchType.ANTITHESIS:
                lines.append(f'    {branch.branch_id}(["{label}"])')
            elif branch.branch_type == BranchType.SYNTHESIS:
                lines.append(f'    {branch.branch_id}{{{{"{label}"}}}}')
            else:
                lines.append(f'    {branch.branch_id}>"{label}"]')
            
            for child_id in branch.children_ids:
                lines.append(f'    {branch.branch_id} --> {child_id}')
        
        return "\n".join(lines)


# =============================================================================
# Thesis → Antithesis Detection (Step 51)
# =============================================================================

class AntithesisPattern(str, Enum):
    """Patterns indicating antithesis relationship."""
    
    NEGATION = "negation"           # "X is not Y" vs "X is Y"
    OPPOSITION = "opposition"       # "X is good" vs "X is bad"
    ALTERNATIVE = "alternative"     # "Use X" vs "Use Y instead"
    LIMITATION = "limitation"       # "X works" vs "X only works when..."
    EXCEPTION = "exception"         # "Always X" vs "Except when Y"


@dataclass
class AntithesisDetection:
    """Result of antithesis detection."""
    
    thesis_nid: int
    thesis_text: str
    antithesis_nid: int | None
    antithesis_text: str | None
    pattern: AntithesisPattern
    confidence: float
    evidence: list[str]


class AntithesisDetector:
    """
    Detects opposing positions in claims.
    
    Uses patterns and semantic similarity to find contradictions.
    """
    
    # Negation indicators
    NEGATION_MARKERS = {
        "not", "never", "no", "none", "neither", "nor", "cannot", "can't",
        "won't", "shouldn't", "mustn't", "isn't", "aren't", "wasn't", "weren't",
        "don't", "doesn't", "didn't", "hasn't", "haven't", "hadn't"
    }
    
    # Opposition pairs
    OPPOSITION_PAIRS = {
        ("good", "bad"), ("safe", "unsafe"), ("fast", "slow"),
        ("simple", "complex"), ("easy", "difficult"), ("correct", "incorrect"),
        ("secure", "insecure"), ("efficient", "inefficient"),
        ("should", "should not"), ("must", "must not"),
        ("always", "never"), ("all", "none"),
    }
    
    def detect_antithesis(
        self,
        thesis: str,
        candidate_claims: list[tuple[int, str]],  # List of (nid, text)
    ) -> list[AntithesisDetection]:
        """
        Detect potential antitheses to a thesis.
        
        Args:
            thesis: The thesis statement
            candidate_claims: Claims to check for opposition
        
        Returns:
            List of detected antitheses with confidence scores
        """
        detections = []
        thesis_lower = thesis.lower()
        thesis_words = set(thesis_lower.split())
        
        for nid, claim in candidate_claims:
            claim_lower = claim.lower()
            claim_words = set(claim_lower.split())
            
            # Check for negation pattern
            negation_in_thesis = bool(thesis_words & self.NEGATION_MARKERS)
            negation_in_claim = bool(claim_words & self.NEGATION_MARKERS)
            
            if negation_in_thesis != negation_in_claim:
                # One has negation, other doesn't — potential antithesis
                overlap = thesis_words & claim_words - self.NEGATION_MARKERS
                if len(overlap) >= 2:  # Enough shared content
                    detections.append(AntithesisDetection(
                        thesis_nid=0,  # Would be set by caller
                        thesis_text=thesis,
                        antithesis_nid=nid,
                        antithesis_text=claim,
                        pattern=AntithesisPattern.NEGATION,
                        confidence=min(0.9, 0.5 + len(overlap) * 0.1),
                        evidence=[f"Negation difference with {len(overlap)} shared terms"],
                    ))
            
            # Check for opposition pairs
            for pos, neg in self.OPPOSITION_PAIRS:
                if pos in thesis_lower and neg in claim_lower:
                    detections.append(AntithesisDetection(
                        thesis_nid=0,
                        thesis_text=thesis,
                        antithesis_nid=nid,
                        antithesis_text=claim,
                        pattern=AntithesisPattern.OPPOSITION,
                        confidence=0.8,
                        evidence=[f"Opposition pair: {pos} vs {neg}"],
                    ))
                elif neg in thesis_lower and pos in claim_lower:
                    detections.append(AntithesisDetection(
                        thesis_nid=0,
                        thesis_text=thesis,
                        antithesis_nid=nid,
                        antithesis_text=claim,
                        pattern=AntithesisPattern.OPPOSITION,
                        confidence=0.8,
                        evidence=[f"Opposition pair: {neg} vs {pos}"],
                    ))
        
        return sorted(detections, key=lambda d: -d.confidence)


# =============================================================================
# Synthesis Candidate Generation (Step 52)
# =============================================================================

@dataclass
class SynthesisCandidate:
    """A potential synthesis of thesis and antithesis."""
    
    thesis: str
    antithesis: str
    synthesis: str
    strategy: str
    confidence: float
    conditions: list[str] = field(default_factory=list)


class SynthesisGenerator:
    """
    Generates synthesis candidates from thesis/antithesis pairs.
    
    Uses multiple strategies: contextualization, scoping, integration.
    """
    
    STRATEGIES = {
        "contextualization": "Both are true in different contexts",
        "scoping": "Thesis applies narrowly, antithesis more broadly (or vice versa)",
        "integration": "Combine elements of both into a unified view",
        "hierarchy": "One is more fundamental than the other",
        "dialectical": "A new position transcending both",
    }
    
    def generate_candidates(
        self,
        thesis: str,
        antithesis: str,
        domain_context: str | None = None,
    ) -> list[SynthesisCandidate]:
        """
        Generate synthesis candidates.
        
        In a full implementation, this would use LLM-based generation.
        Here we provide templates.
        """
        candidates = []
        
        # Strategy 1: Contextualization
        candidates.append(SynthesisCandidate(
            thesis=thesis,
            antithesis=antithesis,
            synthesis=f"[CONTEXT] {thesis}; however, {antithesis} when [CONDITION]",
            strategy="contextualization",
            confidence=0.6,
            conditions=["Requires identifying differentiating context"],
        ))
        
        # Strategy 2: Scoping
        candidates.append(SynthesisCandidate(
            thesis=thesis,
            antithesis=antithesis,
            synthesis=f"Generally {thesis}, but {antithesis} in specific cases",
            strategy="scoping",
            confidence=0.5,
            conditions=["Requires evidence for scope differences"],
        ))
        
        # Strategy 3: Integration
        candidates.append(SynthesisCandidate(
            thesis=thesis,
            antithesis=antithesis,
            synthesis=f"A balanced approach incorporating aspects of both: [INTEGRATED]",
            strategy="integration",
            confidence=0.4,
            conditions=["Requires creative integration"],
        ))
        
        return candidates


# =============================================================================
# Socratic Questioning Protocol (Step 53)
# =============================================================================

class QuestionType(str, Enum):
    """Types of Socratic questions."""
    
    # Clarification
    CLARIFY_MEANING = "clarify_meaning"
    CLARIFY_EXAMPLE = "clarify_example"
    CLARIFY_CONTRAST = "clarify_contrast"
    
    # Assumptions
    PROBE_ASSUMPTION = "probe_assumption"
    CHALLENGE_ASSUMPTION = "challenge_assumption"
    
    # Evidence
    REQUEST_EVIDENCE = "request_evidence"
    CHALLENGE_EVIDENCE = "challenge_evidence"
    
    # Implications
    EXPLORE_CONSEQUENCE = "explore_consequence"
    EXPLORE_ALTERNATIVE = "explore_alternative"
    
    # Meta
    SUMMARIZE = "summarize"
    STEELMAN = "steelman"


@dataclass
class SocraticQuestion:
    """A Socratic question in the protocol."""
    
    question_type: QuestionType
    question: str
    target_claim: str
    purpose: str
    expected_response_type: str


class SocraticProtocol:
    """
    Implements Socratic questioning for dialectical reasoning.
    
    Generates questions to probe, challenge, and refine positions.
    """
    
    QUESTION_TEMPLATES = {
        QuestionType.CLARIFY_MEANING: [
            "What exactly do you mean by '{term}'?",
            "Can you define '{term}' more precisely?",
            "How are you using the term '{term}' here?",
        ],
        QuestionType.CLARIFY_EXAMPLE: [
            "Can you give an example of '{claim}'?",
            "What would this look like in practice?",
            "How would '{claim}' manifest in a real scenario?",
        ],
        QuestionType.PROBE_ASSUMPTION: [
            "What assumptions underlie '{claim}'?",
            "What must be true for '{claim}' to hold?",
            "What are you taking for granted here?",
        ],
        QuestionType.CHALLENGE_ASSUMPTION: [
            "What if '{assumption}' were false?",
            "Is it always the case that '{assumption}'?",
            "Can you think of cases where '{assumption}' doesn't apply?",
        ],
        QuestionType.REQUEST_EVIDENCE: [
            "What evidence supports '{claim}'?",
            "How do we know '{claim}' is true?",
            "What data or sources back this up?",
        ],
        QuestionType.EXPLORE_CONSEQUENCE: [
            "If '{claim}' is true, what follows?",
            "What are the implications of '{claim}'?",
            "What consequences would '{claim}' have?",
        ],
        QuestionType.EXPLORE_ALTERNATIVE: [
            "What alternatives to '{claim}' exist?",
            "Is there another way to think about this?",
            "What would someone who disagrees say?",
        ],
        QuestionType.STEELMAN: [
            "What's the strongest argument for the opposing view?",
            "How would a defender of the antithesis respond?",
            "What merit does the opposing position have?",
        ],
    }
    
    def generate_questions(
        self,
        claim: str,
        question_types: list[QuestionType] | None = None,
        max_questions: int = 3,
    ) -> list[SocraticQuestion]:
        """
        Generate Socratic questions for a claim.
        
        Args:
            claim: The claim to question
            question_types: Specific types to generate, or None for auto
            max_questions: Maximum number of questions
        
        Returns:
            List of Socratic questions
        """
        import random
        
        if question_types is None:
            question_types = [
                QuestionType.CLARIFY_MEANING,
                QuestionType.PROBE_ASSUMPTION,
                QuestionType.REQUEST_EVIDENCE,
                QuestionType.EXPLORE_CONSEQUENCE,
            ]
        
        questions = []
        for q_type in question_types[:max_questions]:
            templates = self.QUESTION_TEMPLATES.get(q_type, [])
            if templates:
                template = random.choice(templates)
                # Simple placeholder replacement
                question = template.format(
                    claim=claim,
                    term=claim.split()[0],
                    assumption="[extract_assumption]",
                )
                questions.append(SocraticQuestion(
                    question_type=q_type,
                    question=question,
                    target_claim=claim,
                    purpose=f"Apply {q_type.value} to probe the claim",
                    expected_response_type="clarification" if "clarify" in q_type.value else "elaboration",
                ))
        
        return questions
    
    def steelman_opposition(self, thesis: str, antithesis: str) -> str:
        """
        Generate a steelmanned version of the antithesis.
        
        Makes the opposing argument as strong as possible.
        """
        # Template-based for now
        return f"The strongest argument for '{antithesis}' over '{thesis}' is that [STEELMAN]. This matters because [IMPORTANCE]."


# =============================================================================
# Integration with InceptionContext
# =============================================================================

def create_dialectical_session(
    thesis: str,
    idea_nid: int | None = None,
) -> tuple[DialecticalTree, SocraticProtocol]:
    """
    Create a new dialectical reasoning session.
    
    Returns a tree for tracking branches and a protocol for questioning.
    """
    tree = DialecticalTree(root_thesis=thesis, idea_nid=idea_nid)
    protocol = SocraticProtocol()
    return tree, protocol
