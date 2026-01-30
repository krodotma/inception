"""
Taxonomic Types for Phase 2 — Schema.org Grounded

Defines the realistic concept relationships per plan_v2:
- Domain (schema:Organization)
- Idea (schema:CreativeWork with thesis/antithesis/synthesis)
- Project (schema:Project)
- Contact (schema:Person/Organization)

Plus dialectical relations and InceptionContext.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Schema.org Type Mappings
# =============================================================================

class SchemaOrgType(str, Enum):
    """Schema.org types mapped to Inception concepts."""
    
    # Core types
    THING = "schema:Thing"
    PERSON = "schema:Person"
    ORGANIZATION = "schema:Organization"
    
    # Creative types
    CREATIVE_WORK = "schema:CreativeWork"
    HOW_TO = "schema:HowTo"
    HOW_TO_STEP = "schema:HowToStep"
    
    # Action/Event types
    ACTION = "schema:Action"
    EVENT = "schema:Event"
    
    # Tech types
    SOFTWARE_SOURCE_CODE = "schema:SoftwareSourceCode"
    WEB_API = "schema:WebAPI"
    
    # Knowledge types
    CLAIM = "schema:Claim"
    CLAIM_REVIEW = "schema:ClaimReview"


# =============================================================================
# Extended Node Kinds (Phase 2)
# =============================================================================

class NodeKindV2(IntEnum):
    """Extended node kinds for Phase 2 taxonomic types."""
    
    # Existing (from keys.py)
    ENTITY = 1
    CONCEPT = 2
    CLAIM = 3
    PROCEDURE = 4
    DECISION = 5
    ACTION = 6
    QUESTION = 7
    GAP = 8
    SIGN = 9
    
    # Phase 2 additions
    DOMAIN = 20      # schema:Organization - knowledge domain
    IDEA = 21        # schema:CreativeWork - thesis/antithesis/synthesis
    PROJECT = 22     # schema:Project - active work context
    CONTACT = 23     # schema:Person - people/agents
    DIALECTIC = 24   # schema:Claim - thesis/antithesis pair
    SKILL = 25       # schema:Action - executable skill


class RelationType(IntEnum):
    """Extended relation types for dialectical reasoning."""
    
    # Existing structural (from keys.py EdgeType)
    MENTIONS = 1
    CONTAINS = 2
    DERIVED_FROM = 3
    
    # Existing semantic
    SUPPORTS = 10
    CONTRADICTS = 11
    REQUIRES = 12
    DEPENDS_ON = 13
    
    # Existing temporal
    TEMPORAL_BEFORE = 20
    TEMPORAL_AFTER = 21
    CONCURRENT = 22
    
    # Existing identity
    SAME_AS = 30
    SIMILAR_TO = 31
    
    # Existing gap
    BLOCKS = 40
    RESOLVES = 41
    
    # Phase 2 additions: Classification
    IS_A = 50        # Classification (instance → category)
    HAS_A = 51       # Composition (whole → part)
    PART_OF = 52     # Inverse of HAS_A
    
    # Phase 2 additions: Causal
    CAUSES = 60      # Direct causation
    ENABLES = 61     # Enabling condition
    PREVENTS = 62    # Prevention
    
    # Phase 2 additions: Dialectical
    THESIS_OF = 70        # Thesis for an idea
    ANTITHESIS_OF = 71    # Antithesis for an idea
    SYNTHESIS_OF = 72     # Synthesis resolving thesis/antithesis
    SUPERSEDES = 73       # New knowledge replaces old


# =============================================================================
# Domain Type (schema:Organization)
# =============================================================================

class DomainPayload(BaseModel):
    """
    Payload for a knowledge domain.
    
    Maps to schema:Organization — a coherent area of knowledge.
    Examples: "OAuth 2.0", "Frontend Development", "Machine Learning"
    """
    
    name: str = Field(description="Human-readable domain name")
    schema_type: SchemaOrgType = SchemaOrgType.ORGANIZATION
    
    # Hierarchy
    parent_nid: int | None = Field(default=None, description="Parent domain NID")
    children_nids: list[int] = Field(default_factory=list, description="Child domain NIDs")
    
    # Statistics
    claims_count: int = Field(default=0, description="Number of claims in domain")
    procedures_count: int = Field(default=0, description="Number of procedures")
    ideas_count: int = Field(default=0, description="Number of ideas")
    
    # Metadata
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    external_refs: list[str] = Field(default_factory=list, description="URLs to authoritative sources")
    
    # Pre-population tracking
    seeding_status: Literal["unseeded", "partial", "seeded"] = "unseeded"
    seeded_at: datetime | None = None


# =============================================================================
# Idea Type (schema:CreativeWork with Dialectical Structure)
# =============================================================================

class DialecticalState(str, Enum):
    """State of dialectical resolution."""
    
    THESIS_ONLY = "thesis_only"           # Only thesis stated
    ANTITHESIS_PROPOSED = "antithesis_proposed"  # Opposition identified
    SYNTHESIS_PENDING = "synthesis_pending"      # Awaiting synthesis
    RESOLVED = "resolved"                 # Synthesis achieved
    UNRESOLVABLE = "unresolvable"         # Fundamental disagreement


class IdeaPayload(BaseModel):
    """
    Payload for an idea with dialectical structure.
    
    Maps to schema:CreativeWork — a concept under active development.
    Supports thesis/antithesis/synthesis for reasoning.
    """
    
    name: str = Field(description="Idea name/title")
    schema_type: SchemaOrgType = SchemaOrgType.CREATIVE_WORK
    
    # Domain context
    domain_nid: int = Field(description="Parent domain NID")
    
    # Dialectical structure
    thesis: str | None = Field(default=None, description="Primary position")
    antithesis: str | None = Field(default=None, description="Opposing position")
    synthesis: str | None = Field(default=None, description="Resolution/integration")
    dialectical_state: DialecticalState = DialecticalState.THESIS_ONLY
    
    # Supporting evidence
    thesis_evidence_nids: list[int] = Field(default_factory=list)
    antithesis_evidence_nids: list[int] = Field(default_factory=list)
    synthesis_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    resolution_method: Literal["consensus", "evidence", "authority", "experimental", None] = None
    
    # Uncertainty tracking
    epistemic_gaps: list[str] = Field(default_factory=list, description="Knowledge we need")
    aleatoric_ambiguities: list[str] = Field(default_factory=list, description="Inherent ambiguities")


# =============================================================================
# Project Type (schema:Project)
# =============================================================================

class ProjectPayload(BaseModel):
    """
    Payload for a project — active work context.
    
    Links ideas, contacts, and procedures together.
    """
    
    name: str = Field(description="Project name")
    schema_type: Literal["schema:Project"] = "schema:Project"
    
    # Context links
    domain_nid: int = Field(description="Primary domain")
    related_domains: list[int] = Field(default_factory=list)
    
    # Purpose (Entelexis alignment)
    goal: str = Field(description="Project goal")
    entelexis_phase: Literal["potential", "developing", "actualized"] = "potential"
    
    # Resources
    idea_nids: list[int] = Field(default_factory=list, description="Ideas in this project")
    contact_nids: list[int] = Field(default_factory=list, description="People/agents involved")
    procedure_nids: list[int] = Field(default_factory=list, description="Procedures used")
    skill_nids: list[int] = Field(default_factory=list, description="Skills available")
    
    # Status
    status: Literal["planning", "active", "paused", "completed", "archived"] = "planning"
    priority: int = Field(default=0, ge=0, le=10)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Blocking gaps
    blocking_gap_nids: list[int] = Field(default_factory=list, description="Gaps blocking progress")


# =============================================================================
# Contact Type (schema:Person or schema:Organization)
# =============================================================================

class ContactPayload(BaseModel):
    """
    Payload for a contact — person or agent.
    
    Maps to schema:Person or schema:Organization.
    """
    
    name: str
    schema_type: Literal["schema:Person", "schema:Organization"] = "schema:Person"
    contact_type: Literal["human", "agent", "organization"] = "human"
    
    # For agents
    agent_id: str | None = Field(default=None, description="Agent persona ID (e.g., 'DIALECTICA')")
    agent_capabilities: list[str] = Field(default_factory=list)
    
    # For humans/orgs
    email: str | None = None
    url: str | None = None
    affiliation: str | None = None
    
    # Authority/trust
    expertise_domains: list[int] = Field(default_factory=list, description="Domain NIDs of expertise")
    trust_score: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Project involvement
    project_nids: list[int] = Field(default_factory=list)


# =============================================================================
# InceptionContext — The Central Context Object
# =============================================================================

class EntelexisState(BaseModel):
    """State tracking for Entelexis (purpose actualization)."""
    
    phase: Literal["potential", "developing", "actualized", "suspended"] = "potential"
    potential_id: str | None = Field(default=None, description="ID of the potential being actualized")
    form_signature: str | None = Field(default=None, description="Expected form when actualized")
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    blockers: list[str] = Field(default_factory=list)


class Goal(BaseModel):
    """A goal in the goal stack."""
    
    id: str
    description: str
    priority: int = Field(default=0, ge=0, le=10)
    blocking_gap_nids: list[int] = Field(default_factory=list)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    parent_goal_id: str | None = None


class AgentState(BaseModel):
    """State of an active agent."""
    
    agent_id: str
    status: Literal["idle", "active", "waiting", "error"] = "idle"
    current_task: str | None = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)


class InceptionContext(BaseModel):
    """
    The central context object tracking all active state.
    
    This is passed through all skill executions and agent interactions.
    """
    
    # Identity
    context_id: str = Field(description="Unique context ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Entelexis (Purpose Tracking)
    entelexis: EntelexisState = Field(default_factory=EntelexisState)
    current_purpose: str = ""
    goal_stack: list[Goal] = Field(default_factory=list)
    
    # Resource Tracking
    active_domain_nids: list[int] = Field(default_factory=list, description="Active knowledge domains")
    active_idea_nids: list[int] = Field(default_factory=list, description="In-flight ideas")
    active_project_nids: list[int] = Field(default_factory=list, description="Active projects")
    active_contact_nids: list[int] = Field(default_factory=list, description="Relevant contacts")
    
    # Agent State
    agents: dict[str, AgentState] = Field(default_factory=dict, description="Active agents")
    mesh_topology: Literal["star", "peer", "hierarchical"] = "star"
    coordinator_agent: str = "ARCHON"
    
    # Dialectical State  
    current_thesis: str | None = None
    current_antithesis: str | None = None
    synthesis_candidates: list[str] = Field(default_factory=list)
    socratic_depth: int = 0
    
    # Uncertainty State
    epistemic_gaps: list[str] = Field(default_factory=list, description="Active epistemic gaps")
    aleatoric_expansions: list[str] = Field(default_factory=list, description="Active meaning expansions")
    
    # Session tracking
    referenced_terms: list[str] = Field(default_factory=list, description="Terms referenced in session")
    session_start: datetime = Field(default_factory=datetime.utcnow)
    turn_count: int = 0


# =============================================================================
# Interpretation Surface (from knowledge_seeding_strategy.md)
# =============================================================================

class InterpretationSurface(BaseModel):
    """
    A point where neural and symbolic processing meet.
    
    Surfaces are the interpretation points in the knowledge flow.
    """
    
    name: str
    input_type: str  # e.g., "str", "Claim", "Gap"
    output_type: str  # e.g., "EnrichedIntent", "Verified", "Expanded"
    responsible_agent: str  # e.g., "DIALECTICA", "FUSION"
    learning_signal: str  # e.g., "user_corrections", "kg_consistency"
    
    # Neural components
    embedding_model: str = "all-MiniLM-L6-v2"
    classifier: str | None = None
    
    # Symbolic components
    type_constraints: list[str] = Field(default_factory=list, description="schema.org types accepted")
    inference_rules: list[str] = Field(default_factory=list, description="AUOM laws applied")
    
    # Metrics
    throughput_target: float = Field(default=100.0, description="Target ops/second")
    accuracy_target: float = Field(default=0.90, description="Target accuracy")


# =============================================================================
# Pre-defined Interpretation Surfaces
# =============================================================================

PROMPT_INTENT_SURFACE = InterpretationSurface(
    name="prompt_to_intent",
    input_type="str",
    output_type="EnrichedIntent",
    responsible_agent="DIALECTICA",
    learning_signal="user_corrections",
    type_constraints=["schema:Action", "schema:SearchAction", "schema:AskAction"],
    inference_rules=["AUOM.Lawfulness", "AUOM.Observability"],
)

CLAIM_VERIFICATION_SURFACE = InterpretationSurface(
    name="claim_to_verification",
    input_type="Claim",
    output_type="VerifiedClaim",
    responsible_agent="FUSION",
    learning_signal="kg_consistency",
    classifier="claim_verifier_v1",
    type_constraints=["schema:Claim", "schema:ClaimReview"],
    inference_rules=["AUOM.Lawfulness", "AUOM.Uniqueness"],
)

GAP_CLARIFICATION_SURFACE = InterpretationSurface(
    name="gap_to_clarification",
    input_type="Gap",
    output_type="EnrichedGap",
    responsible_agent="DIALECTICA",
    learning_signal="fill_success_rate",
    type_constraints=["schema:Question"],
    inference_rules=["AUOM.Observability", "AUOM.Measurability"],
)


# =============================================================================
# Utility: Type Registry
# =============================================================================

TAXONOMIC_TYPE_REGISTRY = {
    NodeKindV2.DOMAIN: {
        "payload_class": DomainPayload,
        "schema_org": SchemaOrgType.ORGANIZATION,
        "description": "Knowledge domain with hierarchical structure",
    },
    NodeKindV2.IDEA: {
        "payload_class": IdeaPayload,
        "schema_org": SchemaOrgType.CREATIVE_WORK,
        "description": "Concept with thesis/antithesis/synthesis",
    },
    NodeKindV2.PROJECT: {
        "payload_class": ProjectPayload,
        "schema_org": "schema:Project",
        "description": "Active work context linking resources",
    },
    NodeKindV2.CONTACT: {
        "payload_class": ContactPayload,
        "schema_org": SchemaOrgType.PERSON,
        "description": "Person or agent with expertise",
    },
}
