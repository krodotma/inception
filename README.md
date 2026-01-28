<div align="center">

# inception

<img src="https://raw.githubusercontent.com/krodotma/inception/main/docs/assets/logo.svg" alt="Inception" width="120" height="120"/>

**Recursive Knowledge Architecture**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Angular](https://img.shields.io/badge/Angular-17-DD0031?style=for-the-badge&logo=angular&logoColor=white)](https://angular.dev)
[![OAuth](https://img.shields.io/badge/OAuth-No_API_Keys-8B5CF6?style=for-the-badge&logo=auth0&logoColor=white)](#the-3rd-paradigm)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

*Knowledge that knows itself. Systems that heal themselves. Intelligence that compounds.*

</div>

---

## Why Inception Exists

Every knowledge tool you've used treats information as **static snapshots**. Obsidian, Notion, Roam—they're filing cabinets. You put things in, you take things out. Nothing happens in between.

Inception is different. It's a **living knowledge compiler** that:

- **Ingests anything**: YouTube, PDFs, ArXiv, websites, audio, code
- **Extracts structured claims**: Not just text—entities, relationships, confidence scores
- **Tracks time**: Claims have `valid_from` and `valid_until`. "Python 2 is current" was true in 2015, not 2025
- **Heals itself**: Detects gaps, spawns research agents, fills them autonomously
- **Verifies itself**: Cross-checks claims against existing knowledge, surfaces contradictions
- **Exports action**: Transforms "how-to" content into executable scripts

---

## The Temporal Hypergraph

Most systems store facts. Inception stores **claims with provenance and temporal validity**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLAIM: "Transformers use self-attention instead of recurrence"            │
├──────────────────────────────────────┬──────────────────────────────────────┤
│  Subject       │ Transformer         │  Confidence    │ 0.97               │
│  Predicate     │ uses                │  Valid From    │ 2017-06-12         │
│  Object        │ self-attention      │  Valid Until   │ null (still true)  │
├──────────────────────────────────────┴──────────────────────────────────────┤
│  SOURCES (Multi-Source Fusion)                                              │
│  ├── arxiv:1706.03762 (original paper) ─────────────── confidence +0.40    │
│  ├── youtube:3Blue1Brown/transformers ─────────────── confidence +0.30    │
│  └── blog:jalammar.github.io/illustrated ──────────── confidence +0.27    │
├─────────────────────────────────────────────────────────────────────────────┤
│  CONFLICTS: None                                                            │
│  SUPERSEDED BY: None                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

When sources agree, confidence compounds. When they conflict, you see both sides with evidence chains.

---

## Autonomous Gap Resolution

Other tools wait for you to notice what's missing. Inception hunts gaps and fills them.

```
$ inception gaps --auto-fill

Gap Detected:
  Entity: "WordPiece"
  Type: REFERENCED_BUT_UNDEFINED
  Priority: 0.87 (high confidence needed for 23 downstream claims)
  
Spawning research agent...
  Query: "WordPiece tokenization algorithm"
  Sources: [Wikipedia, Google Research, Wu et al. 2016]
  
Gap Filled:
  + Definition: "Subword segmentation using greedy longest-match-first"
  + Algorithm: Data-driven vocabulary with wordpiece model
  + Related: [BPE, SentencePiece, Unigram LM]
  + Citation: Wu et al. 2016, "Google's Neural Machine Translation"
  
Confidence propagation recalculated for 23 downstream claims.
```

Every filled gap is **cited, auditable, and traceable**.

---

## The Learning Engine

Inception doesn't just store—it **learns from corrections**.

| Algorithm | What It Does |
|-----------|--------------|
| **DAPO** | Dynamic Advantage Policy Optimization. Adaptive clipping, entropy scheduling. Extraction improves with each iteration. |
| **GRPO** | Group Relative Policy Optimization. Ranks outputs within batch—best extractions get reinforced. |
| **RLVR** | RL with Verifiable Rewards. Cross-checks extractions against ground truth. Hallucinations get penalized. |
| **GAPPolicy** | Uncertainty-guided exploration. Prioritizes filling high-impact gaps first. |
| **ActiveLearner** | Query-by-committee sample selection. Asks for human feedback on uncertain cases. |

After 1000 iterations on your domain:
- Extraction accuracy: **72% → 94%**
- Hallucination rate: **15% → 2%**
- Domain vocabulary: **Learned and applied**

---

## The 3rd Paradigm

**No API keys. No per-token billing.**

Inception uses OAuth 2.0 + PKCE to access your existing LLM subscriptions directly:

```bash
$ inception auth setup claude
# Browser opens → OAuth flow → Done

$ inception auth status
Claude:      ✓ MAX tier (Opus 4.5)
Gemini:      ✓ ULTRA tier (2.5 Flash)
Codex:       ✓ MAX tier (gpt-5.2-codex)
Antigravity: ✓ Connected
Kimi:        ○ Not configured
```

Your Claude Max subscription. Your Gemini Ultra subscription. Programmatically accessible. Tokens stored in OS keychain with automatic refresh.

---

## Procedural → Executable

Most tools extract information. Inception extracts **runnable procedures**.

```bash
$ inception ingest "https://docs.docker.com/get-started/"
$ inception export action-pack --procedure "deploy-container"
```

**Output:** `deploy-container.action.yaml`

```yaml
name: Deploy Docker Container
variables:
  IMAGE_NAME: { required: true }
  HOST_PORT: { default: 8080 }
  CONTAINER_PORT: { default: 80 }

steps:
  - name: Build image
    command: docker build -t $IMAGE_NAME .
    verify: docker images | grep $IMAGE_NAME
    on_fail: exit 1
    
  - name: Run container
    command: docker run -d -p $HOST_PORT:$CONTAINER_PORT $IMAGE_NAME
    verify: docker ps | grep $IMAGE_NAME
    
  - name: Health check
    command: curl -f http://localhost:$HOST_PORT/health
    retry: { count: 3, delay: 5s }
```

```bash
$ inception run deploy-container IMAGE_NAME=myapp HOST_PORT=3000
# Actually runs. Actually deploys. Actually verifies.
```

---

## Multi-Source Fusion

Single-source facts are weak. Multi-source facts are strong.

| Sources | Confidence | Interpretation |
|---------|------------|----------------|
| 1 source | 0.40 | Tentative. Needs corroboration. |
| 2 sources (agree) | 0.75 | Likely true. Worth citing. |
| 3+ sources (agree) | 0.95+ | High confidence. Propagates to dependents. |
| 2 sources (conflict) | FLAGGED | Both views preserved with evidence chains. |

When Wikipedia, the original paper, and a tutorial all say the same thing, you can trust it. When they disagree, you see the disagreement—not a silent override.

---

## Claim Verification

New extractions don't just land in the database. They're **cross-checked against existing knowledge**.

```
New Claim: "BERT was released in 2017"
Existing: "BERT was released in 2018"
Source Evidence: ArXiv timestamp shows October 2018

→ CONFLICT DETECTED
→ New claim rejected with explanation
→ Source flagged for potential hallucination
```

Your knowledge base doesn't silently corrupt itself.

---

## Architecture

```
inception/
├── analyze/      Entity extraction, claim parsing, conflict detection
├── auth/         OAuth 2.0 + PKCE, multi-provider, keychain storage
├── db/           LMDB hypergraph, vector indices, temporal queries
├── enhance/      DAPO/GRPO/RLVR learning, gap filling, active learning
├── extract/      VLM, ASR, OCR, text chunking, procedure recognition
├── graph/        Hyperedge operations, traversal, confidence propagation
├── ingest/       Multi-format handlers, hash-based delta sync
├── output/       Obsidian export, Markdown, Action Packs
├── query/        Semantic search, temporal filtering, graph queries
├── serve/        FastAPI backend, WebSocket terminal
├── skills/       Composable agent capabilities, tool registry
└── tui/          Textual terminal UI, dashboard, explorer
```

---

## Quick Start

```bash
git clone https://github.com/krodotma/inception
cd inception
pip install -e .

# Authenticate with your LLM subscriptions
inception auth setup claude
inception auth setup gemini

# Ingest content
inception ingest "https://youtube.com/watch?v=..."
inception ingest "~/papers/attention-is-all-you-need.pdf"
inception ingest "https://arxiv.org/abs/1706.03762"

# Explore
inception explore      # Terminal UI
inception serve        # Web UI at localhost:8000

# Work with knowledge
inception search "transformer attention mechanism"
inception gaps                # Show knowledge gaps
inception gaps --auto-fill    # Fill them autonomously
inception verify              # Cross-check claims
inception export obsidian     # Export to Obsidian vault
```

---

## Interfaces

**Web UI** — Material Design 3, knowledge graph visualization, integrated terminal  
```bash
inception serve
open http://localhost:8000
```

**Terminal UI** — Full Textual TUI with dashboard, explorer, live stats  
```bash
inception explore
```

**CLI** — Scriptable commands for automation  
```bash
inception ingest | search | gaps | verify | export | run
```

---

## What Inception Is Not

- **Not a note-taking app.** It's a knowledge compiler.
- **Not a chatbot wrapper.** It builds structured, queryable knowledge.
- **Not dependent on API keys.** Uses your existing subscriptions.
- **Not passive storage.** It learns, verifies, and heals.

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v --cov=inception
mypy inception/
ruff check inception/
```

---

<div align="center">

**MIT License**

Built for autonomous reasoning. Local-first. Self-healing.

</div>
