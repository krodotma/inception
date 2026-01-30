"""
ENTELECHEIA+ Surface Package

The reactive knowledge surface that processes any input blob.
"""

from inception.surface.reactive import (
    BlobType,
    BlobClassifier,
    BlobDetector,
    DetectionResult,
    NormalizedBlob,
    InputNormalizer,
    ReactiveSurface,
    SurfaceEvent,
)

from inception.surface.coobject import (
    CoObject,
    CoObjectEdge,
    CoObjectGraph,
    CoObjectInferrer,
    CoObjectRelation,
    RheoTransformer,
)

from inception.surface.stigmergic import (
    TraceType,
    NeuralTrace,
    StigmergicWorkspace,
    EmergentTopology,
    # Backward compat
    PheromoneTrace,
    StigmergicCoordinator,
)

from inception.surface.neurosymbolic import (
    ReasoningMode,
    GroundingResult,
    EmbeddingResult,
    NeuralToSymbolicBridge,
    SymbolicToNeuralBridge,
    HybridReasoner,
    ReasoningStep,
    ReasoningResult,
)

__all__ = [
    # Reactive Surface
    "BlobType",
    "BlobClassifier",
    "BlobDetector",
    "DetectionResult",
    "NormalizedBlob",
    "InputNormalizer",
    "ReactiveSurface",
    "SurfaceEvent",
    # Co-Object
    "CoObject",
    "CoObjectEdge",
    "CoObjectGraph",
    "CoObjectInferrer",
    "CoObjectRelation",
    "RheoTransformer",
    # Stigmergic
    "TraceType",
    "NeuralTrace",
    "StigmergicWorkspace",
    "EmergentTopology",
    "PheromoneTrace",
    "StigmergicCoordinator",
    # Neurosymbolic
    "ReasoningMode",
    "GroundingResult",
    "EmbeddingResult",
    "NeuralToSymbolicBridge",
    "SymbolicToNeuralBridge",
    "HybridReasoner",
    "ReasoningStep",
    "ReasoningResult",
]
