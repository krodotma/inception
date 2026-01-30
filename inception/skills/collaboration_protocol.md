# Inception Agent Collaboration Protocol

> PBTSO Orchestration · Agent Handoffs · Context Preservation

---

## Overview

This protocol governs how Inception's 12 agent personas collaborate, hand off work, and maintain context across the pipeline.

---

## Core Principles

### 1. Context Preservation

Every handoff must include the full `InceptionContext`:

```python
@dataclass
class HandoffPayload:
    from_agent: str
    to_agent: str
    context: InceptionContext
    artifacts: list[str]  # NIDs or paths
    reason: str
    priority: int  # 1=critical, 5=normal, 10=background
```

### 2. Entelexis Tracking

Every handoff advances or maintains Entelexis phase:

| Transition | Phase Change | Example |
|------------|--------------|---------|
| Request → Processing | potential → actualizing | User query → DIALECTICA |
| Processing → Complete | actualizing → actualized | Extraction → Graph build |
| Error/Timeout | actualizing → decaying | Failed extraction |

### 3. AUOM Compliance

All handoffs must pass 6-law check:

- **Lawfulness**: Within declared capabilities
- **Observability**: Handoff is logged
- **Provenance**: Source agent recorded
- **Recurrence**: Pattern matches prior successful handoffs
- **Evolvability**: Handoff can be improved
- **Boundedness**: Resource limits respected

---

## Handoff Patterns

### Pattern 1: Sequential Pipeline

```
INGEST → DECOMP → TEMPORAL → DIALECTICA → COMPILER
```

Each agent completes before handing off:

```python
async def sequential_pipeline(source_nid: int, context: InceptionContext):
    # Stage 1: Ingestion
    artifacts = await INGEST.process(source_nid, context)
    context = context.with_artifacts(artifacts)
    
    # Stage 2: Decomposition
    entities, claims = await DECOMP.extract(artifacts, context)
    context = context.with_entities(entities).with_claims(claims)
    
    # Stage 3: Temporal reasoning
    temporal = await TEMPORAL.analyze(claims, context)
    context = context.with_temporal(temporal)
    
    # Stage 4: Dialectical synthesis
    synthesis = await DIALECTICA.synthesize(context)
    
    return synthesis
```

### Pattern 2: Parallel Fan-Out

```
         ┌→ DECOMP (entities)
ARCHON ──┼→ TEMPORAL (intervals)
         └→ DIALECTICA (causal)
              ↓
           FUSION (merge)
```

ARCHON coordinates parallel work:

```python
async def parallel_fanout(source_nid: int, context: InceptionContext):
    # Fan out to parallel workers
    results = await asyncio.gather(
        DECOMP.extract_entities(source_nid, context),
        TEMPORAL.extract_intervals(source_nid, context),
        DIALECTICA.extract_causal(source_nid, context),
    )
    
    # Fan in to merger
    merged = await FUSION.merge(results, context)
    return merged
```

### Pattern 3: Dialectical Debate

```
DIALECTICA → FUSION
    ↑          ↓
    └── thesis/antithesis loop ──┘
```

For contradiction resolution:

```python
async def dialectical_debate(claims: list[Claim], context: InceptionContext):
    contradictions = await FUSION.find_contradictions(claims, context)
    
    for c in contradictions:
        # DIALECTICA proposes synthesis
        thesis = c.claim_a
        antithesis = c.claim_b
        synthesis = await DIALECTICA.propose_synthesis(thesis, antithesis, context)
        
        # FUSION validates
        if await FUSION.validate_synthesis(synthesis, context):
            claims = await FUSION.integrate_synthesis(claims, synthesis, context)
        else:
            # Escalate to human
            await escalate(c, synthesis, context)
    
    return claims
```

### Pattern 4: Socratic Questioning

```
User → DIALECTICA → Agent → DIALECTICA → User
           ↓            ↓
       clarify?     interpret
```

For ambiguous requests:

```python
async def socratic_clarify(user_input: str, context: InceptionContext):
    # DIALECTICA interprets
    interpretation = await DIALECTICA.interpret(user_input, context)
    
    if interpretation.confidence < 0.8:
        # Ask clarifying questions
        questions = await DIALECTICA.generate_clarifications(interpretation, context)
        user_response = await ask_user(questions)
        
        # Re-interpret with clarification
        interpretation = await DIALECTICA.interpret(
            user_input, 
            context.with_clarification(user_response)
        )
    
    return interpretation
```

---

## Agent Mesh Topologies

### Star (Default)

ARCHON at center, coordinates all:

```
        DECOMP
           ↑
TEMPORAL ← ARCHON → DIALECTICA
           ↓
        FUSION
```

### Peer Debate

Equal agents debate without coordinator:

```
DIALECTICA ↔ FUSION ↔ TEMPORAL
     ↑           ↑           ↑
     └───────────┴───────────┘
```

### Cascade

Escalation through tiers:

```
Tier 5 (CODEX) → Tier 4 (AUOM) → Tier 3 (DIALECTICA) → ... → Tier 0 (ARCHON)
```

---

## Error Handling

### Graceful Degradation

```python
async def with_fallback(primary: Agent, fallback: Agent, task: Task, context: InceptionContext):
    try:
        return await primary.execute(task, context)
    except AgentError as e:
        # Log and fallback
        await log_error(e, primary, context)
        return await fallback.execute(task, context)
```

### Circuit Breaker

```python
class AgentCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failures = 0
        self.state = "closed"  # closed | open | half-open
        
    async def call(self, agent: Agent, task: Task, context: InceptionContext):
        if self.state == "open":
            raise CircuitOpen()
        
        try:
            result = await agent.execute(task, context)
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise
```

---

## Event Emission

All collaboration emits to Pluribus bus:

```python
async def emit_handoff(handoff: HandoffPayload, context: InceptionContext):
    event = DimensionalEvent.create(
        topic="inception.agent.handoff",
        data={
            "from": handoff.from_agent,
            "to": handoff.to_agent,
            "reason": handoff.reason,
        },
        actor=handoff.from_agent,
        context=context.to_omega(),
    )
    await emit_dimensional(event)
```

---

## Eval Integration

Collaboration patterns are evaluated:

| Metric | Target | Description |
|--------|--------|-------------|
| Handoff latency | < 50ms | Time to transfer context |
| Context preservation | 100% | No data loss in handoff |
| Error recovery rate | > 95% | Successful fallback execution |
| Debate convergence | < 3 rounds | Dialectical resolution speed |
