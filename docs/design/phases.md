# Inception Project Design Documentation

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-01-27 | Initial Enhancement Epic Complete |
| 2.0.0 | 2026-01-27 | Future Phase Planning (OAuth + Web UX) |

---

# MAJOR PHASE 1: Enhancement Epic (COMPLETE)

**Status**: ✅ 100/100 Steps Complete  
**Tests**: 289 passed, 3 skipped

## Subphase 1.1: Tier 1 - Intelligence Foundation

### 1.1.1 LLM Extractor (Steps 1-10) ✅
| Step | Description | Status |
|------|-------------|--------|
| 1 | LLMProvider abstract base class | ✅ |
| 2 | OllamaProvider implementation | ✅ |
| 3 | OpenRouterProvider implementation | ✅ |
| 4 | CloudProvider (OpenAI/Anthropic) | ✅ |
| 5 | get_provider() factory function | ✅ |
| 6 | Structured extraction prompts | ✅ |
| 7 | Entity extraction prompt | ✅ |
| 8 | Claim extraction prompt | ✅ |
| 9 | Procedure extraction prompt | ✅ |
| 10 | LLMExtractor orchestrator class | ✅ |

**Deliverables**: `inception/enhance/llm/` package (28 tests)

---

### 1.1.2 Vector Index (Steps 11-20) ✅
| Step | Description | Status |
|------|-------------|--------|
| 11 | EmbeddingModel with sentence-transformers | ✅ |
| 12 | Model caching and batch encoding | ✅ |
| 13 | VectorStore abstract base class | ✅ |
| 14 | InMemoryVectorStore implementation | ✅ |
| 15 | ChromaVectorStore implementation | ✅ |
| 16 | VectorIndex manager class | ✅ |
| 17 | Text indexing with metadata | ✅ |
| 18 | Similarity search implementation | ✅ |
| 19 | HybridSearcher (vector + LMDB) | ✅ |
| 20 | Filter support in searches | ✅ |

**Deliverables**: `inception/enhance/vectors/` package (27 tests)

---

### 1.1.3 Vision VLM (Steps 21-25) ✅
| Step | Description | Status |
|------|-------------|--------|
| 21 | VLMProvider abstract base class | ✅ |
| 22 | LLaVAProvider (local) | ✅ |
| 23 | OpenAI Vision provider | ✅ |
| 24 | Anthropic Vision provider | ✅ |
| 25 | VisionAnalyzer orchestrator | ✅ |

**Deliverables**: `inception/enhance/vision/` package (25 tests)

---

## Subphase 1.2: Tier 2 - Agency Capabilities

### 1.2.1 Gap Explorer (Steps 26-35) ✅
| Step | Description | Status |
|------|-------------|--------|
| 26 | ExplorationConfig with safety rails | ✅ |
| 27 | Rate limiting configuration | ✅ |
| 28 | Budget caps and domain filtering | ✅ |
| 29 | GapClassifier with OPUS-1 taxonomy | ✅ |
| 30 | Gap type classification | ✅ |
| 31 | Query generation from gaps | ✅ |
| 32 | WebSearcher with DuckDuckGo | ✅ |
| 33 | Search rate limiting | ✅ |
| 34 | GapResolver orchestrator | ✅ |
| 35 | Resolution workflow | ✅ |

**Deliverables**: `inception/enhance/agency/explorer/` package

---

### 1.2.2 Fact Validator (Steps 36-40) ✅
| Step | Description | Status |
|------|-------------|--------|
| 36 | ValidationSource abstract base | ✅ |
| 37 | WikipediaSource implementation | ✅ |
| 38 | WikidataSource implementation | ✅ |
| 39 | FactValidator orchestrator | ✅ |
| 40 | Evidence analysis and caching | ✅ |

**Deliverables**: `inception/enhance/agency/validator/` package

---

### 1.2.3 Execution Engine (Steps 41-50) ✅
| Step | Description | Status |
|------|-------------|--------|
| 41 | SkillParser for SKILL.md files | ✅ |
| 42 | Frontmatter extraction | ✅ |
| 43 | Step and code block parsing | ✅ |
| 44 | ExecutionConfig with safety | ✅ |
| 45 | Command allowlist/blocklist | ✅ |
| 46 | Sandbox configuration | ✅ |
| 47 | ExecutionEngine class | ✅ |
| 48 | Command validation | ✅ |
| 49 | Dry-run support | ✅ |
| 50 | Execution logging | ✅ |

**Deliverables**: `inception/enhance/agency/executor/` package (29 tests total for Tier 2)

---

## Subphase 1.3: Tier 3 - Synthesis Layer

### 1.3.1 Multi-Source Fusion (Steps 51-60) ✅
| Step | Description | Status |
|------|-------------|--------|
| 51 | SourceRegistry with reliability weighting | ✅ |
| 52 | Domain authority auto-detection | ✅ |
| 53 | Source freshness calculation | ✅ |
| 54 | ClaimMatcher with semantic similarity | ✅ |
| 55 | Match type classification | ✅ |
| 56 | Contradiction detection | ✅ |
| 57 | ConflictResolver with strategies | ✅ |
| 58 | Resolution strategy implementations | ✅ |
| 59 | UncertaintyQuantifier (Bayesian fusion) | ✅ |
| 60 | FusionEngine orchestrator | ✅ |

**Deliverables**: `inception/enhance/synthesis/fusion/` package

---

### 1.3.2 Ontology Linker (Steps 61-70) ✅
| Step | Description | Status |
|------|-------------|--------|
| 61 | WikidataClient with search API | ✅ |
| 62 | SPARQL query support | ✅ |
| 63 | DBpediaClient with lookup API | ✅ |
| 64 | DBpedia resource fetching | ✅ |
| 65 | Schema.org type mapping | ✅ |
| 66 | LinkedEntity dataclass | ✅ |
| 67 | OntologyLinker orchestrator | ✅ |
| 68 | Candidate generation | ✅ |
| 69 | Disambiguation scoring | ✅ |
| 70 | NIL entity detection | ✅ |

**Deliverables**: `inception/enhance/synthesis/ontology/` package

---

### 1.3.3 Temporal Reasoner (Steps 71-75) ✅
| Step | Description | Status |
|------|-------------|--------|
| 71 | Allen's 13 Interval Relations | ✅ |
| 72 | Composition table implementation | ✅ |
| 73 | TemporalParser with date patterns | ✅ |
| 74 | TemporalNetwork with constraint propagation | ✅ |
| 75 | TemporalReasoner orchestrator | ✅ |

**Deliverables**: `inception/enhance/synthesis/temporal/` package (37 tests total for Tier 3)

---

## Subphase 1.4: Tier 4 - Operations

### 1.4.1 Incremental Sync (Steps 76-85) ✅
| Step | Description | Status |
|------|-------------|--------|
| 76 | WatchConfig dataclass | ✅ |
| 77 | Include/exclude patterns | ✅ |
| 78 | FileWatcher with polling | ✅ |
| 79 | Debouncing implementation | ✅ |
| 80 | ChangeDetector with SHA256 | ✅ |
| 81 | SQLite state persistence | ✅ |
| 82 | SyncQueue with priority | ✅ |
| 83 | Retry mechanism | ✅ |
| 84 | SyncEngine orchestrator | ✅ |
| 85 | Worker thread management | ✅ |

**Deliverables**: `inception/enhance/operations/sync/` package

---

### 1.4.2 Export Pipeline (Steps 86-95) ✅
| Step | Description | Status |
|------|-------------|--------|
| 86 | ExportFormat enum | ✅ |
| 87 | File extension mapping | ✅ |
| 88 | ExportPipeline orchestrator | ✅ |
| 89 | Exporter base class | ✅ |
| 90 | ObsidianExporter | ✅ |
| 91 | Wikilinks and frontmatter | ✅ |
| 92 | Index generation | ✅ |
| 93 | MarkdownExporter | ✅ |
| 94 | JSONExporter | ✅ |
| 95 | Separate entity/claim files | ✅ |

**Deliverables**: `inception/enhance/operations/export/` package

---

### 1.4.3 Interactive TUI (Steps 96-100) ✅
| Step | Description | Status |
|------|-------------|--------|
| 96 | TUIConfig dataclass | ✅ |
| 97 | InceptionTUI class | ✅ |
| 98 | Main menu system | ✅ |
| 99 | Entity browser stub | ✅ |
| 100 | Search interface stub | ✅ |

**Deliverables**: `inception/enhance/operations/tui/` package (27 tests total for Tier 4)

---

# MAJOR PHASE 2: OAuth Authentication + Web UX (PLANNED)

**Status**: 🔄 Planning  
**Target**: 200+ Steps

## Subphase 2.1: OAuth Authentication System (Steps 101-150)

### 2.1.1 OAuth Research & Architecture (Steps 101-110)
| Step | Description | Status |
|------|-------------|--------|
| 101 | Study Claude Code OAuth flow | 📋 |
| 102 | Study Antigravity OAuth plugin | 📋 |
| 103 | Study OpenCode integration patterns | 📋 |
| 104 | Design unified OAuth architecture | 📋 |
| 105 | Define token storage strategy | 📋 |
| 106 | Design browser auth flow | 📋 |
| 107 | Plan refresh token handling | 📋 |
| 108 | Design multi-provider abstraction | 📋 |
| 109 | Create OAuth security spec | 📋 |
| 110 | Document subscription tier mapping | 📋 |

---

### 2.1.2 Claude OAuth Provider (Steps 111-125)
| Step | Description | Status |
|------|-------------|--------|
| 111 | ClaudeOAuthConfig dataclass | 📋 |
| 112 | Browser-based auth launcher | 📋 |
| 113 | Local HTTP callback server | 📋 |
| 114 | OAuth code exchange | 📋 |
| 115 | Bearer token acquisition | 📋 |
| 116 | Token secure storage (keychain) | 📋 |
| 117 | Token refresh mechanism | 📋 |
| 118 | Pro/Max subscription detection | 📋 |
| 119 | Rate limit handling | 📋 |
| 120 | Session management | 📋 |
| 121 | Error recovery flows | 📋 |
| 122 | Multi-account rotation | 📋 |
| 123 | Usage tracking | 📋 |
| 124 | Quota monitoring | 📋 |
| 125 | ClaudeOAuthProvider class | 📋 |

---

### 2.1.3 Gemini OAuth Provider (Steps 126-135)
| Step | Description | Status |
|------|-------------|--------|
| 126 | GeminiOAuthConfig dataclass | 📋 |
| 127 | Google OAuth flow integration | 📋 |
| 128 | Vertex AI auth bridge | 📋 |
| 129 | Pro/Ultra tier detection | 📋 |
| 130 | Token management | 📋 |
| 131 | Refresh flow | 📋 |
| 132 | Rate limit handling | 📋 |
| 133 | Multi-account support | 📋 |
| 134 | Usage analytics | 📋 |
| 135 | GeminiOAuthProvider class | 📋 |

---

### 2.1.4 OpenAI OAuth Provider (Steps 136-145)
| Step | Description | Status |
|------|-------------|--------|
| 136 | OpenAIOAuthConfig dataclass | 📋 |
| 137 | ChatGPT Plus/Pro auth flow | 📋 |
| 138 | Session cookie handling | 📋 |
| 139 | Browser session extraction | 📋 |
| 140 | Token persistence | 📋 |
| 141 | Refresh mechanism | 📋 |
| 142 | GPT-4/GPT-4o routing | 📋 |
| 143 | Usage tracking | 📋 |
| 144 | Rate limit handling | 📋 |
| 145 | OpenAIOAuthProvider class | 📋 |

---

### 2.1.5 Unified OAuth Manager (Steps 146-150)
| Step | Description | Status |
|------|-------------|--------|
| 146 | OAuthManager orchestrator | 📋 |
| 147 | Provider auto-detection | 📋 |
| 148 | Fallback chain configuration | 📋 |
| 149 | Health check system | 📋 |
| 150 | OAuth tests (30+ tests) | 📋 |

---

## Subphase 2.2: Angular Web UX (Steps 151-250)

### 2.2.1 Project Setup (Steps 151-160)
| Step | Description | Status |
|------|-------------|--------|
| 151 | Angular 17+ project initialization | 📋 |
| 152 | Material Web 3 integration | 📋 |
| 153 | Angular Material setup | 📋 |
| 154 | Design system tokens | 📋 |
| 155 | Theme configuration (dark/light) | 📋 |
| 156 | Responsive breakpoints | 📋 |
| 157 | Base layout components | 📋 |
| 158 | Router configuration | 📋 |
| 159 | State management (signals) | 📋 |
| 160 | API service layer | 📋 |

---

### 2.2.2 Core UI Components (Steps 161-180)
| Step | Description | Status |
|------|-------------|--------|
| 161 | Navigation shell | 📋 |
| 162 | Sidebar component | 📋 |
| 163 | Header with status | 📋 |
| 164 | Command palette | 📋 |
| 165 | File upload dropzone | 📋 |
| 166 | Progress indicators | 📋 |
| 167 | Toast notifications | 📋 |
| 168 | Modal dialogs | 📋 |
| 169 | Confirmation dialogs | 📋 |
| 170 | Search input component | 📋 |
| 171 | Entity card component | 📋 |
| 172 | Claim card component | 📋 |
| 173 | Procedure card component | 📋 |
| 174 | Source citation component | 📋 |
| 175 | Evidence chain component | 📋 |
| 176 | Gap alert component | 📋 |
| 177 | Sync status component | 📋 |
| 178 | Export dialog | 📋 |
| 179 | Settings panel | 📋 |
| 180 | OAuth connection cards | 📋 |

---

### 2.2.3 Knowledge Graph Views (Steps 181-200)
| Step | Description | Status |
|------|-------------|--------|
| 181 | Entity list view | 📋 |
| 182 | Entity detail view | 📋 |
| 183 | Entity edit form | 📋 |
| 184 | Claim list view | 📋 |
| 185 | Claim detail view | 📋 |
| 186 | Procedure list view | 📋 |
| 187 | Procedure step viewer | 📋 |
| 188 | Source list view | 📋 |
| 189 | Graph visualization (D3/Cytoscape) | 📋 |
| 190 | Node hover tooltips | 📋 |
| 191 | Edge relationship display | 📋 |
| 192 | Zoom/pan controls | 📋 |
| 193 | Node search highlighting | 📋 |
| 194 | Subgraph extraction | 📋 |
| 195 | Timeline view (temporal) | 📋 |
| 196 | Fusion conflicts view | 📋 |
| 197 | Ontology links view | 📋 |
| 198 | Gap explorer view | 📋 |
| 199 | Validation results view | 📋 |
| 200 | Dashboard home | 📋 |

---

### 2.2.4 CLI Passthrough (Steps 201-220)
| Step | Description | Status |
|------|-------------|--------|
| 201 | WebSocket CLI bridge | 📋 |
| 202 | Terminal emulator component | 📋 |
| 203 | Command input with history | 📋 |
| 204 | Output streaming | 📋 |
| 205 | ANSI color rendering | 📋 |
| 206 | Command autocomplete | 📋 |
| 207 | File path completion | 📋 |
| 208 | Inline help display | 📋 |
| 209 | Command palette integration | 📋 |
| 210 | Binary file upload integration | 📋 |
| 211 | Remote VPS connection | 📋 |
| 212 | SSH tunnel support | 📋 |
| 213 | Session persistence | 📋 |
| 214 | Split terminal panes | 📋 |
| 215 | Terminal themes | 📋 |
| 216 | Scroll buffer management | 📋 |
| 217 | Copy/paste handling | 📋 |
| 218 | Keyboard shortcuts | 📋 |
| 219 | Command history search | 📋 |
| 220 | Quick actions from UI | 📋 |

---

### 2.2.5 TUI Mirror Implementation (Steps 221-240)
| Step | Description | Status |
|------|-------------|--------|
| 221 | Textual library integration | 📋 |
| 222 | TUI layout matching web | 📋 |
| 223 | Entity browser panel | 📋 |
| 224 | Claim browser panel | 📋 |
| 225 | Search panel | 📋 |
| 226 | Graph explorer panel | 📋 |
| 227 | Evidence viewer panel | 📋 |
| 228 | Status bar | 📋 |
| 229 | Command input | 📋 |
| 230 | Keyboard navigation | 📋 |
| 231 | Mouse support | 📋 |
| 232 | Theme parity with web | 📋 |
| 233 | Unicode box drawing | 📋 |
| 234 | Color scheme | 📋 |
| 235 | Responsive terminal sizing | 📋 |
| 236 | Modal dialogs | 📋 |
| 237 | Toast notifications | 📋 |
| 238 | Progress indicators | 📋 |
| 239 | File browser | 📋 |
| 240 | Help overlay | 📋 |

---

### 2.2.6 Testing & Polish (Steps 241-250)
| Step | Description | Status |
|------|-------------|--------|
| 241 | Unit tests for components | 📋 |
| 242 | Integration tests | 📋 |
| 243 | E2E tests (Playwright) | 📋 |
| 244 | Accessibility audit | 📋 |
| 245 | Performance optimization | 📋 |
| 246 | Bundle size optimization | 📋 |
| 247 | PWA configuration | 📋 |
| 248 | Documentation | 📋 |
| 249 | VPS deployment config | 📋 |
| 250 | Final integration testing | 📋 |

---

## Agent Assignments

| Agent | Role | Tasks |
|-------|------|-------|
| **OPUS-1** | OAuth Architecture Lead | 101-110, 146-150 |
| **OPUS-2** | Claude OAuth Implementation | 111-125 |
| **OPUS-3** | Gemini/OpenAI OAuth | 126-145 |
| **GEMINI-PRO-1** | Angular Core & Components | 151-180 |
| **GEMINI-PRO-2** | Knowledge Graph Views | 181-200 |
| **CODEX** | CLI Passthrough & TUI | 201-240 |

---

## Dependencies

### OAuth System
- `keyring` - Secure credential storage
- `httpx` - HTTP client with async
- `webbrowser` - Browser launcher
- `aiohttp` - Local callback server

### Angular Web UX
- `@angular/core@17+` - Framework
- `@angular/material@17+` - Material Design
- `@angular/cdk` - Component Dev Kit
- `@nicholasq/angular-material-web` - Material Web 3
- `d3` or `cytoscape` - Graph visualization
- `xterm.js` - Terminal emulator

### TUI Enhancement
- `textual>=0.47` - Modern TUI framework
- `rich` - Rich text rendering
