# Inception Error Taxonomy

> 15 Named Error Buckets for Diagnosis

---

## Extraction Errors (E1-E5)

| Code | Name | Description | Example |
|------|------|-------------|---------|
| **E1** | `CLAIM_MISS` | Valid claim not extracted | "OAuth uses tokens" missed entirely |
| **E2** | `CLAIM_HALLUC` | Extracted claim not in source | Added "OAuth 3.0" when source said "2.0" |
| **E3** | `SPO_MALFORM` | Subject/Predicate/Object malformed | Subject empty, predicate too vague |
| **E4** | `ENTITY_MISS` | Entity not recognized | "RFC 6749" not tagged as entity |
| **E5** | `ENTITY_WRONG` | Entity misclassified | Person classified as Organization |

---

## Linking Errors (L1-L3)

| Code | Name | Description | Example |
|------|------|-------------|---------|
| **L1** | `LINK_MISS` | No link when one exists | "OAuth" not linked to Wikidata Q1650915 |
| **L2** | `LINK_WRONG` | Linked to wrong entity | "Apple" linked to fruit instead of company |
| **L3** | `LINK_AMBIG` | Ambiguous link not resolved | "Python" could be language or snake |

---

## Temporal Errors (T1-T3)

| Code | Name | Description | Example |
|------|------|-------------|---------|
| **T1** | `TIME_MISS` | Temporal info not captured | "In 2012" not extracted |
| **T2** | `TIME_WRONG` | Wrong temporal relation | "Before" extracted as "after" |
| **T3** | `VALID_MISS` | Validity window not tracked | Old info treated as current |

---

## Procedural Errors (P1-P2)

| Code | Name | Description | Example |
|------|------|-------------|---------|
| **P1** | `STEP_ORDER` | Procedure steps out of order | Step 3 before Step 2 |
| **P2** | `STEP_MISS` | Critical step omitted | Missing error handling step |

---

## System Errors (S1-S2)

| Code | Name | Description | Example |
|------|------|-------------|---------|
| **S1** | `TIMEOUT` | Processing exceeded time limit | > 500ms for single extraction |
| **S2** | `RESOURCE` | Resource exhaustion | OOM, file handle leak |

---

## Diagnosis Flow

```
Error Detected
     │
     ├── Is it in the taxonomy? 
     │        │
     │        ├── YES → Record with code, fix root cause
     │        │
     │        └── NO → Add new error type (max 20 total)
     │
     ├── Classify cause:
     │        │
     │        ├── SPEC_GAP: Behavior never defined
     │        │
     │        ├── EVAL_GAP: Harness didn't catch it
     │        │
     │        └── SYSTEM_GAP: Implementation bug
     │
     └── Fix and verify against goldens
```

---

## Error Counts (Current)

| Code | Count | Trend |
|------|-------|-------|
| E1 | 0 | — |
| E2 | 0 | — |
| E3 | 0 | — |
| E4 | 0 | — |
| E5 | 0 | — |
| L1 | 0 | — |
| L2 | 0 | — |
| L3 | 0 | — |
| T1 | 0 | — |
| T2 | 0 | — |
| T3 | 0 | — |
| P1 | 0 | — |
| P2 | 0 | — |
| S1 | 0 | — |
| S2 | 0 | — |

---

## Adding New Error Types

1. Ensure < 20 total types (cognitive limit)
2. Error must be distinct from existing types
3. Add to this document with code, name, description, example
4. Update `run_eval.py` to detect new type
