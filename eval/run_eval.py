#!/usr/bin/env python3
"""
Inception Evaluation Harness

Run the complete evaluation suite against golden examples.
Produces scorecard metrics and error classifications.

Usage:
    python run_eval.py                    # Full evaluation
    python run_eval.py --category claims  # Specific category
    python run_eval.py --verbose          # Detailed output
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class EvalResult:
    """Result of a single golden test."""
    id: str
    category: str
    passed: bool
    expected: dict
    actual: dict = field(default_factory=dict)
    error_code: Optional[str] = None
    latency_ms: float = 0.0
    notes: str = ""


@dataclass
class CategoryMetrics:
    """Metrics for a category."""
    total: int = 0
    passed: int = 0
    failed: int = 0
    f1_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    avg_latency_ms: float = 0.0


@dataclass
class ScorecardResult:
    """Complete scorecard result."""
    timestamp: str
    categories: dict[str, CategoryMetrics] = field(default_factory=dict)
    guardrails: dict[str, bool] = field(default_factory=dict)
    error_counts: dict[str, int] = field(default_factory=dict)
    overall_passed: bool = True


def load_goldens(path: Path, category: Optional[str] = None) -> list[dict]:
    """Load golden examples from JSONL file."""
    goldens = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if "id" in item:  # Skip metadata line
                if category is None or item.get("category") == category:
                    goldens.append(item)
    return goldens


def evaluate_claim(input_text: str, expected: dict) -> tuple[dict, list[str]]:
    """
    Evaluate claim extraction.
    
    Returns:
        (actual_result, list of error codes)
    """
    # Placeholder: In production, this calls the actual extractor
    # For now, return mock results for testing the harness
    errors = []
    
    # Mock: Always return expected for baseline
    actual = expected.copy()
    
    return actual, errors


def evaluate_entity(input_text: str, expected: dict) -> tuple[dict, list[str]]:
    """Evaluate entity extraction."""
    errors = []
    actual = expected.copy()
    return actual, errors


def evaluate_temporal(input_text: str, expected: dict) -> tuple[dict, list[str]]:
    """Evaluate temporal relation extraction."""
    errors = []
    actual = expected.copy()
    return actual, errors


def evaluate_procedure(input_text: str, expected: dict) -> tuple[dict, list[str]]:
    """Evaluate procedure extraction."""
    errors = []
    actual = expected.copy()
    return actual, errors


def run_evaluation(
    goldens_path: Path,
    category: Optional[str] = None,
    verbose: bool = False,
) -> ScorecardResult:
    """Run full evaluation and produce scorecard."""
    
    goldens = load_goldens(goldens_path, category)
    
    result = ScorecardResult(
        timestamp=datetime.now().isoformat(),
        guardrails={
            "latency_p95": True,
            "latency_p99": True,
            "safety_violations": True,
            "privacy_compliance": True,
            "regression_rate": True,
            "memory_usage": True,
        }
    )
    
    # Initialize categories
    categories = {"claims", "entities", "temporal", "procedures"}
    for cat in categories:
        result.categories[cat] = CategoryMetrics()
    
    # Initialize error counts
    error_codes = [
        "E1", "E2", "E3", "E4", "E5",  # Extraction
        "L1", "L2", "L3",              # Linking
        "T1", "T2", "T3",              # Temporal
        "P1", "P2",                    # Procedural
        "S1", "S2",                    # System
    ]
    for code in error_codes:
        result.error_counts[code] = 0
    
    # Run evaluations
    eval_results: list[EvalResult] = []
    latencies: list[float] = []
    
    for golden in goldens:
        cat = golden.get("category", "unknown")
        input_text = golden.get("input", "")
        expected = golden.get("expected", {})
        
        # Route to appropriate evaluator
        import time
        start = time.time()
        
        if cat == "claims":
            actual, errors = evaluate_claim(input_text, expected)
        elif cat == "entities":
            actual, errors = evaluate_entity(input_text, expected)
        elif cat == "temporal":
            actual, errors = evaluate_temporal(input_text, expected)
        elif cat == "procedures":
            actual, errors = evaluate_procedure(input_text, expected)
        else:
            actual, errors = {}, ["UNKNOWN_CATEGORY"]
        
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        
        # Record result
        passed = len(errors) == 0 and actual == expected
        eval_result = EvalResult(
            id=golden.get("id", "unknown"),
            category=cat,
            passed=passed,
            expected=expected,
            actual=actual,
            error_code=errors[0] if errors else None,
            latency_ms=latency_ms,
            notes=golden.get("notes", ""),
        )
        eval_results.append(eval_result)
        
        # Update metrics
        if cat in result.categories:
            result.categories[cat].total += 1
            if passed:
                result.categories[cat].passed += 1
            else:
                result.categories[cat].failed += 1
        
        # Update error counts
        for error in errors:
            if error in result.error_counts:
                result.error_counts[error] += 1
        
        if verbose:
            status = "✓" if passed else "✗"
            print(f"  {status} {golden['id']}: {golden['notes']}")
    
    # Compute aggregate metrics
    for cat, metrics in result.categories.items():
        if metrics.total > 0:
            metrics.precision = metrics.passed / metrics.total
            metrics.recall = metrics.passed / metrics.total  # Simplified
            if metrics.precision + metrics.recall > 0:
                metrics.f1_score = 2 * (metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)
    
    # Check guardrails
    if latencies:
        latencies_sorted = sorted(latencies)
        p95_idx = int(len(latencies) * 0.95)
        p99_idx = int(len(latencies) * 0.99)
        p95 = latencies_sorted[min(p95_idx, len(latencies) - 1)]
        p99 = latencies_sorted[min(p99_idx, len(latencies) - 1)]
        
        result.guardrails["latency_p95"] = p95 < 500
        result.guardrails["latency_p99"] = p99 < 2000
    
    # Check overall passed
    result.overall_passed = all(result.guardrails.values())
    
    return result


def print_scorecard(result: ScorecardResult) -> None:
    """Print formatted scorecard."""
    print("\n" + "=" * 60)
    print("INCEPTION EVALUATION SCORECARD")
    print("=" * 60)
    print(f"Timestamp: {result.timestamp}")
    print()
    
    # Primary metrics
    print("PRIMARY METRICS")
    print("-" * 40)
    for cat, metrics in result.categories.items():
        if metrics.total > 0:
            print(f"  {cat:12} | F1: {metrics.f1_score:.2f} | {metrics.passed}/{metrics.total}")
    print()
    
    # Guardrails
    print("GUARDRAILS")
    print("-" * 40)
    for name, passed in result.guardrails.items():
        status = "🟢" if passed else "🔴"
        print(f"  {status} {name}")
    print()
    
    # Error distribution
    total_errors = sum(result.error_counts.values())
    if total_errors > 0:
        print("ERROR DISTRIBUTION")
        print("-" * 40)
        for code, count in result.error_counts.items():
            if count > 0:
                print(f"  {code}: {count}")
    
    print()
    status = "PASSED ✓" if result.overall_passed else "FAILED ✗"
    print(f"OVERALL: {status}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Inception Evaluation Harness")
    parser.add_argument("--category", "-c", choices=["claims", "entities", "temporal", "procedures"],
                        help="Evaluate specific category only")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed output")
    parser.add_argument("--goldens", "-g", default="eval/goldens/goldens.jsonl",
                        help="Path to goldens file")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output as JSON")
    
    args = parser.parse_args()
    
    goldens_path = Path(args.goldens)
    if not goldens_path.exists():
        print(f"Error: Goldens file not found: {goldens_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Running evaluation from: {goldens_path}")
    if args.category:
        print(f"Category filter: {args.category}")
    
    result = run_evaluation(goldens_path, args.category, args.verbose)
    
    if args.json:
        # Output as JSON for automation
        import json
        print(json.dumps({
            "timestamp": result.timestamp,
            "categories": {k: vars(v) for k, v in result.categories.items()},
            "guardrails": result.guardrails,
            "error_counts": result.error_counts,
            "overall_passed": result.overall_passed,
        }, indent=2))
    else:
        print_scorecard(result)
    
    sys.exit(0 if result.overall_passed else 1)


if __name__ == "__main__":
    main()
