# Inception Component Intents

> One-sentence purpose statements for each component

---

## Extraction Components

| Component | Intent |
|-----------|--------|
| **ClaimExtractor** | Exists to decompose text into SPO triples with modality and hedges for knowledge graph population, under latency constraint < 500ms. |
| **EntityRecognizer** | Exists to identify named entities (persons, orgs, protocols, documents) in text with type classification, under recall target > 0.85. |
| **EntityLinker** | Exists to disambiguate entities and link them to Wikidata/DBpedia for semantic enrichment, under precision target > 0.80. |
| **ProcedureExtractor** | Exists to identify ordered steps, conditionals, and error handling from instructional content, under step-order accuracy > 0.90. |
| **TemporalParser** | Exists to extract temporal expressions and Allen interval relations for validity tracking, under temporal F1 > 0.75. |

---

## Synthesis Components

| Component | Intent |
|-----------|--------|
| **SkillCompiler** | Exists to transform procedures into executable skill definitions with declared dependencies, under executability rate > 0.85. |
| **GapDetector** | Exists to identify undefined terms, missing prerequisites, and contradictions for autonomous resolution queuing. |
| **GapResolver** | Exists to autonomously research and fill knowledge gaps within safety constraints (rate limits, domain allowlists). |
| **SourceFuser** | Exists to merge claims across multiple sources with Bayesian confidence aggregation and contradiction flagging. |

---

## Learning Components

| Component | Intent |
|-----------|--------|
| **DAPOOptimizer** | Exists to enable high-variance exploration in extraction optimization using dynamic clip range based on advantage variance. |
| **GRPOOptimizer** | Exists to optimize extraction preferences using group-relative advantages without a critic network for memory efficiency. |
| **RLVROptimizer** | Exists to provide verifiable reward signals by matching extracted content against source ground truth. |
| **GAPLearner** | Exists to prioritize learning from actions that fill knowledge gaps, focusing on epistemic uncertainty reduction. |
| **TextGradOptimizer** | Exists to iteratively refine claims and prompts using LLM-generated textual gradients for semantic improvement. |

---

## Interface Components

| Component | Intent |
|-----------|--------|
| **RheoEngine** | Exists to enable bidirectional synthesis/analysis flow with interactive expansion ("why?", "how?", "when?") and automatic branching. |
| **KnowledgeGraph** | Exists to store entities, claims, procedures, and skills in a versioned hypergraph with temporal validity and provenance tracking. |
| **APIServer** | Exists to expose all capabilities via REST/WebSocket API for client integration, under P95 latency < 200ms for queries. |
| **TUIClient** | Exists to provide terminal-based interaction with RheoMode output levels and real-time progress for CLI users. |

---

## Output Components

| Component | Intent |
|-----------|--------|
| **ActionPackGenerator** | Exists to package related claims, procedures, and skills into distributable ActionPacks with RheoMode output levels. |
| **ObsidianExporter** | Exists to export knowledge to Obsidian vault format with wikilinks, frontmatter, and graph visualization. |
| **SkillPacker** | Exists to serialize skills into portable formats (JSON, YAML) with environment requirements and test suites. |

---

## Update Protocol

When adding a new component:

1. Write Intent statement (one sentence)
2. Add to this document
3. Define Invariants in `invariants.md`
4. Add interface contract in `schemas/`
5. Add golden examples in `eval/goldens/`
