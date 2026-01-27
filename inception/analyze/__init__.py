"""Analysis layer for semantic extraction."""

from inception.analyze.entities import (
    Entity,
    EntityCluster,
    EntityExtractionResult,
    EntityExtractor,
    extract_entities,
    resolve_entity,
    normalize_entity_type,
)
from inception.analyze.claims import (
    Claim,
    ClaimExtractionResult,
    ClaimExtractor,
    extract_claims,
    compute_claim_similarity,
    detect_contradiction,
)
from inception.analyze.procedures import (
    ProcedureStep,
    Procedure,
    ProcedureExtractionResult,
    ProcedureExtractor,
    extract_procedures,
    procedure_to_skill,
)
from inception.analyze.gaps import (
    GapType,
    Gap,
    GapDetectionResult,
    GapDetector,
    detect_gaps,
    create_gap_node,
)

__all__ = [
    # Entities
    "Entity",
    "EntityCluster",
    "EntityExtractionResult",
    "EntityExtractor",
    "extract_entities",
    "resolve_entity",
    "normalize_entity_type",
    # Claims
    "Claim",
    "ClaimExtractionResult",
    "ClaimExtractor",
    "extract_claims",
    "compute_claim_similarity",
    "detect_contradiction",
    # Procedures
    "ProcedureStep",
    "Procedure",
    "ProcedureExtractionResult",
    "ProcedureExtractor",
    "extract_procedures",
    "procedure_to_skill",
    # Gaps
    "GapType",
    "Gap",
    "GapDetectionResult",
    "GapDetector",
    "detect_gaps",
    "create_gap_node",
]
