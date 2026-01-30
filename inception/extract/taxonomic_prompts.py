"""
Extraction Prompts for Taxonomic Types

LLM prompts to extract Domain, Idea, Project, and Contact entities
from unstructured text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# =============================================================================
# Domain Extraction
# =============================================================================

DOMAIN_EXTRACTION_SYSTEM = """You are an expert at identifying knowledge domains from text.
A domain is a coherent area of knowledge or expertise (like "OAuth 2.0", "Machine Learning", "Frontend Development").

When extracting domains:
1. Identify the main subject area being discussed
2. Look for hierarchical relationships (parent/child domains)
3. Note any keywords that characterize the domain
4. Assess how well-covered the domain is in the text

Output JSON with these fields:
- name: Domain name
- description: Brief description
- parent: Parent domain if mentioned
- children: Child domains if mentioned
- keywords: Key terms associated with this domain
"""

DOMAIN_EXTRACTION_PROMPT = """Extract knowledge domains from the following text.
Return a JSON array of domains.

Text:
{text}

Domains:"""


# =============================================================================
# Idea Extraction (with Dialectical Structure)
# =============================================================================

IDEA_EXTRACTION_SYSTEM = """You are an expert at identifying ideas with dialectical structure.
An idea is a concept that may have:
- THESIS: A primary position or claim
- ANTITHESIS: An opposing position or counterargument
- SYNTHESIS: A resolution or integration of both positions

Look for:
1. Statements of position ("X is better because...")
2. Counterarguments ("However, X has problems...")
3. Resolutions ("The best approach is to...")
4. Unresolved debates (no synthesis yet)

Output JSON with:
- name: Idea name
- domain: Which domain this belongs to
- thesis: The primary position (or null)
- antithesis: The opposing position (or null)
- synthesis: The resolution (or null)
- dialectical_state: "thesis_only" | "antithesis_proposed" | "synthesis_pending" | "resolved"
- epistemic_gaps: Knowledge missing to resolve debate
- aleatoric_ambiguities: Inherent uncertainties that can't be eliminated
"""

IDEA_EXTRACTION_PROMPT = """Extract ideas with dialectical structure from the following text.
Pay special attention to debates, tradeoffs, and competing perspectives.
Return a JSON array of ideas.

Text:
{text}

Ideas:"""


# =============================================================================
# Project Extraction
# =============================================================================

PROJECT_EXTRACTION_SYSTEM = """You are an expert at identifying projects from text.
A project is an active work context with:
- A clear goal or objective
- Related resources (ideas, people, procedures)
- A status (planning, active, completed, etc.)

Look for:
1. Statements of intent ("We need to...", "The goal is...")
2. Progress indicators ("We've completed...", "Next we will...")
3. Blockers or gaps ("We're blocked on...", "Missing...")
4. Team/stakeholder mentions

Output JSON with:
- name: Project name
- domain: Primary knowledge domain
- goal: The project's objective
- status: "planning" | "active" | "paused" | "completed"
- blocking_gaps: What's blocking progress
"""

PROJECT_EXTRACTION_PROMPT = """Extract projects and work contexts from the following text.
Return a JSON array of projects.

Text:
{text}

Projects:"""


# =============================================================================
# Contact Extraction
# =============================================================================

CONTACT_EXTRACTION_SYSTEM = """You are an expert at identifying people and agents from text.
A contact can be:
- Human: A person with expertise
- Agent: An AI or automated system with capabilities
- Organization: A team or company

Look for:
1. Named individuals and their roles
2. References to AI systems or tools
3. Team or organization mentions
4. Expertise indicators ("expert in...", "responsible for...")

Output JSON with:
- name: Contact name
- contact_type: "human" | "agent" | "organization"
- affiliation: Organization if mentioned
- expertise_domains: Areas of expertise
- role: Their role if mentioned
"""

CONTACT_EXTRACTION_PROMPT = """Extract contacts (people, agents, organizations) from the following text.
Return a JSON array of contacts.

Text:
{text}

Contacts:"""


# =============================================================================
# Dialectical Relation Detection
# =============================================================================

ANTITHESIS_DETECTION_SYSTEM = """You are an expert at detecting opposing positions.
Given a thesis (primary claim), identify if the text contains an antithesis (opposing view).

Patterns to look for:
1. NEGATION: "X is not Y" vs "X is Y"
2. OPPOSITION: "X is good" vs "X is bad"
3. ALTERNATIVE: "Use X" vs "Use Y instead"
4. LIMITATION: "X works" vs "X only works when..."
5. EXCEPTION: "Always X" vs "Except when Y"

Output JSON with:
- has_antithesis: boolean
- antithesis: The opposing statement (or null)
- pattern: Which pattern was detected
- confidence: 0.0 to 1.0
"""

ANTITHESIS_DETECTION_PROMPT = """Given this thesis:
"{thesis}"

Does the following text contain an antithesis (opposing position)?

Text:
{text}

Analysis:"""


# =============================================================================
# Synthesis Generation
# =============================================================================

SYNTHESIS_GENERATION_SYSTEM = """You are an expert at generating syntheses that integrate opposing positions.
Given a thesis and antithesis, propose a synthesis that:
1. Acknowledges the validity of both positions
2. Identifies the conditions under which each is correct
3. Proposes an integrated view or resolution
4. Notes any remaining uncertainties

Strategies:
- CONTEXTUALIZATION: Both are true in different contexts
- SCOPING: One applies more narrowly than the other
- INTEGRATION: Combine elements of both
- HIERARCHY: One is more fundamental
- DIALECTICAL: A new position transcending both
"""

SYNTHESIS_GENERATION_PROMPT = """Generate a synthesis integrating these opposing positions:

THESIS: {thesis}

ANTITHESIS: {antithesis}

DOMAIN CONTEXT: {domain}

Propose a synthesis and explain your reasoning.

Synthesis:"""


# =============================================================================
# Prompt Registry
# =============================================================================

@dataclass
class ExtractionPrompt:
    """An extraction prompt with system message and user template."""
    name: str
    target_type: str
    system_message: str
    user_template: str
    output_schema: dict[str, Any] | None = None


EXTRACTION_PROMPTS = {
    "domain": ExtractionPrompt(
        name="domain_extraction",
        target_type="Domain",
        system_message=DOMAIN_EXTRACTION_SYSTEM,
        user_template=DOMAIN_EXTRACTION_PROMPT,
    ),
    "idea": ExtractionPrompt(
        name="idea_extraction",
        target_type="Idea",
        system_message=IDEA_EXTRACTION_SYSTEM,
        user_template=IDEA_EXTRACTION_PROMPT,
    ),
    "project": ExtractionPrompt(
        name="project_extraction",
        target_type="Project",
        system_message=PROJECT_EXTRACTION_SYSTEM,
        user_template=PROJECT_EXTRACTION_PROMPT,
    ),
    "contact": ExtractionPrompt(
        name="contact_extraction",
        target_type="Contact",
        system_message=CONTACT_EXTRACTION_SYSTEM,
        user_template=CONTACT_EXTRACTION_PROMPT,
    ),
    "antithesis": ExtractionPrompt(
        name="antithesis_detection",
        target_type="AntithesisDetection",
        system_message=ANTITHESIS_DETECTION_SYSTEM,
        user_template=ANTITHESIS_DETECTION_PROMPT,
    ),
    "synthesis": ExtractionPrompt(
        name="synthesis_generation",
        target_type="Synthesis",
        system_message=SYNTHESIS_GENERATION_SYSTEM,
        user_template=SYNTHESIS_GENERATION_PROMPT,
    ),
}


def get_extraction_prompt(prompt_type: str) -> ExtractionPrompt:
    """Get an extraction prompt by type."""
    if prompt_type not in EXTRACTION_PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}. Available: {list(EXTRACTION_PROMPTS.keys())}")
    return EXTRACTION_PROMPTS[prompt_type]


def format_prompt(prompt_type: str, **kwargs) -> tuple[str, str]:
    """Format an extraction prompt with the given variables.
    
    Returns:
        Tuple of (system_message, user_message)
    """
    prompt = get_extraction_prompt(prompt_type)
    user_message = prompt.user_template.format(**kwargs)
    return prompt.system_message, user_message
