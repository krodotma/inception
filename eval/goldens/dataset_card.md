# Dataset Card: Inception Seed Sources

---

## Overview

| Attribute | Value |
|-----------|-------|
| **Name** | Inception Seed Goldens v1.0 |
| **Created** | 2026-01-28 |
| **Size** | 50 examples |
| **Categories** | Claims (20), Entities (15), Temporal (10), Procedures (5) |
| **Domain** | OAuth/OIDC security protocols |
| **Language** | English |

---

## Intended Use

### Primary Use
- Evaluation of Inception extraction capabilities
- Baseline measurement for scorecard metrics
- Regression testing after changes

### Out of Scope
- Training data (too small)
- Production evaluation (domain-limited)
- Multilingual evaluation (English only)

---

## Data Composition

### Category Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| Claims | 20 | 40% |
| Entities | 15 | 30% |
| Temporal | 10 | 20% |
| Procedures | 5 | 10% |

### Modality Distribution (Claims)

| Modality | Count |
|----------|-------|
| Assertion | 12 |
| Possibility | 4 |
| Necessity | 3 |
| Negation | 1 |

### Entity Type Distribution

| Type | Count |
|------|-------|
| PROTOCOL | 6 |
| DOCUMENT | 5 |
| ORGANIZATION | 6 |
| PERSON | 1 |
| CONCEPT | 5 |
| PARAMETER | 3 |
| Other | 4 |

---

## Collection Process

### Source
Examples crafted by domain experts based on:
- OAuth 2.0 specification (RFC 6749)
- OpenID Connect specification
- OAuth 2.1 draft
- Common OAuth implementation guides

### Annotation Process
1. Expert writes input sentence
2. Expert annotates expected output
3. Second expert reviews
4. Added to goldens.jsonl

### Quality Assurance
- All examples reviewed by at least 2 annotators
- Schema validation on all expected outputs
- Consistency check for similar inputs

---

## Known Limitations

### Domain Bias
- All examples from OAuth/OIDC domain
- May not generalize to other technical domains
- Limited coverage of edge cases

### Size Limitations
- 50 examples insufficient for statistical confidence
- Each category has limited diversity
- Adversarial cases not included

### Annotation Limitations
- Single annotation source (no crowdsourcing)
- Possible annotator bias toward explicit claims
- Temporal relations may have subjective interpretation

---

## Bias Assessment

### Identified Biases

| Bias Type | Description | Mitigation |
|-----------|-------------|------------|
| Domain | All security/auth focused | Add examples from other domains |
| Formality | All technical writing | Add informal/spoken examples |
| Recency | All modern (2012-2024) | Add historical examples |
| Length | All short sentences | Add paragraph-level examples |

### Recommended Expansions
1. Add 50 examples from different technical domains
2. Add 20 adversarial/edge case examples
3. Add 30 informal/conversational examples
4. Add 20 multi-sentence paragraph examples

---

## Provenance

### Original Sources
- RFC 6749: The OAuth 2.0 Authorization Framework
- RFC 6750: The OAuth 2.0 Authorization Framework: Bearer Token Usage
- RFC 7519: JSON Web Token (JWT)
- RFC 7662: OAuth 2.0 Token Introspection
- OpenID Connect Core 1.0

### License
- Examples are derivative works for evaluation purposes
- Original RFCs are public domain (IETF contribution)
- Use limited to evaluation, not redistribution

---

## Maintenance

### Versioning
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-28 | Initial seed set |

### Update Protocol
1. New examples require expert review
2. Schema must validate before merge
3. Scorecard re-run after any update
4. Version increment on each change

### Contact
- Owner: DECOMP agent
- Reviewer: EVAL-PRIME agent
