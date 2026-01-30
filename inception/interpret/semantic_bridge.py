"""
Semantic Bridge Layer — Bohm's Rheomode Implementation

Based on David Bohm's "rheomode" (flowing mode) of language where:
- Meaning flows continuously (not frozen in static definitions)
- Verbs become primary (processes vs objects)
- Language participates in thought (not just describes it)

Core principle: "The word does not merely denote a meaning;
it is itself a movement of mind that IS the meaning."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field


# =============================================================================
# BOHM RHEOMODE PHILOSOPHY (Step 66)
# =============================================================================
"""
RHEOMODE: A Mode of Language for Wholeness

David Bohm proposed that conventional language fragments thought through:
1. Subject-verb-object structure creates false divisions
2. Nouns freeze processes into static objects
3. Meanings become fixed instead of flowing

His solution — the Rheomode (from Greek "rheo" = to flow):
1. Verbs become gerunds (observe → observing)
2. Nouns become verbified (knowledge → knowing)
3. Meaning flows contextually, not fixed

IMPLEMENTATION STRATEGY:
- Interpret prompts through flowing meaning lens
- Track semantic flow across conversation
- Allow meanings to evolve without fragmentation
- Support wholeness through dialectical integration

KEY RHEOMODE TRANSFORMATIONS:
- "The observation" → "the act of observing"
- "This thought" → "this movement of thought"
- "The concept" → "the conceiving"
- "I know X" → "knowing is happening"
"""


class RheoLevel(str, Enum):
    """Levels of rheomomde transformation."""
    
    LITERAL = "literal"           # Surface meaning only
    GERUNDIVE = "gerundive"       # Noun→gerund transformation
    PROCESSUAL = "processual"     # Full process orientation
    PARTICIPATORY = "participatory"  # Speaker as participant in meaning


class MeaningFlow(str, Enum):
    """Direction of meaning flow."""
    
    EXPANDING = "expanding"       # Meaning grows with context
    CONTRACTING = "contracting"   # Meaning focuses/narrows
    SPIRALING = "spiraling"       # Dialectical circulation
    CRYSTALLIZING = "crystallizing"  # Resolution forming


# =============================================================================
# INTERPRETATION LAYER ARCHITECTURE (Step 67)
# =============================================================================

@dataclass
class SemanticFlow:
    """
    A flow of meaning through the interpretation layer.
    
    Tracks how meaning evolves across a conversation.
    """
    
    flow_id: str
    initial_prompt: str
    current_meaning: str
    
    # Flow state
    level: RheoLevel = RheoLevel.LITERAL
    direction: MeaningFlow = MeaningFlow.EXPANDING
    
    # Evolution history
    transformations: list[dict[str, Any]] = field(default_factory=list)
    
    # Uncertainty tracking
    epistemic_gaps: list[str] = field(default_factory=list)
    aleatoric_expansions: list[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_transformation(self, transform_type: str, before: str, after: str) -> None:
        """Record a meaning transformation."""
        self.transformations.append({
            "type": transform_type,
            "before": before,
            "after": after,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.current_meaning = after
        self.updated_at = datetime.utcnow()


class InterpretationSurface(BaseModel):
    """
    A point where neural and symbolic processing meet.
    
    Surfaces are where raw input becomes structured meaning.
    """
    
    name: str
    input_type: str  # e.g., "prompt", "claim", "gap"
    output_type: str  # e.g., "meaning", "verified", "expanded"
    
    # Processing components
    responsible_agent: str = "DIALECTICA"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Rheomode settings
    rheo_level: RheoLevel = RheoLevel.GERUNDIVE
    allow_meaning_flow: bool = True


# =============================================================================
# PROMPT → MEANING EXTRACTOR (Step 68)
# =============================================================================

@dataclass
class ExtractedMeaning:
    """Extracted meaning from a prompt."""
    
    original: str
    core_intent: str                          # What the user wants
    surface_meaning: str                      # Literal interpretation
    deeper_meaning: str | None = None         # Contextual interpretation
    
    # Rheomode analysis
    frozen_concepts: list[str] = field(default_factory=list)  # Nouns to unfreeze
    implicit_processes: list[str] = field(default_factory=list)  # Hidden verbs
    
    # Uncertainty
    confidence: float = 0.5
    clarification_needed: list[str] = field(default_factory=list)


class MeaningExtractor:
    """
    Extracts meaning from prompts using Rheomode principles.
    
    Transforms static language into flowing meaning.
    """
    
    # Common static→process transformations
    NOUN_TO_GERUND = {
        "thought": "thinking",
        "knowledge": "knowing",
        "understanding": "understanding",  # already gerund
        "explanation": "explaining",
        "analysis": "analyzing",
        "creation": "creating",
        "decision": "deciding",
        "observation": "observing",
        "perception": "perceiving",
        "belief": "believing",
        "definition": "defining",
        "concept": "conceiving",
        "memory": "remembering",
    }
    
    # Intent patterns
    INTENT_PATTERNS = {
        "explain": "seeks understanding of process",
        "define": "seeks formal boundary",
        "compare": "seeks relational meaning",
        "evaluate": "seeks value judgment",
        "create": "seeks actualization",
        "find": "seeks discovery",
        "fix": "seeks correction",
        "improve": "seeks enhancement",
        "understand": "seeks deep knowing",
    }
    
    def extract_meaning(self, prompt: str) -> ExtractedMeaning:
        """
        Extract meaning from a prompt.
        
        Applies Rheomode transformations to reveal flowing meaning.
        """
        prompt_lower = prompt.lower()
        
        # Identify frozen concepts (nouns that could be processes)
        frozen = []
        implicit = []
        for noun, gerund in self.NOUN_TO_GERUND.items():
            if noun in prompt_lower:
                frozen.append(noun)
                implicit.append(gerund)
        
        # Identify primary intent
        core_intent = "seeks information"  # default
        for keyword, intent in self.INTENT_PATTERNS.items():
            if keyword in prompt_lower:
                core_intent = intent
                break
        
        # Generate surface meaning
        surface = f"User {core_intent}: {prompt[:100]}"
        
        # Generate deeper meaning by unfreezing concepts
        deeper = None
        if frozen:
            deeper = f"This is about the process of {', '.join(implicit[:3])}"
        
        # Identify what needs clarification
        clarification = []
        if "?" not in prompt:
            # Not a question — might need to confirm intent
            clarification.append("Confirm this is the intended direction?")
        if len(prompt.split()) > 50:  # Long prompt
            clarification.append("Which aspect should be prioritized?")
        
        return ExtractedMeaning(
            original=prompt,
            core_intent=core_intent,
            surface_meaning=surface,
            deeper_meaning=deeper,
            frozen_concepts=frozen,
            implicit_processes=implicit,
            confidence=0.7 if deeper else 0.5,
            clarification_needed=clarification,
        )


# =============================================================================
# MEANING → ENRICHED PROMPT GENERATOR (Step 69)
# =============================================================================

class EnrichedPrompt(BaseModel):
    """An enriched prompt with Rheomode context."""
    
    original: str
    enriched: str
    rheo_level: RheoLevel
    context_injections: list[str] = Field(default_factory=list)
    flow_state: MeaningFlow = MeaningFlow.EXPANDING


class EnrichmentGenerator:
    """
    Generates enriched prompts by adding Rheomode context.
    """
    
    CONTEXT_TEMPLATES = {
        "process_focus": "Consider this as an ongoing process rather than static state: {content}",
        "wholeness": "Viewing this holistically, including implicit connections: {content}",
        "dialectical": "Exploring both perspectives before synthesis: {content}",
        "participatory": "As active participant in this meaning: {content}",
    }
    
    def enrich(
        self,
        meaning: ExtractedMeaning,
        rheo_level: RheoLevel = RheoLevel.GERUNDIVE,
    ) -> EnrichedPrompt:
        """
        Enrich extracted meaning into an enhanced prompt.
        """
        injections = []
        enriched = meaning.original
        
        if rheo_level == RheoLevel.GERUNDIVE and meaning.implicit_processes:
            # Add process focus
            process_note = f"[Note: This involves {', '.join(meaning.implicit_processes[:3])}]"
            injections.append(process_note)
            enriched = f"{meaning.original}\n{process_note}"
        
        elif rheo_level == RheoLevel.PROCESSUAL:
            # Full process orientation
            template = self.CONTEXT_TEMPLATES["process_focus"]
            enriched = template.format(content=meaning.original)
            injections.append("Applied process orientation")
        
        elif rheo_level == RheoLevel.PARTICIPATORY:
            # Participatory framing
            template = self.CONTEXT_TEMPLATES["participatory"]
            enriched = template.format(content=meaning.original)
            injections.append("Applied participatory framing")
        
        return EnrichedPrompt(
            original=meaning.original,
            enriched=enriched,
            rheo_level=rheo_level,
            context_injections=injections,
        )


# =============================================================================
# CLARIFICATION HANDLERS (Steps 70-72)
# =============================================================================

@dataclass
class ClarificationRequest:
    """A request for clarification."""
    
    clarification_type: str  # "meaning", "intent", "implications"
    question: str
    trigger: str             # What triggered the clarification need
    options: list[str] = field(default_factory=list)


class ClarificationHandler:
    """
    Handles clarification requests using Rheomode questioning.
    """
    
    # Step 70: "What did you mean by X?"
    def clarify_meaning(self, term: str, context: str) -> ClarificationRequest:
        """Generate a meaning clarification question."""
        return ClarificationRequest(
            clarification_type="meaning",
            question=f"When you say '{term}', are you referring to the process of {self._verbify(term)}, or to a specific instance/definition?",
            trigger=term,
            options=[
                f"The process of {self._verbify(term)}",
                f"A specific definition of '{term}'",
                f"An example of '{term}'",
            ],
        )
    
    # Step 71: "Clarify intent"
    def clarify_intent(self, action: str, context: str) -> ClarificationRequest:
        """Generate an intent clarification question."""
        return ClarificationRequest(
            clarification_type="intent",
            question=f"To help me understand: when you want to '{action}', what outcome are you looking towards?",
            trigger=action,
            options=[
                "I want to understand deeply",
                "I want to take action",
                "I want to evaluate/compare",
                "I want to create something new",
            ],
        )
    
    # Step 72: "Explore implications"
    def explore_implications(self, claim: str) -> ClarificationRequest:
        """Generate an implications exploration question."""
        return ClarificationRequest(
            clarification_type="implications",
            question=f"Considering '{claim}': should we explore what this implies, what it assumes, or how it connects to other ideas?",
            trigger=claim,
            options=[
                "Explore implications (what follows from this)",
                "Examine assumptions (what must be true)",
                "Find connections (related ideas)",
                "All of the above",
            ],
        )
    
    def _verbify(self, noun: str) -> str:
        """Convert a noun to its process form."""
        verbifications = {
            "thought": "thinking",
            "knowledge": "knowing",
            "code": "coding",
            "design": "designing",
            "analysis": "analyzing",
            "plan": "planning",
        }
        return verbifications.get(noun.lower(), f"{noun}ing")


# =============================================================================
# FLOW STATE TRACKING (Step 73)
# =============================================================================

@dataclass
class FlowState:
    """
    Tracks the flow state of meaning in a conversation.
    
    Implements KINESIS-style motion tracking for meaning.
    """
    
    session_id: str
    
    # Current flow
    active_flows: list[SemanticFlow] = field(default_factory=list)
    
    # Direction tracking
    overall_direction: MeaningFlow = MeaningFlow.EXPANDING
    momentum: float = 0.5  # 0=stalled, 1=strong flow
    
    # Dialectical state
    thesis_active: str | None = None
    antithesis_active: str | None = None
    synthesis_forming: bool = False
    
    # Turn tracking
    turn_count: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    def update_momentum(self, delta: float) -> None:
        """Update the flow momentum."""
        self.momentum = max(0.0, min(1.0, self.momentum + delta))
        self.last_activity = datetime.utcnow()
    
    def enter_dialectical(self, thesis: str) -> None:
        """Enter dialectical mode with a thesis."""
        self.thesis_active = thesis
        self.overall_direction = MeaningFlow.SPIRALING
        self.momentum = 0.8
    
    def propose_antithesis(self, antithesis: str) -> None:
        """Propose an antithesis."""
        self.antithesis_active = antithesis
        self.synthesis_forming = False
    
    def begin_synthesis(self) -> None:
        """Begin forming a synthesis."""
        self.synthesis_forming = True
        self.overall_direction = MeaningFlow.CRYSTALLIZING


# =============================================================================
# INTERPRETATION ANNOTATIONS (Step 74)
# =============================================================================

@dataclass
class InterpretationAnnotation:
    """
    An interpretation annotation added by an agent.
    """
    
    agent_id: str
    annotation_type: str  # "meaning", "context", "caution", "suggestion"
    content: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AgentAnnotator:
    """
    Manages interpretation annotations from agents.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.annotations: list[InterpretationAnnotation] = []
    
    def add_meaning_annotation(self, content: str, confidence: float = 0.7) -> InterpretationAnnotation:
        """Add a meaning interpretation annotation."""
        ann = InterpretationAnnotation(
            agent_id=self.agent_id,
            annotation_type="meaning",
            content=content,
            confidence=confidence,
        )
        self.annotations.append(ann)
        return ann
    
    def add_context_annotation(self, content: str, confidence: float = 0.8) -> InterpretationAnnotation:
        """Add a contextual annotation."""
        ann = InterpretationAnnotation(
            agent_id=self.agent_id,
            annotation_type="context",
            content=content,
            confidence=confidence,
        )
        self.annotations.append(ann)
        return ann
    
    def add_caution_annotation(self, content: str, confidence: float = 0.9) -> InterpretationAnnotation:
        """Add a cautionary annotation."""
        ann = InterpretationAnnotation(
            agent_id=self.agent_id,
            annotation_type="caution",
            content=content,
            confidence=confidence,
        )
        self.annotations.append(ann)
        return ann


# =============================================================================
# UNIFIED SEMANTIC BRIDGE
# =============================================================================

class SemanticBridge:
    """
    The unified semantic bridge implementing Bohm's Rheomode.
    
    Orchestrates meaning extraction, enrichment, and flow tracking.
    """
    
    def __init__(self, session_id: str):
        from uuid import uuid4
        self.session_id = session_id
        self.extractor = MeaningExtractor()
        self.enricher = EnrichmentGenerator()
        self.clarifier = ClarificationHandler()
        self.flow_state = FlowState(session_id=session_id)
        self.annotators: dict[str, AgentAnnotator] = {}
    
    def process_prompt(
        self,
        prompt: str,
        rheo_level: RheoLevel = RheoLevel.GERUNDIVE,
    ) -> tuple[EnrichedPrompt, list[ClarificationRequest]]:
        """
        Process a prompt through the semantic bridge.
        
        Returns enriched prompt and any clarification requests.
        """
        # Extract meaning
        meaning = self.extractor.extract_meaning(prompt)
        
        # Generate enriched prompt
        enriched = self.enricher.enrich(meaning, rheo_level)
        
        # Check if clarification needed
        clarifications = []
        for item in meaning.clarification_needed:
            clarifications.append(ClarificationRequest(
                clarification_type="general",
                question=item,
                trigger="automatic",
            ))
        
        # Update flow state
        self.flow_state.turn_count += 1
        self.flow_state.update_momentum(0.1)
        
        return enriched, clarifications
    
    def register_agent(self, agent_id: str) -> AgentAnnotator:
        """Register an agent for annotations."""
        if agent_id not in self.annotators:
            self.annotators[agent_id] = AgentAnnotator(agent_id)
        return self.annotators[agent_id]
    
    def get_flow_summary(self) -> dict[str, Any]:
        """Get a summary of current flow state."""
        return {
            "session_id": self.session_id,
            "turn_count": self.flow_state.turn_count,
            "direction": self.flow_state.overall_direction.value,
            "momentum": self.flow_state.momentum,
            "dialectical": {
                "thesis": self.flow_state.thesis_active,
                "antithesis": self.flow_state.antithesis_active,
                "synthesizing": self.flow_state.synthesis_forming,
            },
            "annotations_count": sum(len(a.annotations) for a in self.annotators.values()),
        }
