# Inception CLI Reference

## Overview

Inception is a local-first multimodal learning ingestion system. It processes YouTube videos, web pages, and documents into a temporal knowledge hypergraph.

## Installation

```bash
# Clone and install
git clone https://github.com/user/inceptional.git
cd inceptional
uv sync

# Verify installation
inception doctor
```

## Commands

### Core Commands

#### `inception doctor`

Check environment and dependencies.

```bash
inception doctor
```

Verifies:
- Python version (≥3.11)
- Required libraries (LMDB, yt-dlp, faster-whisper, PaddleOCR, spaCy)
- Data directories exist
- spaCy models installed

---

#### `inception ingest <URI>`

Ingest a source (URL or file path).

```bash
# YouTube video
inception ingest "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Web page
inception ingest "https://example.com/article"

# Local PDF
inception ingest /path/to/document.pdf

# With filters
inception ingest <URI> --since 2024-01-01 --until 2024-12-31 --topic "machine learning"
```

**Options:**
| Option | Description |
|--------|-------------|
| `--since DATE` | Only process content since this date (YYYY-MM-DD) |
| `--until DATE` | Only process content until this date (YYYY-MM-DD) |
| `--topic TEXT` | Topic filters (can use multiple) |
| `--profile TEXT` | Ingestion profile to use |

---

#### `inception ingest-channel <CHANNEL_URL>`

Ingest a YouTube channel incrementally.

```bash
inception ingest-channel "@3blue1brown" --since 2024-01-01
inception ingest-channel "https://youtube.com/@lexfridman" --since 2023-06-01 --until 2024-01-01
```

**Options:**
| Option | Description |
|--------|-------------|
| `--since DATE` | Start date (required) |
| `--until DATE` | End date |
| `--topic-rules FILE` | Topic rules YAML file |

---

#### `inception ingest-batch <SOURCES_FILE>`

Ingest multiple sources from a JSONL file.

```bash
inception ingest-batch sources.jsonl
```

**File format:**
```jsonl
{"uri": "https://youtube.com/watch?v=xxx", "topics": ["python"]}
{"uri": "https://example.com/article", "since": "2024-01-01"}
```

---

### Query Commands

#### `inception query <QUERY_TEXT>`

Query the knowledge graph.

```bash
inception query "what is machine learning"
inception query "claims about Python" --source video123
inception query "procedures for deployment" --format json
```

**Options:**
| Option | Description |
|--------|-------------|
| `--time TEXT` | Time range filter |
| `--source TEXT` | Limit to specific source |
| `--format` | Output format: `md` (default) or `json` |

---

### Output Commands

#### `inception action-pack <TARGET>`

Generate an Action Pack from a source.

```bash
inception action-pack source:123 --rheomode 2
inception action-pack query:"python tutorials" --rheomode 4
```

**Options:**
| Option | Description |
|--------|-------------|
| `--rheomode N` | Detail level 0-4 (default: 1) |

**RheoMode Levels:**
| Level | Name | Content |
|-------|------|---------|
| 0 | GIST | 1-line summary |
| 1 | TAKEAWAYS | Key points + actions |
| 2 | EVIDENCE | Evidence-linked claims |
| 3 | FULL | Complete deconstruction |
| 4 | SKILLS | Derived skills/playbooks |

---

#### `inception skillify <TARGET>`

Convert procedures into executable skills.

```bash
# From a source
inception skillify 123 --output ./skills

# All procedures
inception skillify all --output ./skills
```

**Options:**
| Option | Description |
|--------|-------------|
| `--output, -o` | Output directory |
| `--all` | Generate skills for all procedures |

Generates SKILL.md files with:
- Frontmatter (name, description, difficulty)
- Prerequisites
- Step-by-step instructions
- Warnings and fallbacks

---

### Management Commands

#### `inception list-sources`

List all ingested sources.

```bash
inception list-sources
inception list-sources --limit 50
```

---

#### `inception stats`

Show database statistics.

```bash
inception stats
```

Shows:
- Source count
- Span count
- Node counts by type (entity, claim, procedure, gap)

---

#### `inception export <TARGET>`

Export data from the knowledge graph.

```bash
inception export source:123 --format md -o output.md
inception export all --format jsonl -o export.jsonl
inception export query:"python" --format parquet -o data.parquet
```

**Options:**
| Option | Description |
|--------|-------------|
| `--format` | Output format: `md`, `jsonl`, `parquet` |
| `--output, -o` | Output file path |

---

### Development Commands

#### `inception test`

Run the test suite.

```bash
# All tests
inception test

# Specific categories
inception test --unit
inception test --integration
inception test --e2e

# With coverage
inception test --coverage
```

---

## Global Options

| Option | Description |
|--------|-------------|
| `--config, -c FILE` | Path to configuration file |
| `--offline` | Run in offline mode |
| `--seed INT` | Random seed for reproducibility |
| `--version` | Show version |
| `--help` | Show help |

## Configuration

Create `~/.inception/config.yaml`:

```yaml
# Data directories
data_dir: ~/.inception
artifacts_dir: ~/.inception/artifacts
cache_dir: ~/.inception/cache

# LMDB settings
lmdb:
  path: ~/.inception/db
  map_size: 10737418240  # 10GB

# Whisper settings
whisper:
  model_size: base
  device: auto
  compute_type: float16

# OCR settings
ocr:
  engine: paddleocr
  languages: [en]

# Pipeline settings
pipeline:
  offline_mode: false
  skip_existing: true
  workers: 4
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `INCEPTION_CONFIG` | Config file path |
| `INCEPTION_DATA_DIR` | Data directory |
| `INCEPTION_OFFLINE` | Enable offline mode |
| `DISABLE_MODEL_SOURCE_CHECK` | Skip model connectivity check |
