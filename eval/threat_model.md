# Inception Threat Model

> Attack Surfaces · Risks · Mitigations

---

## System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        THREAT BOUNDARY                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ User Input  │  │  LLM APIs   │  │   External KBs          │  │
│  │ - Videos    │  │ - OpenAI    │  │   - Wikidata            │  │
│  │ - Documents │  │ - Anthropic │  │   - DBpedia             │  │
│  │ - URLs      │  │ - Local     │  │   - Wikipedia           │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
│         │                │                      │                │
│         ▼                ▼                      ▼                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     INCEPTION CORE                          ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  ││
│  │  │  Extractors  │  │   Learning   │  │  Knowledge Graph │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                │                      │                │
│         ▼                ▼                      ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │    API      │  │   Skills    │  │      Exports            │  │
│  │   Server    │  │ (Sandbox)   │  │  (Obsidian, ActionPacks)│  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Attack Surfaces

### A1: Malicious Input

| Vector | Attack | Impact | Likelihood | Risk |
|--------|--------|--------|------------|------|
| Adversarial text | Prompt injection to manipulate extraction | Medium | High | **High** |
| Malformed media | Crash via corrupted video/PDF | Low | Medium | Medium |
| XSS in content | Stored XSS if content rendered unsanitized | High | Low | Medium |
| Path traversal | Malicious filenames accessing system files | High | Low | Medium |

**Mitigations**:
- Input sanitization before LLM prompts
- Media format validation before processing
- HTML escaping in all outputs
- Filename normalization, reject `..` patterns

### A2: LLM API Attacks

| Vector | Attack | Impact | Likelihood | Risk |
|--------|--------|--------|------------|------|
| Jailbreak | Bypass system prompt to extract harmful content | Medium | Medium | Medium |
| Denial of wallet | Malicious input causing expensive API calls | Medium | Medium | Medium |
| Data exfiltration | LLM leaking training data | Low | Low | Low |

**Mitigations**:
- System prompt hardening with safety reminders
- Token limits per request
- Output validation before acceptance
- No sensitive data in prompts

### A3: External KB Compromise

| Vector | Attack | Impact | Likelihood | Risk |
|--------|--------|--------|------------|------|
| Poisoned data | Malicious edits to Wikipedia/Wikidata | Medium | Low | Low |
| MITM | Attacker modifies KB responses | High | Low | Medium |
| KB unavailable | DoS against external services | Low | Medium | Low |

**Mitigations**:
- HTTPS only for all external requests
- Cross-reference multiple sources
- Cache with TTL, fallback to stale on failure
- Mark claims with source confidence

### A4: Skill Execution Risks

| Vector | Attack | Impact | Likelihood | Risk |
|--------|--------|--------|------------|------|
| Code injection | Skill contains malicious code | Critical | Medium | **High** |
| Resource exhaustion | Skill consumes all CPU/memory | Medium | Medium | Medium |
| Network abuse | Skill makes unauthorized requests | High | Medium | **High** |

**Mitigations**:
- Skills never executed by default (human approval)
- Sandbox with resource limits (CPU, memory, time)
- Network disabled in sandbox by default
- Skill review checklist before execution

### A5: API Abuse

| Vector | Attack | Impact | Likelihood | Risk |
|--------|--------|--------|------------|------|
| Rate limit bypass | Distributed attack from many IPs | Medium | Medium | Medium |
| Auth bypass | Token reuse, session hijacking | High | Low | Medium |
| IDOR | Accessing other users' data | High | Low | Medium |

**Mitigations**:
- Per-IP and per-token rate limiting
- Short-lived tokens with refresh
- Resource ownership checks on all endpoints
- Audit logging of all access

---

## Sensitive Data

| Data Type | Classification | Protection |
|-----------|----------------|------------|
| User credentials | Critical | Never stored, memory-only |
| API keys | Critical | Environment variables, never logged |
| Source content | Sensitive | Hash in logs, not content |
| Extracted claims | Internal | Access-controlled, audit logged |
| User preferences | Personal | Encrypted at rest |

---

## STRIDE Analysis

| Threat | Description | Mitigation |
|--------|-------------|------------|
| **S**poofing | Attacker impersonates user | Token-based auth, HTTPS |
| **T**ampering | Malicious modification of data | Versioned DAG, integrity checks |
| **R**epudiation | Denying actions | Comprehensive audit trail |
| **I**nformation disclosure | Leaking sensitive data | PII scanning, output filtering |
| **D**enial of service | Making system unavailable | Rate limits, circuit breakers |
| **E**levation of privilege | Gaining unauthorized access | Sandboxing, least privilege |

---

## Risk Matrix

| Risk Level | Description | Threshold |
|------------|-------------|-----------|
| **Critical** | Immediate action required | Likelihood × Impact > 20 |
| **High** | Address within 24 hours | Likelihood × Impact 12-20 |
| **Medium** | Address within 1 week | Likelihood × Impact 6-12 |
| **Low** | Monitor, address in sprint | Likelihood × Impact < 6 |

Scoring: Likelihood (1-5) × Impact (1-5)

---

## Current High/Critical Risks

| ID | Risk | Status | Owner |
|----|------|--------|-------|
| A1-1 | Prompt injection | Open | SENTINEL |
| A4-1 | Skill code injection | Open | SENTINEL |
| A4-3 | Skill network abuse | Open | SENTINEL |

---

## Review Schedule

- **Weekly**: Check for new CVEs in dependencies
- **Monthly**: Full threat model review
- **On change**: Re-assess affected attack surfaces
