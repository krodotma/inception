"""
Unit tests for db/taxonomic_types.py

Tests for Schema.org grounded taxonomic types:
- Enums: SchemaOrgType, NodeKindV2, RelationType, DialecticalState
- Pydantic models: DomainPayload, IdeaPayload, ProjectPayload, ContactPayload
- Context: InceptionContext, EntelexisState, Goal, AgentState
- Surfaces: InterpretationSurface
"""

import pytest
from datetime import datetime

from inception.db.taxonomic_types import (
    # Enums
    SchemaOrgType,
    NodeKindV2,
    RelationType,
    DialecticalState,
    # Payloads
    DomainPayload,
    IdeaPayload,
    ProjectPayload,
    ContactPayload,
    # Context
    EntelexisState,
    Goal,
    AgentState,
    InceptionContext,
    # Surfaces
    InterpretationSurface,
    PROMPT_INTENT_SURFACE,
    CLAIM_VERIFICATION_SURFACE,
    GAP_CLARIFICATION_SURFACE,
    # Registry
    TAXONOMIC_TYPE_REGISTRY,
)


# =============================================================================
# Test: Enums
# =============================================================================

class TestSchemaOrgType:
    """Tests for SchemaOrgType enum."""
    
    def test_core_types(self):
        """Test core schema.org type values."""
        assert SchemaOrgType.THING.value == "schema:Thing"
        assert SchemaOrgType.PERSON.value == "schema:Person"
        assert SchemaOrgType.ORGANIZATION.value == "schema:Organization"
    
    def test_creative_types(self):
        """Test creative schema.org type values."""
        assert SchemaOrgType.CREATIVE_WORK.value == "schema:CreativeWork"
        assert SchemaOrgType.HOW_TO.value == "schema:HowTo"
        assert SchemaOrgType.HOW_TO_STEP.value == "schema:HowToStep"
    
    def test_knowledge_types(self):
        """Test knowledge-related types."""
        assert SchemaOrgType.CLAIM.value == "schema:Claim"
        assert SchemaOrgType.CLAIM_REVIEW.value == "schema:ClaimReview"


class TestNodeKindV2:
    """Tests for NodeKindV2 enum."""
    
    def test_existing_kinds(self):
        """Test existing node kinds from Phase 1."""
        assert NodeKindV2.ENTITY == 1
        assert NodeKindV2.CONCEPT == 2
        assert NodeKindV2.CLAIM == 3
        assert NodeKindV2.PROCEDURE == 4
        assert NodeKindV2.GAP == 8
    
    def test_phase2_kinds(self):
        """Test Phase 2 node kinds."""
        assert NodeKindV2.DOMAIN == 20
        assert NodeKindV2.IDEA == 21
        assert NodeKindV2.PROJECT == 22
        assert NodeKindV2.CONTACT == 23
        assert NodeKindV2.DIALECTIC == 24
        assert NodeKindV2.SKILL == 25


class TestRelationType:
    """Tests for RelationType enum."""
    
    def test_structural_relations(self):
        """Test structural relation values."""
        assert RelationType.MENTIONS == 1
        assert RelationType.CONTAINS == 2
        assert RelationType.DERIVED_FROM == 3
    
    def test_semantic_relations(self):
        """Test semantic relation values."""
        assert RelationType.SUPPORTS == 10
        assert RelationType.CONTRADICTS == 11
        assert RelationType.REQUIRES == 12
    
    def test_dialectical_relations(self):
        """Test dialectical relation values."""
        assert RelationType.THESIS_OF == 70
        assert RelationType.ANTITHESIS_OF == 71
        assert RelationType.SYNTHESIS_OF == 72
        assert RelationType.SUPERSEDES == 73


class TestDialecticalState:
    """Tests for DialecticalState enum."""
    
    def test_all_states(self):
        """Test all dialectical state values."""
        assert DialecticalState.THESIS_ONLY.value == "thesis_only"
        assert DialecticalState.ANTITHESIS_PROPOSED.value == "antithesis_proposed"
        assert DialecticalState.SYNTHESIS_PENDING.value == "synthesis_pending"
        assert DialecticalState.RESOLVED.value == "resolved"
        assert DialecticalState.UNRESOLVABLE.value == "unresolvable"


# =============================================================================
# Test: Payload Models
# =============================================================================

class TestDomainPayload:
    """Tests for DomainPayload model."""
    
    def test_domain_creation(self):
        """Test creating a domain."""
        domain = DomainPayload(name="Machine Learning")
        
        assert domain.name == "Machine Learning"
        assert domain.schema_type == SchemaOrgType.ORGANIZATION
        assert domain.seeding_status == "unseeded"
    
    def test_domain_with_hierarchy(self):
        """Test domain with parent/children."""
        domain = DomainPayload(
            name="Deep Learning",
            parent_nid=100,
            children_nids=[101, 102, 103],
        )
        
        assert domain.parent_nid == 100
        assert len(domain.children_nids) == 3
    
    def test_domain_statistics(self):
        """Test domain statistics fields."""
        domain = DomainPayload(
            name="OAuth 2.0",
            claims_count=50,
            procedures_count=10,
            ideas_count=5,
        )
        
        assert domain.claims_count == 50
        assert domain.procedures_count == 10
        assert domain.ideas_count == 5


class TestIdeaPayload:
    """Tests for IdeaPayload model."""
    
    def test_idea_creation(self):
        """Test creating an idea."""
        idea = IdeaPayload(
            name="Use microservices for scalability",
            domain_nid=100,
        )
        
        assert idea.name == "Use microservices for scalability"
        assert idea.dialectical_state == DialecticalState.THESIS_ONLY
    
    def test_idea_with_dialectics(self):
        """Test idea with thesis/antithesis/synthesis."""
        idea = IdeaPayload(
            name="Architecture choice",
            domain_nid=100,
            thesis="Microservices provide better scaling",
            antithesis="Monoliths are simpler to develop",
            synthesis="Use modular monolith with service boundaries",
            dialectical_state=DialecticalState.RESOLVED,
            synthesis_confidence=0.85,
        )
        
        assert idea.thesis is not None
        assert idea.antithesis is not None
        assert idea.synthesis is not None
        assert idea.dialectical_state == DialecticalState.RESOLVED
        assert idea.synthesis_confidence == 0.85


class TestProjectPayload:
    """Tests for ProjectPayload model."""
    
    def test_project_creation(self):
        """Test creating a project."""
        project = ProjectPayload(
            name="Inception Test Suite",
            domain_nid=1,
            goal="Achieve 100% code coverage",
        )
        
        assert project.name == "Inception Test Suite"
        assert project.status == "planning"
        assert project.entelexis_phase == "potential"
    
    def test_project_with_resources(self):
        """Test project with linked resources."""
        project = ProjectPayload(
            name="Knowledge Graph Project",
            domain_nid=1,
            goal="Build complete knowledge extraction",
            idea_nids=[10, 11, 12],
            contact_nids=[20, 21],
            procedure_nids=[30, 31, 32],
            skill_nids=[40],
            status="active",
            priority=8,
        )
        
        assert len(project.idea_nids) == 3
        assert len(project.contact_nids) == 2
        assert project.status == "active"
        assert project.priority == 8


class TestContactPayload:
    """Tests for ContactPayload model."""
    
    def test_human_contact(self):
        """Test creating a human contact."""
        contact = ContactPayload(
            name="Alice Smith",
            email="alice@example.com",
            affiliation="Tech Corp",
        )
        
        assert contact.name == "Alice Smith"
        assert contact.contact_type == "human"
        assert contact.schema_type == "schema:Person"
    
    def test_agent_contact(self):
        """Test creating an agent contact."""
        contact = ContactPayload(
            name="DIALECTICA",
            contact_type="agent",
            agent_id="DIALECTICA",
            agent_capabilities=["socratic", "synthesis", "gap_detection"],
            trust_score=0.95,
        )
        
        assert contact.contact_type == "agent"
        assert contact.agent_id == "DIALECTICA"
        assert len(contact.agent_capabilities) == 3


# =============================================================================
# Test: Context Objects
# =============================================================================

class TestEntelexisState:
    """Tests for EntelexisState model."""
    
    def test_default_state(self):
        """Test default entelexis state."""
        state = EntelexisState()
        
        assert state.phase == "potential"
        assert state.progress == 0.0
        assert state.blockers == []
    
    def test_developing_state(self):
        """Test entelexis in developing phase."""
        state = EntelexisState(
            phase="developing",
            potential_id="pot-001",
            form_signature="KnowledgeGraph.complete",
            progress=0.65,
            blockers=["missing data sources"],
        )
        
        assert state.phase == "developing"
        assert state.progress == 0.65
        assert len(state.blockers) == 1


class TestGoal:
    """Tests for Goal model."""
    
    def test_goal_creation(self):
        """Test creating a goal."""
        goal = Goal(
            id="goal-001",
            description="Complete test coverage",
            priority=8,
            progress=0.47,
        )
        
        assert goal.id == "goal-001"
        assert goal.priority == 8
        assert goal.progress == 0.47
    
    def test_goal_with_blockers(self):
        """Test goal with blocking gaps."""
        goal = Goal(
            id="goal-002",
            description="Deploy to production",
            blocking_gap_nids=[100, 101],
            parent_goal_id="goal-001",
        )
        
        assert len(goal.blocking_gap_nids) == 2
        assert goal.parent_goal_id == "goal-001"


class TestAgentState:
    """Tests for AgentState model."""
    
    def test_idle_agent(self):
        """Test idle agent state."""
        agent = AgentState(agent_id="ARCHON")
        
        assert agent.status == "idle"
        assert agent.current_task is None
    
    def test_active_agent(self):
        """Test active agent state."""
        agent = AgentState(
            agent_id="DIALECTICA",
            status="active",
            current_task="Synthesizing thesis and antithesis",
        )
        
        assert agent.status == "active"
        assert agent.current_task is not None


class TestInceptionContext:
    """Tests for InceptionContext model."""
    
    def test_context_creation(self):
        """Test creating an inception context."""
        ctx = InceptionContext(context_id="ctx-001")
        
        assert ctx.context_id == "ctx-001"
        assert ctx.coordinator_agent == "ARCHON"
        assert ctx.mesh_topology == "star"
    
    def test_context_with_state(self):
        """Test context with full state."""
        ctx = InceptionContext(
            context_id="ctx-002",
            current_purpose="Achieve 100% coverage",
            active_domain_nids=[1, 2],
            active_project_nids=[10],
            current_thesis="Testing is necessary",
            current_antithesis="Testing slows development",
            socratic_depth=3,
        )
        
        assert ctx.current_purpose == "Achieve 100% coverage"
        assert len(ctx.active_domain_nids) == 2
        assert ctx.socratic_depth == 3


# =============================================================================
# Test: Interpretation Surfaces
# =============================================================================

class TestInterpretationSurface:
    """Tests for InterpretationSurface model."""
    
    def test_surface_creation(self):
        """Test creating an interpretation surface."""
        surface = InterpretationSurface(
            name="test_surface",
            input_type="str",
            output_type="Result",
            responsible_agent="TEST",
            learning_signal="accuracy",
        )
        
        assert surface.name == "test_surface"
        assert surface.embedding_model == "all-MiniLM-L6-v2"
    
    def test_predefined_surfaces(self):
        """Test predefined interpretation surfaces."""
        assert PROMPT_INTENT_SURFACE.name == "prompt_to_intent"
        assert PROMPT_INTENT_SURFACE.responsible_agent == "DIALECTICA"
        
        assert CLAIM_VERIFICATION_SURFACE.name == "claim_to_verification"
        assert CLAIM_VERIFICATION_SURFACE.classifier == "claim_verifier_v1"
        
        assert GAP_CLARIFICATION_SURFACE.name == "gap_to_clarification"


# =============================================================================
# Test: Registry
# =============================================================================

class TestTaxonomicTypeRegistry:
    """Tests for TAXONOMIC_TYPE_REGISTRY."""
    
    def test_registry_has_required_types(self):
        """Test registry contains required types."""
        assert NodeKindV2.DOMAIN in TAXONOMIC_TYPE_REGISTRY
        assert NodeKindV2.IDEA in TAXONOMIC_TYPE_REGISTRY
        assert NodeKindV2.PROJECT in TAXONOMIC_TYPE_REGISTRY
        assert NodeKindV2.CONTACT in TAXONOMIC_TYPE_REGISTRY
    
    def test_registry_payload_classes(self):
        """Test registry links to correct payload classes."""
        assert TAXONOMIC_TYPE_REGISTRY[NodeKindV2.DOMAIN]["payload_class"] == DomainPayload
        assert TAXONOMIC_TYPE_REGISTRY[NodeKindV2.IDEA]["payload_class"] == IdeaPayload
        assert TAXONOMIC_TYPE_REGISTRY[NodeKindV2.PROJECT]["payload_class"] == ProjectPayload
        assert TAXONOMIC_TYPE_REGISTRY[NodeKindV2.CONTACT]["payload_class"] == ContactPayload


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
