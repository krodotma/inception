"""
Extraction prompts for LLM-enhanced analysis.

These prompts are designed to extract structured information
from text spans for claim, entity, and procedure detection.
"""

SYSTEM_PROMPT = """You are an expert knowledge extraction system. Your task is to analyze text and extract structured information with high precision. Always output valid JSON."""

CLAIM_EXTRACTION_PROMPT = """Analyze the following text and extract all factual claims.

TEXT:
{text}

For each claim, identify:
1. The claim text (normalized, declarative form)
2. Subject-Predicate-Object structure (if applicable)
3. Modality: assertion, possibility, necessity, or conditional
4. Hedging words (e.g., "might", "probably", "seems")
5. Negation: true if the claim is negated
6. Confidence: your confidence in the extraction (0.0-1.0)

Output as JSON array:
```json
{{
  "claims": [
    {{
      "text": "normalized claim statement",
      "subject": "subject entity",
      "predicate": "relationship or action",
      "object": "object entity or value",
      "modality": "assertion|possibility|necessity|conditional",
      "hedging": ["word1", "word2"],
      "negated": false,
      "confidence": 0.9
    }}
  ]
}}
```

Extract ALL claims, including implicit ones. Be thorough."""

ENTITY_EXTRACTION_PROMPT = """Analyze the following text and extract all named entities.

TEXT:
{text}

For each entity, identify:
1. Name (canonical form)
2. Type: PERSON, ORG, PRODUCT, CONCEPT, LOCATION, EVENT, WORK, OTHER
3. Aliases (other names used in the text)
4. Description (brief description if mentioned)
5. Confidence: your confidence in the extraction (0.0-1.0)

Output as JSON array:
```json
{{
  "entities": [
    {{
      "name": "canonical entity name",
      "type": "PERSON|ORG|PRODUCT|CONCEPT|LOCATION|EVENT|WORK|OTHER",
      "aliases": ["alias1", "alias2"],
      "description": "brief description if available",
      "confidence": 0.9
    }}
  ]
}}
```

Include technical terms, product names, and important concepts.
Resolve coreferences (he/she/it → actual entity)."""

PROCEDURE_EXTRACTION_PROMPT = """Analyze the following text and extract procedural instructions.

TEXT:
{text}

For each procedure, identify:
1. Title (what is being accomplished)
2. Goal (end state or outcome)
3. Prerequisites (what's needed before starting)
4. Steps (ordered list of actions)
5. Warnings (cautions or things to avoid)
6. Outcomes (expected results)

For each step:
1. Index (0-based order)
2. Text (the instruction)
3. Action verb (the main action: install, configure, run, etc.)
4. Optional: true if step is optional
5. Prerequisites for this specific step

Output as JSON:
```json
{{
  "procedures": [
    {{
      "title": "procedure title",
      "goal": "what this accomplishes",
      "prerequisites": ["prereq1", "prereq2"],
      "steps": [
        {{
          "index": 0,
          "text": "step instruction",
          "action_verb": "install",
          "optional": false,
          "prerequisites": []
        }}
      ],
      "warnings": ["warning1"],
      "outcomes": ["expected result"]
    }}
  ]
}}
```

Extract implicit procedures from instructional content."""

GAP_DETECTION_PROMPT = """Analyze the following text and identify knowledge gaps or uncertainties.

TEXT:
{text}

Look for:
1. Undefined terms (concepts used without explanation)
2. Missing context (assumptions or background not provided)
3. Incomplete procedures (steps that skip details)
4. Unresolved references (mentions of external content)
5. Contradictions (conflicting statements)
6. Hedged claims (uncertain statements)

For each gap:
1. Type: undefined_term, missing_context, incomplete_procedure, unresolved_reference, contradiction, uncertain_claim
2. Description (what's missing or unclear)
3. Location hint (where in the text)
4. Severity: low, medium, high
5. Resolution hints (how to resolve)

Output as JSON:
```json
{{
  "gaps": [
    {{
      "type": "undefined_term",
      "description": "RLHF mentioned without definition",
      "location_hint": "first paragraph",
      "severity": "medium",
      "resolution_hints": ["search for RLHF definition", "check ML glossary"]
    }}
  ]
}}
```

Be thorough - gaps are valuable for improving understanding."""

SYNTHESIS_PROMPT = """Perform comprehensive extraction on the following text.

TEXT:
{text}

Extract:
1. All entities (people, organizations, products, concepts)
2. All claims (factual statements, opinions, predictions)
3. All procedures (step-by-step instructions)
4. All gaps (undefined terms, missing context)

Output as unified JSON:
```json
{{
  "entities": [...],
  "claims": [...],
  "procedures": [...],
  "gaps": [...]
}}
```

Use the detailed schemas from individual extraction tasks.
Ensure cross-references between entities and claims are consistent."""
