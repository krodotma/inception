"""
Continuous Refinement Loop
Phase 8, Steps 186-200

Implements:
- Eval harness (186)
- Automated regression detection (187)
- Scorecard dashboard (188)
- Experiment log viewer (189)
- Ablation automation (190)
- Golden promotion workflow (191)
- Error taxonomy updates (192)
- Goal audit process (193)
- Human-anchored test rotation (194)
- Adversarial test generation (195)
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar


# =============================================================================
# Step 186: Eval Harness
# =============================================================================

@dataclass
class Golden:
    """A golden test case."""
    id: str
    input: Any
    expected_output: Any
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_verified: Optional[datetime] = None
    stability_score: float = 1.0


@dataclass
class EvalResult:
    """Result of evaluating a single golden."""
    golden_id: str
    passed: bool
    actual_output: Any
    score: float
    latency_ms: float
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass 
class EvalRunSummary:
    """Summary of an eval run."""
    run_id: str
    total: int
    passed: int
    failed: int
    avg_score: float
    avg_latency_ms: float
    started_at: datetime
    completed_at: datetime
    regressions: list[str] = field(default_factory=list)


class EvalHarness:
    """
    Evaluation harness for running goldens and tracking metrics.
    """
    
    def __init__(self, goldens_path: Optional[Path] = None):
        self.goldens: dict[str, Golden] = {}
        self.results: list[EvalResult] = []
        self.runs: list[EvalRunSummary] = []
        self.baselines: dict[str, float] = {}
        
        if goldens_path and goldens_path.exists():
            self._load_goldens(goldens_path)
    
    def _load_goldens(self, path: Path) -> None:
        """Load goldens from JSONL file."""
        with open(path) as f:
            for line in f:
                data = json.loads(line)
                golden = Golden(
                    id=data.get("id", hashlib.md5(line.encode()).hexdigest()[:8]),
                    input=data.get("input"),
                    expected_output=data.get("expected"),
                    tags=data.get("tags", []),
                )
                self.goldens[golden.id] = golden
    
    def add_golden(self, golden: Golden) -> str:
        """Add a golden test case."""
        self.goldens[golden.id] = golden
        return golden.id
    
    def run_eval(
        self,
        eval_fn: Callable[[Any], Any],
        score_fn: Callable[[Any, Any], float],
        tags: Optional[list[str]] = None,
    ) -> EvalRunSummary:
        """
        Run evaluation on all goldens (optionally filtered by tags).
        """
        import time
        
        run_id = hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:8]
        started_at = datetime.utcnow()
        
        goldens_to_run = list(self.goldens.values())
        if tags:
            goldens_to_run = [g for g in goldens_to_run if any(t in g.tags for t in tags)]
        
        results = []
        for golden in goldens_to_run:
            start_time = time.time()
            try:
                actual = eval_fn(golden.input)
                latency = (time.time() - start_time) * 1000
                score = score_fn(golden.expected_output, actual)
                passed = score >= 0.95
                error = None
            except Exception as e:
                actual = None
                latency = (time.time() - start_time) * 1000
                score = 0.0
                passed = False
                error = str(e)
            
            result = EvalResult(
                golden_id=golden.id,
                passed=passed,
                actual_output=actual,
                score=score,
                latency_ms=latency,
                error=error,
            )
            results.append(result)
            self.results.append(result)
        
        completed_at = datetime.utcnow()
        
        # Compute summary
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        avg_latency = sum(r.latency_ms for r in results) / len(results) if results else 0
        
        # Detect regressions
        regressions = self._detect_regressions(results)
        
        summary = EvalRunSummary(
            run_id=run_id,
            total=len(results),
            passed=passed,
            failed=failed,
            avg_score=avg_score,
            avg_latency_ms=avg_latency,
            started_at=started_at,
            completed_at=completed_at,
            regressions=regressions,
        )
        
        self.runs.append(summary)
        return summary
    
    # -------------------------------------------------------------------------
    # Step 187: Automated Regression Detection
    # -------------------------------------------------------------------------
    
    def _detect_regressions(self, results: list[EvalResult]) -> list[str]:
        """Detect regressions from baseline."""
        regressions = []
        
        for result in results:
            baseline = self.baselines.get(result.golden_id)
            if baseline is not None:
                if result.score < baseline - 0.05:  # 5% tolerance
                    regressions.append(result.golden_id)
        
        return regressions
    
    def set_baseline(self, golden_id: str, score: float) -> None:
        """Set baseline score for a golden."""
        self.baselines[golden_id] = score
    
    def set_baselines_from_run(self, run_id: str) -> int:
        """Set baselines from a successful run."""
        run_results = [r for r in self.results if r.passed]
        for result in run_results:
            self.baselines[result.golden_id] = result.score
        return len(run_results)
    
    # -------------------------------------------------------------------------
    # Step 188: Scorecard Dashboard Data
    # -------------------------------------------------------------------------
    
    def get_scorecard(self) -> dict[str, Any]:
        """Get scorecard data for dashboard."""
        recent_runs = self.runs[-10:] if self.runs else []
        
        # Compute trends
        scores = [r.avg_score for r in recent_runs]
        latencies = [r.avg_latency_ms for r in recent_runs]
        
        score_trend = "stable"
        if len(scores) >= 2:
            if scores[-1] > scores[0] + 0.05:
                score_trend = "improving"
            elif scores[-1] < scores[0] - 0.05:
                score_trend = "declining"
        
        return {
            "total_goldens": len(self.goldens),
            "total_runs": len(self.runs),
            "recent_avg_score": scores[-1] if scores else 0,
            "score_trend": score_trend,
            "recent_avg_latency_ms": latencies[-1] if latencies else 0,
            "regressions_detected": sum(len(r.regressions) for r in recent_runs),
            "pass_rate": sum(r.passed for r in recent_runs) / sum(r.total for r in recent_runs) if recent_runs else 0,
            "runs_history": [
                {
                    "run_id": r.run_id,
                    "score": r.avg_score,
                    "passed": r.passed,
                    "total": r.total,
                    "date": r.completed_at.isoformat(),
                }
                for r in recent_runs
            ],
        }


# =============================================================================
# Step 189: Experiment Log Viewer
# =============================================================================

@dataclass
class Experiment:
    """An experiment with hypothesis and results."""
    id: str
    name: str
    hypothesis: str
    config: dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: dict[str, Any] = field(default_factory=dict)
    notes: str = ""


class ExperimentLog:
    """
    Log for tracking experiments and their outcomes.
    """
    
    def __init__(self, log_path: Optional[Path] = None):
        self.experiments: dict[str, Experiment] = {}
        self.log_path = log_path
    
    def create_experiment(
        self,
        name: str,
        hypothesis: str,
        config: dict[str, Any],
    ) -> Experiment:
        """Create a new experiment."""
        exp_id = hashlib.md5(f"{name}{datetime.utcnow()}".encode()).hexdigest()[:8]
        
        exp = Experiment(
            id=exp_id,
            name=name,
            hypothesis=hypothesis,
            config=config,
        )
        
        self.experiments[exp_id] = exp
        self._persist()
        
        return exp
    
    def start_experiment(self, exp_id: str) -> None:
        """Mark experiment as started."""
        if exp_id in self.experiments:
            self.experiments[exp_id].status = "running"
            self.experiments[exp_id].started_at = datetime.utcnow()
            self._persist()
    
    def complete_experiment(self, exp_id: str, results: dict[str, Any]) -> None:
        """Mark experiment as completed with results."""
        if exp_id in self.experiments:
            self.experiments[exp_id].status = "completed"
            self.experiments[exp_id].completed_at = datetime.utcnow()
            self.experiments[exp_id].results = results
            self._persist()
    
    def fail_experiment(self, exp_id: str, error: str) -> None:
        """Mark experiment as failed."""
        if exp_id in self.experiments:
            self.experiments[exp_id].status = "failed"
            self.experiments[exp_id].completed_at = datetime.utcnow()
            self.experiments[exp_id].notes = error
            self._persist()
    
    def get_experiment_summary(self) -> dict[str, Any]:
        """Get summary for viewer."""
        by_status = {}
        for exp in self.experiments.values():
            by_status[exp.status] = by_status.get(exp.status, 0) + 1
        
        return {
            "total": len(self.experiments),
            "by_status": by_status,
            "recent": [
                {
                    "id": e.id,
                    "name": e.name,
                    "status": e.status,
                    "hypothesis": e.hypothesis[:50] + "..." if len(e.hypothesis) > 50 else e.hypothesis,
                    "date": (e.completed_at or e.started_at or datetime.utcnow()).isoformat(),
                }
                for e in sorted(
                    self.experiments.values(),
                    key=lambda x: x.completed_at or x.started_at or datetime.min,
                    reverse=True,
                )[:10]
            ],
        }
    
    def _persist(self) -> None:
        """Persist experiments to file."""
        if self.log_path:
            data = {
                exp_id: {
                    "id": exp.id,
                    "name": exp.name,
                    "hypothesis": exp.hypothesis,
                    "config": exp.config,
                    "status": exp.status,
                    "results": exp.results,
                    "notes": exp.notes,
                }
                for exp_id, exp in self.experiments.items()
            }
            self.log_path.write_text(json.dumps(data, indent=2))


# =============================================================================
# Step 190: Ablation Automation
# =============================================================================

@dataclass
class AblationResult:
    """Result of an ablation study."""
    component: str
    baseline_score: float
    ablated_score: float
    impact: float  # baseline - ablated
    significant: bool


class AblationAutomation:
    """
    Automated ablation studies to understand component contributions.
    """
    
    def __init__(self, eval_harness: EvalHarness):
        self.eval_harness = eval_harness
        self.results: list[AblationResult] = []
    
    def run_ablation(
        self,
        component: str,
        baseline_fn: Callable,
        ablated_fn: Callable,
        score_fn: Callable,
    ) -> AblationResult:
        """Run ablation study for a component."""
        # Run baseline
        baseline_summary = self.eval_harness.run_eval(baseline_fn, score_fn)
        
        # Run ablated
        ablated_summary = self.eval_harness.run_eval(ablated_fn, score_fn)
        
        impact = baseline_summary.avg_score - ablated_summary.avg_score
        
        result = AblationResult(
            component=component,
            baseline_score=baseline_summary.avg_score,
            ablated_score=ablated_summary.avg_score,
            impact=impact,
            significant=abs(impact) > 0.05,
        )
        
        self.results.append(result)
        return result
    
    def get_ablation_table(self) -> list[dict[str, Any]]:
        """Get ablation results as table data."""
        return [
            {
                "component": r.component,
                "baseline": round(r.baseline_score, 3),
                "ablated": round(r.ablated_score, 3),
                "impact": round(r.impact, 3),
                "significant": r.significant,
            }
            for r in sorted(self.results, key=lambda x: abs(x.impact), reverse=True)
        ]


# =============================================================================
# Step 191: Golden Promotion Workflow
# =============================================================================

class GoldenPromotionWorkflow:
    """
    Workflow for promoting successful test cases to golden status.
    """
    
    def __init__(self, eval_harness: EvalHarness):
        self.eval_harness = eval_harness
        self.candidates: list[dict[str, Any]] = []
        self.promotion_threshold = 0.95
        self.stability_runs = 3
    
    def add_candidate(self, input_data: Any, expected: Any, tags: list[str] = None) -> str:
        """Add a candidate for promotion."""
        candidate = {
            "id": hashlib.md5(str(input_data).encode()).hexdigest()[:8],
            "input": input_data,
            "expected": expected,
            "tags": tags or [],
            "scores": [],
            "promoted": False,
        }
        self.candidates.append(candidate)
        return candidate["id"]
    
    def evaluate_candidate(
        self,
        candidate_id: str,
        eval_fn: Callable,
        score_fn: Callable,
    ) -> float:
        """Evaluate a candidate and record score."""
        candidate = next((c for c in self.candidates if c["id"] == candidate_id), None)
        if not candidate:
            return 0.0
        
        actual = eval_fn(candidate["input"])
        score = score_fn(candidate["expected"], actual)
        candidate["scores"].append(score)
        
        return score
    
    def check_promotion(self, candidate_id: str) -> bool:
        """Check if candidate should be promoted."""
        candidate = next((c for c in self.candidates if c["id"] == candidate_id), None)
        if not candidate:
            return False
        
        scores = candidate["scores"]
        if len(scores) < self.stability_runs:
            return False
        
        # Check stability
        avg_score = sum(scores[-self.stability_runs:]) / self.stability_runs
        score_variance = sum((s - avg_score) ** 2 for s in scores[-self.stability_runs:]) / self.stability_runs
        
        if avg_score >= self.promotion_threshold and score_variance < 0.01:
            return True
        
        return False
    
    def promote(self, candidate_id: str) -> Optional[Golden]:
        """Promote candidate to golden."""
        candidate = next((c for c in self.candidates if c["id"] == candidate_id), None)
        if not candidate or candidate["promoted"]:
            return None
        
        golden = Golden(
            id=f"g_{candidate['id']}",
            input=candidate["input"],
            expected_output=candidate["expected"],
            tags=candidate["tags"],
            stability_score=sum(candidate["scores"]) / len(candidate["scores"]),
        )
        
        self.eval_harness.add_golden(golden)
        candidate["promoted"] = True
        
        return golden


# =============================================================================
# Step 192: Error Taxonomy Updates
# =============================================================================

@dataclass
class ErrorCategory:
    """A category in the error taxonomy."""
    id: str
    name: str
    description: str
    parent_id: Optional[str] = None
    examples: list[str] = field(default_factory=list)
    count: int = 0


class ErrorTaxonomy:
    """
    Taxonomy of error types for classification and analysis.
    """
    
    def __init__(self):
        self.categories: dict[str, ErrorCategory] = {}
        self.error_log: list[dict[str, Any]] = []
    
    def add_category(
        self,
        id: str,
        name: str,
        description: str,
        parent_id: Optional[str] = None,
    ) -> ErrorCategory:
        """Add an error category."""
        cat = ErrorCategory(
            id=id,
            name=name,
            description=description,
            parent_id=parent_id,
        )
        self.categories[id] = cat
        return cat
    
    def classify_error(self, error: str, category_id: str) -> None:
        """Classify an error into a category."""
        if category_id in self.categories:
            self.categories[category_id].count += 1
            self.categories[category_id].examples.append(error[:100])
            
            self.error_log.append({
                "error": error,
                "category": category_id,
                "timestamp": datetime.utcnow().isoformat(),
            })
    
    def get_taxonomy_tree(self) -> dict[str, Any]:
        """Get taxonomy as tree structure."""
        roots = [c for c in self.categories.values() if c.parent_id is None]
        
        def build_tree(cat: ErrorCategory) -> dict:
            children = [c for c in self.categories.values() if c.parent_id == cat.id]
            return {
                "id": cat.id,
                "name": cat.name,
                "count": cat.count,
                "children": [build_tree(c) for c in children],
            }
        
        return {"roots": [build_tree(r) for r in roots]}
    
    def get_top_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most frequent error categories."""
        sorted_cats = sorted(self.categories.values(), key=lambda c: c.count, reverse=True)
        return [
            {"id": c.id, "name": c.name, "count": c.count}
            for c in sorted_cats[:limit]
        ]


# =============================================================================
# Step 193: Monthly Goal Audit Process
# =============================================================================

@dataclass
class GoalAuditResult:
    """Result of a goal audit."""
    goal_id: str
    goal_name: str
    status: str
    progress: float
    days_since_update: int
    recommendation: str


class GoalAuditProcess:
    """
    Monthly goal audit to ensure goals are being pursued.
    """
    
    def __init__(self, goal_registry):
        self.goal_registry = goal_registry
        self.audit_history: list[dict[str, Any]] = []
    
    def run_audit(self) -> list[GoalAuditResult]:
        """Run monthly goal audit."""
        results = []
        now = datetime.utcnow()
        
        for goal in self.goal_registry.goals.values():
            days_stale = (now - goal.created_at).days
            
            if goal.status == "completed":
                recommendation = "Archive or spawn follow-up"
            elif goal.progress < 0.1 and days_stale > 30:
                recommendation = "Review: No progress in 30+ days"
            elif goal.progress < 0.5 and days_stale > 60:
                recommendation = "Escalate: Slow progress"
            elif goal.progress > 0.9:
                recommendation = "Push to completion"
            else:
                recommendation = "On track"
            
            result = GoalAuditResult(
                goal_id=goal.id,
                goal_name=goal.name,
                status=goal.status,
                progress=goal.progress,
                days_since_update=days_stale,
                recommendation=recommendation,
            )
            results.append(result)
        
        self.audit_history.append({
            "date": now.isoformat(),
            "total_goals": len(results),
            "at_risk": sum(1 for r in results if "Review" in r.recommendation or "Escalate" in r.recommendation),
        })
        
        return results
    
    def get_audit_summary(self) -> dict[str, Any]:
        """Get audit summary."""
        return {
            "total_audits": len(self.audit_history),
            "recent": self.audit_history[-5:] if self.audit_history else [],
        }


# =============================================================================
# Step 194: Human-Anchored Test Rotation
# =============================================================================

class HumanAnchoredRotation:
    """
    Rotation of tests that require human verification.
    """
    
    def __init__(self, eval_harness: EvalHarness):
        self.eval_harness = eval_harness
        self.human_anchored_ids: list[str] = []
        self.last_rotation: Optional[datetime] = None
        self.rotation_interval_days = 7
    
    def mark_human_anchored(self, golden_id: str) -> None:
        """Mark a golden as requiring human verification."""
        if golden_id not in self.human_anchored_ids:
            self.human_anchored_ids.append(golden_id)
    
    def get_rotation_batch(self, batch_size: int = 5) -> list[Golden]:
        """Get next batch of human-anchored tests for verification."""
        goldens = [
            self.eval_harness.goldens[gid]
            for gid in self.human_anchored_ids
            if gid in self.eval_harness.goldens
        ]
        
        # Prioritize by staleness
        goldens.sort(key=lambda g: g.last_verified or datetime.min)
        
        return goldens[:batch_size]
    
    def record_human_verification(self, golden_id: str, passed: bool) -> None:
        """Record human verification result."""
        if golden_id in self.eval_harness.goldens:
            self.eval_harness.goldens[golden_id].last_verified = datetime.utcnow()
            if not passed:
                self.eval_harness.goldens[golden_id].stability_score *= 0.9
    
    def needs_rotation(self) -> bool:
        """Check if rotation is needed."""
        if self.last_rotation is None:
            return True
        return (datetime.utcnow() - self.last_rotation).days >= self.rotation_interval_days


# =============================================================================
# Step 195: Adversarial Test Generation
# =============================================================================

class AdversarialTestGenerator:
    """
    Generate adversarial test cases to find edge cases.
    """
    
    def __init__(self, eval_harness: EvalHarness):
        self.eval_harness = eval_harness
        self.strategies = [
            self._mutate_input,
            self._boundary_case,
            self._empty_input,
            self._oversized_input,
        ]
    
    def generate_adversarial(self, base_golden: Golden, count: int = 5) -> list[dict[str, Any]]:
        """Generate adversarial variants from a base golden."""
        variants = []
        
        for strategy in self.strategies[:count]:
            variant = strategy(base_golden)
            if variant:
                variants.append(variant)
        
        return variants
    
    def _mutate_input(self, golden: Golden) -> Optional[dict[str, Any]]:
        """Mutate input slightly."""
        if isinstance(golden.input, str):
            # Character swap, deletion, insertion
            s = list(golden.input)
            if len(s) > 2:
                i, j = random.sample(range(len(s)), 2)
                s[i], s[j] = s[j], s[i]
            return {"input": "".join(s), "type": "mutation"}
        return None
    
    def _boundary_case(self, golden: Golden) -> Optional[dict[str, Any]]:
        """Generate boundary case."""
        if isinstance(golden.input, str):
            return {"input": golden.input[0] if golden.input else "", "type": "boundary"}
        return None
    
    def _empty_input(self, golden: Golden) -> Optional[dict[str, Any]]:
        """Generate empty input."""
        if isinstance(golden.input, str):
            return {"input": "", "type": "empty"}
        if isinstance(golden.input, list):
            return {"input": [], "type": "empty"}
        if isinstance(golden.input, dict):
            return {"input": {}, "type": "empty"}
        return None
    
    def _oversized_input(self, golden: Golden) -> Optional[dict[str, Any]]:
        """Generate oversized input."""
        if isinstance(golden.input, str):
            return {"input": golden.input * 100, "type": "oversized"}
        return None
    
    def run_adversarial_suite(
        self,
        eval_fn: Callable,
        sample_size: int = 10,
    ) -> list[dict[str, Any]]:
        """Run adversarial tests on sample of goldens."""
        goldens = list(self.eval_harness.goldens.values())[:sample_size]
        findings = []
        
        for golden in goldens:
            variants = self.generate_adversarial(golden)
            
            for variant in variants:
                try:
                    result = eval_fn(variant["input"])
                    findings.append({
                        "base_id": golden.id,
                        "variant_type": variant["type"],
                        "crashed": False,
                        "result": str(result)[:50],
                    })
                except Exception as e:
                    findings.append({
                        "base_id": golden.id,
                        "variant_type": variant["type"],
                        "crashed": True,
                        "error": str(e),
                    })
        
        return findings


# =============================================================================
# Factory and Exports
# =============================================================================

def create_eval_harness(goldens_path: Optional[str] = None) -> EvalHarness:
    """Create an eval harness."""
    path = Path(goldens_path) if goldens_path else None
    return EvalHarness(path)


def create_experiment_log(log_path: Optional[str] = None) -> ExperimentLog:
    """Create an experiment log."""
    path = Path(log_path) if log_path else None
    return ExperimentLog(path)


__all__ = [
    # Eval
    "Golden",
    "EvalResult",
    "EvalRunSummary",
    "EvalHarness",
    
    # Experiments
    "Experiment",
    "ExperimentLog",
    
    # Ablation
    "AblationResult",
    "AblationAutomation",
    
    # Promotion
    "GoldenPromotionWorkflow",
    
    # Error Taxonomy
    "ErrorCategory",
    "ErrorTaxonomy",
    
    # Audit
    "GoalAuditResult",
    "GoalAuditProcess",
    
    # Human Rotation
    "HumanAnchoredRotation",
    
    # Adversarial
    "AdversarialTestGenerator",
    
    # Factory
    "create_eval_harness",
    "create_experiment_log",
]
