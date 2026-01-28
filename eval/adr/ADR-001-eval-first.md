# ADR-001: Evaluation-First Development Discipline

**Status**: Accepted  
**Date**: 2026-01-28  
**Authors**: ARCHON, EVAL-PRIME  

---

## Context

Inception is a complex multimodal knowledge extraction system with 15+ components. Without structured iteration discipline, development becomes "thrash"—endless tweaking without compounding progress.

The user's refinement principles emphasize:
1. Controlled feedback loops that convert ambiguity into invariants
2. Iterating on evaluations and interfaces BEFORE outputs
3. The loop: Intent → Invariants → Observable Rubric → Generate Change → Evaluate → Diagnose → Lock

## Decision

We adopt **Evaluation-First Development** as the core discipline for all Inception work.

### Core Principles

1. **No change is real unless it moves the scorecard without breaking a golden.**

2. **Evals before model changes**: If you can't measure it, iteration becomes superstition.

3. **Interfaces before optimization**: Stable tool schemas + deterministic pre/post-processing beat cleverness.

4. **Guardrails as first-class metrics**: Safety, privacy, latency, cost are not afterthoughts—they're gate checks.

5. **Operational reality baked in**: Telemetry, rollback, caching, rate limits are part of design.

### Required Artifacts

Before any feature development:

| Artifact | Purpose | Location |
|----------|---------|----------|
| Intent statement | What does this exist to do? | `eval/intents.md` |
| Invariants | What must never break? | `eval/invariants.md` |
| Golden examples | Input → expected output | `eval/goldens/` |
| Scorecard entry | How we measure success | `eval/scorecard.md` |
| Error taxonomy | Named failure buckets | `eval/error_taxonomy.md` |

### Diagnosis Protocol

Every regression gets diagnosed:

| Cause | Definition | Action |
|-------|------------|--------|
| **Spec Gap** | Behavior was never defined | Update intents/invariants |
| **Eval Gap** | Harness didn't catch what mattered | Add golden, update scorecard |
| **System Gap** | Implementation can't satisfy spec | Fix code |

### Lock Protocol

Verified improvements become goldens:

1. Run evaluation harness
2. Confirm primary metric improved by ≥ 2 points
3. Confirm no guardrail regression
4. Add to goldens.jsonl as new expected behavior
5. Commit with "Lock: [metric] improved to [value]"

## Consequences

### Positive

- Progress compounds instead of thrashes
- Regressions are caught immediately
- New team members understand "what good looks like"
- Architecture decisions are traceable (ADRs)

### Negative

- Initial overhead to set up eval infrastructure
- Requires discipline to write goldens first
- May slow initial velocity (speeds long-term velocity)

## Alternatives Considered

1. **Output-first development**: Build features, test later
   - Rejected: Leads to "it looked better yesterday" fragility

2. **Manual testing only**: Human review each PR
   - Rejected: Doesn't scale, not reproducible

3. **Metrics-only**: Track numbers without goldens
   - Rejected: Metrics can be gamed; goldens anchor reality

## References

- Implementation plan: `/Users/kroma/.gemini/antigravity/brain/cac43e96-1473-4fa2-96ac-55d32d746e44/implementation_plan.md`
- Scorecard: `/eval/scorecard.md`
- Error taxonomy: `/eval/error_taxonomy.md`
