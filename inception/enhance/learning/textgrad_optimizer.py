"""
TextGrad Optimizer for Inception.

Implements differentiable text optimization using "textual gradients"
for iterative self-improvement of extracted knowledge.

References:
- https://textgrad.com/
- TextGrad: Automatic Differentiation via Text (2024)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Lazy import TextGrad
_textgrad = None


def _get_textgrad():
    """Lazy-load TextGrad module."""
    global _textgrad
    if _textgrad is None:
        try:
            import textgrad as tg
            _textgrad = tg
        except ImportError:
            raise ImportError(
                "TextGrad is required for this feature. "
                "Install with: pip install textgrad"
            )
    return _textgrad


@dataclass
class RefinementResult:
    """Result of a text refinement operation."""
    original: str
    refined: str
    iterations: int = 1
    feedback: list[str] = field(default_factory=list)
    improvement_score: float = 0.0


@dataclass
class OptimizationResult:
    """Result of prompt optimization."""
    original_prompt: str
    optimized_prompt: str
    iterations: int
    final_loss: float


class TextGradOptimizer:
    """
    Differentiable text optimization using textual gradients.
    
    Uses LLMs to provide natural language "gradients" that guide
    the iterative refinement of text (claims, prompts, etc.).
    
    Example:
        optimizer = TextGradOptimizer()
        result = optimizer.refine_claim(
            claim="OAuth uses tokens",
            sources=["RFC 6749: OAuth 2.0 uses bearer tokens..."],
        )
        # result.refined = "OAuth 2.0 uses bearer tokens for authorization"
    """
    
    def __init__(
        self,
        model: str = "gpt-4o",
        max_iterations: int = 3,
        convergence_threshold: float = 0.05,
    ):
        """
        Initialize TextGrad optimizer.
        
        Args:
            model: LLM model for gradient computation
            max_iterations: Maximum refinement iterations
            convergence_threshold: Stop if improvement < threshold
        """
        self.model = model
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self._engine = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazily initialize TextGrad engine."""
        if self._initialized:
            return
        
        try:
            tg = _get_textgrad()
            self._engine = tg.get_engine(self.model)
            tg.set_backward_engine(self._engine)
            self._initialized = True
            logger.info(f"TextGrad initialized with {self.model}")
        except Exception as e:
            logger.warning(f"TextGrad initialization failed: {e}")
            self._initialized = False
    
    def refine_claim(
        self,
        claim: str,
        sources: list[str] | None = None,
        criteria: str | None = None,
    ) -> RefinementResult:
        """
        Refine a claim using textual backpropagation.
        
        Args:
            claim: Original claim text
            sources: Source texts for verification
            criteria: Custom evaluation criteria
        
        Returns:
            RefinementResult with refined claim
        """
        self._ensure_initialized()
        
        if not self._initialized:
            # Fallback: return original if TextGrad unavailable
            return RefinementResult(
                original=claim,
                refined=claim,
                iterations=0,
            )
        
        tg = _get_textgrad()
        
        # Define the claim as a differentiable variable
        claim_var = tg.Variable(
            claim,
            role_description="factual claim extracted from a knowledge source",
            requires_grad=True,
        )
        
        # Build evaluation criteria
        if criteria is None:
            criteria = self._build_claim_criteria(sources)
        
        # Define loss function
        loss_fn = tg.TextLoss(criteria)
        
        # Optimization loop
        optimizer = tg.TGD(parameters=[claim_var])
        feedback_history = []
        best_claim = claim
        best_score = 0.0
        
        for i in range(self.max_iterations):
            try:
                # Forward pass: compute loss
                loss = loss_fn(claim_var)
                
                # Backward pass: compute textual gradients
                loss.backward()
                
                # Capture feedback
                if hasattr(claim_var, 'gradients') and claim_var.gradients:
                    feedback = str(claim_var.gradients[-1])
                    feedback_history.append(feedback)
                
                # Optimizer step: apply gradients
                optimizer.step()
                
                # Check convergence
                current_score = self._score_claim(claim_var.value, sources)
                if current_score > best_score:
                    best_score = current_score
                    best_claim = claim_var.value
                
                if i > 0 and abs(current_score - best_score) < self.convergence_threshold:
                    logger.info(f"Converged after {i+1} iterations")
                    break
                    
            except Exception as e:
                logger.warning(f"TextGrad iteration {i} failed: {e}")
                break
        
        return RefinementResult(
            original=claim,
            refined=best_claim,
            iterations=len(feedback_history),
            feedback=feedback_history,
            improvement_score=best_score,
        )
    
    def _build_claim_criteria(self, sources: list[str] | None) -> str:
        """Build evaluation criteria for claim refinement."""
        base = (
            "Evaluate if this claim is:\n"
            "1. Accurate: Does it match factual information?\n"
            "2. Complete: Does it include all relevant details?\n"
            "3. Precise: Is the language specific and unambiguous?\n"
            "4. Well-sourced: Can it be traced to reliable sources?\n\n"
            "Provide specific criticism if the claim can be improved. "
            "Suggest exact wording changes."
        )
        
        if sources:
            source_text = "\n".join(f"- {s[:200]}..." for s in sources[:3])
            base += f"\n\nReference sources:\n{source_text}"
        
        return base
    
    def _score_claim(self, claim: str, sources: list[str] | None) -> float:
        """Score a claim based on source alignment."""
        if not sources:
            return 0.5
        
        # Simple word overlap scoring
        claim_words = set(claim.lower().split())
        source_words = set()
        for s in sources:
            source_words.update(s.lower().split())
        
        if not source_words:
            return 0.5
        
        overlap = len(claim_words & source_words)
        return min(1.0, overlap / len(claim_words))
    
    def optimize_prompt(
        self,
        prompt: str,
        examples: list[dict],
        loss_fn: Callable[[str, dict], float] | None = None,
    ) -> OptimizationResult:
        """
        Optimize a prompt using TextGrad.
        
        Args:
            prompt: Original prompt template
            examples: List of {input, expected_output} examples
            loss_fn: Custom loss function
        
        Returns:
            OptimizationResult with optimized prompt
        """
        self._ensure_initialized()
        
        if not self._initialized:
            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=prompt,
                iterations=0,
                final_loss=0.0,
            )
        
        tg = _get_textgrad()
        
        # Define prompt as differentiable variable
        prompt_var = tg.Variable(
            prompt,
            role_description="instruction prompt for an LLM extraction task",
            requires_grad=True,
        )
        
        optimizer = tg.TGD(parameters=[prompt_var])
        
        total_loss = 0.0
        for i in range(self.max_iterations):
            iteration_loss = 0.0
            
            for example in examples[:5]:  # Limit examples per iteration
                try:
                    # Generate output with current prompt
                    full_prompt = prompt_var.value + "\n\n" + example["input"]
                    output = self._engine.generate(full_prompt)
                    
                    # Compute loss
                    if loss_fn:
                        loss_val = loss_fn(output, example)
                    else:
                        loss_val = self._default_loss(output, example)
                    
                    iteration_loss += loss_val
                except Exception as e:
                    logger.warning(f"Prompt optimization example failed: {e}")
            
            # Backward and step
            try:
                loss = tg.TextLoss(
                    f"Improve this prompt to get better results. "
                    f"Current average loss: {iteration_loss / max(1, len(examples)):.2f}"
                )
                loss_result = loss(prompt_var)
                loss_result.backward()
                optimizer.step()
            except Exception as e:
                logger.warning(f"Prompt optimization step failed: {e}")
                break
            
            total_loss = iteration_loss / max(1, len(examples))
        
        return OptimizationResult(
            original_prompt=prompt,
            optimized_prompt=prompt_var.value,
            iterations=self.max_iterations,
            final_loss=total_loss,
        )
    
    def _default_loss(self, output: str, example: dict) -> float:
        """Default loss: word overlap with expected output."""
        expected = example.get("expected_output", "")
        if not expected:
            return 0.5
        
        output_words = set(output.lower().split())
        expected_words = set(expected.lower().split())
        
        if not expected_words:
            return 0.5
        
        overlap = len(output_words & expected_words)
        return 1.0 - (overlap / len(expected_words))
    
    def refine_entity_description(
        self,
        entity: str,
        description: str,
        context: str = "",
    ) -> RefinementResult:
        """
        Refine an entity description for accuracy and completeness.
        
        Args:
            entity: Entity name
            description: Current description
            context: Surrounding context
        
        Returns:
            RefinementResult with refined description
        """
        criteria = (
            f"Evaluate this description of '{entity}':\n\n"
            f"Description: {description}\n\n"
            f"Context: {context}\n\n"
            "Is it accurate, complete, and properly scoped? "
            "Suggest improvements if needed."
        )
        
        return self.refine_claim(description, criteria=criteria)
