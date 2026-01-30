"""
Pluribus Integration Tests
Phase 7, Steps 181-184

Tests for:
- Entelexis alignment
- Goal registry and mapping
- AuOm OODA loop
- Sextet fusion
- Message bus
"""

import asyncio
from datetime import datetime

import pytest

from inception.integration.pluribus import (
    # Entelexis
    EntelexisState,
    EntelexisAlignment,
    
    # Goals
    Goal,
    GoalRegistry,
    SkillGoalMapping,
    GapGoalPriority,
    SkillGoalMapper,
    
    # AuOm
    AuOmLaw,
    OODAState,
    AuOmLoop,
    
    # Sextet
    SextetVector,
    SextetFusion,
    
    # Message Bus
    DimensionalEventType,
    DimensionalEvent,
    PluribusMessageBus,
)


# =============================================================================
# Test: Entelexis Alignment
# =============================================================================

class TestEntelexisAlignment:
    """Tests for purpose alignment."""
    
    def test_initial_state(self):
        """Test initial latent state."""
        ea = EntelexisAlignment()
        
        assert ea.state == EntelexisState.LATENT
        assert ea.current_purpose is None
    
    def test_state_transitions(self):
        """Test state machine transitions."""
        ea = EntelexisAlignment()
        
        ea.activate_purpose("Build knowledge graph", 0.8)
        assert ea.state == EntelexisState.EMERGING
        
        ea.focus()
        assert ea.state == EntelexisState.FOCUSED
        
        ea.flow()
        assert ea.state == EntelexisState.FLOWING
        
        ea.reflect()
        assert ea.state == EntelexisState.REFLECTIVE
        
        ea.complete()
        assert ea.state == EntelexisState.COMPLETE
        assert "Build knowledge graph" in ea.completed_goals
    
    def test_alignment_computation(self):
        """Test action-goal alignment."""
        ea = EntelexisAlignment()
        ea.active_goals = ["improve_accuracy", "reduce_latency"]
        
        score = ea.compute_alignment("optimize_model", "improve_accuracy")
        assert score > 0.5


# =============================================================================
# Test: Goal Registry
# =============================================================================

class TestGoalRegistry:
    """Tests for goal management."""
    
    def test_register_goal(self):
        """Test registering a goal."""
        registry = GoalRegistry()
        
        goal = Goal(
            id="g1",
            name="Build KG",
            description="Build knowledge graph",
            priority=0.9,
        )
        
        registry.register(goal)
        
        assert registry.get("g1") == goal
        assert "g1" in registry.root_goals
    
    def test_goal_hierarchy(self):
        """Test parent-child goal relationships."""
        registry = GoalRegistry()
        
        parent = Goal(id="p1", name="Parent", description="Parent goal")
        registry.register(parent)
        
        child1 = Goal(id="c1", name="Child1", description="Child 1", parent_id="p1")
        child2 = Goal(id="c2", name="Child2", description="Child 2", parent_id="p1")
        
        registry.register(child1)
        registry.register(child2)
        
        assert "c1" in registry.get("p1").child_ids
        assert "c2" in registry.get("p1").child_ids
    
    def test_progress_propagation(self):
        """Test progress propagates to parent."""
        registry = GoalRegistry()
        
        parent = Goal(id="p1", name="Parent", description="Parent goal")
        registry.register(parent)
        
        child1 = Goal(id="c1", name="Child1", description="Child 1", parent_id="p1")
        child2 = Goal(id="c2", name="Child2", description="Child 2", parent_id="p1")
        
        registry.register(child1)
        registry.register(child2)
        
        registry.update_progress("c1", 1.0)
        registry.update_progress("c2", 0.5)
        
        parent_progress = registry.get("p1").progress
        assert parent_progress == 0.75  # (1.0 + 0.5) / 2
    
    def test_get_goals_by_priority(self):
        """Test filtering by priority."""
        registry = GoalRegistry()
        
        registry.register(Goal(id="low", name="Low", description="", priority=0.3))
        registry.register(Goal(id="med", name="Med", description="", priority=0.6))
        registry.register(Goal(id="high", name="High", description="", priority=0.9))
        
        high_priority = registry.get_goals_by_priority(0.5)
        
        assert len(high_priority) == 2
        assert high_priority[0].id == "high"


# =============================================================================
# Test: Skill-Goal Mapper
# =============================================================================

class TestSkillGoalMapper:
    """Tests for skill and gap mapping."""
    
    def test_map_skill_to_goal(self):
        """Test skill-goal mapping."""
        registry = GoalRegistry()
        goal = Goal(id="g1", name="Goal", description="")
        registry.register(goal)
        
        mapper = SkillGoalMapper(registry)
        mapper.map_skill_to_goal("skill_1", "g1", weight=0.8)
        
        goals = mapper.get_goals_for_skill("skill_1")
        assert len(goals) == 1
        assert goals[0].id == "g1"
        assert "skill_1" in goal.contributing_skills
    
    def test_gap_priority(self):
        """Test gap priority calculation."""
        registry = GoalRegistry()
        registry.register(Goal(id="g1", name="Goal", description=""))
        
        mapper = SkillGoalMapper(registry)
        
        mapper.map_gap_to_goal("gap_1", "g1", urgency=0.9, impact=0.8)
        
        priority = mapper.get_gap_priority("gap_1")
        assert priority == pytest.approx(0.85)  # (0.9 + 0.8) / 2
    
    def test_prioritized_gaps(self):
        """Test getting gaps sorted by priority."""
        registry = GoalRegistry()
        registry.register(Goal(id="g1", name="Goal", description=""))
        
        mapper = SkillGoalMapper(registry)
        
        mapper.map_gap_to_goal("gap_low", "g1", urgency=0.3, impact=0.2)
        mapper.map_gap_to_goal("gap_high", "g1", urgency=0.9, impact=0.95)
        mapper.map_gap_to_goal("gap_med", "g1", urgency=0.5, impact=0.5)
        
        prioritized = mapper.get_prioritized_gaps()
        
        assert prioritized[0][0] == "gap_high"
        assert prioritized[-1][0] == "gap_low"


# =============================================================================
# Test: AuOm Loop
# =============================================================================

class TestAuOmLoop:
    """Tests for OODA self-improvement loop."""
    
    def test_ooda_cycle(self):
        """Test complete OODA cycle."""
        registry = GoalRegistry()
        loop = AuOmLoop(registry)
        
        assert loop.state.current_phase == AuOmLaw.OBSERVE
        
        loop.observe({"metric": 0.85})
        assert loop.state.current_phase == AuOmLaw.ORIENT
        
        loop.orient({"analysis": "Good but can improve"})
        assert loop.state.current_phase == AuOmLaw.DECIDE
        
        loop.decide({"action": "Tune hyperparameters"})
        assert loop.state.current_phase == AuOmLaw.ACT
        
        loop.act({"executed": "tune_params()"})
        assert loop.state.current_phase == AuOmLaw.EVALUATE
        
        loop.evaluate({"new_metric": 0.90}, success=True)
        assert loop.state.current_phase == AuOmLaw.ADAPT
        
        loop.adapt({"learned": "Higher learning rate works"})
        assert loop.state.current_phase == AuOmLaw.OBSERVE
        assert loop.state.cycles_completed == 1
    
    def test_golden_promotion(self):
        """Test promoting test cases to golden status."""
        registry = GoalRegistry()
        loop = AuOmLoop(registry)
        
        test_case = {"input": "x", "expected": "y"}
        
        promoted = loop.check_golden_promotion(test_case, score=0.98)
        
        assert promoted
        assert len(loop.goldens) == 1
    
    def test_regression_detection(self):
        """Test detecting performance regression."""
        registry = GoalRegistry()
        loop = AuOmLoop(registry)
        
        # No regression
        assert not loop.detect_regression(0.90, 0.85)
        
        # Regression detected
        assert loop.detect_regression(0.75, 0.90)
        assert len(loop.regressions) == 1
    
    def test_success_rate_tracking(self):
        """Test success rate calculation."""
        registry = GoalRegistry()
        loop = AuOmLoop(registry)
        
        loop.observe({})
        loop.orient({})
        loop.decide({})
        loop.act({})
        loop.evaluate({}, success=True)
        
        loop.adapt({})
        loop.observe({})
        loop.orient({})
        loop.decide({})
        loop.act({})
        loop.evaluate({}, success=False)
        
        assert loop.state.success_rate == 0.5


# =============================================================================
# Test: Sextet Fusion
# =============================================================================

class TestSextetFusion:
    """Tests for 6D vector fusion."""
    
    def test_sextet_vector(self):
        """Test basic vector operations."""
        vec = SextetVector(
            epistemic=0.9,
            temporal=0.8,
            source=0.7,
            semantic=0.85,
            pragmatic=0.6,
            ethical=0.95,
        )
        
        assert vec.magnitude() > 0
        assert 0 < vec.weighted_average() < 1
    
    def test_vector_fusion(self):
        """Test fusing multiple vectors."""
        v1 = SextetVector(epistemic=0.9, temporal=0.9, source=0.9, 
                          semantic=0.9, pragmatic=0.9, ethical=0.9)
        v2 = SextetVector(epistemic=0.5, temporal=0.5, source=0.5,
                          semantic=0.5, pragmatic=0.5, ethical=0.5)
        
        fused = SextetVector.fuse([v1, v2])
        
        # Average should be 0.7
        assert abs(fused.epistemic - 0.7) < 0.01
    
    def test_weighted_fusion(self):
        """Test weighted fusion."""
        v1 = SextetVector(epistemic=1.0, temporal=1.0, source=1.0,
                          semantic=1.0, pragmatic=1.0, ethical=1.0)
        v2 = SextetVector(epistemic=0.0, temporal=0.0, source=0.0,
                          semantic=0.0, pragmatic=0.0, ethical=0.0)
        
        # Weight v1 3x more
        fused = SextetVector.fuse([v1, v2], weights=[3.0, 1.0])
        
        assert abs(fused.epistemic - 0.75) < 0.01
    
    def test_fusion_engine(self):
        """Test SextetFusion engine."""
        engine = SextetFusion()
        
        engine.add_vector("entity_1", SextetVector(epistemic=0.9))
        engine.add_vector("entity_2", SextetVector(epistemic=0.5))
        engine.add_vector("entity_3", SextetVector(epistemic=0.7))
        
        rankings = engine.rank_by_dimension("epistemic")
        
        assert rankings[0][0] == "entity_1"
        assert rankings[-1][0] == "entity_2"


# =============================================================================
# Test: Message Bus
# =============================================================================

class TestMessageBus:
    """Tests for Pluribus message bus integration."""
    
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connecting to bus."""
        bus = PluribusMessageBus()
        
        assert not bus.connected
        
        connected = await bus.connect()
        
        assert connected
        assert bus.connected
        assert bus.health_status["status"] == "connected"
    
    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        """Test event publishing and subscription."""
        bus = PluribusMessageBus()
        await bus.connect()
        
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        bus.subscribe(DimensionalEventType.KNOWLEDGE_UPDATE, handler)
        
        event = DimensionalEvent(
            event_type=DimensionalEventType.KNOWLEDGE_UPDATE,
            source="test",
            payload={"data": "test_data"},
        )
        
        await bus.publish(event)
        
        assert len(received_events) == 1
        assert received_events[0].payload["data"] == "test_data"
    
    def test_event_serialization(self):
        """Test event serialization."""
        event = DimensionalEvent(
            event_type=DimensionalEventType.GOAL_PROGRESS,
            source="inception",
            payload={"goal_id": "g1", "progress": 0.5},
            sextet=SextetVector(epistemic=0.8),
        )
        
        json_str = event.to_json()
        
        assert "GOAL_PROGRESS" in json_str or "goal_progress" in json_str
        assert "inception" in json_str
    
    @pytest.mark.asyncio
    async def test_queue_when_disconnected(self):
        """Test events are queued when disconnected."""
        bus = PluribusMessageBus()
        
        event = DimensionalEvent(
            event_type=DimensionalEventType.SKILL_EXECUTED,
            source="test",
            payload={},
        )
        
        await bus.publish(event)  # Should queue
        
        assert len(bus.event_queue) == 1
        
        await bus.connect()
        flushed = await bus.flush_queue()
        
        assert flushed == 1
        assert len(bus.event_queue) == 0
    
    @pytest.mark.asyncio
    async def test_health_reporting(self):
        """Test health status reporting."""
        bus = PluribusMessageBus()
        await bus.connect()
        
        health = await bus.report_health()
        
        assert health["status"] == "connected"
        assert "last_heartbeat" in health


# =============================================================================
# Integration Test
# =============================================================================

class TestPluribusIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete Pluribus integration workflow."""
        # Set up goal registry
        registry = GoalRegistry()
        
        root_goal = Goal(
            id="root",
            name="Extract Knowledge",
            description="Extract knowledge from videos",
            priority=1.0,
        )
        registry.register(root_goal)
        
        sub_goal = Goal(
            id="sub1",
            name="Identify Claims",
            description="Identify claims in content",
            priority=0.8,
            parent_id="root",
        )
        registry.register(sub_goal)
        
        # Set up skill mapper
        mapper = SkillGoalMapper(registry)
        mapper.map_skill_to_goal("claim_extraction", "sub1", weight=1.0)
        mapper.map_gap_to_goal("missing_context", "sub1", urgency=0.7, impact=0.8)
        
        # Set up AuOm loop
        auom = AuOmLoop(registry)
        
        # Set up Entelexis
        entelexis = EntelexisAlignment()
        entelexis.activate_purpose("Extract knowledge from lecture videos")
        entelexis.active_goals = ["root", "sub1"]
        
        # Set up message bus
        bus = PluribusMessageBus()
        await bus.connect()
        
        events_received = []
        bus.subscribe(DimensionalEventType.GOAL_PROGRESS, lambda e: events_received.append(e))
        
        # Simulate workflow
        auom.observe({"accuracy": 0.7})
        auom.orient({"needs": "improvement"})
        auom.decide({"action": "tune model"})
        auom.act({"tuned": True})
        auom.evaluate({"new_accuracy": 0.85}, success=True)
        auom.adapt({"learning": "more data helps"})
        
        # Update progress
        registry.update_progress("sub1", 0.85)
        
        # Publish progress event
        event = DimensionalEvent(
            event_type=DimensionalEventType.GOAL_PROGRESS,
            source="inception",
            payload={"goal_id": "sub1", "progress": 0.85},
            sextet=SextetVector(epistemic=0.85, pragmatic=0.8),
        )
        await bus.publish(event)
        
        # Verify
        assert entelexis.state == EntelexisState.EMERGING
        assert auom.state.cycles_completed == 1
        assert registry.get("sub1").progress == 0.85
        assert len(events_received) == 1
        
        # Check gap priority
        gap_priority = mapper.get_gap_priority("missing_context")
        assert gap_priority > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
