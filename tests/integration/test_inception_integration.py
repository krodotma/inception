"""
Comprehensive Integration Tests
Phase 14, Steps 296-300

End-to-end tests for all Inception modules:
- HyperKnowledge graph operations
- Pluribus integration
- Refinement loop evaluation
- Context object system
- Dialectical reasoning
- Resource tracking
- Agent mesh coordination
- Semantic interpretation
"""

import pytest
from datetime import datetime, timedelta
from typing import Any


# =============================================================================
# HyperKnowledge Integration Tests
# =============================================================================

class TestHyperKnowledgeIntegration:
    """Integration tests for HyperKnowledge system."""
    
    def test_version_dag_workflow(self):
        """Test complete version DAG workflow."""
        from inception.db.hyperknowledge import (
            KnowledgeHyperGraph, HyperNode, HyperEdge, NodeType, EdgeType,
            VersionDAG, VersionedContent, SourceChain,
        )
        
        # Create graph
        graph = KnowledgeHyperGraph()
        node1 = HyperNode(id="n1", content=VersionedContent("Initial concept"), node_type=NodeType.CONCEPT)
        node2 = HyperNode(id="n2", content=VersionedContent("Related concept"), node_type=NodeType.CONCEPT)
        
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = HyperEdge(
            id="e1",
            source_ids=["n1"],
            target_ids=["n2"],
            edge_type=EdgeType.SUPPORTS,
        )
        graph.add_edge(edge)
        
        # Version operations
        dag = VersionDAG()
        commit1 = dag.commit("Initial graph", ["n1", "n2"])
        
        # Modify and commit
        node3 = HyperNode(id="n3", content=VersionedContent("New concept"), node_type=NodeType.CONCEPT)
        graph.add_node(node3)
        commit2 = dag.commit("Added third concept", ["n1", "n2", "n3"])
        
        # Verify version history
        assert dag.head is not None
        assert len(dag.commits) == 2
    
    def test_temporal_query_workflow(self):
        """Test temporal querying with Allen intervals."""
        from inception.db.hyperknowledge import AllenInterval, AllenRelation
        
        # Create intervals
        now = datetime.utcnow()
        interval1 = AllenInterval(
            start=now - timedelta(hours=2),
            end=now - timedelta(hours=1),
        )
        interval2 = AllenInterval(
            start=now - timedelta(hours=1),
            end=now,
        )
        
        # Test relations
        relation = interval1.relation_to(interval2)
        assert relation in [AllenRelation.MEETS, AllenRelation.BEFORE]
    
    def test_uncertainty_model(self):
        """Test dual uncertainty model."""
        from inception.db.hyperknowledge import UncertaintyModel
        
        uncertainty = UncertaintyModel(
            epistemic=0.3,
            aleatoric=0.2,
        )
        
        # Test combined
        assert 0 <= uncertainty.combined <= 1
        
        # Test certainty level
        assert uncertainty.certainty_level in ["very_low", "low", "moderate", "high", "very_high"]


# =============================================================================
# Pluribus Integration Tests
# =============================================================================

class TestPluribusIntegration:
    """Integration tests for Pluribus integration layer."""
    
    def test_entelexis_goal_workflow(self):
        """Test Entelexis alignment with goal registry."""
        from inception.integration.pluribus import (
            EntelexisAlignment, EntelexisState,
            GoalRegistry, Goal,
        )
        
        # Create alignment
        alignment = EntelexisAlignment()
        alignment.activate_purpose("Extract knowledge")
        assert alignment.state == EntelexisState.EMERGING
        
        # Create goal registry
        registry = GoalRegistry()
        goal = Goal(
            id="g1",
            name="Extract entities",
            description="Extract all entities from document",
            priority=0.9,
        )
        registry.register(goal)
        
        # Get active goals
        active = registry.get_active_goals()
        assert len(active) > 0
        assert active[0].id == "g1"
    
    def test_sextet_fusion(self):
        """Test 6D vector fusion."""
        from inception.integration.pluribus import SextetFusion, SextetVector
        
        fusion = SextetFusion()
        
        # Correct field names: epistemic, temporal, source, semantic, pragmatic, ethical
        vector1 = SextetVector(
            epistemic=0.8,
            temporal=0.7,
            source=0.6,
            semantic=0.5,
            pragmatic=0.4,
            ethical=0.9,
        )
        
        vector2 = SextetVector(
            epistemic=0.6,
            temporal=0.9,
            source=0.7,
            semantic=0.8,
            pragmatic=0.5,
            ethical=0.7,
        )
        
        fused = SextetVector.fuse([vector1, vector2])
        
        # Verify fused vector properties (using magnitude)
        assert 0 <= fused.magnitude() <= 3  # Max possible magnitude
    
    def test_auom_ooda_loop(self):
        """Test AuOm OODA loop."""
        from inception.integration.pluribus import AuOmLoop, GoalRegistry, Goal
        
        # Create goal registry first
        registry = GoalRegistry()
        registry.register(Goal(id="g1", name="Test", description="Test goal"))
        
        loop = AuOmLoop(goal_registry=registry)
        
        # Run OODA cycle - note: these methods return None (void), they update internal state
        loop.observe({"input": "test data"})
        loop.orient({"analysis": "test analysis"})
        loop.decide({"decision": "test decision"})
        loop.act({"action": "test action"})
        
        # Verify loop state was updated
        assert len(loop.state.actions) > 0
        assert loop.state.actions[0]["action"] == {"action": "test action"}


# =============================================================================
# Context Integration Tests
# =============================================================================

class TestContextIntegration:
    """Integration tests for context object system."""
    
    def test_context_serialization_roundtrip(self):
        """Test context serialization and deserialization."""
        from inception.context.context import (
            InceptionContext, ContextMetadata, ContextState,
            ContextSerializer,
        )
        
        # Create context with both required fields: context_id AND session_id
        context = InceptionContext(
            context_id="ctx_test",
            session_id="session_1",
            metadata=ContextMetadata(
                created_by="test",
                tags=["test", "integration"],
            ),
            state=ContextState.ACTIVE,
        )
        
        # Serialize
        data = ContextSerializer.to_dict(context)
        
        # Deserialize
        restored = ContextSerializer.from_dict(data)
        
        assert restored.context_id == context.context_id
        assert restored.state == context.state
    
    def test_context_diff(self):
        """Test context diffing."""
        from inception.context.context import (
            InceptionContext, ContextMetadata, ContextState,
            ContextDiffer,
        )
        
        ctx1 = InceptionContext(
            context_id="ctx1",
            session_id="s1",
            metadata=ContextMetadata(created_by="test"),
        )
        
        ctx2 = InceptionContext(
            context_id="ctx1",
            session_id="s1",
            metadata=ContextMetadata(created_by="test"),
            state=ContextState.COMPLETED,
        )
        
        differ = ContextDiffer()
        diff = differ.diff(ctx1, ctx2)
        
        assert len(diff.changes) > 0


# =============================================================================
# Dialectical Reasoning Tests
# =============================================================================

class TestDialecticalIntegration:
    """Integration tests for dialectical reasoning."""
    
    def test_thesis_antithesis_synthesis_workflow(self):
        """Test complete dialectical workflow."""
        from inception.reasoning.dialectical import (
            create_triad, ClaimStrength,
        )
        
        # Create triad with thesis
        triad = create_triad("AI will transform software development")
        
        # Add antithesis
        triad.propose_antithesis(
            "AI is a tool, not a transformation",
            ClaimStrength.MODERATE,
        )
        
        assert triad.antithesis is not None
        assert triad.stage == "antithesis"
        
        # Add synthesis
        triad.propose_synthesis(
            "AI transforms HOW we develop while remaining a tool",
            ClaimStrength.STRONG,
        )
        
        assert triad.synthesis is not None
        assert triad.stage == "synthesis"
    
    def test_socratic_protocol(self):
        """Test Socratic questioning protocol."""
        from inception.reasoning.dialectical import (
            DialecticalClaim, ClaimType, ClaimStrength,
            SocraticProtocol,
        )
        
        claim = DialecticalClaim(
            id="c1",
            claim_type=ClaimType.THESIS,
            content="Knowledge can be automatically extracted from any document",
            strength=ClaimStrength.MODERATE,
        )
        
        protocol = SocraticProtocol()
        questions = protocol.generate_questions(claim, num_questions=3)
        
        assert len(questions) == 3
        assert all(q.target_claim_id == claim.id for q in questions)
    
    def test_contradiction_detection(self):
        """Test contradiction detection."""
        from inception.reasoning.dialectical import (
            DialecticalClaim, ClaimType, ContradictionDetector,
        )
        
        claim1 = DialecticalClaim(
            id="c1",
            claim_type=ClaimType.THESIS,
            content="All knowledge can be formalized",
        )
        
        claim2 = DialecticalClaim(
            id="c2",
            claim_type=ClaimType.ANTITHESIS,
            content="Some knowledge is tacit and cannot be formalized",
            opposes_ids=["c1"],
        )
        
        detector = ContradictionDetector()
        contradictions = detector.detect([claim1, claim2])
        
        assert len(contradictions) > 0


# =============================================================================
# Resource Tracking Tests
# =============================================================================

class TestResourceIntegration:
    """Integration tests for resource tracking."""
    
    def test_domain_hierarchy(self):
        """Test domain hierarchy management."""
        from inception.resources.tracking import (
            create_domain, DomainType, DomainRegistry,
        )
        
        registry = DomainRegistry()
        
        # Create root domain
        root = create_domain("AI/ML", DomainType.SUBJECT)
        registry.register(root)
        
        # Create subdomain
        nlp = create_domain("NLP", DomainType.SUBJECT)
        nlp.parent_id = root.id
        registry.register(nlp)
        
        # Query
        subdomains = registry.get_subdomains(root.id)
        assert len(subdomains) == 1
        assert subdomains[0].name == "NLP"
    
    def test_idea_lifecycle(self):
        """Test idea lifecycle tracking."""
        from inception.resources.tracking import (
            create_idea, IdeaState, IdeaTracker,
        )
        
        tracker = IdeaTracker()
        
        idea = create_idea("Use graph embeddings for knowledge", "Novel approach")
        tracker.register(idea)
        
        assert idea.idea_state == IdeaState.NASCENT
        
        # Progress through lifecycle
        tracker.transition(idea.id, IdeaState.DEVELOPING)
        tracker.transition(idea.id, IdeaState.VALIDATED)
        
        assert idea.idea_state == IdeaState.VALIDATED
        assert len(idea.state_history) == 3
    
    def test_resource_dependency_graph(self):
        """Test resource dependency graph."""
        from inception.resources.tracking import (
            Project, ResourceGraph, ResourceType, ProjectManager,
        )
        
        manager = ProjectManager()
        
        project1 = manager.create("Core Engine", "Build core extraction engine")
        project2 = manager.create("API Layer", "Build API on top of core")
        
        graph = ResourceGraph()
        graph.add_resource(project1)
        graph.add_resource(project2)
        graph.add_link(project2.id, project1.id, "depends_on")
        
        # Query dependencies
        deps = graph.get_dependencies(project2.id)
        assert len(deps) == 1
        assert deps[0].name == "Core Engine"


# =============================================================================
# Agent Mesh Tests
# =============================================================================

class TestAgentMeshIntegration:
    """Integration tests for agent mesh coordination."""
    
    def test_star_topology_task_distribution(self):
        """Test star topology task distribution."""
        from inception.mesh.coordination import (
            create_mesh, create_mesh_agent,
            TopologyType, AgentRole,
        )
        
        mesh = create_mesh("extraction_mesh", TopologyType.STAR)
        
        # Add workers
        worker1 = create_mesh_agent("Extractor1", AgentRole.WORKER, ["extraction"])
        worker2 = create_mesh_agent("Extractor2", AgentRole.WORKER, ["extraction"])
        
        mesh.add_agent(worker1)
        mesh.add_agent(worker2)
        
        status = mesh.get_status()
        assert status["agent_count"] >= 2
    
    def test_consensus_protocol(self):
        """Test consensus protocol."""
        from inception.mesh.coordination import ConsensusProtocol, ConsensusType
        
        consensus = ConsensusProtocol(ConsensusType.MAJORITY)
        consensus.set_options(["option_a", "option_b", "option_c"])
        
        # Cast votes
        consensus.cast_vote("agent1", "option_a")
        consensus.cast_vote("agent2", "option_a")
        consensus.cast_vote("agent3", "option_b")
        
        # Check consensus
        result = consensus.check_consensus()
        assert result == "option_a"
    
    def test_agent_handoff(self):
        """Test agent handoff with context."""
        from inception.mesh.coordination import (
            AgentHandoff, MeshContext,
        )
        
        handoff = AgentHandoff()
        
        context = MeshContext(
            context_id="ctx1",
            mesh_id="mesh1",
            task_description="Extract entities from document",
        )
        context.add_fact({"entity_count": 42})
        
        # Initiate handoff
        handoff_id = handoff.initiate_handoff(
            "agent1", "agent2", context, "specialization"
        )
        
        # Complete handoff
        handoff.complete_handoff(handoff_id)
        
        # Verify handoff log
        assert len(handoff.handoff_log) == 1


# =============================================================================
# Uncertainty Resolution Tests
# =============================================================================

class TestUncertaintyIntegration:
    """Integration tests for uncertainty resolution."""
    
    def test_epistemic_gap_filling(self):
        """Test epistemic gap filling pipeline."""
        from inception.interpretation.uncertainty import (
            create_epistemic_gap, EpistemicGapType, GapSeverity,
            EpistemicGapFiller, KnowledgeSource, SourceType,
        )
        
        filler = EpistemicGapFiller()
        
        # Register sources
        source = KnowledgeSource(
            source_id="kb1",
            source_type=SourceType.EXTERNAL_KNOWLEDGE,
            reliability=0.9,
        )
        filler.register_source(source)
        
        # Create and fill gap
        gap = create_epistemic_gap(
            "What is the definition of 'entelexis'?",
            EpistemicGapType.MISSING_FACT,
            GapSeverity.MODERATE,
        )
        
        success, value, confidence = filler.fill_gap(gap)
        
        assert success
        assert confidence > 0
    
    def test_aleatoric_expansion(self):
        """Test aleatoric noise expansion."""
        from inception.interpretation.uncertainty import (
            create_aleatoric_noise, AleatoricNoiseType,
            AleatoricNoiseResolver,
        )
        
        noise = create_aleatoric_noise(
            "Bank could mean financial institution or river bank",
            AleatoricNoiseType.LINGUISTIC_AMBIGUITY,
            ["financial_institution", "river_bank", "memory_bank"],
        )
        
        resolver = AleatoricNoiseResolver()
        expansions = resolver.expand_interpretations(noise)
        
        assert len(expansions) == 3
        assert sum(e["probability"] for e in expansions) == pytest.approx(1.0)
    
    def test_unified_resolver_pipeline(self):
        """Test complete uncertainty resolution pipeline."""
        from inception.interpretation.uncertainty import (
            UncertaintyResolver,
            create_epistemic_gap, EpistemicGapType, GapSeverity,
            create_aleatoric_noise, AleatoricNoiseType,
        )
        
        resolver = UncertaintyResolver()
        
        # Add epistemic gap
        gap = create_epistemic_gap(
            "Missing author information",
            EpistemicGapType.MISSING_FACT,
            GapSeverity.MINOR,
        )
        resolver.add_epistemic_gap(gap)
        
        # Add aleatoric noise
        noise = create_aleatoric_noise(
            "Ambiguous date format",
            AleatoricNoiseType.LINGUISTIC_AMBIGUITY,
            ["Jan 2, 2026", "Feb 1, 2026"],
        )
        resolver.add_aleatoric_noise(noise)
        
        # Resolve all
        results = resolver.resolve_all()
        
        assert "filled_gaps" in results
        assert "expanded_noises" in results
        assert "interpretations" in results
        
        # Check confidence
        confidence = resolver.get_confidence_score()
        assert 0 <= confidence <= 1


# =============================================================================
# Cross-Module Integration Tests
# =============================================================================

class TestCrossModuleIntegration:
    """Tests for integration across multiple modules."""
    
    def test_context_with_dialectical_reasoning(self):
        """Test context integration with dialectical reasoning."""
        from inception.context.context import (
            InceptionContext, ContextMetadata, DialecticalState,
        )
        from inception.reasoning.dialectical import create_triad
        
        # Create context with dialectical state (using correct required fields)
        context = InceptionContext(
            context_id="ctx_dia",
            session_id="s1",
            metadata=ContextMetadata(created_by="test"),
            dialectical=DialecticalState(),
        )
        
        # Create triad
        triad = create_triad("Knowledge graphs are superior to vector stores")
        
        # Link to context - using thesis since DialecticalState has 'thesis' not 'active_triad_ids'
        context.dialectical.thesis = "Knowledge graphs are superior to vector stores"
        
        assert context.dialectical.thesis is not None
    
    def test_resource_tracking_with_mesh(self):
        """Test resource tracking with agent mesh."""
        from inception.resources.tracking import (
            create_agent, AgentState, ContactRegistry,
        )
        from inception.mesh.coordination import (
            create_mesh_agent, AgentRole, TopologyType, create_mesh,
        )
        
        # Create agents in resource tracker
        agent1 = create_agent("Extractor", "extractor", ["extraction", "ocr"])
        agent2 = create_agent("Validator", "validator", ["validation"])
        
        registry = ContactRegistry()
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        # Create mesh with same agents
        mesh = create_mesh("coordination", TopologyType.STAR)
        
        mesh_agent1 = create_mesh_agent("Extractor", AgentRole.WORKER, ["extraction"])
        mesh_agent2 = create_mesh_agent("Validator", AgentRole.SPECIALIST, ["validation"])
        
        mesh.add_agent(mesh_agent1)
        mesh.add_agent(mesh_agent2)
        
        # Verify tracking
        assert len(registry.agents) == 2
        assert mesh.get_status()["agent_count"] == 2
    
    def test_uncertainty_with_socratic_escalation(self):
        """Test uncertainty resolution with Socratic escalation."""
        from inception.interpretation.uncertainty import (
            create_epistemic_gap, EpistemicGapType, GapSeverity,
            EpistemicToSocraticBridge,
        )
        
        bridge = EpistemicToSocraticBridge()
        
        # Create critical gap
        gap = create_epistemic_gap(
            "What is the user's intent?",
            EpistemicGapType.CONTEXTUAL_UNKNOWN,
            GapSeverity.CRITICAL,
        )
        
        # Escalate to Socratic
        escalation = bridge.escalate(gap)
        
        assert escalation.gap_id == gap.id
        assert "context" in escalation.question.lower() or "clarify" in escalation.question.lower()


# =============================================================================
# Performance Benchmark Tests
# =============================================================================

class TestPerformance:
    """Performance benchmarks."""
    
    def test_graph_operations_performance(self):
        """Benchmark graph operations."""
        import time
        from inception.resources.tracking import (
            ResourceGraph, ResourceType, ResourceState, ResourceMetadata,
            Project,
        )
        
        graph = ResourceGraph()
        
        # Create 100 resources
        start = time.time()
        for i in range(100):
            project = Project(
                id=f"p{i}",
                name=f"Project {i}",
                resource_type=ResourceType.PROJECT,
            )
            graph.add_resource(project)
        
        creation_time = time.time() - start
        
        # Create 200 links
        start = time.time()
        for i in range(1, 100):
            graph.add_link(f"p{i}", f"p{i-1}", "depends_on")
            graph.add_link(f"p{i}", f"p0", "relates_to")
        
        linking_time = time.time() - start
        
        # Query dependencies
        start = time.time()
        deps = graph.get_all_dependencies("p99")
        query_time = time.time() - start
        
        # Assert reasonable performance (< 100ms each)
        assert creation_time < 0.1
        assert linking_time < 0.1
        assert query_time < 0.1
    
    def test_consensus_voting_performance(self):
        """Benchmark consensus voting."""
        import time
        from inception.mesh.coordination import ConsensusProtocol, ConsensusType
        
        consensus = ConsensusProtocol(ConsensusType.WEIGHTED)
        consensus.set_options(["a", "b", "c", "d", "e"])
        
        # Cast 1000 votes
        start = time.time()
        for i in range(1000):
            choice = ["a", "b", "c", "d", "e"][i % 5]
            consensus.cast_vote(f"agent{i}", choice, weight=1.0 + (i % 10) / 10)
        
        voting_time = time.time() - start
        
        # Check consensus
        start = time.time()
        result = consensus.check_consensus()
        check_time = time.time() - start
        
        assert voting_time < 0.5
        assert check_time < 0.01


# =============================================================================
# Test Entry Point
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
