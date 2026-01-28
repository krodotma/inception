# Inception Experiment Log

> Hypothesis → Change → Result → Decision

---

## Format

Each experiment follows:

```yaml
id: EXP-XXX
date: YYYY-MM-DD
hypothesis: "If we [change], then [expected result]"
change:
  component: [which component]
  lever: [prompt|model|data|parameter|architecture]
  description: [what changed]
result:
  claim_f1: [before → after]
  entity_acc: [before → after]
  guardrails: [all pass? which failed?]
  latency_p95: [before → after]
decision: [lock|revert|iterate]
notes: [learnings]
```

---

## Experiments

### EXP-001: Baseline Establishment

```yaml
id: EXP-001
date: 2026-01-28
hypothesis: "Establishing baseline metrics from current system state"
change:
  component: N/A
  lever: N/A
  description: Initial measurement with no changes
result:
  claim_f1: — → 0.72
  entity_acc: — → 0.68
  skill_exec: — → N/A
  guardrails: 6/6 pass
  latency_p95: — → 320ms
decision: lock
notes: |
  Baseline established. Key observations:
  - Claim extraction functional but hedge detection weak
  - Entity linking misses ambiguous entities
  - Temporal extraction not yet implemented (N/A)
  - Procedure extraction not yet implemented (N/A)
```

---

## Experiment Queue

| ID | Hypothesis | Status |
|----|------------|--------|
| EXP-002 | Adding hedge words to prompt improves modality detection | Queued |
| EXP-003 | Chain-of-thought improves SPO decomposition | Queued |
| EXP-004 | DSPy optimization improves claim F1 | Queued |
| EXP-005 | TextGrad refinement reduces hallucination | Queued |

---

## Decision Key

| Decision | Meaning |
|----------|---------|
| **lock** | Improvement verified, promote to golden |
| **revert** | Regression detected, undo change |
| **iterate** | Inconclusive, needs further testing |
| **park** | Valid but not priority, revisit later |

---

## Ablation Summary

*(Updated after each experiment)*

| Lever | Best Result | Notes |
|-------|-------------|-------|
| System prompt | — | Not yet tested |
| Temperature | — | Not yet tested |
| Model | — | Not yet tested |
| Context length | — | Not yet tested |
| Chain-of-thought | — | Not yet tested |
| DSPy optimization | — | Not yet tested |
| TextGrad refinement | — | Not yet tested |
