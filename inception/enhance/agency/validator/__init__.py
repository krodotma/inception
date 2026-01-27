"""
Fact Validator - Claim verification against authoritative sources.

Sources by priority (OPUS-1 design):
1. Wikipedia (broad coverage, CC license)
2. Wikidata (structured facts with QIDs)
3. Semantic Scholar (academic claims)
"""

from inception.enhance.agency.validator.sources import (
    WikipediaSource,
    WikidataSource,
)
from inception.enhance.agency.validator.validator import (
    FactValidator,
    ValidationResult,
    ValidationStatus,
)

__all__ = [
    "FactValidator",
    "ValidationResult",
    "ValidationStatus",
    "WikipediaSource",
    "WikidataSource",
]
