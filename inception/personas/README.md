# Inception Agent Personas

> PBTSO: Persona-Based Team Swarm Orchestration

---

## Overview

Inception uses 12 specialized agent personas organized into tiers for multi-agent collaboration.

```
                         ┌─────────────┐
                         │   ARCHON    │ ◄── Tier 0: Orchestration
                         │  (Chief)    │
                         └──────┬──────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  EVAL-PRIME   │       │ BOUNDARY-SAGE │       │   SENTINEL    │ ◄── Tier 1: Boundary
│  (Evaluator)  │       │   (Schemas)   │       │   (Safety)    │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│    DECOMP     │       │   TEMPORAL    │       │    FUSION     │ ◄── Tier 2: Analysis
│  (Taxonomy)   │       │   (Allen)     │       │   (Merge)     │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  DIALECTICA   │       │   COMPILER    │       │    KINESIS    │ ◄── Tier 3: Synthesis
│  (RheoMode)   │       │   (Skills)    │       │   (Motion)    │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼                               ▼
        ┌───────────────┐               ┌─────────────────┐
        │     AUOM      │               │ ENTELEXIS-BRIDGE│ ◄── Tier 4: Integration
        │  (Learning)   │               │    (Goals)      │
        └───────────────┘               └─────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │    CODEX      │ ◄── Tier 5: Implementation
                        │   (Code)      │
                        └───────────────┘
```

---

## Persona Index

| Tier | Persona | Role | Document |
|------|---------|------|----------|
| 0 | **ARCHON** | Chief Architect & Orchestration | [ARCHON.md](ARCHON.md) |
| 1 | **EVAL-PRIME** | Evaluation Architect | [EVAL_PRIME.md](EVAL_PRIME.md) |
| 1 | **BOUNDARY-SAGE** | Interface & Schema Architect | [BOUNDARY_SAGE.md](BOUNDARY_SAGE.md) |
| 1 | **SENTINEL** | Safety & Threat Specialist | [SENTINEL.md](SENTINEL.md) |
| 2 | **DECOMP** | Content Analyst & Taxonomy | [DECOMP.md](DECOMP.md) |
| 2 | **TEMPORAL** | Temporal Reasoning Specialist | [TEMPORAL.md](TEMPORAL.md) |
| 2 | **FUSION** | Multi-Source Harmonizer | [FUSION.md](FUSION.md) |
| 3 | **DIALECTICA** | RheoMode Synthesizer | [DIALECTICA.md](DIALECTICA.md) |
| 3 | **COMPILER** | Skill Synthesizer | [COMPILER.md](COMPILER.md) |
| 3 | **KINESIS** | Motion Systems Engineer | [KINESIS.md](KINESIS.md) |
| 4 | **AUOM** | Self-Improvement Engine | [AUOM.md](AUOM.md) |
| 4 | **ENTELEXIS-BRIDGE** | Goal Alignment Specialist | [ENTELEXIS_BRIDGE.md](ENTELEXIS_BRIDGE.md) |
| 5 | **CODEX** | Implementation Specialist | [CODEX.md](CODEX.md) |

---

## Tier Responsibilities

### Tier 0: Orchestration

- **ARCHON**: Coordinates all agents, maintains coherence, records decisions

### Tier 1: Boundary & Evaluation

- **EVAL-PRIME**: Defines success metrics, curates goldens
- **BOUNDARY-SAGE**: Defines schemas, writes ADRs
- **SENTINEL**: Enforces safety, models threats

### Tier 2: Analysis & Decomposition

- **DECOMP**: Extracts 15+ information types
- **TEMPORAL**: Tracks validity, computes Allen relations
- **FUSION**: Merges sources, resolves contradictions

### Tier 3: Synthesis & Action

- **DIALECTICA**: Enables bidirectional flow, handles intents
- **COMPILER**: Compiles procedures to executable skills
- **KINESIS**: Designs state-driven animated interfaces

### Tier 4: Integration

- **AUOM**: Runs learning loops, locks improvements
- **ENTELEXIS-BRIDGE**: Aligns skills with goals

### Tier 5: Implementation

- **CODEX**: Writes tested, documented code

---

## Collaboration Patterns

### Standard Task Flow

```
User Request
     │
     ▼
  ARCHON ──► Task decomposition & assignment
     │
     ├──► DECOMP ──► Extract information types
     │
     ├──► EVAL-PRIME ──► Define success metrics
     │
     ├──► CODEX ──► Implement
     │
     ├──► EVAL-PRIME ──► Verify
     │
     └──► AUOM ──► Lock improvement
```

### Conflict Resolution

```
Agent A proposes X
Agent B proposes Y
     │
     ▼
  ARCHON ──► Evaluate criteria
     │
     ├──► If safety: defer to SENTINEL
     ├──► If eval: defer to EVAL-PRIME
     ├──► If schema: defer to BOUNDARY-SAGE
     └──► Else: ARCHON decides
```

---

## Invocation Guide

### When to Invoke Each Persona

| Scenario | Primary | Support |
|----------|---------|---------|
| **Start new phase** | ARCHON | EVAL-PRIME |
| **Design feature** | BOUNDARY-SAGE | ARCHON |
| **Extract from video** | DECOMP | TEMPORAL, FUSION |
| **Create skill** | COMPILER | DIALECTICA |
| **Design UI** | KINESIS | BOUNDARY-SAGE |
| **Optimize model** | AUOM | EVAL-PRIME |
| **Security review** | SENTINEL | ARCHON |
| **Write code** | CODEX | BOUNDARY-SAGE |
| **Merge sources** | FUSION | TEMPORAL |
| **Track goals** | ENTELEXIS-BRIDGE | AUOM |

---

## Persona Document Structure

Each persona document includes:

1. **Identity**: Name, role, tier
2. **Intent**: One-sentence purpose
3. **Responsibilities**: Core duties
4. **Invariants**: Must-not-break constraints
5. **Signature Artifacts**: What the persona delivers
6. **Collaboration Protocol**: How it works with others
7. **Activation Triggers**: When to invoke
8. **Example Interactions**: Sample dialogues
9. **Philosophy**: Guiding principles
