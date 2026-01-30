# Inception Extraction Skills Registry

> PBTSO Skill Definitions · Eval Criteria · Neural Integration Points

---

## Overview

This registry defines the extraction skills used by Inception agents. Each skill category follows the **Taxonomic Type System** from the approved 300-step plan.

---

## Skill Categories

| Category | ID Range | Agent | Purpose |
|----------|----------|-------|---------|
| Declarative | D1-D4 | DECOMP | Facts, definitions, classifications, relations |
| Procedural | P1-P5 | COMPILER | Steps, conditionals, loops, errors, prerequisites |
| Causal | C1-C4 | DIALECTICA | Causes, motivations, purposes, consequences |
| Temporal | T1-T4 | TEMPORAL | Sequences, durations, validity, periodicity |
| Meta | M1-M4 | FUSION | Confidence, attribution, contradiction, update |

---

## D: Declarative Extraction Skills

### D1: Factual Claims

```yaml
skill_id: declarative_factual_claims
agent: DECOMP
description: Extract verifiable factual claims from content
input_schema:
  text: string
  source_nid: int
  context: InceptionContext
output_schema:
  claims:
    - statement: string
      subject: string
      predicate: string
      object: string
      confidence: float
      evidence_spans: list[int]
      modality: certainty | possibility | necessity

eval_criteria:
  precision: claims that are actually stated (not inferred) / total claims
  recall: extracted claims / all factual claims in source
  spo_accuracy: correct subject-predicate-object extraction rate
  minimum_f1: 0.85
  
neural_hooks:
  pre: embedding_similarity_boost(domain_terms)
  post: confidence_calibration(historical_accuracy)
```

### D2: Definitions

```yaml
skill_id: declarative_definitions
agent: DECOMP
description: Extract term definitions and explanations
input_schema:
  text: string
  context: InceptionContext
output_schema:
  definitions:
    - term: string
      definition: string
      domain: string | null
      is_authoritative: bool
      source_type: explicit | implicit | contextual

eval_criteria:
  term_detection_rate: detected definitions / actual definitions
  definition_completeness: essential properties captured / total properties
  domain_accuracy: correct domain assignment rate
  minimum_f1: 0.80
```

### D3: Classifications

```yaml
skill_id: declarative_classifications
agent: DECOMP
description: Extract taxonomic classifications and categories
input_schema:
  text: string
  context: InceptionContext
output_schema:
  classifications:
    - entity: string
      category: string
      parent_category: string | null
      relation_type: is-a | instance-of | member-of
      confidence: float

eval_criteria:
  entity_extraction_rate: extracted / actual classifiable entities
  category_accuracy: correct category assignment rate
  hierarchy_consistency: valid parent-child relations / total relations
  minimum_f1: 0.80
```

### D4: Relations

```yaml
skill_id: declarative_relations
agent: DECOMP
description: Extract entity relationships and associations
input_schema:
  text: string
  context: InceptionContext
output_schema:
  relations:
    - subject: string
      relation_type: string
      object: string
      directionality: unidirectional | bidirectional
      strength: float
      temporal_scope: Allen interval | null

eval_criteria:
  relation_detection_rate: extracted / actual relations
  type_accuracy: correct relation type assignment
  directionality_accuracy: correct direction detection
  minimum_f1: 0.75
```

---

## P: Procedural Extraction Skills

### P1: Ordered Steps

```yaml
skill_id: procedural_ordered_steps
agent: COMPILER
description: Extract step-by-step procedures with ordering
input_schema:
  text: string
  context: InceptionContext
output_schema:
  procedures:
    - name: string
      goal: string
      steps:
        - order: int
          action: string
          description: string
          dependencies: list[int]
      
eval_criteria:
  procedure_detection: identified procedures / actual procedures
  step_completeness: extracted steps / actual steps
  ordering_accuracy: correctly ordered pairs / total pairs
  minimum_f1: 0.85
```

### P2: Conditionals

```yaml
skill_id: procedural_conditionals
agent: COMPILER
description: Extract conditional logic and branching
input_schema:
  procedure: Procedure
  context: InceptionContext
output_schema:
  conditionals:
    - step_id: int
      condition: string
      if_true: string | int  # action or step ref
      if_false: string | int | null
      condition_type: precondition | decision | guard

eval_criteria:
  conditional_detection: found / actual conditionals
  condition_parsing: correctly parsed conditions
  branch_accuracy: correct if/else assignment
  minimum_f1: 0.80
```

### P3: Loops

```yaml
skill_id: procedural_loops
agent: COMPILER
description: Extract iterative patterns and repetition
input_schema:
  procedure: Procedure
  context: InceptionContext
output_schema:
  loops:
    - step_range: [int, int]
      loop_type: for_each | while | until | repeat_n
      iterator: string | null
      termination_condition: string
      estimated_iterations: int | null

eval_criteria:
  loop_detection: found loops / actual loops
  type_accuracy: correct loop type classification
  termination_clarity: clearly defined termination / total loops
  minimum_f1: 0.75
```

### P4: Error Handling

```yaml
skill_id: procedural_error_handling
agent: COMPILER
description: Extract error cases and recovery procedures
input_schema:
  procedure: Procedure
  context: InceptionContext
output_schema:
  error_handlers:
    - step_id: int
      error_type: string
      symptom: string
      recovery_action: string
      severity: minor | major | critical

eval_criteria:
  error_detection: found errors / mentioned errors
  recovery_completeness: errors with recovery / total errors
  severity_accuracy: correct severity classification
  minimum_f1: 0.70
```

### P5: Prerequisites

```yaml
skill_id: procedural_prerequisites
agent: COMPILER
description: Extract prerequisites and requirements
input_schema:
  procedure: Procedure
  context: InceptionContext
output_schema:
  prerequisites:
    - prereq_type: knowledge | tool | permission | resource | state
      description: string
      optional: bool
      alternatives: list[string]

eval_criteria:
  prereq_detection: found / actual prerequisites
  type_accuracy: correct type classification
  optionality_accuracy: correct optional/required classification
  minimum_f1: 0.80
```

---

## C: Causal Extraction Skills

### C1: Causation

```yaml
skill_id: causal_causation
agent: DIALECTICA
description: Extract cause-effect relationships
input_schema:
  text: string
  context: InceptionContext
output_schema:
  causal_links:
    - cause: string
      effect: string
      mechanism: string | null
      strength: weak | moderate | strong | deterministic
      temporal_lag: immediate | delayed | variable

eval_criteria:
  causal_detection: found / actual causal statements
  direction_accuracy: correct cause→effect direction
  mechanism_extraction: mechanisms captured / total links
  minimum_f1: 0.75
```

### C2: Motivation

```yaml
skill_id: causal_motivation
agent: DIALECTICA
description: Extract motivations and reasons for actions
input_schema:
  text: string
  context: InceptionContext
output_schema:
  motivations:
    - action: string
      motivation: string
      actor: string | null
      motivation_type: goal | fear | obligation | preference

eval_criteria:
  motivation_detection: found / actual motivations
  type_accuracy: correct motivation type
  actor_accuracy: correct actor attribution
  minimum_f1: 0.70
```

### C3: Purpose

```yaml
skill_id: causal_purpose
agent: DIALECTICA
description: Extract purposes, goals, and intentions (Entelexis alignment)
input_schema:
  text: string
  context: InceptionContext
output_schema:
  purposes:
    - entity: string  # What has the purpose
      purpose: string  # The declared goal
      entelexis_phase: potential | actualizing | actualized | decaying
      alignment_score: float  # How well current state serves purpose

eval_criteria:
  purpose_detection: found / actual purposes
  entelexis_mapping: correctly phased / total purposes
  alignment_calculation: valid scores / total purposes
  minimum_f1: 0.80
```

### C4: Consequence

```yaml
skill_id: causal_consequence
agent: DIALECTICA
description: Extract consequences and implications
input_schema:
  text: string
  context: InceptionContext
output_schema:
  consequences:
    - antecedent: string
      consequent: string
      polarity: positive | negative | neutral
      certainty: certain | likely | possible | unlikely
      scope: local | system | global

eval_criteria:
  consequence_detection: found / actual consequences
  polarity_accuracy: correct positive/negative classification
  certainty_calibration: calibrated certainty scores
  minimum_f1: 0.75
```

---

## T: Temporal Extraction Skills

### T1: Sequence

```yaml
skill_id: temporal_sequence
agent: TEMPORAL
description: Extract temporal ordering using Allen intervals
input_schema:
  events: list[string]
  context: InceptionContext
output_schema:
  sequences:
    - event_a: string
      event_b: string
      allen_relation: before | meets | overlaps | starts | during | finishes | equals

eval_criteria:
  relation_detection: found / actual temporal relations
  allen_accuracy: correct Allen relation / total relations
  transitivity_consistency: consistent transitive closure
  minimum_f1: 0.85
```

### T2: Duration

```yaml
skill_id: temporal_duration
agent: TEMPORAL
description: Extract durations and time spans
input_schema:
  text: string
  context: InceptionContext
output_schema:
  durations:
    - entity: string
      duration_value: float
      duration_unit: seconds | minutes | hours | days | weeks | months | years
      precision: exact | approximate | range
      range: [float, float] | null

eval_criteria:
  duration_detection: found / actual duration mentions
  value_accuracy: correct value extraction (within 10%)
  unit_accuracy: correct unit extraction
  minimum_f1: 0.80
```

### T3: Validity Window

```yaml
skill_id: temporal_validity
agent: TEMPORAL
description: Extract validity periods for claims
input_schema:
  claims: list[Claim]
  context: InceptionContext
output_schema:
  validity_windows:
    - claim_id: int
      valid_from: datetime | null
      valid_until: datetime | null
      validity_type: permanent | temporary | conditional
      decay_probability: float  # For Entelexis decaying phase

eval_criteria:
  window_detection: claims with windows / claims with temporal bounds
  boundary_accuracy: correct start/end detection
  type_accuracy: correct validity type classification
  minimum_f1: 0.75
```

### T4: Periodicity

```yaml
skill_id: temporal_periodicity
agent: TEMPORAL
description: Extract recurring patterns and schedules
input_schema:
  text: string
  context: InceptionContext
output_schema:
  periodicities:
    - entity: string
      pattern: string  # cron-like or human-readable
      frequency: daily | weekly | monthly | yearly | irregular
      exceptions: list[string]

eval_criteria:
  periodicity_detection: found / actual periodic patterns
  pattern_accuracy: correctly parsed patterns
  exception_coverage: captured exceptions / mentioned exceptions
  minimum_f1: 0.70
```

---

## M: Meta Extraction Skills

### M1: Confidence

```yaml
skill_id: meta_confidence
agent: FUSION
description: Extract and calibrate confidence levels
input_schema:
  extractions: list[Any]
  context: InceptionContext
output_schema:
  confidence_annotations:
    - extraction_id: int
      stated_confidence: float | null  # From source
      computed_confidence: float  # Our computation
      aleatoric_uncertainty: float  # Inherent randomness
      epistemic_uncertainty: float  # Knowledge gaps

eval_criteria:
  calibration_error: |predicted - actual| over held-out test set
  separation: confidence gap between correct/incorrect predictions
  coverage: predictions with meaningful confidence / total
  target_calibration_error: < 0.15
```

### M2: Attribution

```yaml
skill_id: meta_attribution
agent: FUSION
description: Extract source attribution and provenance
input_schema:
  claims: list[Claim]
  context: InceptionContext
output_schema:
  attributions:
    - claim_id: int
      source_chain: list[string]  # Provenance chain
      original_author: string | null
      citation_type: direct | paraphrase | synthesis
      verification_status: verified | unverified | disputed

eval_criteria:
  attribution_rate: claims with attribution / total claims
  chain_completeness: full chains / partial chains
  verification_accuracy: correct verification status
  minimum_f1: 0.80
```

### M3: Contradiction

```yaml
skill_id: meta_contradiction
agent: FUSION
description: Detect and analyze contradictions (dialectical)
input_schema:
  claims: list[Claim]
  context: InceptionContext
output_schema:
  contradictions:
    - claim_a: int
      claim_b: int
      contradiction_type: direct | indirect | contextual
      resolution_hint: string | null
      synthesis_possible: bool  # Can thesis+antithesis → synthesis?

eval_criteria:
  detection_rate: found contradictions / actual contradictions
  type_accuracy: correct contradiction type
  resolution_feasibility: actionable hints / total contradictions
  minimum_f1: 0.75
```

### M4: Update

```yaml
skill_id: meta_update
agent: FUSION
description: Detect updates, corrections, and supersessions
input_schema:
  claims: list[Claim]
  knowledge_base: KnowledgeGraph
  context: InceptionContext
output_schema:
  updates:
    - old_claim: int | string  # Existing KB claim or external ref
      new_claim: int
      update_type: correction | refinement | supersession | retraction
      effective_date: datetime | null

eval_criteria:
  update_detection: found updates / actual updates
  type_accuracy: correct update type classification
  kb_integration: successfully integrated / detected updates
  minimum_f1: 0.70
```

---

## Skill Composition

Skills can be composed for complex extractions:

```python
# Example: Full source analysis
async def analyze_source(source_nid: int, context: InceptionContext):
    # Layer 1: Declarative
    claims = await D1_factual_claims(source_nid, context)
    definitions = await D2_definitions(source_nid, context)
    
    # Layer 2: Temporal (depends on claims)
    sequences = await T1_sequence(claims, context)
    validity = await T3_validity(claims, context)
    
    # Layer 3: Causal (depends on claims + temporal)
    causal = await C1_causation(claims, context)
    purposes = await C3_purpose(claims, context)  # Entelexis
    
    # Layer 4: Meta (depends on all above)
    contradictions = await M3_contradiction(claims, context)
    confidence = await M1_confidence(all_extractions, context)
    
    return synthesis(claims, definitions, sequences, causal, purposes, contradictions)
```

---

## Neural Adaptation Points

Each skill has neural interception points for adaptive learning:

| Hook Point | Signal | Adaptation |
|------------|--------|------------|
| `pre_extract` | Domain embeddings | Boost domain-relevant patterns |
| `post_extract` | User corrections | Adjust extraction thresholds |
| `pre_classify` | Historical accuracy | Bias toward reliable categories |
| `post_classify` | Acceptance rate | Learn preferred classifications |
| `pre_confidence` | Calibration history | Adjust confidence scaling |
| `post_confidence` | Outcome feedback | Update calibration model |

---

## Eval Integration

All skills integrate with the eval harness:

```bash
# Run skill-specific evaluation
uv run inception eval --skill declarative_factual_claims --goldens eval/goldens.jsonl

# Run full skill suite
uv run inception eval --skill-suite all --report eval/skill_report.md
```
