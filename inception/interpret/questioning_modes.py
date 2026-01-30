"""
Dialectical Questioning Modes — Phase 3 Steps 75-79

Five questioning modes for deep dialectical exploration:
1. WHY mode — causal reasoning
2. HOW mode — procedural reasoning  
3. WHAT-IF mode — hypothetical reasoning
4. STEELMAN mode — strengthening opposition
5. HIDDEN ASSUMPTIONS mode — revealing implicit premises
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterator


# =============================================================================
# QUESTIONING MODE ENUM
# =============================================================================

class QuestioningMode(str, Enum):
    """The five dialectical questioning modes."""
    
    WHY = "why"                    # Causal reasoning
    HOW = "how"                    # Procedural reasoning
    WHAT_IF = "what_if"            # Hypothetical reasoning
    STEELMAN = "steelman"          # Opposition strengthening
    HIDDEN_ASSUMPTIONS = "hidden_assumptions"  # Revealing premises


# =============================================================================
# QUESTION RESULT
# =============================================================================

@dataclass
class DialecticalQuestion:
    """A generated dialectical question."""
    
    mode: QuestioningMode
    original_input: str
    transformed_question: str
    follow_ups: list[str] = field(default_factory=list)
    potential_answers: list[str] = field(default_factory=list)
    dialectical_value: str = ""  # What this question adds to the dialectic
    depth: int = 1  # Question depth level


# =============================================================================
# WHY MODE — CAUSAL REASONING (Step 75)
# =============================================================================

class WhyMode:
    """
    The WHY mode asks for causes, reasons, and explanations.
    
    Transforms statements into causal inquiries.
    Depth increases by asking "why" to answers.
    """
    
    TEMPLATES = [
        "Why is it the case that {claim}?",
        "What causes {claim}?",
        "What are the underlying reasons for {claim}?",
        "Why does this matter?",
        "What's the ultimate cause here?",
    ]
    
    FOLLOW_UPS = [
        "And why is that the case?",
        "What are the root causes?",
        "Is this a proximate or ultimate cause?",
        "Are there multiple contributing causes?",
        "Could the relationship be reversed (effect→cause)?",
    ]
    
    def generate(self, claim: str, depth: int = 1) -> DialecticalQuestion:
        """Generate a WHY question for a claim."""
        import random
        
        template = self.TEMPLATES[min(depth - 1, len(self.TEMPLATES) - 1)]
        question = template.format(claim=claim)
        
        return DialecticalQuestion(
            mode=QuestioningMode.WHY,
            original_input=claim,
            transformed_question=question,
            follow_ups=self.FOLLOW_UPS[:3],
            dialectical_value="Reveals causal structure and explanatory depth",
            depth=depth,
        )
    
    def chain(self, claim: str, max_depth: int = 5) -> Iterator[DialecticalQuestion]:
        """Generate a chain of WHY questions (5 Whys technique)."""
        for depth in range(1, max_depth + 1):
            yield self.generate(claim, depth)


# =============================================================================
# HOW MODE — PROCEDURAL REASONING (Step 76)
# =============================================================================

class HowMode:
    """
    The HOW mode asks for mechanisms, processes, and procedures.
    
    Transforms goals into step-by-step inquiries.
    """
    
    TEMPLATES = {
        "mechanism": "How does {claim} work mechanistically?",
        "process": "What is the process by which {claim}?",
        "implementation": "How would one implement {claim}?",
        "verification": "How can we verify that {claim}?",
        "measurement": "How do we measure {claim}?",
    }
    
    FOLLOW_UPS = [
        "What are the specific steps involved?",
        "What resources/dependencies are required?",
        "What could go wrong at each step?",
        "How long does each step take?",
        "Are there alternative approaches?",
    ]
    
    def generate(
        self,
        claim: str,
        how_type: str = "mechanism",
    ) -> DialecticalQuestion:
        """Generate a HOW question for a claim."""
        template = self.TEMPLATES.get(how_type, self.TEMPLATES["mechanism"])
        question = template.format(claim=claim)
        
        return DialecticalQuestion(
            mode=QuestioningMode.HOW,
            original_input=claim,
            transformed_question=question,
            follow_ups=self.FOLLOW_UPS,
            potential_answers=[
                "Step-by-step procedure",
                "Mechanistic explanation",
                "Implementation guide",
            ],
            dialectical_value="Reveals operational structure and implementation paths",
            depth=1,
        )


# =============================================================================
# WHAT-IF MODE — HYPOTHETICAL REASONING (Step 77)
# =============================================================================

class WhatIfMode:
    """
    The WHAT-IF mode explores hypothetical scenarios.
    
    Transforms claims into counterfactual explorations.
    """
    
    NEGATION_TEMPLATES = [
        "What if {claim} were not true?",
        "What if the opposite of {claim} were the case?",
        "Imagine {claim} is false — what follows?",
    ]
    
    AMPLIFICATION_TEMPLATES = [
        "What if {claim} were taken to its extreme?",
        "What if {claim} were 10x more significant?",
        "What if everyone believed {claim}?",
    ]
    
    CONSTRAINT_TEMPLATES = [
        "What if {claim} but resources are limited?",
        "What if {claim} but time is constrained?",
        "What if {claim} but stakeholders disagree?",
    ]
    
    FOLLOW_UPS = [
        "What are the second-order effects?",
        "Who would be most affected?",
        "What would remain unchanged?",
        "How would we know?",
        "What risks emerge in this scenario?",
    ]
    
    def generate(
        self,
        claim: str,
        scenario_type: str = "negation",
    ) -> DialecticalQuestion:
        """Generate a WHAT-IF question for a claim."""
        import random
        
        templates = {
            "negation": self.NEGATION_TEMPLATES,
            "amplification": self.AMPLIFICATION_TEMPLATES,
            "constraint": self.CONSTRAINT_TEMPLATES,
        }
        
        template_list = templates.get(scenario_type, self.NEGATION_TEMPLATES)
        template = random.choice(template_list)
        question = template.format(claim=claim)
        
        return DialecticalQuestion(
            mode=QuestioningMode.WHAT_IF,
            original_input=claim,
            transformed_question=question,
            follow_ups=self.FOLLOW_UPS,
            dialectical_value="Explores possibility space and strengthens robustness",
            depth=1,
        )
    
    def generate_all_scenarios(self, claim: str) -> list[DialecticalQuestion]:
        """Generate questions for all scenario types."""
        return [
            self.generate(claim, "negation"),
            self.generate(claim, "amplification"),
            self.generate(claim, "constraint"),
        ]


# =============================================================================
# STEELMAN MODE — OPPOSITION STRENGTHENING (Step 78)
# =============================================================================

class SteelmanMode:
    """
    The STEELMAN mode strengthens opposing positions.
    
    Transforms claims by making the strongest case for opposition.
    """
    
    TEMPLATES = [
        "What is the strongest argument AGAINST {claim}?",
        "If someone disagreed with {claim}, what would be their best point?",
        "What would a thoughtful critic of {claim} say?",
        "Where might {claim} be most vulnerable to criticism?",
        "What evidence would most undermine {claim}?",
    ]
    
    ENHANCEMENT_PROMPTS = [
        "Make this objection even stronger",
        "What additional evidence supports the objection?",
        "How would the objector respond to counterarguments?",
        "What's the strongest version of this criticism?",
    ]
    
    FOLLOW_UPS = [
        "How would you respond to this objection?",
        "Does this objection have merit?",
        "What would change your mind?",
        "Can both positions be partially right?",
        "What synthesis might emerge?",
    ]
    
    def generate(self, claim: str) -> DialecticalQuestion:
        """Generate a STEELMAN question for a claim."""
        import random
        
        template = random.choice(self.TEMPLATES)
        question = template.format(claim=claim)
        
        return DialecticalQuestion(
            mode=QuestioningMode.STEELMAN,
            original_input=claim,
            transformed_question=question,
            follow_ups=self.FOLLOW_UPS,
            potential_answers=[
                "Best opposing argument",
                "Strongest criticism",
                "Most challenging objection",
            ],
            dialectical_value="Strengthens dialectic by honoring opposition",
            depth=1,
        )
    
    def enhance_opposition(self, objection: str, claim: str) -> str:
        """Enhance an objection to make it even stronger."""
        return f"Strengthening the objection that '{objection}' against '{claim}': [enhanced version needed]"


# =============================================================================
# HIDDEN ASSUMPTIONS MODE — REVEALING PREMISES (Step 79)
# =============================================================================

class HiddenAssumptionsMode:
    """
    The HIDDEN ASSUMPTIONS mode reveals implicit premises.
    
    Transforms claims by exposing what must be true for them to hold.
    """
    
    TEMPLATES = [
        "What must be true for {claim} to hold?",
        "What hidden assumptions underlie {claim}?",
        "What is {claim} taking for granted?",
        "What premises are implicit in {claim}?",
        "What beliefs does {claim} presuppose?",
    ]
    
    ASSUMPTION_CATEGORIES = [
        ("ontological", "What exists or is real?"),
        ("epistemological", "What can be known or how?"),
        ("value", "What is good or important?"),
        ("causal", "What causes what?"),
        ("scope", "To whom/what does this apply?"),
        ("temporal", "When does this hold?"),
    ]
    
    FOLLOW_UPS = [
        "Are these assumptions warranted?",
        "What if one assumption were false?",
        "Which assumption is most critical?",
        "Are there unstated value judgments?",
        "What worldview does this presuppose?",
    ]
    
    def generate(self, claim: str) -> DialecticalQuestion:
        """Generate a HIDDEN ASSUMPTIONS question for a claim."""
        import random
        
        template = random.choice(self.TEMPLATES)
        question = template.format(claim=claim)
        
        return DialecticalQuestion(
            mode=QuestioningMode.HIDDEN_ASSUMPTIONS,
            original_input=claim,
            transformed_question=question,
            follow_ups=self.FOLLOW_UPS,
            potential_answers=[
                f"{cat[0]}: {cat[1]}" for cat in self.ASSUMPTION_CATEGORIES[:3]
            ],
            dialectical_value="Reveals foundations that may be questioned",
            depth=1,
        )
    
    def categorize_assumption(self, assumption: str) -> str:
        """Categorize an assumption into one of the categories."""
        assumption_lower = assumption.lower()
        
        for cat, desc in self.ASSUMPTION_CATEGORIES:
            if cat in assumption_lower:
                return cat
        
        # Heuristic categorization
        if any(w in assumption_lower for w in ["exist", "real", "is a"]):
            return "ontological"
        if any(w in assumption_lower for w in ["know", "believe", "true"]):
            return "epistemological"
        if any(w in assumption_lower for w in ["should", "good", "bad", "important"]):
            return "value"
        if any(w in assumption_lower for w in ["cause", "lead", "result"]):
            return "causal"
        
        return "unspecified"


# =============================================================================
# UNIFIED DIALECTICAL QUESTIONER
# =============================================================================

class DialecticalQuestioner:
    """
    Unified interface for all dialectical questioning modes.
    
    Orchestrates the five modes to deeply explore any claim.
    """
    
    def __init__(self):
        self.why_mode = WhyMode()
        self.how_mode = HowMode()
        self.what_if_mode = WhatIfMode()
        self.steelman_mode = SteelmanMode()
        self.hidden_assumptions_mode = HiddenAssumptionsMode()
    
    def question(
        self,
        claim: str,
        mode: QuestioningMode,
        **kwargs,
    ) -> DialecticalQuestion:
        """Generate a question using the specified mode."""
        if mode == QuestioningMode.WHY:
            return self.why_mode.generate(claim, **kwargs)
        elif mode == QuestioningMode.HOW:
            return self.how_mode.generate(claim, **kwargs)
        elif mode == QuestioningMode.WHAT_IF:
            return self.what_if_mode.generate(claim, **kwargs)
        elif mode == QuestioningMode.STEELMAN:
            return self.steelman_mode.generate(claim)
        elif mode == QuestioningMode.HIDDEN_ASSUMPTIONS:
            return self.hidden_assumptions_mode.generate(claim)
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def full_examination(self, claim: str) -> list[DialecticalQuestion]:
        """
        Perform a full dialectical examination using all modes.
        
        Returns one question from each mode.
        """
        return [
            self.why_mode.generate(claim),
            self.how_mode.generate(claim),
            self.what_if_mode.generate(claim),
            self.steelman_mode.generate(claim),
            self.hidden_assumptions_mode.generate(claim),
        ]
    
    def socratic_chain(
        self,
        claim: str,
        max_depth: int = 5,
    ) -> Iterator[DialecticalQuestion]:
        """
        Generate a Socratic chain of WHY questions.
        
        This is the classic 5 Whys technique.
        """
        yield from self.why_mode.chain(claim, max_depth)
    
    def dialectical_spiral(
        self,
        thesis: str,
        antithesis: str,
    ) -> list[DialecticalQuestion]:
        """
        Generate questions that spiral between thesis and antithesis.
        
        Useful for finding synthesis opportunities.
        """
        questions = []
        
        # Hidden assumptions on both sides
        questions.append(self.hidden_assumptions_mode.generate(thesis))
        questions.append(self.hidden_assumptions_mode.generate(antithesis))
        
        # Steelman both sides
        questions.append(self.steelman_mode.generate(thesis))
        questions.append(self.steelman_mode.generate(antithesis))
        
        # What-if on synthesis
        potential_synthesis = f"both '{thesis}' and '{antithesis}' are partially correct"
        questions.append(self.what_if_mode.generate(potential_synthesis, "amplification"))
        
        return questions


# =============================================================================
# INTEGRATION WITH SEMANTIC BRIDGE
# =============================================================================

def integrate_with_flow(
    questioner: DialecticalQuestioner,
    claim: str,
    current_depth: int = 0,
) -> dict[str, Any]:
    """
    Integrate dialectical questioning with semantic flow tracking.
    
    Returns a structured exploration result.
    """
    examination = questioner.full_examination(claim)
    
    return {
        "claim": claim,
        "depth": current_depth,
        "questions": [
            {
                "mode": q.mode.value,
                "question": q.transformed_question,
                "value": q.dialectical_value,
            }
            for q in examination
        ],
        "recommended_next": QuestioningMode.WHY if current_depth == 0 else QuestioningMode.HIDDEN_ASSUMPTIONS,
    }
