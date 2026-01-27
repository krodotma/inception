"""
Agency enhancement modules.

Provides autonomous capabilities with safety rails:
- Gap Explorer: Autonomous knowledge acquisition
- Fact Validator: Claim verification against authoritative sources
- Execution Engine: SKILL.md step execution in sandbox

Team Design:
- GEMINI-PRO: Safety-first integration
- OPUS-1: Gap taxonomy and validation sources
- OPUS-3: Security architecture
- SONNET: Interactive UX
"""

from inception.enhance.agency.explorer import (
    GapExplorer,
    GapClassifier,
    GapType,
    ExplorationConfig,
)
from inception.enhance.agency.validator import (
    FactValidator,
    ValidationResult,
    ValidationStatus,
)
from inception.enhance.agency.executor import (
    ExecutionEngine,
    SkillParser,
    ExecutionResult,
)

__all__ = [
    # Explorer
    "GapExplorer",
    "GapClassifier",
    "GapType",
    "ExplorationConfig",
    # Validator
    "FactValidator",
    "ValidationResult",
    "ValidationStatus",
    # Executor
    "ExecutionEngine",
    "SkillParser",
    "ExecutionResult",
]
