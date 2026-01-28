<p align="center">
  <img src="docs/assets/logo.svg" alt="Inception" width="120" height="120">
</p>

<h1 align="center">Inception</h1>

<p align="center">
  <strong>Local-First Knowledge Compiler for Multimodal Sources</strong>
</p>

<p align="center">
  <a href="#what-inception-does">What It Does</a> •
  <a href="#core-capabilities">Capabilities</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#learning-engine">Learning Engine</a>
</p>

---

## What Inception Does

Inception transforms unstructured learning materials—YouTube videos, web pages, PDFs, presentations—into a **temporal knowledge hypergraph** with claims, entities, procedures, and detected gaps, all stored locally in LMDB.

```
                         ┌──────────────────────────────────────┐
                         │           YOUR KNOWLEDGE             │
                         └──────────────────────────────────────┘
                                          ▲
                                          │
    ┌────────────┐   ┌────────────┐   ┌───┴───────┐   ┌────────────┐
    │  Ingest    │ → │  Extract   │ → │  Analyze  │ → │   Output   │
    │  Sources   │   │  Content   │   │  Meaning  │   │  Actions   │
    └────────────┘   └────────────┘   └───────────┘   └────────────┘
       YouTube         Whisper ASR      Claim SPO       ActionPacks
       Web Pages       Scene Detect     Entities        Skills
       PDFs/Docs       OCR/VLM          Procedures      Obsidian
                                        Gaps            Export
```

---

## Core Capabilities

### 1. Multimodal Ingestion

| Source Type | Method | What Gets Extracted |
|-------------|--------|---------------------|
| **YouTube** | yt-dlp + Whisper | Timestamped transcript, keyframes, scene types |
| **Web Pages** | Trafilatura | Clean text, metadata, publication dates |
| **PDF/PPTX/DOCX** | pdfplumber, python-pptx | Text by page, figures, tables |
| **Images** | VLM (LLaVA, GPT-4V) | Descriptions, diagrams, charts |

### 2. Semantic Extraction

**Claims** — Subject-Predicate-Object triples with modality tracking:
```python
Claim(
    text="OAuth uses bearer tokens for authentication",
    subject="OAuth",
    predicate="uses",
    object="bearer tokens for authentication",
    modality="assertion",        # assertion | possibility | necessity | negation
    hedges=["typically"],        # uncertainty markers
    confidence=Confidence(0.92, 0.88)  # (aleatoric, epistemic)
)
```

**Entities** — Named entities clustered and linked to Wikidata/DBpedia:
```python
Entity(
    text="OAuth 2.0",
    entity_type="PROTOCOL",
    normalized="oauth-2.0",
    wikidata_id="Q643697",
    confidence=0.94
)
```

**Procedures** — Step-by-step instructions with preconditions:
```python
Procedure(
    title="Deploy OAuth Server",
    goal="Set up a production OAuth authorization server",
    steps=[
        ProcedureStep(1, "Generate RSA key pair", action_verb="generate"),
        ProcedureStep(2, "Configure JWKS endpoint", action_verb="configure"),
        ...
    ],
    prerequisites=["Docker installed", "Domain configured"]
)
```

**Gaps** — Detected uncertainties classified by type and severity:
```python
Gap(
    gap_type=GapType.UNDEFINED_TERM,
    description="'PKCE code_verifier' referenced but not defined",
    context_text="Using PKCE flow with code_verifier...",
    severity="major",
    is_epistemic=True  # knowledge gap (vs. aleatoric = signal quality)
)
```

### 3. Allen Temporal Reasoning

The system understands time. Facts have validity windows taken from extracted temporal expressions:

```
┌────────────────────────────────────────────────────────────────┐
│ Allen's 13 Interval Relations                                   │
├────────────────────────────────────────────────────────────────┤
│  OAuth 1.0 spec ──────────────────                             │
│                        OAuth 2.0 spec ────────────────────     │
│                                                                │
│  Relation: OAuth 1.0 PRECEDES OAuth 2.0                       │
│  Inferred: OAuth 1.0 claims BEFORE OAuth 2.0 claims           │
└────────────────────────────────────────────────────────────────┘
```

Query facts valid at a specific time:
```bash
curl "http://localhost:8000/api/entities/temporal?at=2020-01-01T00:00:00Z"
```

### 4. Multi-Source Fusion

When the same concept appears in multiple sources, Inception fuses them:

```
Source 1 (RFC 6749):     "Access tokens expire after 1 hour"    [authority: 1.0]
Source 2 (Blog post):    "Tokens typically expire in ~60 min"   [authority: 0.6]
Source 3 (Tutorial):     "Access tokens last 1 hour"            [authority: 0.7]

Fused Claim:
  statement: "Access tokens expire after 1 hour"
  confidence: 0.94 (Bayesian fusion)
  source_count: 3
  conflict_detected: false
```

**Conflict Resolution Strategies:**
- `recency` — Trust newer sources
- `authority` — Trust higher-authority sources (RFCs > blogs)
- `consensus` — Trust majority agreement
- `confidence` — Trust higher-confidence extractions

### 5. Autonomous Gap Resolution

When Inception detects a gap, it can autonomously research and fill it:

```bash
$ inception explore-gaps --auto --max-depth 1 --budget 0.50

Found 3 unresolved gaps:
  [undefined_term] "PKCE code_verifier" referenced but not defined
  [missing_context] "How does PKCE prevent code interception?"
  [incomplete_procedure] "Step 3 references undocumented config flag"

Resolving gap: "PKCE code_verifier"...
  → Searching DuckDuckGo: "PKCE code_verifier explained"
  → Found: RFC 7636 Section 4.1
  → Ingesting source...
  → Extracted: code_verifier is a cryptographically random string...
  ✓ Gap resolved. 1 new claim, 2 new entities added.
```

**Safety Rails:**
- Max exploration depth (default: 2)
- Rate limiting (default: 10 req/min)
- Budget caps (default: $0.50/session)
- Domain allowlist/blocklist
- Human-in-the-loop mode (default: on)

### 6. Fact Validation

Claims are validated against authoritative sources:

```python
from inception.enhance.agency.validator import FactValidator

validator = FactValidator()
result = validator.validate(
    claim=Claim("OAuth 2.0 was published in October 2012"),
    sources=["wikipedia", "wikidata"]
)

# ValidationResult(
#     verified=True,
#     evidence=["RFC 6749 published October 2012"],
#     confidence=0.98,
#     source="wikidata:Q643697"
# )
```

### 7. Procedure → Skill Synthesis

Extracted procedures become executable skills:

```bash
$ inception skillify "deploy-oauth-server" --output skills/

# Generated: skills/deploy-oauth-server.md
```

```yaml
---
name: Deploy OAuth Server
description: Set up a production OAuth authorization server
tags: [devops, security, oauth]
difficulty: hard
estimated_time: 2h
---

## Prerequisites
- Docker installed
- Domain configured with SSL

## Steps

### Step 1: Generate RSA Key Pair
Generate a 2048-bit RSA key for signing tokens.
**Parameters:**
- `key_size`: 2048

### Step 2: Configure JWKS Endpoint
...
```

### 8. RheoMode Output Levels

Control the detail level of outputs:

| Level | Name | Description |
|-------|------|-------------|
| 0 | Gist | 1-line summary |
| 1 | Takeaways | Key points + actions |
| 2 | Evidence | Evidence-linked claims |
| 3 | Full | Complete deconstruction |
| 4 | Skills | Derived executable skills |

```bash
inception action-pack "OAuth Security" --rheomode 2
```

---

## Architecture

```
inception/
├── ingest/           # Source acquisition (YouTube, Web, Documents)
│   ├── youtube.py        # yt-dlp integration
│   ├── web.py            # trafilatura extraction
│   └── documents.py      # PDF/PPTX/DOCX/XLSX
│
├── extract/          # Content extraction
│   ├── transcription.py  # Whisper ASR
│   ├── scenes.py         # PySceneDetect keyframes
│   ├── ocr.py            # PaddleOCR/Tesseract
│   └── alignment.py      # Multimodal temporal fusion
│
├── analyze/          # Semantic analysis
│   ├── entities.py       # NER with spaCy
│   ├── claims.py         # SPO extraction + modality
│   ├── procedures.py     # Step extraction
│   └── gaps.py           # Uncertainty detection
│
├── graph/            # Knowledge hypergraph
│   └── builder.py        # Node/edge construction
│
├── enhance/          # Enhancement layers (100-step epic)
│   ├── llm/              # LLM extraction (Ollama, OpenRouter, Cloud)
│   ├── vectors/          # Embedding + ChromaDB vector search
│   ├── vision/           # VLM analysis (LLaVA, GPT-4V, Claude)
│   ├── agency/           # Agentic capabilities
│   │   ├── explorer/         # Autonomous gap exploration
│   │   ├── validator/        # Fact validation (Wikipedia, Wikidata)
│   │   └── executor/         # Skill execution engine
│   ├── synthesis/        # Knowledge synthesis
│   │   ├── fusion/           # Multi-source Bayesian fusion
│   │   ├── ontology/         # Wikidata/DBpedia linking
│   │   └── temporal/         # Allen interval reasoning
│   ├── operations/       # Operational features
│   │   ├── sync/             # Incremental file watching
│   │   ├── export/           # Obsidian/Markdown/JSON export
│   │   └── tui/              # Terminal UI
│   └── learning.py       # RL learning engine (DAPO/GRPO/RLVR)
│
├── db/               # LMDB storage
│   └── records.py        # Schema: Source, Span, Node, Edge
│
├── query/            # Search engine
│   └── engine.py         # Temporal, entity, claim, full-text search
│
├── skills/           # Skill synthesis
│   └── synthesizer.py    # Procedure → executable SKILL.md
│
└── cli.py            # Click CLI (39k lines)
```

### Database Schema (LMDB)

```
┌─────────────────────────────────────────────────────────────────┐
│                      LMDB Environment                            │
├──────────┬──────────┬───────────┬───────────┬──────────────────┤
│  sources │  spans   │   nodes   │   edges   │  graphtag→nid    │
│(SourceRec│(SpanRec) │(NodeRec)  │(EdgeRec)  │  (deduplication) │
├──────────┼──────────┼───────────┼───────────┼──────────────────┤
│  tindex  │  pindex  │   meta    │           │                  │
│(temporal)│ (page)   │(counters) │           │                  │
└──────────┴──────────┴───────────┴───────────┴──────────────────┘

Node Types: ENTITY | CLAIM | PROCEDURE | GAP
Edge Types: MENTIONS | SUPPORTS | CONTRADICTS | RELATED_TO
```

---

## Learning Engine

Inception uses reinforcement learning to improve extraction quality over time:

### DAPO (Dynamic Advantage Policy Optimization)
Adaptive PPO with dynamic clip ranges based on advantage variance:
```python
dapo = DAPOOptimizer(clip_range=0.2, entropy_coef=0.01)
dynamic_clip = dapo.compute_dynamic_clip(advantages)
# Higher variance → wider clip → more exploration
```

### GRPO (Group Relative Policy Optimization)
Groups experiences by action type, computes relative advantages within groups:
```python
grpo = GRPOOptimizer(group_size=32, top_k_ratio=0.25)
grpo.add_experience(Experience(action="extract_claim", reward=0.8, ...))
advantage = grpo.compute_group_advantage(exp)  # Relative to group baseline
```

### RLVR (Reinforcement Learning with Verifiable Rewards)
Ground-truth verification for reward signals:
```python
rlvr = RLVREngine()
reward = rlvr.compute_verified_reward(
    action="extract_claim",
    result={"statement": "OAuth uses bearer tokens"},
    sources=[{"content": "The OAuth 2.0 protocol uses bearer tokens..."}]
)
# Positive if claim matches sources
```

### GAP Policy (Uncertainty-Guided Exploration)
Prioritizes actions that fill knowledge gaps:
```python
gap_policy = GAPPolicy(exploration_weight=0.3)
action, gap = gap_policy.select_action(gaps, available_actions)
# High priority + high uncertainty → selected first
```

### Active Learner
Selects most informative samples:
```python
learner = ActiveLearner(strategy="uncertainty")
selected = learner.select_queries(candidates, num_queries=5)
```

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/krodotma/inception.git
cd inception
uv sync

# Check environment
uv run inception doctor

# Ingest a YouTube video
uv run inception ingest "https://youtube.com/watch?v=oauth-explained"

# Query your knowledge graph
uv run inception query "What is OAuth?"

# Export to Obsidian
uv run inception export obsidian -o ~/Documents/Vault/Inception

# Generate ActionPack
uv run inception action-pack "OAuth Security" --rheomode 2

# Synthesize skills
uv run inception skillify "deploy-oauth"
```

### OAuth Provider Authentication

Use your existing LLM subscriptions without API keys:

```bash
inception auth setup claude    # Opens browser for Claude OAuth
inception auth setup gemini    # Opens browser for Gemini OAuth
inception auth status          # Show connection status
```

---

## API Server

```bash
uv run inception serve --port 8000
```

**Endpoints:**
| Endpoint | Description |
|----------|-------------|
| `GET /api/stats` | Database statistics |
| `GET /api/entities` | List entities |
| `GET /api/claims` | List claims |
| `GET /api/gaps` | List detected gaps |
| `GET /api/sources` | List ingested sources |
| `POST /api/ingest` | Ingest a source |
| `POST /api/query` | Query knowledge graph |
| `GET /api/entities/temporal?at=<ISO8601>` | Temporal query |
| `POST /api/graph/path` | Find path between nodes |
| `POST /api/learning/step` | RL learning step |
| `GET /api/learning/stats` | Learning engine stats |

---

## Testing

```bash
# Run all tests (289 passed)
uv run pytest

# Run by category
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest tests/e2e

# With coverage
uv run pytest --cov=inception --cov-report=term-missing
```

---

## Dependencies

**Core:** Python 3.11+, LMDB, Click, Pydantic, Rich

**Media:** yt-dlp, faster-whisper, PySceneDetect, OpenCV, PaddleOCR

**NLP:** spaCy (en_core_web_sm)

**Documents:** pdfplumber, python-pptx, python-docx, openpyxl

**Enhancement:** sentence-transformers, chromadb, duckduckgo-search

---

## License

MIT

---

<p align="center">
  <em>Knowledge that compounds. Systems that learn. Intelligence that heals itself.</em>
</p>
