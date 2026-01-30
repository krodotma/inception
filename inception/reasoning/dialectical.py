"""
Dialectical/Socratic Reasoning Framework
Phase 10, Steps 221-240

Implements:
- Thesis/antithesis/synthesis model (221)
- Contradiction detection (222)
- Socratic questioning protocol (223)
- Steelman mode (224)
- Hidden assumptions mode (225)
- Dialectical branching tree (226)
- Dialectical state in context (227)
- Synthesis suggestion engine (228)
- Debate topology (multi-agent) (229)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional, Callable
from abc import ABC, abstractmethod


# =============================================================================
# Step 221: Thesis/Antithesis/Synthesis Model
# =============================================================================

class ClaimType(Enum):
    """Types of dialectical claims."""
    THESIS = "thesis"
    ANTITHESIS = "antithesis"
    SYNTHESIS = "synthesis"
    EVIDENCE = "evidence"
    ASSUMPTION = "assumption"
    QUESTION = "question"


class ClaimStrength(Enum):
    """Strength of a claim."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    COMPELLING = 4


@dataclass
class DialecticalClaim:
    """A claim in dialectical reasoning."""
    id: str
    claim_type: ClaimType
    content: str
    strength: ClaimStrength = ClaimStrength.MODERATE
    confidence: float = 0.5
    source: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Relationships
    supports_ids: list[str] = field(default_factory=list)
    opposes_ids: list[str] = field(default_factory=list)
    derived_from_ids: list[str] = field(default_factory=list)
    
    # Metadata
    author: str = "system"
    tags: list[str] = field(default_factory=list)


@dataclass
class DialecticalTriad:
    """
    A thesis-antithesis-synthesis triad.
    The core unit of dialectical progression.
    """
    
    id: str
    thesis: DialecticalClaim
    antithesis: Optional[DialecticalClaim] = None
    synthesis: Optional[DialecticalClaim] = None
    
    # State tracking
    resolved: bool = False
    resolution_date: Optional[datetime] = None
    
    # Parent triad (for nested dialectics)
    parent_id: Optional[str] = None
    child_ids: list[str] = field(default_factory=list)
    
    def propose_antithesis(self, content: str, strength: ClaimStrength = ClaimStrength.MODERATE) -> DialecticalClaim:
        """Propose an antithesis to the thesis."""
        self.antithesis = DialecticalClaim(
            id=f"{self.id}_anti",
            claim_type=ClaimType.ANTITHESIS,
            content=content,
            strength=strength,
            opposes_ids=[self.thesis.id],
        )
        return self.antithesis
    
    def propose_synthesis(self, content: str, strength: ClaimStrength = ClaimStrength.STRONG) -> DialecticalClaim:
        """Propose a synthesis resolving thesis and antithesis."""
        if not self.antithesis:
            raise ValueError("Cannot synthesize without antithesis")
        
        self.synthesis = DialecticalClaim(
            id=f"{self.id}_synth",
            claim_type=ClaimType.SYNTHESIS,
            content=content,
            strength=strength,
            derived_from_ids=[self.thesis.id, self.antithesis.id],
        )
        return self.synthesis
    
    def resolve(self) -> None:
        """Mark the triad as resolved."""
        self.resolved = True
        self.resolution_date = datetime.utcnow()
    
    @property
    def stage(self) -> str:
        """Current stage of the dialectic."""
        if self.synthesis:
            return "synthesis"
        if self.antithesis:
            return "antithesis"
        return "thesis"


# =============================================================================
# Step 222: Contradiction Detection
# =============================================================================

@dataclass
class Contradiction:
    """A detected contradiction between claims."""
    id: str
    claim_a_id: str
    claim_b_id: str
    contradiction_type: str  # 'direct', 'implicit', 'temporal', 'scope'
    severity: float  # 0-1
    explanation: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False


class ContradictionDetector:
    """
    Detect contradictions between claims.
    """
    
    def __init__(self):
        self.contradictions: list[Contradiction] = []
        self.contradiction_patterns: list[tuple[str, Callable]] = [
            ("direct_negation", self._check_direct_negation),
            ("scope_conflict", self._check_scope_conflict),
            ("temporal_conflict", self._check_temporal_conflict),
        ]
    
    def detect(self, claims: list[DialecticalClaim]) -> list[Contradiction]:
        """Detect contradictions among claims."""
        new_contradictions = []
        
        for i, claim_a in enumerate(claims):
            for claim_b in claims[i+1:]:
                for pattern_name, checker in self.contradiction_patterns:
                    if contradiction := checker(claim_a, claim_b, pattern_name):
                        new_contradictions.append(contradiction)
                        self.contradictions.append(contradiction)
        
        return new_contradictions
    
    def _check_direct_negation(self, a: DialecticalClaim, b: DialecticalClaim, pattern: str) -> Optional[Contradiction]:
        """Check for direct negation."""
        # One opposes the other
        if a.id in b.opposes_ids or b.id in a.opposes_ids:
            return Contradiction(
                id=f"contra_{a.id}_{b.id}",
                claim_a_id=a.id,
                claim_b_id=b.id,
                contradiction_type="direct",
                severity=0.9,
                explanation=f"Claims are in direct opposition",
            )
        
        # Simple negation patterns (would use NLP in production)
        negation_words = ["not", "never", "no", "false", "incorrect"]
        a_lower = a.content.lower()
        b_lower = b.content.lower()
        
        for neg in negation_words:
            if neg in a_lower and neg not in b_lower:
                # Check if core content is similar
                if self._content_similarity(a.content.replace(neg, ""), b.content) > 0.7:
                    return Contradiction(
                        id=f"contra_{a.id}_{b.id}",
                        claim_a_id=a.id,
                        claim_b_id=b.id,
                        contradiction_type="direct",
                        severity=0.8,
                        explanation=f"Negation pattern detected",
                    )
        
        return None
    
    def _check_scope_conflict(self, a: DialecticalClaim, b: DialecticalClaim, pattern: str) -> Optional[Contradiction]:
        """Check for scope conflicts (all vs. some)."""
        universal = ["all", "every", "always", "never", "none"]
        particular = ["some", "sometimes", "usually", "often", "rarely"]
        
        a_universal = any(u in a.content.lower() for u in universal)
        b_particular = any(p in b.content.lower() for p in particular)
        
        if a_universal and b_particular:
            # Check if about same topic
            if self._content_similarity(a.content, b.content) > 0.5:
                return Contradiction(
                    id=f"contra_{a.id}_{b.id}",
                    claim_a_id=a.id,
                    claim_b_id=b.id,
                    contradiction_type="scope",
                    severity=0.6,
                    explanation="Universal vs. particular scope conflict",
                )
        
        return None
    
    def _check_temporal_conflict(self, a: DialecticalClaim, b: DialecticalClaim, pattern: str) -> Optional[Contradiction]:
        """Check for temporal conflicts."""
        past_markers = ["was", "were", "used to", "previously", "formerly"]
        present_markers = ["is", "are", "currently", "now"]
        
        a_past = any(p in a.content.lower() for p in past_markers)
        b_present = any(p in b.content.lower() for p in present_markers)
        
        if a_past and b_present:
            if self._content_similarity(a.content, b.content) > 0.6:
                return Contradiction(
                    id=f"contra_{a.id}_{b.id}",
                    claim_a_id=a.id,
                    claim_b_id=b.id,
                    contradiction_type="temporal",
                    severity=0.4,
                    explanation="Temporal conflict (past vs. present)",
                )
        
        return None
    
    def _content_similarity(self, a: str, b: str) -> float:
        """Simple word overlap similarity."""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        
        if not words_a or not words_b:
            return 0.0
        
        intersection = words_a & words_b
        union = words_a | words_b
        
        return len(intersection) / len(union)


# =============================================================================
# Step 223: Socratic Questioning Protocol
# =============================================================================

class QuestionType(Enum):
    """Types of Socratic questions."""
    CLARIFICATION = "clarification"           # What do you mean by...?
    PROBING_ASSUMPTIONS = "assumptions"       # What are you assuming?
    PROBING_EVIDENCE = "evidence"             # What evidence supports...?
    EXPLORING_VIEWPOINTS = "viewpoints"       # What's an alternative view?
    EXPLORING_IMPLICATIONS = "implications"   # What are the consequences?
    QUESTIONING_THE_QUESTION = "meta"         # Why is this question important?


@dataclass
class SocraticQuestion:
    """A Socratic question."""
    id: str
    question_type: QuestionType
    question: str
    target_claim_id: Optional[str] = None
    answered: bool = False
    answer: Optional[str] = None
    follow_up_ids: list[str] = field(default_factory=list)


class SocraticProtocol:
    """
    Socratic questioning protocol for exploring claims.
    """
    
    def __init__(self):
        self.questions: list[SocraticQuestion] = []
        self.question_templates = {
            QuestionType.CLARIFICATION: [
                "What do you mean by '{key_term}'?",
                "Can you give an example of '{key_term}'?",
                "How would you define '{key_term}' more precisely?",
            ],
            QuestionType.PROBING_ASSUMPTIONS: [
                "What are you assuming when you say '{claim}'?",
                "Why do you think this assumption holds?",
                "What if the opposite were true?",
            ],
            QuestionType.PROBING_EVIDENCE: [
                "What evidence supports '{claim}'?",
                "How do you know this is true?",
                "What would change your mind about this?",
            ],
            QuestionType.EXPLORING_VIEWPOINTS: [
                "What would someone who disagrees say?",
                "What's an alternative explanation?",
                "How might this look from a different perspective?",
            ],
            QuestionType.EXPLORING_IMPLICATIONS: [
                "If this is true, what follows from it?",
                "What are the consequences of this being wrong?",
                "How does this connect to other things we know?",
            ],
            QuestionType.QUESTIONING_THE_QUESTION: [
                "Why is this question important?",
                "What's really at stake here?",
                "Are we asking the right question?",
            ],
        }
    
    def generate_questions(self, claim: DialecticalClaim, num_questions: int = 3) -> list[SocraticQuestion]:
        """Generate Socratic questions for a claim."""
        questions = []
        
        # Determine which question types are most relevant
        types_to_use = self._select_question_types(claim)
        
        for qtype in types_to_use[:num_questions]:
            template = self.question_templates[qtype][0]
            question_text = self._fill_template(template, claim)
            
            q = SocraticQuestion(
                id=f"sq_{claim.id}_{qtype.value}",
                question_type=qtype,
                question=question_text,
                target_claim_id=claim.id,
            )
            questions.append(q)
            self.questions.append(q)
        
        return questions
    
    def _select_question_types(self, claim: DialecticalClaim) -> list[QuestionType]:
        """Select appropriate question types based on claim."""
        types = []
        
        # Weak claims need evidence
        if claim.strength == ClaimStrength.WEAK:
            types.append(QuestionType.PROBING_EVIDENCE)
        
        # Theses need opposition explored
        if claim.claim_type == ClaimType.THESIS:
            types.append(QuestionType.EXPLORING_VIEWPOINTS)
            types.append(QuestionType.PROBING_ASSUMPTIONS)
        
        # Antitheses need implications explored
        if claim.claim_type == ClaimType.ANTITHESIS:
            types.append(QuestionType.EXPLORING_IMPLICATIONS)
        
        # Always include clarification
        types.append(QuestionType.CLARIFICATION)
        
        return types
    
    def _fill_template(self, template: str, claim: DialecticalClaim) -> str:
        """Fill in a question template."""
        # Extract key terms (simplified)
        words = claim.content.split()
        key_term = words[len(words)//2] if words else "this"
        
        return template.format(
            key_term=key_term,
            claim=claim.content[:50],
        )
    
    def answer_question(self, question_id: str, answer: str) -> Optional[list[SocraticQuestion]]:
        """Record an answer and generate follow-ups."""
        q = next((q for q in self.questions if q.id == question_id), None)
        if not q:
            return None
        
        q.answered = True
        q.answer = answer
        
        # Generate follow-up questions
        follow_ups = []
        if len(answer) > 50:  # Detailed answer warrants follow-up
            follow_up = SocraticQuestion(
                id=f"{question_id}_followup",
                question_type=QuestionType.EXPLORING_IMPLICATIONS,
                question=f"What follows from: {answer[:50]}...?",
            )
            follow_ups.append(follow_up)
            q.follow_up_ids.append(follow_up.id)
            self.questions.append(follow_up)
        
        return follow_ups


# =============================================================================
# Step 224-225: Steelman & Hidden Assumptions Modes
# =============================================================================

class ReasoningMode(Enum):
    """Modes of dialectical reasoning."""
    EXPLORATORY = "exploratory"
    STEELMAN = "steelman"
    ASSUMPTIONS = "assumptions"
    SYNTHESIS = "synthesis"
    ADVERSARIAL = "adversarial"


class SteelmanMode:
    """
    Steelman mode: Present the strongest version of the opposing view.
    """
    
    def steelman(self, claim: DialecticalClaim) -> DialecticalClaim:
        """Create a steelmanned version of a claim."""
        # In production, would use LLM to strengthen the argument
        strengthened_content = f"[Steelmanned] {claim.content}"
        
        return DialecticalClaim(
            id=f"{claim.id}_steel",
            claim_type=claim.claim_type,
            content=strengthened_content,
            strength=ClaimStrength.STRONG,
            confidence=min(claim.confidence + 0.2, 1.0),
            derived_from_ids=[claim.id],
            tags=["steelmanned"],
        )
    
    def generate_strongest_counterargument(self, thesis: DialecticalClaim) -> DialecticalClaim:
        """Generate the strongest possible counterargument."""
        counter_content = f"[Strongest counter] The opposite of '{thesis.content[:30]}...' because..."
        
        return DialecticalClaim(
            id=f"{thesis.id}_counter",
            claim_type=ClaimType.ANTITHESIS,
            content=counter_content,
            strength=ClaimStrength.COMPELLING,
            opposes_ids=[thesis.id],
            tags=["steelmanned_counter"],
        )


class AssumptionsFinder:
    """
    Find hidden assumptions in claims.
    """
    
    def find_assumptions(self, claim: DialecticalClaim) -> list[DialecticalClaim]:
        """Find hidden assumptions in a claim."""
        assumptions = []
        content = claim.content.lower()
        
        # Pattern-based assumption detection
        assumption_patterns = [
            ("should", "Normative assumption: There's a right way to do this"),
            ("must", "Necessity assumption: This is required"),
            ("always", "Universal assumption: This holds in all cases"),
            ("never", "Universal negative assumption: This never happens"),
            ("obviously", "Epistemic assumption: This is self-evident"),
            ("clearly", "Epistemic assumption: This is apparent"),
            ("natural", "Naturalistic assumption: This is inherent/default"),
            ("everyone", "Universal quantifier assumption"),
        ]
        
        for pattern, explanation in assumption_patterns:
            if pattern in content:
                assumption = DialecticalClaim(
                    id=f"{claim.id}_assume_{pattern}",
                    claim_type=ClaimType.ASSUMPTION,
                    content=explanation,
                    strength=ClaimStrength.WEAK,  # Assumptions often unexamined
                    supports_ids=[claim.id],
                    tags=["hidden_assumption"],
                )
                assumptions.append(assumption)
        
        return assumptions
    
    def challenge_assumption(self, assumption: DialecticalClaim) -> SocraticQuestion:
        """Generate a question challenging an assumption."""
        return SocraticQuestion(
            id=f"challenge_{assumption.id}",
            question_type=QuestionType.PROBING_ASSUMPTIONS,
            question=f"Is it really the case that {assumption.content.lower()}?",
            target_claim_id=assumption.id,
        )


# =============================================================================
# Step 226: Dialectical Branching Tree
# =============================================================================

@dataclass
class DialecticalNode:
    """A node in the dialectical tree."""
    id: str
    claim: DialecticalClaim
    parent_id: Optional[str] = None
    child_ids: list[str] = field(default_factory=list)
    depth: int = 0
    branch_type: str = "main"  # 'main', 'alternative', 'synthesis'


class DialecticalTree:
    """
    Tree structure for dialectical reasoning with branching.
    """
    
    def __init__(self):
        self.nodes: dict[str, DialecticalNode] = {}
        self.root_id: Optional[str] = None
    
    def add_root(self, thesis: DialecticalClaim) -> str:
        """Add root thesis."""
        node = DialecticalNode(
            id=thesis.id,
            claim=thesis,
            depth=0,
        )
        self.nodes[node.id] = node
        self.root_id = node.id
        return node.id
    
    def add_response(self, parent_id: str, claim: DialecticalClaim, branch_type: str = "main") -> str:
        """Add a response (antithesis, evidence, etc.) to a claim."""
        parent = self.nodes.get(parent_id)
        if not parent:
            raise ValueError(f"Parent {parent_id} not found")
        
        node = DialecticalNode(
            id=claim.id,
            claim=claim,
            parent_id=parent_id,
            depth=parent.depth + 1,
            branch_type=branch_type,
        )
        
        self.nodes[node.id] = node
        parent.child_ids.append(node.id)
        
        return node.id
    
    def create_branch(self, from_node_id: str, branch_claim: DialecticalClaim) -> str:
        """Create an alternative branch from a node."""
        return self.add_response(from_node_id, branch_claim, branch_type="alternative")
    
    def get_path_to_root(self, node_id: str) -> list[DialecticalNode]:
        """Get path from node to root."""
        path = []
        current_id = node_id
        
        while current_id:
            node = self.nodes.get(current_id)
            if node:
                path.append(node)
                current_id = node.parent_id
            else:
                break
        
        return list(reversed(path))
    
    def get_all_leaves(self) -> list[DialecticalNode]:
        """Get all leaf nodes (unresolved endpoints)."""
        return [n for n in self.nodes.values() if not n.child_ids]
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize tree structure."""
        def node_to_dict(node_id: str) -> dict:
            node = self.nodes[node_id]
            return {
                "id": node.id,
                "claim": node.claim.content[:50],
                "type": node.claim.claim_type.value,
                "branch": node.branch_type,
                "children": [node_to_dict(cid) for cid in node.child_ids],
            }
        
        if self.root_id:
            return node_to_dict(self.root_id)
        return {}


# =============================================================================
# Step 228: Synthesis Suggestion Engine
# =============================================================================

class SynthesisSuggester:
    """
    Suggest syntheses for thesis-antithesis pairs.
    """
    
    def __init__(self):
        self.synthesis_patterns = [
            ("both/and", self._both_and_synthesis),
            ("context_dependent", self._context_synthesis),
            ("higher_principle", self._principle_synthesis),
            ("temporal", self._temporal_synthesis),
        ]
    
    def suggest_synthesis(self, thesis: DialecticalClaim, antithesis: DialecticalClaim) -> list[DialecticalClaim]:
        """Suggest possible syntheses."""
        suggestions = []
        
        for pattern_name, generator in self.synthesis_patterns:
            synthesis = generator(thesis, antithesis, pattern_name)
            if synthesis:
                suggestions.append(synthesis)
        
        return suggestions
    
    def _both_and_synthesis(self, thesis: DialecticalClaim, antithesis: DialecticalClaim, pattern: str) -> DialecticalClaim:
        """Both/and synthesis: Both claims hold in different respects."""
        content = f"Both '{thesis.content[:30]}...' AND '{antithesis.content[:30]}...' are true in different respects"
        
        return DialecticalClaim(
            id=f"synth_{thesis.id}_{pattern}",
            claim_type=ClaimType.SYNTHESIS,
            content=content,
            strength=ClaimStrength.MODERATE,
            derived_from_ids=[thesis.id, antithesis.id],
            tags=[pattern],
        )
    
    def _context_synthesis(self, thesis: DialecticalClaim, antithesis: DialecticalClaim, pattern: str) -> DialecticalClaim:
        """Context-dependent synthesis: Claims hold in different contexts."""
        content = f"'{thesis.content[:30]}...' applies in context A, while '{antithesis.content[:30]}...' applies in context B"
        
        return DialecticalClaim(
            id=f"synth_{thesis.id}_{pattern}",
            claim_type=ClaimType.SYNTHESIS,
            content=content,
            strength=ClaimStrength.MODERATE,
            derived_from_ids=[thesis.id, antithesis.id],
            tags=[pattern],
        )
    
    def _principle_synthesis(self, thesis: DialecticalClaim, antithesis: DialecticalClaim, pattern: str) -> DialecticalClaim:
        """Higher principle synthesis: A higher-level principle resolves the tension."""
        content = f"A higher principle reconciles: {thesis.content[:20]}... and {antithesis.content[:20]}..."
        
        return DialecticalClaim(
            id=f"synth_{thesis.id}_{pattern}",
            claim_type=ClaimType.SYNTHESIS,
            content=content,
            strength=ClaimStrength.STRONG,
            derived_from_ids=[thesis.id, antithesis.id],
            tags=[pattern],
        )
    
    def _temporal_synthesis(self, thesis: DialecticalClaim, antithesis: DialecticalClaim, pattern: str) -> DialecticalClaim:
        """Temporal synthesis: Claims hold at different times."""
        content = f"'{thesis.content[:30]}...' was true then, '{antithesis.content[:30]}...' is true now"
        
        return DialecticalClaim(
            id=f"synth_{thesis.id}_{pattern}",
            claim_type=ClaimType.SYNTHESIS,
            content=content,
            strength=ClaimStrength.MODERATE,
            derived_from_ids=[thesis.id, antithesis.id],
            tags=[pattern],
        )


# =============================================================================
# Step 229: Debate Topology (Multi-Agent)
# =============================================================================

class DebateRole(Enum):
    """Roles in a multi-agent debate."""
    PROPOSER = "proposer"       # Proposes thesis
    OPPONENT = "opponent"       # Provides antithesis
    SYNTHESIZER = "synthesizer" # Attempts synthesis
    MODERATOR = "moderator"     # Guides debate
    FACT_CHECKER = "fact_checker"  # Verifies claims
    AUDIENCE = "audience"       # Asks questions


@dataclass
class DebateParticipant:
    """A participant in a debate."""
    participant_id: str
    name: str
    role: DebateRole
    agent_type: str = "ai"  # 'ai', 'human'
    active: bool = True


@dataclass
class DebateTurn:
    """A turn in the debate."""
    turn_id: str
    participant_id: str
    action: str  # 'present', 'counter', 'question', 'synthesize', 'moderate'
    claim_id: Optional[str] = None
    question_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DebateTopology:
    """
    Multi-agent debate structure.
    """
    
    def __init__(self):
        self.participants: dict[str, DebateParticipant] = {}
        self.turns: list[DebateTurn] = []
        self.tree: DialecticalTree = DialecticalTree()
        self.state: str = "setup"  # 'setup', 'thesis', 'antithesis', 'debate', 'synthesis', 'concluded'
    
    def add_participant(self, participant: DebateParticipant) -> None:
        """Add a participant to the debate."""
        self.participants[participant.participant_id] = participant
    
    def start_debate(self, thesis: DialecticalClaim, proposer_id: str) -> str:
        """Start the debate with an opening thesis."""
        self.tree.add_root(thesis)
        self.state = "thesis"
        
        turn = DebateTurn(
            turn_id=f"turn_0",
            participant_id=proposer_id,
            action="present",
            claim_id=thesis.id,
        )
        self.turns.append(turn)
        
        return thesis.id
    
    def counter(self, opponent_id: str, antithesis: DialecticalClaim, target_claim_id: str) -> str:
        """Counter a claim with an antithesis."""
        self.tree.add_response(target_claim_id, antithesis)
        self.state = "debate"
        
        turn = DebateTurn(
            turn_id=f"turn_{len(self.turns)}",
            participant_id=opponent_id,
            action="counter",
            claim_id=antithesis.id,
        )
        self.turns.append(turn)
        
        return antithesis.id
    
    def propose_synthesis(self, synthesizer_id: str, synthesis: DialecticalClaim, 
                          thesis_id: str, antithesis_id: str) -> str:
        """Propose a synthesis."""
        self.tree.add_response(thesis_id, synthesis, branch_type="synthesis")
        self.state = "synthesis"
        
        turn = DebateTurn(
            turn_id=f"turn_{len(self.turns)}",
            participant_id=synthesizer_id,
            action="synthesize",
            claim_id=synthesis.id,
        )
        self.turns.append(turn)
        
        return synthesis.id
    
    def conclude(self, moderator_id: str, conclusion: str) -> None:
        """Conclude the debate."""
        self.state = "concluded"
        
        turn = DebateTurn(
            turn_id=f"turn_{len(self.turns)}",
            participant_id=moderator_id,
            action="moderate",
        )
        self.turns.append(turn)
    
    def get_debate_summary(self) -> dict[str, Any]:
        """Get summary of the debate."""
        return {
            "state": self.state,
            "participants": len(self.participants),
            "turns": len(self.turns),
            "tree_depth": max((n.depth for n in self.tree.nodes.values()), default=0),
            "open_questions": len(self.tree.get_all_leaves()),
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_triad(thesis_content: str) -> DialecticalTriad:
    """Create a new dialectical triad."""
    thesis = DialecticalClaim(
        id=hashlib.md5(thesis_content.encode()).hexdigest()[:8],
        claim_type=ClaimType.THESIS,
        content=thesis_content,
    )
    
    return DialecticalTriad(
        id=f"triad_{thesis.id}",
        thesis=thesis,
    )


def create_debate(topic: str, proposer: DebateParticipant) -> DebateTopology:
    """Create a new debate."""
    debate = DebateTopology()
    debate.add_participant(proposer)
    
    thesis = DialecticalClaim(
        id=f"thesis_{topic[:8]}",
        claim_type=ClaimType.THESIS,
        content=topic,
        author=proposer.name,
    )
    
    debate.start_debate(thesis, proposer.participant_id)
    
    return debate


__all__ = [
    # Claim types
    "ClaimType",
    "ClaimStrength",
    "DialecticalClaim",
    
    # Triad
    "DialecticalTriad",
    
    # Contradiction
    "Contradiction",
    "ContradictionDetector",
    
    # Socratic
    "QuestionType",
    "SocraticQuestion",
    "SocraticProtocol",
    
    # Modes
    "ReasoningMode",
    "SteelmanMode",
    "AssumptionsFinder",
    
    # Tree
    "DialecticalNode",
    "DialecticalTree",
    
    # Synthesis
    "SynthesisSuggester",
    
    # Debate
    "DebateRole",
    "DebateParticipant",
    "DebateTurn",
    "DebateTopology",
    
    # Factory
    "create_triad",
    "create_debate",
]
