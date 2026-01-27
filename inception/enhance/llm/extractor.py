"""
LLM-enhanced extractor for claims, entities, and procedures.

Provides hybrid spaCy + LLM extraction pipeline with automatic
provider selection and fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from inception.enhance.llm.providers import LLMProvider, get_provider, LLMResponse
from inception.enhance.llm.prompts import (
    SYSTEM_PROMPT,
    CLAIM_EXTRACTION_PROMPT,
    ENTITY_EXTRACTION_PROMPT,
    PROCEDURE_EXTRACTION_PROMPT,
    GAP_DETECTION_PROMPT,
    SYNTHESIS_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """An entity extracted by LLM."""
    
    name: str
    entity_type: str
    aliases: list[str] = field(default_factory=list)
    description: str | None = None
    confidence: float = 0.9


@dataclass
class ExtractedClaim:
    """A claim extracted by LLM."""
    
    text: str
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    modality: str = "assertion"
    hedging: list[str] = field(default_factory=list)
    negated: bool = False
    confidence: float = 0.9


@dataclass
class ExtractedStep:
    """A procedure step extracted by LLM."""
    
    index: int
    text: str
    action_verb: str = ""
    optional: bool = False
    prerequisites: list[str] = field(default_factory=list)


@dataclass
class ExtractedProcedure:
    """A procedure extracted by LLM."""
    
    title: str
    goal: str = ""
    prerequisites: list[str] = field(default_factory=list)
    steps: list[ExtractedStep] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)


@dataclass
class ExtractedGap:
    """A knowledge gap extracted by LLM."""
    
    gap_type: str
    description: str
    location_hint: str = ""
    severity: str = "medium"
    resolution_hints: list[str] = field(default_factory=list)


@dataclass
class LLMExtractionResult:
    """Complete extraction result from LLM."""
    
    entities: list[ExtractedEntity] = field(default_factory=list)
    claims: list[ExtractedClaim] = field(default_factory=list)
    procedures: list[ExtractedProcedure] = field(default_factory=list)
    gaps: list[ExtractedGap] = field(default_factory=list)
    
    # Metadata
    provider: str = ""
    model: str = ""
    tokens_used: int = 0
    cost_usd: float = 0.0
    
    def merge(self, other: LLMExtractionResult) -> LLMExtractionResult:
        """Merge another result into this one."""
        return LLMExtractionResult(
            entities=self.entities + other.entities,
            claims=self.claims + other.claims,
            procedures=self.procedures + other.procedures,
            gaps=self.gaps + other.gaps,
            provider=self.provider or other.provider,
            model=self.model or other.model,
            tokens_used=self.tokens_used + other.tokens_used,
            cost_usd=self.cost_usd + other.cost_usd,
        )


class LLMExtractor:
    """
    LLM-enhanced extraction for claims, entities, and procedures.
    
    Provides both individual extraction methods and a unified
    synthesis method for comprehensive extraction.
    """
    
    def __init__(
        self,
        provider: LLMProvider | None = None,
        provider_name: str = "auto",
        offline: bool = False,
        model: str | None = None,
    ):
        """
        Initialize the LLM extractor.
        
        Args:
            provider: Pre-configured provider instance
            provider_name: Provider name for auto-selection
            offline: Use only offline-capable providers
            model: Model override
        """
        self.provider = provider or get_provider(
            name=provider_name,
            offline=offline,
            model=model,
        )
        self._total_tokens = 0
        self._total_cost = 0.0
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used across all extractions."""
        return self._total_tokens
    
    @property
    def total_cost(self) -> float:
        """Total cost in USD across all extractions."""
        return self._total_cost
    
    def extract_entities(self, text: str) -> list[ExtractedEntity]:
        """Extract entities from text."""
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)
        
        try:
            data = self.provider.complete_json(prompt, system=SYSTEM_PROMPT)
            self._update_stats(data)
            
            entities = []
            for e in data.get("entities", []):
                entities.append(ExtractedEntity(
                    name=e.get("name", ""),
                    entity_type=e.get("type", "OTHER"),
                    aliases=e.get("aliases", []),
                    description=e.get("description"),
                    confidence=e.get("confidence", 0.9),
                ))
            return entities
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return []
    
    def extract_claims(self, text: str) -> list[ExtractedClaim]:
        """Extract claims from text."""
        prompt = CLAIM_EXTRACTION_PROMPT.format(text=text)
        
        try:
            data = self.provider.complete_json(prompt, system=SYSTEM_PROMPT)
            self._update_stats(data)
            
            claims = []
            for c in data.get("claims", []):
                claims.append(ExtractedClaim(
                    text=c.get("text", ""),
                    subject=c.get("subject"),
                    predicate=c.get("predicate"),
                    object=c.get("object"),
                    modality=c.get("modality", "assertion"),
                    hedging=c.get("hedging", []),
                    negated=c.get("negated", False),
                    confidence=c.get("confidence", 0.9),
                ))
            return claims
        except Exception as e:
            logger.warning(f"Claim extraction failed: {e}")
            return []
    
    def extract_procedures(self, text: str) -> list[ExtractedProcedure]:
        """Extract procedures from text."""
        prompt = PROCEDURE_EXTRACTION_PROMPT.format(text=text)
        
        try:
            data = self.provider.complete_json(prompt, system=SYSTEM_PROMPT)
            self._update_stats(data)
            
            procedures = []
            for p in data.get("procedures", []):
                steps = []
                for s in p.get("steps", []):
                    steps.append(ExtractedStep(
                        index=s.get("index", 0),
                        text=s.get("text", ""),
                        action_verb=s.get("action_verb", ""),
                        optional=s.get("optional", False),
                        prerequisites=s.get("prerequisites", []),
                    ))
                
                procedures.append(ExtractedProcedure(
                    title=p.get("title", ""),
                    goal=p.get("goal", ""),
                    prerequisites=p.get("prerequisites", []),
                    steps=steps,
                    warnings=p.get("warnings", []),
                    outcomes=p.get("outcomes", []),
                ))
            return procedures
        except Exception as e:
            logger.warning(f"Procedure extraction failed: {e}")
            return []
    
    def extract_gaps(self, text: str) -> list[ExtractedGap]:
        """Extract knowledge gaps from text."""
        prompt = GAP_DETECTION_PROMPT.format(text=text)
        
        try:
            data = self.provider.complete_json(prompt, system=SYSTEM_PROMPT)
            self._update_stats(data)
            
            gaps = []
            for g in data.get("gaps", []):
                gaps.append(ExtractedGap(
                    gap_type=g.get("type", "unknown"),
                    description=g.get("description", ""),
                    location_hint=g.get("location_hint", ""),
                    severity=g.get("severity", "medium"),
                    resolution_hints=g.get("resolution_hints", []),
                ))
            return gaps
        except Exception as e:
            logger.warning(f"Gap detection failed: {e}")
            return []
    
    def extract_all(self, text: str) -> LLMExtractionResult:
        """
        Perform comprehensive extraction in a single LLM call.
        
        More efficient than calling individual methods separately.
        """
        prompt = SYNTHESIS_PROMPT.format(text=text)
        
        try:
            response = self.provider.complete(prompt, system=SYSTEM_PROMPT)
            self._total_tokens += response.tokens_used
            self._total_cost += response.cost_usd
            
            # Parse JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            import json
            data = json.loads(content.strip())
            
            # Build result
            result = LLMExtractionResult(
                provider=response.provider,
                model=response.model,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
            )
            
            # Parse entities
            for e in data.get("entities", []):
                result.entities.append(ExtractedEntity(
                    name=e.get("name", ""),
                    entity_type=e.get("type", "OTHER"),
                    aliases=e.get("aliases", []),
                    description=e.get("description"),
                    confidence=e.get("confidence", 0.9),
                ))
            
            # Parse claims
            for c in data.get("claims", []):
                result.claims.append(ExtractedClaim(
                    text=c.get("text", ""),
                    subject=c.get("subject"),
                    predicate=c.get("predicate"),
                    object=c.get("object"),
                    modality=c.get("modality", "assertion"),
                    hedging=c.get("hedging", []),
                    negated=c.get("negated", False),
                    confidence=c.get("confidence", 0.9),
                ))
            
            # Parse procedures
            for p in data.get("procedures", []):
                steps = []
                for s in p.get("steps", []):
                    steps.append(ExtractedStep(
                        index=s.get("index", 0),
                        text=s.get("text", ""),
                        action_verb=s.get("action_verb", ""),
                        optional=s.get("optional", False),
                        prerequisites=s.get("prerequisites", []),
                    ))
                
                result.procedures.append(ExtractedProcedure(
                    title=p.get("title", ""),
                    goal=p.get("goal", ""),
                    prerequisites=p.get("prerequisites", []),
                    steps=steps,
                    warnings=p.get("warnings", []),
                    outcomes=p.get("outcomes", []),
                ))
            
            # Parse gaps
            for g in data.get("gaps", []):
                result.gaps.append(ExtractedGap(
                    gap_type=g.get("type", "unknown"),
                    description=g.get("description", ""),
                    location_hint=g.get("location_hint", ""),
                    severity=g.get("severity", "medium"),
                    resolution_hints=g.get("resolution_hints", []),
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Comprehensive extraction failed: {e}")
            return LLMExtractionResult()
    
    def _update_stats(self, data: dict[str, Any]) -> None:
        """Update token and cost statistics."""
        # Stats are tracked via provider responses
        pass
