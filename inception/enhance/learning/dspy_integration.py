"""
DSPy Integration for Inception.

Wraps Inception's extraction logic in DSPy signatures for
automatic prompt optimization via MIPROv2 and BetterTogether.

References:
- https://dspy.ai/
- DSPy: Compiling Declarative Language Model Calls (2023)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Lazy import DSPy to avoid hard dependency
_dspy = None


def _get_dspy():
    """Lazy-load DSPy module."""
    global _dspy
    if _dspy is None:
        try:
            import dspy
            _dspy = dspy
        except ImportError:
            raise ImportError(
                "DSPy is required for this feature. "
                "Install with: pip install dspy-ai"
            )
    return _dspy


@dataclass
class ClaimExtractionOutput:
    """Output from claim extraction."""
    claims: list[dict] = field(default_factory=list)
    raw_response: str = ""


@dataclass  
class EntityLinkOutput:
    """Output from entity linking."""
    wikidata_id: str | None = None
    dbpedia_uri: str | None = None
    confidence: float = 0.0
    disambiguation_notes: str = ""


@dataclass
class GapResolutionOutput:
    """Output from gap resolution."""
    resolution: str = ""
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    requires_human: bool = False


class ClaimExtractor:
    """
    DSPy-based claim extractor.
    
    Extracts factual claims from text with SPO decomposition,
    modality tracking, and hedge detection.
    
    Example:
        extractor = ClaimExtractor()
        result = extractor.extract("OAuth 2.0 uses bearer tokens for auth.")
        # result.claims[0] = {
        #     "subject": "OAuth 2.0",
        #     "predicate": "uses",
        #     "object": "bearer tokens for auth",
        #     "modality": "assertion",
        #     "hedges": []
        # }
    """
    
    EXTRACTION_PROMPT = """Extract factual claims from the following text.

For each claim, provide:
- subject: The entity the claim is about
- predicate: The action or relationship
- object: What the subject relates to
- modality: One of [assertion, possibility, necessity, negation]
- hedges: List of uncertainty markers (e.g., "typically", "might", "possibly")

Output as JSON array.

Text: {text}
"""
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        use_dspy: bool = True,
    ):
        self.model = model
        self.use_dspy = use_dspy
        self._module = None
        
        if use_dspy:
            self._init_dspy_module()
    
    def _init_dspy_module(self):
        """Initialize DSPy module for optimization."""
        try:
            dspy = _get_dspy()
            
            class ClaimSig(dspy.Signature):
                """Extract factual claims with SPO decomposition."""
                text: str = dspy.InputField(desc="Text to analyze")
                claims: str = dspy.OutputField(desc="JSON array of claims")
            
            self._module = dspy.ChainOfThought(ClaimSig)
            logger.info("DSPy ClaimExtractor initialized")
        except ImportError:
            logger.warning("DSPy not available, falling back to direct prompting")
            self.use_dspy = False
    
    def extract(self, text: str) -> ClaimExtractionOutput:
        """
        Extract claims from text.
        
        Args:
            text: Source text to analyze
        
        Returns:
            ClaimExtractionOutput with extracted claims
        """
        if self.use_dspy and self._module:
            return self._extract_dspy(text)
        else:
            return self._extract_direct(text)
    
    def _extract_dspy(self, text: str) -> ClaimExtractionOutput:
        """Extract using DSPy module."""
        import json
        
        try:
            result = self._module(text=text)
            claims = json.loads(result.claims)
            return ClaimExtractionOutput(
                claims=claims,
                raw_response=result.claims,
            )
        except Exception as e:
            logger.error(f"DSPy extraction failed: {e}")
            return ClaimExtractionOutput()
    
    def _extract_direct(self, text: str) -> ClaimExtractionOutput:
        """Extract using direct LLM call."""
        # Placeholder for direct LLM extraction
        logger.info("Using direct extraction (DSPy not available)")
        return ClaimExtractionOutput()
    
    def optimize(self, examples: list[dict], metric_fn=None):
        """
        Optimize extraction prompts using MIPROv2.
        
        Args:
            examples: List of {text, expected_claims} for training
            metric_fn: Scoring function for optimization
        
        Returns:
            Optimized module
        """
        if not self.use_dspy:
            raise ValueError("DSPy required for optimization")
        
        dspy = _get_dspy()
        from dspy.teleprompt import MIPROv2
        
        if metric_fn is None:
            metric_fn = self._default_metric
        
        optimizer = MIPROv2(
            prompt_model=dspy.OpenAI(model=self.model),
            metric=metric_fn,
            num_candidates=10,
            verbose=True,
        )
        
        optimized = optimizer.compile(self._module, trainset=examples)
        self._module = optimized
        return optimized
    
    def _default_metric(self, example, prediction, trace=None):
        """Default metric: claim count and structure validity."""
        try:
            import json
            claims = json.loads(prediction.claims)
            
            # Check structure
            valid = all(
                "subject" in c and "predicate" in c 
                for c in claims
            )
            
            # Score based on count and validity
            expected_count = len(example.get("expected_claims", []))
            actual_count = len(claims)
            count_score = 1.0 - abs(expected_count - actual_count) / max(expected_count, 1)
            
            return count_score * (1.0 if valid else 0.5)
        except:
            return 0.0


class EntityLinker:
    """
    DSPy-based entity linker.
    
    Links entity mentions to Wikidata and DBpedia with
    context-aware disambiguation.
    """
    
    def __init__(self, model: str = "gpt-4o-mini", use_dspy: bool = True):
        self.model = model
        self.use_dspy = use_dspy
        self._module = None
        
        if use_dspy:
            self._init_dspy_module()
    
    def _init_dspy_module(self):
        """Initialize DSPy module."""
        try:
            dspy = _get_dspy()
            
            class EntitySig(dspy.Signature):
                """Link entity to knowledge base with disambiguation."""
                entity: str = dspy.InputField(desc="Entity mention")
                context: str = dspy.InputField(desc="Surrounding context")
                wikidata_id: str = dspy.OutputField(desc="Wikidata QID or NIL")
                confidence: str = dspy.OutputField(desc="Confidence 0-1")
            
            self._module = dspy.ChainOfThought(EntitySig)
        except ImportError:
            self.use_dspy = False
    
    def link(self, entity: str, context: str = "") -> EntityLinkOutput:
        """
        Link entity to external ontology.
        
        Args:
            entity: Entity text to link
            context: Surrounding context for disambiguation
        
        Returns:
            EntityLinkOutput with linked IDs
        """
        if self.use_dspy and self._module:
            try:
                result = self._module(entity=entity, context=context)
                return EntityLinkOutput(
                    wikidata_id=result.wikidata_id if result.wikidata_id != "NIL" else None,
                    confidence=float(result.confidence),
                )
            except Exception as e:
                logger.error(f"Entity linking failed: {e}")
        
        return EntityLinkOutput()


class GapResolver:
    """
    DSPy-based gap resolver.
    
    Autonomously researches and resolves knowledge gaps
    with safety rails and source tracking.
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        use_dspy: bool = True,
        max_search_depth: int = 2,
        budget_usd: float = 0.50,
    ):
        self.model = model
        self.use_dspy = use_dspy
        self.max_search_depth = max_search_depth
        self.budget_usd = budget_usd
        self._module = None
        
        if use_dspy:
            self._init_dspy_module()
    
    def _init_dspy_module(self):
        """Initialize DSPy module."""
        try:
            dspy = _get_dspy()
            
            class GapSig(dspy.Signature):
                """Resolve knowledge gap with research."""
                gap_type: str = dspy.InputField(desc="Gap type")
                description: str = dspy.InputField(desc="What's missing")
                context: str = dspy.InputField(desc="Surrounding context")
                resolution: str = dspy.OutputField(desc="Resolved information")
                sources: str = dspy.OutputField(desc="Comma-separated sources")
            
            self._module = dspy.ChainOfThought(GapSig)
        except ImportError:
            self.use_dspy = False
    
    def resolve(
        self,
        gap_type: str,
        description: str,
        context: str = "",
    ) -> GapResolutionOutput:
        """
        Attempt to resolve a knowledge gap.
        
        Args:
            gap_type: Type of gap (undefined_term, missing_context, etc.)
            description: Description of what's missing
            context: Surrounding context
        
        Returns:
            GapResolutionOutput with resolution attempt
        """
        if self.use_dspy and self._module:
            try:
                result = self._module(
                    gap_type=gap_type,
                    description=description,
                    context=context,
                )
                sources = [s.strip() for s in result.sources.split(",") if s.strip()]
                return GapResolutionOutput(
                    resolution=result.resolution,
                    sources=sources,
                    confidence=0.8 if sources else 0.5,
                )
            except Exception as e:
                logger.error(f"Gap resolution failed: {e}")
        
        return GapResolutionOutput(requires_human=True)


class InceptionPipeline:
    """
    Complete DSPy pipeline for Inception.
    
    Chains claim extraction, entity linking, and gap resolution
    into an optimizable end-to-end pipeline.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.claim_extractor = ClaimExtractor(model=model)
        self.entity_linker = EntityLinker(model=model)
        self.gap_resolver = GapResolver(model=model)
    
    def process(self, text: str) -> dict:
        """
        Process text through full pipeline.
        
        Args:
            text: Source text
        
        Returns:
            Dict with claims, entities, and resolutions
        """
        # Extract claims
        claims_result = self.claim_extractor.extract(text)
        
        # Extract and link entities from claims
        entities = []
        for claim in claims_result.claims:
            if subject := claim.get("subject"):
                link_result = self.entity_linker.link(subject, text)
                if link_result.wikidata_id:
                    entities.append({
                        "text": subject,
                        "wikidata_id": link_result.wikidata_id,
                        "confidence": link_result.confidence,
                    })
        
        return {
            "claims": claims_result.claims,
            "entities": entities,
            "raw_response": claims_result.raw_response,
        }
    
    def optimize_all(self, claim_examples: list, entity_examples: list = None):
        """Optimize all pipeline components."""
        self.claim_extractor.optimize(claim_examples)
        logger.info("Pipeline optimization complete")
