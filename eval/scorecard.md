# Inception Evaluation Scorecard

> Primary + Guardrail + Human-Truth Metrics

---

## Primary Metrics (Success Indicators)

| Metric | Current | Target | Threshold | Method |
|--------|---------|--------|-----------|--------|
| **Claim F1** | 0.72 | 0.85 | ≥ 0.80 | `goldens/claims.jsonl` |
| **Entity Linking Accuracy** | 0.68 | 0.82 | ≥ 0.75 | `goldens/entities.jsonl` |
| **Skill Executability Rate** | N/A | 0.90 | ≥ 0.85 | `goldens/skills.jsonl` |
| **Taxonomy Coverage** | 1/15 | 15/15 | ≥ 12/15 | Information type extraction |

---

## Guardrail Metrics (Must-Not-Break)

| Metric | Threshold | Status | Method |
|--------|-----------|--------|--------|
| **Latency P95** | < 500ms | 🟢 | Performance harness |
| **Latency P99** | < 2000ms | 🟢 | Performance harness |
| **Safety Violations** | 0 | 🟢 | Sentinel audit |
| **Privacy Compliance (PII)** | 100% | 🟢 | PII scanner |
| **Regression Rate** | < 5% | 🟢 | Golden comparison |
| **Memory Usage** | < 2GB | 🟢 | Resource monitor |

---

## Human-Truth Metrics (Reality Checks)

| Check | Frequency | Last Run | Result | Notes |
|-------|-----------|----------|--------|-------|
| **Expert Review** | Weekly | — | — | Domain expert validates 20 samples |
| **Usability Test** | Bi-weekly | — | — | End user completes 5 tasks |
| **Adversarial Test** | Monthly | — | — | Red team attempts 10 edge cases |

---

## Minimum Meaningful Change

An improvement is **real** only if:
1. Primary metric improves by **≥ 2 points** (e.g., F1 0.72 → 0.74)
2. **No guardrail regression** (all green)
3. **No golden failures** introduced

---

## Scorecard History

| Date | Claim F1 | Entity Acc | Skill Rate | Guardrails | Notes |
|------|----------|------------|------------|------------|-------|
| 2026-01-28 | 0.72 | 0.68 | N/A | 6/6 🟢 | Baseline established |

---

## How to Run

```bash
# Full evaluation
uv run python eval/run_eval.py

# Specific category
uv run python eval/run_eval.py --category claims
uv run python eval/run_eval.py --category entities
uv run python eval/run_eval.py --category skills

# With verbose output
uv run python eval/run_eval.py --verbose
```

---

## Scorecard Update Protocol

1. Run `eval/run_eval.py` after every change
2. Record results in History table
3. If regression: diagnose (Spec gap? Eval gap? System gap?)
4. If improvement verified: promote to golden
