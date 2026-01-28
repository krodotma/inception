# Inception Component Invariants

> Must-not-break constraints for each component

---

## Global Invariants

These apply to ALL components:

| Invariant | Threshold | Enforcement |
|-----------|-----------|-------------|
| **Latency** | P95 < 500ms, P99 < 2000ms | Performance harness |
| **Memory** | < 2GB per process | Resource monitor |
| **Determinism** | Same input → same output (where applicable) | Golden comparison |
| **Failure Behavior** | Never crash, graceful degradation | Exception handlers |
| **Logging** | All operations logged with correlation ID | Audit trail |

---

## Extraction Invariants

### ClaimExtractor

| Invariant | Description | Test |
|-----------|-------------|------|
| **SPO_COMPLETE** | Every claim must have non-empty subject, predicate, object | Schema validation |
| **MODALITY_VALID** | Modality must be: assertion, possibility, necessity, negation | Enum validation |
| **SOURCE_PRESERVED** | Claim text must be traceable to source span | Provenance check |
| **NO_HALLUCINATION** | Claims must derive from input, not invented | Source overlap > 0.5 |

### EntityRecognizer

| Invariant | Description | Test |
|-----------|-------------|------|
| **TYPE_KNOWN** | Entity type must be from defined taxonomy | Enum validation |
| **SPAN_VALID** | Entity span must be within input bounds | Range check |
| **NO_OVERLAP** | Entity spans must not overlap | Overlap detection |

### EntityLinker

| Invariant | Description | Test |
|-----------|-------------|------|
| **LINK_VALID** | Linked ID must exist in target KB | KB lookup |
| **CONFIDENCE_BOUNDED** | Linking confidence must be 0.0-1.0 | Range check |
| **AMBIGUITY_FLAGGED** | If confidence < 0.7, mark as ambiguous | Threshold check |

### ProcedureExtractor

| Invariant | Description | Test |
|-----------|-------------|------|
| **STEPS_ORDERED** | Steps must have sequential order values | Order validation |
| **NO_DANGLING** | Conditional branches must have actions | Completeness check |
| **PREREQS_EXPLICIT** | Prerequisites must be declared | Dependency check |

### TemporalParser

| Invariant | Description | Test |
|-----------|-------------|------|
| **ALLEN_VALID** | Temporal relation must be valid Allen relation | Enum validation |
| **INTERVAL_CONSISTENT** | Start must precede end | Logic check |
| **NO_PARADOX** | No circular temporal dependencies | Cycle detection |

---

## Synthesis Invariants

### SkillCompiler

| Invariant | Description | Test |
|-----------|-------------|------|
| **DEPS_DECLARED** | All external dependencies must be listed | Dependency scan |
| **TESTABLE** | Each skill must have at least one test | Test presence |
| **SANDBOXABLE** | Skill must run in sandbox without escape | Sandbox audit |

### GapResolver

| Invariant | Description | Test |
|-----------|-------------|------|
| **HUMAN_LOOP_DEFAULT** | Auto-resolution requires explicit opt-in | Config check |
| **RATE_LIMITED** | Max 10 resolution attempts per minute | Rate limiter |
| **DOMAIN_ALLOWLIST** | Only resolve from approved domains | Domain filter |
| **NO_PII** | Never include PII in resolution queries | PII scanner |

### SourceFuser

| Invariant | Description | Test |
|-----------|-------------|------|
| **PROVENANCE_COMPLETE** | Fused claim must cite all sources | Source count |
| **CONFIDENCE_AGGREGATED** | Combined confidence uses Bayesian update | Formula check |
| **CONTRADICTION_FLAGGED** | Conflicting claims must be marked | Conflict detection |

---

## Learning Invariants

### All Optimizers

| Invariant | Description | Test |
|-----------|-------------|------|
| **NO_REGRESSION** | Must not regress on golden set | Golden comparison |
| **IMPROVEMENT_LOCKED** | Verified improvements promoted to golden | Promotion workflow |
| **REPRODUCIBLE** | Same seed → same optimization trajectory | Seed control |

---

## Interface Invariants

### RheoEngine

| Invariant | Description | Test |
|-----------|-------------|------|
| **SYNTHESIS_PRESERVES** | Compression must preserve core meaning | Semantic similarity > 0.85 |
| **ANALYSIS_DISCOVERS** | Expansion must add new valid info | New content check |
| **BRANCH_BOUNDED** | Max 10 active branches per session | Branch limit |

### KnowledgeGraph

| Invariant | Description | Test |
|-----------|-------------|------|
| **ACYCLIC** | No circular entity references | Cycle detection |
| **VERSIONED** | All mutations create new version | Version increment |
| **QUERYABLE** | Historical state always retrievable | Time-travel query |

### APIServer

| Invariant | Description | Test |
|-----------|-------------|------|
| **AUTH_REQUIRED** | All mutating endpoints require auth | Auth check |
| **RATE_LIMITED** | Max 100 req/min per client | Rate limiter |
| **CORS_RESTRICTED** | CORS only for approved origins | Origin check |

---

## Update Protocol

When adding a new invariant:

1. Define invariant with clear threshold
2. Add to this document
3. Implement enforcement mechanism
4. Add test in evaluation harness
5. Add to guardrail metrics if critical
