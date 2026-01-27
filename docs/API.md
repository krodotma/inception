# Inception API Reference

> Complete API documentation with testable examples

## Base URL

```
http://localhost:8000
```

## Health & Status

### `GET /`

Returns API metadata.

```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "name": "Inception API",
  "version": "0.3.0",
  "phase": "Hyper-PKG"
}
```

### `GET /health`

Health check with component status.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "lmdb": "connected",
  "oauth": "available",
  "learning": "ready"
}
```

---

## Knowledge API

### `GET /api/stats`

Get database statistics.

```bash
curl http://localhost:8000/api/stats
```

**Response:**
```json
{
  "entities": 1247,
  "claims": 5892,
  "procedures": 312,
  "gaps": 23,
  "sources": 80
}
```

### `GET /api/entities`

List entities with optional filtering.

| Param | Type | Description |
|-------|------|-------------|
| `type` | string | Filter by entity type |
| `search` | string | Search by name/description |
| `limit` | int | Max results (default: 50) |

```bash
# Get all entities
curl http://localhost:8000/api/entities

# Filter by type
curl "http://localhost:8000/api/entities?type=concept"

# Search
curl "http://localhost:8000/api/entities?search=OAuth"
```

### `GET /api/entities/{entity_id}`

Get single entity by ID.

```bash
curl http://localhost:8000/api/entities/oauth-2.0
```

### `GET /api/claims`

List claims with filtering.

| Param | Type | Description |
|-------|------|-------------|
| `entity_id` | string | Claims for entity |
| `min_confidence` | float | Minimum confidence |
| `limit` | int | Max results |

```bash
curl "http://localhost:8000/api/claims?min_confidence=0.8"
```

### `GET /api/gaps`

List knowledge gaps.

```bash
curl http://localhost:8000/api/gaps
```

---

## Temporal API

### `GET /api/timeline`

Get event timeline.

| Param | Type | Description |
|-------|------|-------------|
| `entity_id` | string | Filter by entity |
| `limit` | int | Max events |

```bash
curl "http://localhost:8000/api/timeline?limit=50"
```

### `GET /api/entities/temporal`

Get entities valid at a specific time.

| Param | Type | Description |
|-------|------|-------------|
| `at` | string | ISO timestamp |
| `type` | string | Entity type filter |

```bash
# Entities valid on Jan 1, 2024
curl "http://localhost:8000/api/entities/temporal?at=2024-01-01T00:00:00Z"
```

### `GET /api/conflicts`

Detect temporal conflicts in claims.

```bash
curl http://localhost:8000/api/conflicts
```

---

## Source API

### `GET /api/sources`

List ingested sources.

```bash
curl http://localhost:8000/api/sources
```

**Response:**
```json
[
  {
    "id": "s1",
    "url": "https://oauth.net/2/",
    "type": "web",
    "title": "OAuth 2.0 Spec",
    "credibility": 0.95
  }
]
```

### `GET /api/sources/{source_id}/credibility`

Calculate source credibility score.

```bash
curl http://localhost:8000/api/sources/s1/credibility
```

---

## Graph Intelligence API

### `GET /api/graph`

Get graph visualization data.

```bash
curl http://localhost:8000/api/graph
```

**Response:**
```json
{
  "nodes": [...],
  "edges": [...]
}
```

### `GET /api/graph/clusters`

Get semantic clusters.

```bash
curl "http://localhost:8000/api/graph/clusters?num_clusters=5"
```

### `POST /api/graph/path`

Find path between entities.

```bash
curl -X POST http://localhost:8000/api/graph/path \
  -H "Content-Type: application/json" \
  -d '{"source_id": "oauth", "target_id": "pkce"}'
```

### `POST /api/graph/infer`

Infer new relationships.

```bash
curl -X POST http://localhost:8000/api/graph/infer \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "oauth"}'
```

### `GET /api/graph/explain`

Explain relationship between entities.

```bash
curl "http://localhost:8000/api/graph/explain?entity_a=oauth&entity_b=pkce"
```

---

## Extraction API

### `POST /api/extract/text`

Extract knowledge from text.

```bash
curl -X POST http://localhost:8000/api/extract/text \
  -H "Content-Type: application/json" \
  -d '{"text": "OAuth 2.0 is an authorization framework."}'
```

### `POST /api/extract/image`

Extract from image using VLM.

```bash
curl -X POST http://localhost:8000/api/extract/image \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/diagram.png"}'
```

### `POST /api/extract/audio`

Transcribe and extract from audio.

```bash
curl -X POST http://localhost:8000/api/extract/audio \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/lecture.mp3"}'
```

---

## ActionPack API

### `POST /api/actionpack`

Generate executable script from procedure.

```bash
curl -X POST http://localhost:8000/api/actionpack \
  -H "Content-Type: application/json" \
  -d '{"procedure_id": "oauth-setup", "format": "bash"}'
```

**Response:**
```json
{
  "procedure_id": "oauth-setup",
  "title": "OAuth Setup Procedure",
  "format": "bash",
  "script": "#!/bin/bash\n...",
  "parameters": [
    {"name": "API_URL", "default": "http://localhost:8000"}
  ]
}
```

### `GET /api/procedures/{id}/actionpack`

Shorthand to get ActionPack.

```bash
curl "http://localhost:8000/api/procedures/oauth-setup/actionpack?format=bash"
```

---

## Learning API (DAPO/GRPO/RLVR)

### `POST /api/learning/step`

Execute learning step.

```bash
curl -X POST http://localhost:8000/api/learning/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": "extract_claim",
    "state": {"entities": 10},
    "result": {"statement": "OAuth uses tokens"},
    "sources": [{"content": "OAuth protocol docs"}]
  }'
```

**Response:**
```json
{
  "step": 1,
  "reward": 0.75,
  "action": "extract_claim"
}
```

### `POST /api/learning/train`

Run DAPO+GRPO training update.

```bash
curl -X POST "http://localhost:8000/api/learning/train?batch_size=64"
```

### `GET /api/learning/stats`

Get learning statistics.

```bash
curl http://localhost:8000/api/learning/stats
```

**Response:**
```json
{
  "total_steps": 150,
  "buffer_size": 150,
  "dapo_updates": 2,
  "grpo_groups": 3,
  "rlvr_verification": {
    "verified_rate": 0.87
  }
}
```

### `GET /api/learning/dapo`

DAPO optimizer status.

### `GET /api/learning/grpo`

GRPO optimizer status.

### `GET /api/learning/rlvr`

RLVR verification stats.

### `POST /api/learning/gap/select`

Use GAP policy to select action.

```bash
curl -X POST http://localhost:8000/api/learning/gap/select \
  -H "Content-Type: application/json" \
  -d '{
    "gaps": [{"id": "g1", "priority": "high", "gap_type": "missing"}],
    "available_actions": ["research_gap", "resolve_conflict"]
  }'
```

### `POST /api/learning/active/select`

Active learning sample selection.

```bash
curl -X POST http://localhost:8000/api/learning/active/select \
  -H "Content-Type: application/json" \
  -d '{"candidates": [{"id": "c1"}, {"id": "c2"}], "num_queries": 1}'
```

---

## WebSocket

### `WS /ws/terminal`

Interactive terminal session.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/terminal');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({type: 'input', data: 'ls -la\n'}));
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

| Code | Meaning |
|------|---------|
| 400 | Bad request (invalid params) |
| 404 | Resource not found |
| 503 | Service unavailable |
