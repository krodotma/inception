"""
Learning Metrics for Inception.

Unified metrics for evaluating learning engine performance across
all optimization strategies (DAPO, GRPO, TextGrad, DSPy).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ClaimMetrics:
    """Metrics for claim extraction evaluation."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)


@dataclass
class EntityMetrics:
    """Metrics for entity extraction and linking."""
    correct_extractions: int = 0
    total_extractions: int = 0
    correct_links: int = 0
    total_links: int = 0
    
    @property
    def extraction_accuracy(self) -> float:
        if self.total_extractions == 0:
            return 0.0
        return self.correct_extractions / self.total_extractions
    
    @property
    def linking_accuracy(self) -> float:
        if self.total_links == 0:
            return 0.0
        return self.correct_links / self.total_links


@dataclass
class LearningMetrics:
    """
    Comprehensive metrics container for learning engine.
    
    Tracks performance across all optimization strategies and
    extraction tasks.
    """
    
    # Task-specific metrics
    claim_metrics: ClaimMetrics = field(default_factory=ClaimMetrics)
    entity_metrics: EntityMetrics = field(default_factory=EntityMetrics)
    
    # Strategy performance
    strategy_rewards: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    strategy_iterations: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Overall tracking
    total_optimizations: int = 0
    successful_optimizations: int = 0
    total_improvement: float = 0.0
    
    def record_claim_evaluation(
        self,
        predicted: list[dict],
        ground_truth: list[dict],
        match_threshold: float = 0.7,
    ):
        """
        Record claim extraction evaluation.
        
        Args:
            predicted: Predicted claims
            ground_truth: Ground truth claims
            match_threshold: Threshold for claim matching
        """
        matched_truth = set()
        
        for pred in predicted:
            matched = False
            for i, truth in enumerate(ground_truth):
                if i in matched_truth:
                    continue
                if self._claims_match(pred, truth, match_threshold):
                    matched = True
                    matched_truth.add(i)
                    break
            
            if matched:
                self.claim_metrics.true_positives += 1
            else:
                self.claim_metrics.false_positives += 1
        
        # Unmatched ground truth = false negatives
        self.claim_metrics.false_negatives += len(ground_truth) - len(matched_truth)
    
    def _claims_match(self, pred: dict, truth: dict, threshold: float) -> bool:
        """Check if two claims match."""
        # Compare subject, predicate, object
        for key in ["subject", "predicate", "object"]:
            pred_val = (pred.get(key) or "").lower()
            truth_val = (truth.get(key) or "").lower()
            
            if not pred_val or not truth_val:
                continue
            
            # Simple word overlap
            pred_words = set(pred_val.split())
            truth_words = set(truth_val.split())
            
            if not truth_words:
                continue
            
            overlap = len(pred_words & truth_words) / len(truth_words)
            if overlap < threshold:
                return False
        
        return True
    
    def record_entity_evaluation(
        self,
        predicted: list[dict],
        ground_truth: list[dict],
    ):
        """
        Record entity extraction evaluation.
        
        Args:
            predicted: Predicted entities
            ground_truth: Ground truth entities
        """
        self.entity_metrics.total_extractions += len(predicted)
        
        for pred in predicted:
            pred_text = (pred.get("text") or "").lower()
            
            for truth in ground_truth:
                truth_text = (truth.get("text") or "").lower()
                
                if pred_text == truth_text:
                    self.entity_metrics.correct_extractions += 1
                    
                    # Check linking
                    if pred.get("wikidata_id"):
                        self.entity_metrics.total_links += 1
                        if pred.get("wikidata_id") == truth.get("wikidata_id"):
                            self.entity_metrics.correct_links += 1
                    break
    
    def record_strategy_result(
        self,
        strategy: str,
        reward: float,
        success: bool = True,
    ):
        """
        Record optimization strategy result.
        
        Args:
            strategy: Strategy name
            reward: Reward/improvement achieved
            success: Whether optimization succeeded
        """
        self.strategy_rewards[strategy].append(reward)
        self.strategy_iterations[strategy] += 1
        self.total_optimizations += 1
        
        if success:
            self.successful_optimizations += 1
        
        self.total_improvement += reward
    
    def get_summary(self) -> dict:
        """Get comprehensive metrics summary."""
        strategy_avg_rewards = {}
        for strategy, rewards in self.strategy_rewards.items():
            if rewards:
                strategy_avg_rewards[strategy] = sum(rewards) / len(rewards)
        
        return {
            "claims": {
                "precision": self.claim_metrics.precision,
                "recall": self.claim_metrics.recall,
                "f1": self.claim_metrics.f1,
                "true_positives": self.claim_metrics.true_positives,
                "false_positives": self.claim_metrics.false_positives,
                "false_negatives": self.claim_metrics.false_negatives,
            },
            "entities": {
                "extraction_accuracy": self.entity_metrics.extraction_accuracy,
                "linking_accuracy": self.entity_metrics.linking_accuracy,
                "total_extractions": self.entity_metrics.total_extractions,
                "total_links": self.entity_metrics.total_links,
            },
            "strategies": {
                "avg_rewards": strategy_avg_rewards,
                "iterations": dict(self.strategy_iterations),
            },
            "overall": {
                "total_optimizations": self.total_optimizations,
                "success_rate": (
                    self.successful_optimizations / max(1, self.total_optimizations)
                ),
                "total_improvement": self.total_improvement,
                "avg_improvement": (
                    self.total_improvement / max(1, self.total_optimizations)
                ),
            },
        }
    
    def reset(self):
        """Reset all metrics."""
        self.claim_metrics = ClaimMetrics()
        self.entity_metrics = EntityMetrics()
        self.strategy_rewards = defaultdict(list)
        self.strategy_iterations = defaultdict(int)
        self.total_optimizations = 0
        self.successful_optimizations = 0
        self.total_improvement = 0.0


def compute_claim_f1(predicted: list[dict], ground_truth: list[dict]) -> float:
    """
    Compute F1 score for claim extraction.
    
    Args:
        predicted: Predicted claims
        ground_truth: Ground truth claims
    
    Returns:
        F1 score (0-1)
    """
    metrics = LearningMetrics()
    metrics.record_claim_evaluation(predicted, ground_truth)
    return metrics.claim_metrics.f1


def compute_entity_accuracy(predicted: list[dict], ground_truth: list[dict]) -> float:
    """
    Compute accuracy for entity extraction.
    
    Args:
        predicted: Predicted entities
        ground_truth: Ground truth entities
    
    Returns:
        Accuracy (0-1)
    """
    metrics = LearningMetrics()
    metrics.record_entity_evaluation(predicted, ground_truth)
    return metrics.entity_metrics.extraction_accuracy


def compute_linking_accuracy(predicted: list[dict], ground_truth: list[dict]) -> float:
    """
    Compute accuracy for entity linking.
    
    Args:
        predicted: Predicted entities with wikidata_id
        ground_truth: Ground truth entities with wikidata_id
    
    Returns:
        Linking accuracy (0-1)
    """
    metrics = LearningMetrics()
    metrics.record_entity_evaluation(predicted, ground_truth)
    return metrics.entity_metrics.linking_accuracy
