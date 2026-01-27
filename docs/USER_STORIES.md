# User Stories: Inception Knowledge Compiler

> Feature leverage scenarios demonstrating end-to-end workflows

---

## Story 1: YouTube Learning Ingestion

**As a** learner studying OAuth 2.0  
**I want to** ingest a YouTube tutorial  
**So that** I can extract structured knowledge automatically

### CLI Flow
```bash
inception ingest https://youtube.com/watch?v=oauth-explained

# System:
# 1. Downloads audio via yt-dlp
# 2. Transcribes with Whisper
# 3. Extracts entities: OAuth, PKCE, Bearer Token, JWT
# 4. Extracts claims: "PKCE prevents authorization code interception"
# 5. Detects gaps: "What is PKCE code_verifier?"
# 6. Stores in LMDB temporal hypergraph
```

### API Verification
```bash
curl http://localhost:8000/api/entities
curl http://localhost:8000/api/claims
curl http://localhost:8000/api/gaps
```

---

## Story 2: Knowledge Graph Exploration

**As a** researcher  
**I want to** find paths between concepts  
**So that** I can understand hidden relationships

### CLI Flow
```bash
inception query "How does OAuth relate to JWT?"
```

### API Verification
```bash
curl -X POST http://localhost:8000/api/graph/path \
  -H "Content-Type: application/json" \
  -d '{"source_id":"oauth","target_id":"jwt"}'

# Response:
# {"path_found":true,"path":["oauth","claim-1","jwt"],"hops":2}
```

---

## Story 3: Gap Resolution with Learning Engine

**As a** knowledge maintainer  
**I want to** resolve detected gaps  
**So that** my knowledge base becomes complete

### CLI Flow
```bash
inception gaps          # List gaps
inception learn -a resolve_gap -s research_sources.json
```

### API Verification
```bash
# Get gaps
curl http://localhost:8000/api/gaps

# Trigger learning step
curl -X POST http://localhost:8000/api/learning/step \
  -H "Content-Type: application/json" \
  -d '{"action":"resolve_gap","state":{},"result":{"resolved":true},"sources":[...]}'

# Check learning stats
curl http://localhost:8000/api/learning/stats
```

---

## Story 4: Export to Obsidian

**As a** PKM user  
**I want to** export to my Obsidian vault  
**So that** I can link with my existing notes

### CLI Flow
```bash
inception export obsidian -o ~/Documents/Vault/Inception
```

### API Verification
```bash
curl "http://localhost:8000/api/export?format=obsidian"
```

---

## Story 5: Procedure to ActionPack

**As a** developer  
**I want to** convert tutorial steps to scripts  
**So that** I can automate the procedure

### CLI Flow
```bash
inception action-pack "deploy-oauth" --format bash
```

### API Verification
```bash
curl -X POST http://localhost:8000/api/actionpack \
  -H "Content-Type: application/json" \
  -d '{"procedure_id":"deploy-oauth","format":"bash"}'
```

---

## Story 6: Multi-Source Fusion

**As a** researcher  
**I want to** verify claims across sources  
**So that** I can trust high-confidence information

### API Verification
```bash
# Get source credibility
curl http://localhost:8000/api/sources/rfc6749/credibility

# Check claim conflicts
curl http://localhost:8000/api/sources/rfc6749/conflicts
```

---

## Story 7: Temporal Query

**As a** historian  
**I want to** query knowledge valid at a specific time  
**So that** I can understand historical context

### API Verification
```bash
# Entities valid on Jan 1, 2020
curl "http://localhost:8000/api/entities/temporal?at=2020-01-01T00:00:00Z"

# Claim interval
curl http://localhost:8000/api/claims/c1/interval
```

---

## Story 8: WebUI Dashboard

**As a** visual learner  
**I want to** see my knowledge graph  
**So that** I can explore connections visually

### Verification
```bash
# Open WebUI
curl http://localhost:8000/ui

# Check stats are populated
curl http://localhost:8000/api/stats
```

---

## Verification Matrix

| Story | CLI | API | WebUI | Status |
|-------|-----|-----|-------|--------|
| 1. YouTube Ingestion | ✓ | ✓ | - | ⚠️ Needs media deps |
| 2. Graph Exploration | ✓ | ✓ | ✓ | ✅ Working |
| 3. Gap Resolution | ✓ | ✓ | - | ✅ Working |
| 4. Obsidian Export | ✓ | ✓ | - | ✅ Working |
| 5. ActionPack | ✓ | ✓ | - | ✅ Working |
| 6. Multi-Source | - | ✓ | - | ✅ Working |
| 7. Temporal Query | - | ✓ | - | ✅ Working |
| 8. WebUI Dashboard | - | ✓ | ✓ | ✅ Working |
