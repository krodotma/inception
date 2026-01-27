# Inception

**Knowledge compiler with temporal reasoning and autonomous gap resolution**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OAuth: No API Keys](https://img.shields.io/badge/OAuth-No%20API%20Keys-purple.svg)](#oauth-authentication)

> Inception ingests video/audio/PDF/web, extracts structured knowledge into a temporal hypergraph, cross-validates claims, autonomously fills gaps, and exports executable Action Packs—all local-first with OAuth-based LLM access (no API keys).

---

## What Makes Inception Different

| Capability | What It Means | Why It's Rare |
|------------|--------------|---------------|
| **Temporal Hypergraph** | Claims have validity windows (`valid_from`, `valid_until`). "Python 2 is current" was true in 2015, not 2025. | Most PKM tools treat knowledge as timeless |
| **Autonomous Gap Resolution** | System detects "X referenced but undefined" → spawns research agent → fills gap → cites source | Tools don't self-heal their knowledge |
| **Multi-source Fusion** | Same claim from 3 sources → confidence 0.95. Conflicting claims → flags conflict with evidence | No confidence quantification in Obsidian/Notion |
| **Claim Verification** | Cross-checks extracted claims against existing KB → detects contradictions | PKM doesn't fact-check itself |
| **Procedural → Executable** | "How to deploy X" → extracts steps → generates runnable Action Packs | Action scripts, not just notes |
| **Hash-based Incremental Sync** | Watches directories, detects changes by content hash, re-ingests only deltas | Live knowledge that updates itself |
| **No API Keys (OAuth)** | Uses your Claude Max/Gemini Ultra subscription directly via browser auth | No per-token costs, no key management |

---

## Quick Start

```bash
# Clone
git clone https://github.com/kroma/inception.git
cd inception

# Install
pip install -e .

# Authenticate (opens browser)
inception auth setup claude

# Ingest content
inception ingest https://youtube.com/watch?v=...
inception ingest ~/Documents/paper.pdf

# Explore
inception explore  # TUI
# or
inception serve    # Web UI at localhost:8000
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      INPUT LAYER                            │
│  Video │ Audio │ PDF │ Web │ Markdown │ Code                │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTRACTION LAYER                          │
│  Vision VLM │ Audio Transcription │ Text Chunking           │
│  LLM Entity/Claim Extraction │ Procedure Recognition        │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE LAYER                           │
│  LMDB Hypergraph │ Vector Index │ Temporal Reasoning        │
│  Multi-source Fusion │ Uncertainty Quantification           │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   VALIDATION LAYER                          │
│  Claim Verification │ Gap Detection │ Conflict Resolution   │
│  Autonomous Gap Filler │ Fact Validator                     │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                             │
│  Web UX │ TUI │ Obsidian Export │ Markdown │ Action Packs   │
└─────────────────────────────────────────────────────────────┘
```

---

## OAuth Authentication

Inception uses OAuth 2.0 + PKCE to authenticate with LLM providers. This means:

- **No API keys** to manage or leak
- **Uses your subscription** (Claude Max, Gemini Ultra, etc.)
- **Secure token storage** in OS keychain
- **Automatic refresh** without re-authentication

```bash
# Setup providers
inception auth setup claude   # Opens browser, authenticates
inception auth setup gemini
inception auth setup openai

# Check status
inception auth status
# Claude: ✓ MAX tier (Opus 4.5)
# Gemini: ✓ PRO tier (Pro 3)
# OpenAI: ○ Not connected
```

---

## Interfaces

### Web UX

Material Design 3 interface with KINESIS motion patterns:

```bash
uvicorn inception.serve.api:app --reload
open http://localhost:8000
```

Features:
- Knowledge graph visualization (Cytoscape.js)
- Integrated terminal (xterm.js + WebSocket)
- View Transitions API for native-like navigation
- State machine driven UI (no ad-hoc booleans)

### Terminal UI

Full-featured Textual TUI:

```bash
python -m inception.tui
```

Features:
- Dashboard with live stats
- Knowledge explorer with search
- ASCII graph visualization
- Settings and auth management

### CLI

```bash
inception ingest <url|file>    # Ingest content
inception search <query>       # Search knowledge
inception export obsidian      # Export to Obsidian
inception gaps                 # Show knowledge gaps
inception verify               # Run claim verification
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=inception --cov-report=html

# Type check
mypy inception/

# Lint
ruff check inception/
```

---

## License

MIT

---

## Credits

Built with:
- [Textual](https://textual.textualize.io/) - Terminal UI framework
- [FastAPI](https://fastapi.tiangolo.com/) - Web API framework
- [LMDB](https://lmdb.readthedocs.io/) - Lightning Memory-Mapped Database
- [Cytoscape.js](https://js.cytoscape.org/) - Graph visualization
- [xterm.js](https://xtermjs.org/) - Terminal emulator
- [Material Web 3](https://material-web.dev/) - Design system

Motion patterns: **KINESIS** (Motion Systems Engineer persona)
