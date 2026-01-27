"""
Synthesis enhancement modules.

Advanced knowledge synthesis capabilities:
- Multi-Source Fusion: Combine knowledge with conflict resolution
- Ontology Linker: Connect entities to semantic web resources
- Temporal Reasoner: Infer and validate temporal relationships

Team Design:
- OPUS-1: Fusion model, Allen's Interval Algebra
- OPUS-2: Bayesian uncertainty, semantic matching
- OPUS-3: Clean architecture, constraint propagation
- GEMINI-PRO: SPARQL integration, federated queries
- SONNET: CLI experience, confidence display
"""

from inception.enhance.synthesis.fusion import (
    FusionEngine,
    SourceRegistry,
    ClaimMatcher,
    ConflictResolver,
    ContradictionType,
)
from inception.enhance.synthesis.ontology import (
    OntologyLinker,
    LinkedEntity,
    WikidataClient,
    DBpediaClient,
)
from inception.enhance.synthesis.temporal import (
    TemporalReasoner,
    TemporalFact,
    TemporalRelation,
    TemporalNetwork,
)

__all__ = [
    # Fusion
    "FusionEngine",
    "SourceRegistry",
    "ClaimMatcher",
    "ConflictResolver",
    "ContradictionType",
    # Ontology
    "OntologyLinker",
    "LinkedEntity",
    "WikidataClient",
    "DBpediaClient",
    # Temporal
    "TemporalReasoner",
    "TemporalFact",
    "TemporalRelation",
    "TemporalNetwork",
]
