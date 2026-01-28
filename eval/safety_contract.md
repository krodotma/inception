# Inception Safety Contract

> What We Refuse To Do · How We Fail Safely

---

## Absolute Constraints (Never Violate)

### Privacy

| Constraint | Description | Enforcement |
|------------|-------------|-------------|
| **NO_PII_EXTRACTION** | Never extract PII (SSN, credit cards, passwords) into knowledge graph | PII scanner on all outputs |
| **NO_PII_LOGGING** | Never log PII in any form | Log sanitization |
| **NO_PII_RESOLUTION** | Never include PII in gap resolution queries | Query sanitization |

### Security

| Constraint | Description | Enforcement |
|------------|-------------|-------------|
| **NO_CODE_EXECUTION** | Skills describe actions but never execute arbitrary code | Sandbox isolation |
| **NO_NETWORK_DEFAULT** | Gap resolution disabled by default | Explicit opt-in |
| **NO_CREDENTIAL_STORAGE** | Never persist user credentials | Memory-only handling |
| **NO_ELEVATED_PRIVILEGES** | All operations run as unprivileged user | Process isolation |

### Integrity

| Constraint | Description | Enforcement |
|------------|-------------|-------------|
| **NO_HALLUCINATION** | Claims must derive from source | Source overlap check |
| **NO_SILENT_MUTATE** | All mutations create audit trail | Version DAG |
| **NO_UNDECLARED_DEPS** | Skills must declare all dependencies | Dependency scan |

---

## Rate Limits

| Resource | Limit | Period | Action on Exceed |
|----------|-------|--------|------------------|
| API requests | 100 | per minute | 429 response |
| Gap resolution attempts | 10 | per minute | Queue with backoff |
| Learning iterations | 1000 | per hour | Pause with alert |
| Knowledge graph mutations | 500 | per minute | Queue with backoff |
| File operations | 50 | per minute | Reject with error |

---

## Domain Allowlists

### Gap Resolution Sources

Only these domains may be accessed during autonomous gap resolution:

```yaml
allowed_domains:
  - wikipedia.org
  - wikidata.org
  - dbpedia.org
  - schema.org
  - rfc-editor.org
  - datatracker.ietf.org
  - developer.mozilla.org
  - docs.python.org
  - docs.rust-lang.org
```

### Blocked Domains

Never access these domains:

```yaml
blocked_domains:
  - "*social*"       # Social networks
  - "*forum*"        # Forums
  - "*reddit*"       # Reddit
  - "*facebook*"     # Facebook
  - "*twitter*"      # Twitter/X
  - "*.onion"        # Tor
```

---

## Failure Behaviors

### Graceful Degradation

| Failure Mode | System Response | User Feedback |
|--------------|-----------------|---------------|
| LLM timeout | Return partial results + warning | "Extraction incomplete: [reason]" |
| LLM unavailable | Fall back to local models | "Using local extraction" |
| KB lookup failure | Skip linking, mark as unlinked | "Entity not linked: [name]" |
| Memory exhaustion | Pause, GC, resume | "Processing paused for resources" |
| Rate limit hit | Exponential backoff | "Rate limited, retrying in [N]s" |

### Circuit Breaker

If consecutive failures exceed threshold:

| Consecutive Failures | Action |
|---------------------|--------|
| 3 | Log warning |
| 5 | Reduce request rate by 50% |
| 10 | Open circuit, reject new requests |
| 60s cool-down | Half-open, test with single request |
| Test succeeds | Close circuit, resume normal |

---

## Human-in-the-Loop Requirements

These operations REQUIRE human approval:

| Operation | Default | Override |
|-----------|---------|----------|
| Gap resolution with network | Disabled | `--allow-network` flag |
| Skill execution | Disabled | `--execute` flag |
| Data deletion | Confirm prompt | `--force` flag |
| External KB modification | Disabled | Not overridable |

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **P0** | Security breach, data loss | Immediate | PII exposed in logs |
| **P1** | Service outage, safety violation | < 1 hour | Hallucination in critical claims |
| **P2** | Degraded service | < 4 hours | High latency |
| **P3** | Minor issue | < 24 hours | UI glitch |

### Response Playbooks

Located in: `docs/playbooks/`

- `playbook-pii-exposure.md`
- `playbook-hallucination.md`
- `playbook-outage.md`
- `playbook-security-breach.md`

---

## Audit Trail

All operations logged with:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 timestamp |
| `correlation_id` | Request tracking ID |
| `operation` | What was done |
| `actor` | Who/what initiated |
| `input_hash` | SHA256 of input (not content) |
| `output_hash` | SHA256 of output (not content) |
| `duration_ms` | How long it took |
| `status` | Success/failure |

---

## Review Schedule

This contract is reviewed:

- **Weekly**: SENTINEL reviews violation logs
- **Monthly**: Full contract audit with ARCHON
- **On incident**: Immediate review and update
