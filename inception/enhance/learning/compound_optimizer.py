"""
Compound Optimizer for Inception.

Orchestrates multiple learning strategies and selects the optimal
approach based on task characteristics.

Strategies:
- DAPO: High-variance exploration
- GRPO: Preference ranking with group baselines
- TextGrad: Iterative refinement with LLM feedback
- DSPy: Full pipeline optimization
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Available optimization strategies."""
    DAPO = "dapo"
    GRPO = "grpo"
    TEXTGRAD = "textgrad"
    DSPY = "dspy"
    HYBRID = "hybrid"


@dataclass
class TaskContext:
    """Context for strategy selection."""
    task_type: str = "extraction"  # extraction, refinement, optimization
    needs_exploration: bool = False
    has_preferences: bool = False
    needs_refinement: bool = False
    full_pipeline: bool = False
    has_sources: bool = False
    uncertainty: float = 0.5
    budget_remaining: float = 1.0


@dataclass
class OptimizationResult:
    """Result from compound optimization."""
    strategy_used: OptimizationStrategy
    result: Any
    improvement: float = 0.0
    iterations: int = 1
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CompoundOptimizer:
    """
    Unified optimizer that selects the best strategy per task.
    
    Strategy selection logic:
    - DAPO: When variance is high and exploration needed
    - GRPO: For preference ranking and sparse reward scenarios
    - TextGrad: When iterative LLM-guided refinement is suitable
    - DSPy: For full pipeline optimization with examples
    
    Example:
        compound = CompoundOptimizer()
        result = compound.optimize(
            task="extract_claims",
            inputs={"text": "OAuth 2.0 uses bearer tokens..."},
            context=TaskContext(task_type="extraction"),
        )
    """
    
    def __init__(
        self,
        enable_dapo: bool = True,
        enable_grpo: bool = True,
        enable_textgrad: bool = True,
        enable_dspy: bool = True,
    ):
        """
        Initialize compound optimizer.
        
        Args:
            enable_dapo: Enable DAPO optimizer
            enable_grpo: Enable GRPOv2 optimizer
            enable_textgrad: Enable TextGrad optimizer
            enable_dspy: Enable DSPy integration
        """
        self.enable_dapo = enable_dapo
        self.enable_grpo = enable_grpo
        self.enable_textgrad = enable_textgrad
        self.enable_dspy = enable_dspy
        
        # Lazy-loaded optimizers
        self._dapo = None
        self._grpo = None
        self._textgrad = None
        self._dspy_pipeline = None
        
        # Statistics
        self.strategy_counts: dict[str, int] = {}
        self.strategy_improvements: dict[str, list[float]] = {}
    
    @property
    def dapo(self):
        """Lazy-load DAPO optimizer."""
        if self._dapo is None and self.enable_dapo:
            try:
                from inception.enhance.learning import DAPOOptimizer
                self._dapo = DAPOOptimizer()
            except ImportError:
                logger.warning("DAPO optimizer not available")
        return self._dapo
    
    @property
    def grpo(self):
        """Lazy-load GRPOv2 optimizer."""
        if self._grpo is None and self.enable_grpo:
            try:
                from inception.enhance.learning.grpo_v2 import GRPOv2Optimizer
                self._grpo = GRPOv2Optimizer()
            except ImportError:
                logger.warning("GRPOv2 optimizer not available")
        return self._grpo
    
    @property
    def textgrad(self):
        """Lazy-load TextGrad optimizer."""
        if self._textgrad is None and self.enable_textgrad:
            try:
                from inception.enhance.learning.textgrad_optimizer import TextGradOptimizer
                self._textgrad = TextGradOptimizer()
            except ImportError:
                logger.warning("TextGrad optimizer not available")
        return self._textgrad
    
    @property
    def dspy_pipeline(self):
        """Lazy-load DSPy pipeline."""
        if self._dspy_pipeline is None and self.enable_dspy:
            try:
                from inception.enhance.learning.dspy_integration import InceptionPipeline
                self._dspy_pipeline = InceptionPipeline()
            except ImportError:
                logger.warning("DSPy pipeline not available")
        return self._dspy_pipeline
    
    def select_strategy(self, task: str, context: TaskContext) -> OptimizationStrategy:
        """
        Select optimal strategy based on task and context.
        
        Args:
            task: Task identifier
            context: Task context for selection
        
        Returns:
            Selected optimization strategy
        """
        # High exploration need → DAPO
        if context.needs_exploration and context.uncertainty > 0.7:
            if self.dapo is not None:
                return OptimizationStrategy.DAPO
        
        # Preference ranking → GRPO
        if context.has_preferences or context.has_sources:
            if self.grpo is not None:
                return OptimizationStrategy.GRPO
        
        # Iterative refinement → TextGrad
        if context.needs_refinement:
            if self.textgrad is not None:
                return OptimizationStrategy.TEXTGRAD
        
        # Full pipeline → DSPy
        if context.full_pipeline:
            if self.dspy_pipeline is not None:
                return OptimizationStrategy.DSPY
        
        # Default: GRPO for memory efficiency
        if self.grpo is not None:
            return OptimizationStrategy.GRPO
        
        # Fallback
        return OptimizationStrategy.TEXTGRAD if self.textgrad else OptimizationStrategy.DSPY
    
    def optimize(
        self,
        task: str,
        inputs: dict,
        context: Optional[TaskContext] = None,
        strategy_override: Optional[OptimizationStrategy] = None,
    ) -> OptimizationResult:
        """
        Run optimization with selected strategy.
        
        Args:
            task: Task identifier (e.g., "extract_claims", "refine_entity")
            inputs: Task-specific inputs
            context: Task context for strategy selection
            strategy_override: Force a specific strategy
        
        Returns:
            OptimizationResult with strategy output
        """
        if context is None:
            context = TaskContext()
        
        # Select strategy
        if strategy_override:
            strategy = strategy_override
        else:
            strategy = self.select_strategy(task, context)
        
        logger.info(f"Using {strategy.value} for task: {task}")
        
        # Execute strategy
        try:
            result = self._execute_strategy(strategy, task, inputs, context)
            
            # Track statistics
            self._track_stats(strategy, result.improvement)
            
            return result
        except Exception as e:
            logger.error(f"Strategy {strategy.value} failed: {e}")
            
            # Fallback to next available strategy
            return self._fallback(task, inputs, context, strategy)
    
    def _execute_strategy(
        self,
        strategy: OptimizationStrategy,
        task: str,
        inputs: dict,
        context: TaskContext,
    ) -> OptimizationResult:
        """Execute the selected strategy."""
        
        if strategy == OptimizationStrategy.DAPO:
            return self._run_dapo(inputs)
        
        elif strategy == OptimizationStrategy.GRPO:
            return self._run_grpo(inputs, context)
        
        elif strategy == OptimizationStrategy.TEXTGRAD:
            return self._run_textgrad(inputs)
        
        elif strategy == OptimizationStrategy.DSPY:
            return self._run_dspy(inputs)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _run_dapo(self, inputs: dict) -> OptimizationResult:
        """Run DAPO optimization."""
        if self.dapo is None:
            raise RuntimeError("DAPO not available")
        
        experiences = inputs.get("experiences", [])
        result = self.dapo.update(experiences)
        
        return OptimizationResult(
            strategy_used=OptimizationStrategy.DAPO,
            result=result,
            improvement=result.get("improvement", 0.0) if isinstance(result, dict) else 0.0,
        )
    
    def _run_grpo(self, inputs: dict, context: TaskContext) -> OptimizationResult:
        """Run GRPO optimization."""
        if self.grpo is None:
            raise RuntimeError("GRPO not available")
        
        prompt = inputs.get("prompt", "")
        policy_fn = inputs.get("policy_fn")
        
        if policy_fn is None:
            # Create default policy
            def policy_fn(p):
                return f"Generated response for: {p[:50]}..."
        
        result = self.grpo.step(prompt=prompt, policy_fn=policy_fn)
        
        return OptimizationResult(
            strategy_used=OptimizationStrategy.GRPO,
            result=result,
            improvement=result.mean_reward,
            metadata={"best_response": result.best_response},
        )
    
    def _run_textgrad(self, inputs: dict) -> OptimizationResult:
        """Run TextGrad optimization."""
        if self.textgrad is None:
            raise RuntimeError("TextGrad not available")
        
        claim = inputs.get("claim", inputs.get("text", ""))
        sources = inputs.get("sources", [])
        
        result = self.textgrad.refine_claim(claim=claim, sources=sources)
        
        return OptimizationResult(
            strategy_used=OptimizationStrategy.TEXTGRAD,
            result=result,
            improvement=result.improvement_score,
            iterations=result.iterations,
            metadata={"refined": result.refined},
        )
    
    def _run_dspy(self, inputs: dict) -> OptimizationResult:
        """Run DSPy pipeline optimization."""
        if self.dspy_pipeline is None:
            raise RuntimeError("DSPy not available")
        
        text = inputs.get("text", "")
        result = self.dspy_pipeline.process(text)
        
        return OptimizationResult(
            strategy_used=OptimizationStrategy.DSPY,
            result=result,
            improvement=len(result.get("claims", [])) * 0.1,  # Heuristic
            metadata={"claims": result.get("claims", [])},
        )
    
    def _fallback(
        self,
        task: str,
        inputs: dict,
        context: TaskContext,
        failed_strategy: OptimizationStrategy,
    ) -> OptimizationResult:
        """Fallback to alternative strategy."""
        fallback_order = [
            OptimizationStrategy.GRPO,
            OptimizationStrategy.TEXTGRAD,
            OptimizationStrategy.DSPY,
            OptimizationStrategy.DAPO,
        ]
        
        for strategy in fallback_order:
            if strategy == failed_strategy:
                continue
            
            try:
                return self._execute_strategy(strategy, task, inputs, context)
            except Exception as e:
                logger.warning(f"Fallback {strategy.value} also failed: {e}")
                continue
        
        # All failed
        return OptimizationResult(
            strategy_used=OptimizationStrategy.GRPO,
            result=None,
            improvement=0.0,
            metadata={"error": "All strategies failed"},
        )
    
    def _track_stats(self, strategy: OptimizationStrategy, improvement: float):
        """Track strategy usage and performance."""
        strategy_name = strategy.value
        
        self.strategy_counts[strategy_name] = (
            self.strategy_counts.get(strategy_name, 0) + 1
        )
        
        if strategy_name not in self.strategy_improvements:
            self.strategy_improvements[strategy_name] = []
        self.strategy_improvements[strategy_name].append(improvement)
    
    def get_stats(self) -> dict:
        """Get optimizer statistics."""
        avg_improvements = {}
        for strategy, improvements in self.strategy_improvements.items():
            if improvements:
                avg_improvements[strategy] = sum(improvements) / len(improvements)
        
        return {
            "strategy_counts": self.strategy_counts,
            "avg_improvements": avg_improvements,
            "total_optimizations": sum(self.strategy_counts.values()),
        }
    
    def recommend_strategy(self, task: str, context: TaskContext) -> dict:
        """
        Recommend a strategy with reasoning.
        
        Args:
            task: Task identifier
            context: Task context
        
        Returns:
            Dict with recommended strategy and reasoning
        """
        strategy = self.select_strategy(task, context)
        
        reasoning = []
        if context.needs_exploration:
            reasoning.append("High uncertainty requires exploration (DAPO preferred)")
        if context.has_preferences:
            reasoning.append("Preference data available (GRPO preferred)")
        if context.needs_refinement:
            reasoning.append("Iterative refinement needed (TextGrad preferred)")
        if context.full_pipeline:
            reasoning.append("Full pipeline optimization (DSPy preferred)")
        
        # Add historical performance
        if strategy.value in self.strategy_improvements:
            avg = sum(self.strategy_improvements[strategy.value]) / len(self.strategy_improvements[strategy.value])
            reasoning.append(f"Historical avg improvement: {avg:.3f}")
        
        return {
            "recommended": strategy.value,
            "reasoning": reasoning,
            "alternatives": [s.value for s in OptimizationStrategy if s != strategy],
        }
