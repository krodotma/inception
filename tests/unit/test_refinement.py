"""
Continuous Refinement Tests
Phase 8, Steps 196-199

Tests for:
- Eval harness and scorecard
- Experiment logging
- Ablation automation
- Golden promotion
- Error taxonomy
- Goal audit
- Human-anchored rotation
- Adversarial test generation
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from inception.eval.refinement import (
    # Eval
    Golden,
    EvalResult,
    EvalHarness,
    
    # Experiments
    Experiment,
    ExperimentLog,
    
    # Ablation  
    AblationAutomation,
    
    # Promotion
    GoldenPromotionWorkflow,
    
    # Error Taxonomy
    ErrorCategory,
    ErrorTaxonomy,
    
    # Audit
    GoalAuditProcess,
    
    # Human Rotation
    HumanAnchoredRotation,
    
    # Adversarial
    AdversarialTestGenerator,
    
    # Factory
    create_eval_harness,
)


# =============================================================================
# Test: Eval Harness
# =============================================================================

class TestEvalHarness:
    """Tests for evaluation harness."""
    
    @pytest.fixture
    def harness(self):
        """Create a test harness."""
        harness = create_eval_harness()
        harness.add_golden(Golden(id="g1", input="hello", expected_output="HELLO"))
        harness.add_golden(Golden(id="g2", input="world", expected_output="WORLD"))
        return harness
    
    def test_add_golden(self, harness):
        """Test adding goldens."""
        assert len(harness.goldens) == 2
        assert harness.goldens["g1"].input == "hello"
    
    def test_run_eval(self, harness):
        """Test running evaluation."""
        def eval_fn(x):
            return x.upper()
        
        def score_fn(expected, actual):
            return 1.0 if expected == actual else 0.0
        
        summary = harness.run_eval(eval_fn, score_fn)
        
        assert summary.total == 2
        assert summary.passed == 2
        assert summary.avg_score == 1.0
    
    def test_regression_detection(self, harness):
        """Test detecting regressions."""
        harness.set_baseline("g1", 1.0)
        harness.set_baseline("g2", 1.0)
        
        def eval_fn(x):
            # Introduce regression
            if x == "hello":
                return "WRONG"
            return x.upper()
        
        def score_fn(expected, actual):
            return 1.0 if expected == actual else 0.0
        
        summary = harness.run_eval(eval_fn, score_fn)
        
        assert "g1" in summary.regressions
        assert "g2" not in summary.regressions
    
    def test_scorecard(self, harness):
        """Test scorecard generation."""
        def eval_fn(x):
            return x.upper()
        
        def score_fn(expected, actual):
            return 1.0 if expected == actual else 0.0
        
        harness.run_eval(eval_fn, score_fn)
        harness.run_eval(eval_fn, score_fn)
        
        scorecard = harness.get_scorecard()
        
        assert scorecard["total_goldens"] == 2
        assert scorecard["total_runs"] == 2
        assert scorecard["recent_avg_score"] == 1.0
        assert scorecard["score_trend"] == "stable"


# =============================================================================
# Test: Experiment Log
# =============================================================================

class TestExperimentLog:
    """Tests for experiment logging."""
    
    def test_create_experiment(self):
        """Test creating an experiment."""
        log = ExperimentLog()
        
        exp = log.create_experiment(
            name="Test Experiment",
            hypothesis="Increasing batch size improves accuracy",
            config={"batch_size": 64},
        )
        
        assert exp.id is not None
        assert exp.status == "pending"
        assert exp.name == "Test Experiment"
    
    def test_experiment_lifecycle(self):
        """Test full experiment lifecycle."""
        log = ExperimentLog()
        
        exp = log.create_experiment("Exp", "Hypothesis", {"param": 1})
        
        log.start_experiment(exp.id)
        assert log.experiments[exp.id].status == "running"
        
        log.complete_experiment(exp.id, {"accuracy": 0.95})
        assert log.experiments[exp.id].status == "completed"
        assert log.experiments[exp.id].results["accuracy"] == 0.95
    
    def test_experiment_failure(self):
        """Test failing an experiment."""
        log = ExperimentLog()
        
        exp = log.create_experiment("Exp", "Hypothesis", {})
        log.start_experiment(exp.id)
        log.fail_experiment(exp.id, "Out of memory")
        
        assert log.experiments[exp.id].status == "failed"
        assert "memory" in log.experiments[exp.id].notes


# =============================================================================
# Test: Ablation Automation
# =============================================================================

class TestAblationAutomation:
    """Tests for ablation studies."""
    
    def test_run_ablation(self):
        """Test running an ablation study."""
        harness = create_eval_harness()
        harness.add_golden(Golden(id="g1", input=10, expected_output=20))
        
        ablation = AblationAutomation(harness)
        
        def baseline(x):
            return x * 2
        
        def ablated(x):
            return x * 1.5  # Worse performance
        
        def score(expected, actual):
            return 1.0 - abs(expected - actual) / expected
        
        result = ablation.run_ablation("multiplier", baseline, ablated, score)
        
        assert result.component == "multiplier"
        assert result.baseline_score > result.ablated_score
        assert result.significant  # Impact > 0.05


# =============================================================================
# Test: Golden Promotion
# =============================================================================

class TestGoldenPromotion:
    """Tests for golden promotion workflow."""
    
    def test_add_candidate(self):
        """Test adding a candidate."""
        harness = create_eval_harness()
        workflow = GoldenPromotionWorkflow(harness)
        
        cid = workflow.add_candidate("input", "expected", tags=["test"])
        
        assert len(workflow.candidates) == 1
        assert workflow.candidates[0]["id"] == cid
    
    def test_promotion_check(self):
        """Test checking for promotion."""
        harness = create_eval_harness()
        workflow = GoldenPromotionWorkflow(harness)
        
        cid = workflow.add_candidate("x", "X")
        
        # Need 3 stable runs
        for _ in range(3):
            workflow.evaluate_candidate(cid, lambda x: x.upper(), lambda e, a: 1.0)
        
        should_promote = workflow.check_promotion(cid)
        assert should_promote
    
    def test_actual_promotion(self):
        """Test promoting to golden."""
        harness = create_eval_harness()
        workflow = GoldenPromotionWorkflow(harness)
        
        cid = workflow.add_candidate("test", "TEST")
        
        for _ in range(3):
            workflow.evaluate_candidate(cid, lambda x: x.upper(), lambda e, a: 1.0)
        
        golden = workflow.promote(cid)
        
        assert golden is not None
        assert f"g_{cid}" in harness.goldens


# =============================================================================
# Test: Error Taxonomy
# =============================================================================

class TestErrorTaxonomy:
    """Tests for error classification."""
    
    def test_add_category(self):
        """Test adding error categories."""
        taxonomy = ErrorTaxonomy()
        
        taxonomy.add_category("parse", "Parse Errors", "Errors during parsing")
        taxonomy.add_category("parse.json", "JSON Parse", "JSON specific", parent_id="parse")
        
        assert len(taxonomy.categories) == 2
        assert taxonomy.categories["parse.json"].parent_id == "parse"
    
    def test_classify_error(self):
        """Test classifying errors."""
        taxonomy = ErrorTaxonomy()
        taxonomy.add_category("timeout", "Timeout Errors", "Request timeouts")
        
        taxonomy.classify_error("Connection timed out after 30s", "timeout")
        taxonomy.classify_error("Request timeout", "timeout")
        
        assert taxonomy.categories["timeout"].count == 2
    
    def test_taxonomy_tree(self):
        """Test getting taxonomy tree."""
        taxonomy = ErrorTaxonomy()
        
        taxonomy.add_category("root1", "Root 1", "First root")
        taxonomy.add_category("child1", "Child 1", "First child", parent_id="root1")
        taxonomy.add_category("root2", "Root 2", "Second root")
        
        tree = taxonomy.get_taxonomy_tree()
        
        assert len(tree["roots"]) == 2


# =============================================================================
# Test: Goal Audit
# =============================================================================

class TestGoalAudit:
    """Tests for goal audit process."""
    
    def test_run_audit(self):
        """Test running a goal audit."""
        # Mock goal registry
        class MockGoal:
            def __init__(self, id, name, status, progress, days_old):
                self.id = id
                self.name = name
                self.status = status
                self.progress = progress
                self.created_at = datetime.utcnow()
        
        class MockRegistry:
            def __init__(self):
                self.goals = {
                    "g1": MockGoal("g1", "Goal 1", "active", 0.95, 10),  # > 0.9 triggers "Push to completion"
                    "g2": MockGoal("g2", "Goal 2", "completed", 1.0, 30),
                }
        
        registry = MockRegistry()
        audit = GoalAuditProcess(registry)
        
        results = audit.run_audit()
        
        assert len(results) == 2
        assert any("Push to completion" in r.recommendation for r in results)


# =============================================================================
# Test: Human-Anchored Rotation
# =============================================================================

class TestHumanAnchoredRotation:
    """Tests for human-anchored test rotation."""
    
    def test_mark_human_anchored(self):
        """Test marking tests as human-anchored."""
        harness = create_eval_harness()
        harness.add_golden(Golden(id="h1", input="x", expected_output="y"))
        
        rotation = HumanAnchoredRotation(harness)
        rotation.mark_human_anchored("h1")
        
        assert "h1" in rotation.human_anchored_ids
    
    def test_get_rotation_batch(self):
        """Test getting rotation batch."""
        harness = create_eval_harness()
        harness.add_golden(Golden(id="h1", input="a", expected_output="A"))
        harness.add_golden(Golden(id="h2", input="b", expected_output="B"))
        
        rotation = HumanAnchoredRotation(harness)
        rotation.mark_human_anchored("h1")
        rotation.mark_human_anchored("h2")
        
        batch = rotation.get_rotation_batch(batch_size=1)
        
        assert len(batch) == 1
    
    def test_record_verification(self):
        """Test recording human verification."""
        harness = create_eval_harness()
        harness.add_golden(Golden(id="h1", input="x", expected_output="y"))
        
        rotation = HumanAnchoredRotation(harness)
        rotation.record_human_verification("h1", passed=True)
        
        assert harness.goldens["h1"].last_verified is not None


# =============================================================================
# Test: Adversarial Test Generation
# =============================================================================

class TestAdversarialTestGeneration:
    """Tests for adversarial test generation."""
    
    def test_generate_adversarial(self):
        """Test generating adversarial variants."""
        harness = create_eval_harness()
        golden = Golden(id="base", input="hello world", expected_output="HELLO WORLD")
        harness.add_golden(golden)
        
        generator = AdversarialTestGenerator(harness)
        variants = generator.generate_adversarial(golden, count=4)
        
        assert len(variants) >= 2
        types = [v["type"] for v in variants]
        assert "empty" in types or "boundary" in types
    
    def test_run_adversarial_suite(self):
        """Test running adversarial suite."""
        harness = create_eval_harness()
        harness.add_golden(Golden(id="g1", input="test", expected_output="TEST"))
        
        generator = AdversarialTestGenerator(harness)
        
        def eval_fn(x):
            if not x:
                raise ValueError("Empty input")
            return x.upper()
        
        findings = generator.run_adversarial_suite(eval_fn, sample_size=1)
        
        # Should have some findings (crashes or results)
        assert len(findings) > 0
        # Empty input should crash
        empty_finding = next((f for f in findings if f["variant_type"] == "empty"), None)
        if empty_finding:
            assert empty_finding["crashed"]


# =============================================================================
# Integration Test
# =============================================================================

class TestRefinementIntegration:
    """End-to-end integration tests."""
    
    def test_full_refinement_cycle(self):
        """Test complete refinement cycle."""
        # Create harness with goldens
        harness = create_eval_harness()
        
        for i in range(5):
            harness.add_golden(Golden(
                id=f"g{i}",
                input=f"input_{i}",
                expected_output=f"OUTPUT_{i}",
                tags=["batch1"],
            ))
        
        # Define eval and score functions
        def eval_fn(x):
            return x.upper().replace("INPUT_", "OUTPUT_")
        
        def score_fn(expected, actual):
            return 1.0 if expected == actual else 0.0
        
        # Run initial eval
        summary1 = harness.run_eval(eval_fn, score_fn, tags=["batch1"])
        assert summary1.passed == 5
        
        # Set baselines
        harness.set_baselines_from_run(summary1.run_id)
        
        # Create promotion workflow
        promotion = GoldenPromotionWorkflow(harness)
        
        # Add candidate
        cid = promotion.add_candidate("input_new", "OUTPUT_NEW", tags=["batch2"])
        
        # Evaluate candidate multiple times
        for _ in range(3):
            score = promotion.evaluate_candidate(cid, eval_fn, score_fn)
            assert score == 1.0
        
        # Promote to golden
        new_golden = promotion.promote(cid)
        assert new_golden is not None
        assert f"g_{cid}" in harness.goldens
        
        # Get scorecard
        scorecard = harness.get_scorecard()
        assert scorecard["total_goldens"] == 6
        assert scorecard["pass_rate"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
