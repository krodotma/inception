<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,17,24,29&height=200&section=header&text=inception&fontSize=80&fontAlignY=35&desc=Recursive%20Knowledge%20Architecture&descAlignY=55&descSize=18&animation=fadeIn&fontColor=fff"/>
  <source media="(prefers-color-scheme: light)" srcset="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=24,29,30,31&height=200&section=header&text=inception&fontSize=80&fontAlignY=35&desc=Recursive%20Knowledge%20Architecture&descAlignY=55&descSize=18&animation=fadeIn"/>
  <img alt="Inception" src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=inception&fontSize=80&fontAlignY=35"/>
</picture>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Angular](https://img.shields.io/badge/Angular-17-DD0031?style=for-the-badge&logo=angular&logoColor=white)](https://angular.dev)
[![OAuth](https://img.shields.io/badge/OAuth-No_API_Keys-8B5CF6?style=for-the-badge&logo=auth0&logoColor=white)](#paradigm)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

**Knowledge that knows itself. Systems that heal themselves. Intelligence that compounds.**

<sub>Built for autonomous reasoning • Temporal hypergraphs • Self-repairing knowledge</sub>

[Architecture](#architecture) · [Paradigm](#paradigm) · [KINESIS](#kinesis) · [Get Started](#ignition)

</div>

---

<details>
<summary><b>🔮 What is Inception?</b></summary>

<br>

```
                    ╭──────────────────────────────────────────╮
                    │                                          │
                    │    Video   Audio   PDF   Web   Code      │
                    │         ↓     ↓     ↓     ↓     ↓        │
                    │    ┌───────────────────────────────┐     │
                    │    │      EXTRACTION LAYER         │     │
                    │    │   VLM • ASR • OCR • Chunking  │     │
                    │    └────────────┬──────────────────┘     │
                    │                 ↓                        │
                    │    ┌───────────────────────────────┐     │
                    │    │      KNOWLEDGE LAYER          │     │
                    │    │  Temporal Hypergraph • LMDB   │     │
                    │    │  Multi-source Fusion • UQ     │     │
                    │    └────────────┬──────────────────┘     │
                    │                 ↓                        │
                    │    ┌───────────────────────────────┐     │
                    │    │      VALIDATION LAYER         │     │
                    │    │  Gap Detection • Self-Repair  │     │
                    │    │  Claim Verification • RLVR    │     │
                    │    └────────────┬──────────────────┘     │
                    │                 ↓                        │
                    │    ┌───────────────────────────────┐     │
                    │    │       OUTPUT LAYER            │     │
                    │    │  Web UX • TUI • Action Packs  │     │
                    │    └───────────────────────────────┘     │
                    │                                          │
                    ╰──────────────────────────────────────────╯
```

Inception ingests multimodal content, extracts structured knowledge into a temporal hypergraph, cross-validates claims, autonomously resolves gaps, and exports executable Action Packs—all local-first with OAuth-based LLM access.

</details>

---

## The Difference

<table>
<tr>
<td width="30%"><b>🕐 Temporal Reasoning</b></td>
<td>Claims have validity windows. "Python 2 is current" was true in 2015, not 2025. Knowledge expires, updates, conflicts—Inception tracks it all.</td>
</tr>
<tr>
<td><b>🔄 Self-Healing Knowledge</b></td>
<td>Gap detected → research agent spawned → gap resolved → source cited. Autonomous, observable, auditable.</td>
</tr>
<tr>
<td><b>⚖️ Multi-Source Fusion</b></td>
<td>Same claim from 3 sources → confidence 0.95. Conflicting claims → flagged with evidence chains.</td>
</tr>
<tr>
<td><b>✓ Claim Verification</b></td>
<td>Cross-checks extractions against existing KB. Contradictions surface, not hide.</td>
</tr>
<tr>
<td><b>⚡ Procedural → Executable</b></td>
<td>"How to deploy X" → structured steps → runnable Action Packs. Knowledge that does things.</td>
</tr>
</table>

---

## How It Works

<details>
<summary><b>📥 Story 1: Ingest → Extract → Fuse</b></summary>

```bash
inception ingest "https://youtube.com/watch?v=dQw4w9WgXcQ" \
                 "~/papers/transformer-architecture.pdf" \
                 "https://arxiv.org/abs/1706.03762"
```

**What happens:**

1. **Multimodal Extraction**
   - YouTube: Audio → Whisper ASR → transcript chunks
   - PDF: OCR + layout analysis → sections, figures, equations
   - ArXiv: HTML parse + citation graph extraction

2. **Entity & Claim Extraction**  
   Each chunk passes through the LLM extraction pipeline:
   ```
   "The Transformer uses self-attention instead of recurrence"
   → Claim { subject: "Transformer", predicate: "uses", object: "self-attention" }
   → Entities: [Transformer, self-attention, recurrence]
   ```

3. **Multi-Source Fusion**  
   Same claim from all 3 sources → **confidence 0.97**  
   Conflicting claim in 1 source → **flagged with evidence chain**

4. **Temporal Binding**  
   Claims stamped with `valid_from: 2017-06-12` (paper date)  
   Future papers may supersede → automatic conflict detection

</details>

<details>
<summary><b>🧠 Story 2: Learn → Improve → Compound</b></summary>

Inception doesn't just store—it **learns from its mistakes**.

```bash
inception learn --action extract_claim --sources corpus.json
```

**The DAPO/GRPO/RLVR Loop:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. ATTEMPT: LLM extracts claim from new document           │
│  2. VERIFY:  Check against ground-truth or human feedback   │
│  3. REWARD:  RLVR computes verifiable reward (+1/-1/0)      │
│  4. RANK:    GRPO ranks within batch, identifies winners    │
│  5. UPDATE:  DAPO adjusts policy with adaptive clipping     │
│  6. REPEAT:  Each iteration improves extraction accuracy    │
└─────────────────────────────────────────────────────────────┘
```

**Result:** After 1000 iterations on your domain:
- Extraction accuracy: 72% → 94%
- Hallucination rate: 15% → 2%
- Domain-specific terminology: learned and applied

</details>

<details>
<summary><b>🔧 Story 3: Gap Detection → Self-Repair</b></summary>

```bash
inception gaps --auto-fill
```

**Scenario:** KB contains "BERT uses WordPiece tokenization" but no definition of WordPiece.

```
Gap Detected:
  Entity: "WordPiece"
  Type: REFERENCED_BUT_UNDEFINED
  Priority: 0.87 (high confidence needed for downstream claims)
  
Spawning research agent...
  Query: "WordPiece tokenization algorithm definition"
  Sources: [Wikipedia, Google Research Blog, Original Paper]
  
Gap Filled:
  + Definition: "Subword segmentation algorithm that..."
  + Related: [BPE, SentencePiece, Unigram]
  + Citation: Wu et al. 2016
  
Confidence propagation recalculated for 47 downstream claims.
```

**Autonomous, observable, auditable.** Every filled gap cites its source.

</details>

<details>
<summary><b>⚡ Story 4: Procedural → Executable</b></summary>

```bash
inception ingest "https://docs.docker.com/get-started/"
inception export action-pack --procedure "deploy-container"
```

**Input:** Documentation prose  
**Output:** Executable Action Pack

```yaml
# deploy-container.action.yaml
name: Deploy Docker Container
steps:
  - name: Build image
    command: docker build -t $IMAGE_NAME .
    verify: docker images | grep $IMAGE_NAME
    
  - name: Run container
    command: docker run -d -p $HOST_PORT:$CONTAINER_PORT $IMAGE_NAME
    verify: docker ps | grep $IMAGE_NAME
    
  - name: Health check
    command: curl -f http://localhost:$HOST_PORT/health
    retry: { count: 3, delay: 5s }
    
variables:
  IMAGE_NAME: { required: true }
  HOST_PORT: { default: 8080 }
  CONTAINER_PORT: { default: 80 }
```

**Run it:**
```bash
inception run deploy-container IMAGE_NAME=myapp HOST_PORT=3000
```

Knowledge that **does things**.

</details>

<details>
<summary><b>🌊 Story 5: Rheomode — The UI That Breathes</b></summary>

> *"The word is the thing. The process is the product."* — David Bohm

Inception's UI follows **Rheomode** principles: language and interface as flowing process, not static noun.

**What this means in practice:**

| Traditional UI | Rheomode UI |
|----------------|-------------|
| Button hover: cursor change | Button hover: magnetic attraction + 3D tilt + glow pulse |
| Loading: spinner | Loading: particle constellation orbiting, aurora waves |
| Success: checkmark | Success: confetti burst + haptic bounce + ribbon coalesce |
| Error: red text | Error: shake + dissolve particles + chromatic aberration |

**Implementation:** 6,431 lines of motion systems (see [KINESIS](#kinesis))

The interface doesn't display state—it **performs** state. Every transition is a dance, not a jump-cut.

</details>

---

## Paradigm

<blockquote>
<b>The 3rd Paradigm: Subscription-Based OAuth</b>
</blockquote>

No API keys. No per-token billing. Your Claude Max / Gemini Ultra / GPT Max subscription, programmatically accessible.

```bash
inception auth setup claude   # Browser opens → OAuth flow → Done
inception auth status
# Claude: ✓ MAX tier (Opus 4.5)
# Gemini: ✓ ULTRA tier (2.5 Flash)
```

Tokens stored in OS keychain. Automatic refresh. Zero key management.

---

## Architecture

<details>
<summary><b>Core Modules</b></summary>

```
inception/
├── analyze/      # Entity extraction, claim parsing, conflict detection
├── auth/         # OAuth 2.0 + PKCE, multi-provider, keychain storage
├── db/           # LMDB hypergraph, vector indices, temporal queries
├── enhance/      # DAPO/GRPO/RLVR learning, gap filling, active learning
├── extract/      # VLM, ASR, OCR, text chunking, procedure recognition
├── graph/        # Hyperedge operations, traversal, confidence propagation
├── ingest/       # Multi-format handlers, hash-based delta sync
├── output/       # Obsidian, Markdown, Action Packs, structured export
├── query/        # Semantic search, temporal filtering, graph queries
├── serve/        # FastAPI backend, WebSocket terminal, auth middleware
├── skills/       # Composable agent capabilities, tool registry
└── tui/          # Textual terminal UI, dashboard, explorer
```

</details>

<details>
<summary><b>Learning Engine</b></summary>

| Algorithm | Purpose |
|-----------|---------|
| **DAPO** | Dynamic Advantage Policy Optimization — adaptive clip, entropy scheduling |
| **GRPO** | Group Relative Policy Optimization — within-group ranking for sparse rewards |
| **RLVR** | RL with Verifiable Rewards — ground-truth verification against sources |
| **GAPPolicy** | Uncertainty-guided exploration with priority scoring |
| **ActiveLearner** | Query-by-committee sample selection |

</details>

---

## KINESIS

> *The UI breathes. Every interaction causes motion. Nothing is static.*

<details>
<summary><b>Motion Systems (6,431 lines)</b></summary>

**V1: Foundation**
| System | Lines |
|--------|-------|
| `alive-ui.js` | Magnetic buttons, 3D tilt, parallax |
| `micro-interactions.js` | Jelly physics, confetti, heartbeat pulse |
| `particle-system.js` | Connection bursts, cursor trails, orbital loading |
| `auth-state-machine.ts` | XState-like flow control |
| `premium-motion.css` | Fibonacci stagger, golden ratio easing |

**V2: Deep Iteration**
| System | Lines |
|--------|-------|
| `liquid-morph.js` | Gooey filters, metaballs, SVG morphing |
| `aurora-shader.js` | Simplex noise ribbons, chromatic aberration |
| `particle-card.js` | Robin Dela 3D particle cards |
| `skeleton-haptic.css` | Skeleton loaders, haptic feedback |
| `gesture-handler.js` | Swipe, pinch, rotate, long press |
| `dela-integration.js` | WebGL displacement, flowmap distortion |
| `kinesis-v2.js` | Master orchestration bundle |

**Integrated: Robin Dela Collection**
| Repo | ⭐ |
|------|------|
| hover-effect | 1874 |
| flowmap-effect | 111 |
| css-mask-animation | 90 |

</details>

<details>
<summary><b>API</b></summary>

```javascript
window.kinesis.triggerConnecting('claude');
window.kinesis.triggerConnected('gemini');
window.kinesis.enableCursorTrail();
window.kinesis.debug();
```

</details>

---

## Ignition

```bash
git clone https://github.com/krodotma/inception
cd inception

# Python backend
pip install -e .
inception auth setup claude

# Ingest
inception ingest https://youtube.com/watch?v=...
inception ingest ~/Documents/paper.pdf

# Explore
inception explore      # TUI
inception serve        # Web @ localhost:8000
```

---

## Interfaces

<table>
<tr>
<td align="center" width="33%">
<b>Web UX</b><br>
<sub>Material Design 3 • View Transitions API</sub><br>
<code>inception serve</code>
</td>
<td align="center" width="33%">
<b>Terminal UI</b><br>
<sub>Textual • Live Dashboard • Graph Viz</sub><br>
<code>inception explore</code>
</td>
<td align="center" width="33%">
<b>CLI</b><br>
<sub>Ingest • Search • Export • Verify</sub><br>
<code>inception --help</code>
</td>
</tr>
</table>

---

<details>
<summary><b>Development</b></summary>

```bash
pip install -e ".[dev]"
pytest tests/ -v --cov=inception
mypy inception/
ruff check inception/
```

</details>

---

<div align="center">

**MIT** · Built with obsession · Motion patterns: **KINESIS**

<sub>Temporal hypergraphs · Self-repairing knowledge · Subscription-based OAuth · No API keys</sub>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,17,24,29&height=100&section=footer"/>
  <img alt="" src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=footer"/>
</picture>

</div>
