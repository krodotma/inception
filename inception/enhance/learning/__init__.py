"""
Advanced Learning Module for Inception.

Extends the core learning engine with:
- DSPy integration for declarative LLM programming
- TextGrad for differentiable text optimization
- GRPO v2 for enhanced preference optimization
- Compound optimizer for strategy selection
"""

from inception.enhance.learning.dspy_integration import (
    ClaimExtractor,
    EntityLinker,
    GapResolver,
    InceptionPipeline,
)
from inception.enhance.learning.textgrad_optimizer import TextGradOptimizer
from inception.enhance.learning.grpo_v2 import GRPOv2Optimizer
from inception.enhance.learning.compound_optimizer import CompoundOptimizer
from inception.enhance.learning.metrics import (
    LearningMetrics,
    compute_claim_f1,
    compute_entity_accuracy,
)

__all__ = [
    # DSPy
    "ClaimExtractor",
    "EntityLinker", 
    "GapResolver",
    "InceptionPipeline",
    # TextGrad
    "TextGradOptimizer",
    # GRPO
    "GRPOv2Optimizer",
    # Compound
    "CompoundOptimizer",
    # Metrics
    "LearningMetrics",
    "compute_claim_f1",
    "compute_entity_accuracy",
]
