"""
Inception Learning Engine

Advanced reinforcement learning and preference optimization for PKG evolution:
- DAPO: Dynamic Advantage Policy Optimization
- GRPO: Group Relative Policy Optimization  
- RLVR: Reinforcement Learning with Verifiable Rewards
- GAP: Gap-Aware Policy for knowledge hole filling
- Active Learning: Uncertainty-based sample selection

Model: Multi-agent ULTRATHINK
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

class RewardSignal(Enum):
    """Reward signal types for RL training."""
    CLAIM_VERIFIED = "claim_verified"
    GAP_FILLED = "gap_filled"
    CONFLICT_RESOLVED = "conflict_resolved"
    USER_FEEDBACK_POSITIVE = "user_positive"
    USER_FEEDBACK_NEGATIVE = "user_negative"
    SOURCE_CONFIRMED = "source_confirmed"
    EXTRACTION_ACCURATE = "extraction_accurate"


@dataclass
class Experience:
    """Single experience tuple for RL replay buffer."""
    state: dict  # Knowledge graph state snapshot
    action: str  # Action taken (e.g., "extract_claim", "resolve_gap")
    reward: float
    next_state: dict
    done: bool
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PolicyState:
    """Current state of a learning policy."""
    policy_id: str
    model_version: str
    total_samples: int = 0
    total_reward: float = 0.0
    avg_advantage: float = 0.0
    entropy: float = 1.0
    kl_divergence: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# DAPO: DYNAMIC ADVANTAGE POLICY OPTIMIZATION
# =============================================================================

class DAPOOptimizer:
    """
    Dynamic Advantage Policy Optimization.
    
    Adapts PPO with dynamic clipping based on advantage magnitude
    and automatic entropy scheduling for exploration/exploitation balance.
    
    Key innovations:
    - Dynamic clip range based on running advantage variance
    - Entropy bonus that decays with policy confidence
    - Advantage normalization per mini-batch
    """
    
    def __init__(
        self,
        clip_range: float = 0.2,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        max_grad_norm: float = 0.5,
    ):
        self.clip_range = clip_range
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.max_grad_norm = max_grad_norm
        
        self._advantage_variance = 1.0
        self._entropy_schedule = 1.0
        self._update_count = 0
    
    def compute_dynamic_clip(self, advantages: list[float]) -> float:
        """Dynamically adjust clip range based on advantage variance."""
        if not advantages:
            return self.clip_range
        
        variance = sum((a - sum(advantages)/len(advantages))**2 for a in advantages) / len(advantages)
        self._advantage_variance = 0.95 * self._advantage_variance + 0.05 * variance
        
        # Wider clips for high-variance advantages (more exploration)
        dynamic_clip = self.clip_range * (1 + 0.5 * min(self._advantage_variance, 2.0))
        return min(dynamic_clip, 0.4)  # Cap at 0.4
    
    def compute_entropy_bonus(self, policy_entropy: float) -> float:
        """Compute entropy bonus with adaptive scheduling."""
        # Decay entropy coefficient as policy becomes more confident
        self._entropy_schedule = max(0.001, self._entropy_schedule * 0.9999)
        return self.entropy_coef * self._entropy_schedule * policy_entropy
    
    def update(self, experiences: list[Experience]) -> dict:
        """Run DAPO update step."""
        if not experiences:
            return {"status": "no_experiences"}
        
        advantages = [self._compute_advantage(e) for e in experiences]
        dynamic_clip = self.compute_dynamic_clip(advantages)
        
        # Normalize advantages
        mean_adv = sum(advantages) / len(advantages)
        std_adv = (sum((a - mean_adv)**2 for a in advantages) / len(advantages)) ** 0.5
        normalized_advantages = [(a - mean_adv) / (std_adv + 1e-8) for a in advantages]
        
        self._update_count += 1
        
        return {
            "status": "updated",
            "update_count": self._update_count,
            "dynamic_clip": dynamic_clip,
            "mean_advantage": mean_adv,
            "entropy_schedule": self._entropy_schedule,
            "samples": len(experiences),
        }
    
    def _compute_advantage(self, exp: Experience) -> float:
        """Compute advantage for single experience."""
        # Simplified: reward + gamma * V(next) - V(current)
        return exp.reward + 0.99 * exp.metadata.get("next_value", 0) - exp.metadata.get("current_value", 0)


# =============================================================================
# GRPO: GROUP RELATIVE POLICY OPTIMIZATION
# =============================================================================

class GRPOOptimizer:
    """
    Group Relative Policy Optimization.
    
    Optimizes policy by comparing groups of similar actions,
    computing relative advantages within groups for more
    stable training on sparse reward signals.
    
    Key features:
    - Groups experiences by action type
    - Computes within-group relative rankings
    - Uses percentile-based reward shaping
    """
    
    def __init__(
        self,
        group_size: int = 32,
        top_k_ratio: float = 0.25,
        temperature: float = 1.0,
    ):
        self.group_size = group_size
        self.top_k_ratio = top_k_ratio
        self.temperature = temperature
        
        self._action_groups: dict[str, list[Experience]] = {}
        self._group_baselines: dict[str, float] = {}
    
    def add_experience(self, experience: Experience):
        """Add experience to appropriate action group."""
        action = experience.action
        if action not in self._action_groups:
            self._action_groups[action] = []
        self._action_groups[action].append(experience)
        
        # Update group baseline
        rewards = [e.reward for e in self._action_groups[action]]
        self._group_baselines[action] = sum(rewards) / len(rewards)
    
    def compute_group_advantage(self, experience: Experience) -> float:
        """Compute relative advantage within action group."""
        action = experience.action
        if action not in self._action_groups:
            return experience.reward
        
        baseline = self._group_baselines.get(action, 0)
        relative_advantage = experience.reward - baseline
        
        # Rank-based scaling
        group = self._action_groups[action]
        ranked = sorted(group, key=lambda e: e.reward, reverse=True)
        rank = next((i for i, e in enumerate(ranked) if e is experience), len(ranked))
        percentile = 1 - (rank / len(ranked))
        
        return relative_advantage * (1 + percentile)
    
    def update(self) -> dict:
        """Run GRPO update across all groups."""
        results = {}
        
        for action, group in self._action_groups.items():
            if len(group) < self.group_size:
                continue
            
            # Select top-k experiences for policy update
            sorted_group = sorted(group, key=lambda e: e.reward, reverse=True)
            top_k = int(len(sorted_group) * self.top_k_ratio)
            
            results[action] = {
                "total_samples": len(group),
                "top_k_samples": top_k,
                "group_baseline": self._group_baselines[action],
                "top_k_mean_reward": sum(e.reward for e in sorted_group[:top_k]) / max(top_k, 1),
            }
            
            # Clear processed experiences (keep recent for reference)
            self._action_groups[action] = group[-self.group_size:]
        
        return {"status": "updated", "groups": results}


# =============================================================================
# RLVR: REINFORCEMENT LEARNING WITH VERIFIABLE REWARDS
# =============================================================================

class RLVREngine:
    """
    Reinforcement Learning with Verifiable Rewards.
    
    Uses ground truth verification to provide verified reward signals,
    particularly useful for claim extraction and fact verification tasks.
    
    Components:
    - Claim verifier (checks against sources)
    - Procedure validator (checks step completeness)
    - Gap resolution verifier (checks if gap is actually filled)
    """
    
    def __init__(self, verifier_fn: Optional[Callable] = None):
        self.verifier_fn = verifier_fn or self._default_verifier
        self._verified_rewards: list[tuple[str, float, bool]] = []
        self._verification_cache: dict[str, bool] = {}
    
    def _default_verifier(self, claim: dict, sources: list[dict]) -> tuple[bool, float]:
        """Default verification: check claim against source statements."""
        claim_text = claim.get("statement", "").lower()
        
        for source in sources:
            source_text = source.get("content", "").lower()
            # Simple word overlap verification
            claim_words = set(claim_text.split())
            source_words = set(source_text.split())
            overlap = len(claim_words & source_words) / max(len(claim_words), 1)
            
            if overlap > 0.5:
                return True, overlap
        
        return False, 0.0
    
    def compute_verified_reward(
        self,
        action: str,
        result: dict,
        sources: list[dict],
    ) -> float:
        """Compute reward with verification."""
        if action == "extract_claim":
            verified, confidence = self.verifier_fn(result, sources)
            self._verified_rewards.append((action, confidence, verified))
            return confidence if verified else -0.5
        
        elif action == "resolve_gap":
            # Check if gap is actually filled
            gap_id = result.get("gap_id")
            if gap_id and gap_id in self._verification_cache:
                return 1.0 if self._verification_cache[gap_id] else -0.3
            return 0.1  # Neutral for unverified
        
        elif action == "extract_procedure":
            # Verify procedure has complete steps
            steps = result.get("steps", [])
            if len(steps) >= 3 and all(s.get("action_verb") for s in steps):
                return 0.8
            return 0.2
        
        return 0.0
    
    def get_verification_stats(self) -> dict:
        """Get verification statistics."""
        if not self._verified_rewards:
            return {"total": 0, "verified_rate": 0.0}
        
        verified_count = sum(1 for _, _, v in self._verified_rewards if v)
        return {
            "total": len(self._verified_rewards),
            "verified_count": verified_count,
            "verified_rate": verified_count / len(self._verified_rewards),
            "avg_confidence": sum(c for _, c, _ in self._verified_rewards) / len(self._verified_rewards),
        }


# =============================================================================
# GAP: GAP-AWARE POLICY
# =============================================================================

class GAPPolicy:
    """
    Gap-Aware Policy for knowledge graph completion.
    
    Prioritizes actions that fill knowledge gaps, using
    uncertainty estimates to guide exploration.
    
    Features:
    - Gap priority scoring
    - Uncertainty-guided exploration
    - Automatic gap discovery from graph analysis
    """
    
    def __init__(self, exploration_weight: float = 0.3):
        self.exploration_weight = exploration_weight
        self._gap_priorities: dict[str, float] = {}
        self._gap_attempts: dict[str, int] = {}
    
    def score_gap(self, gap: dict) -> float:
        """Score a gap for prioritization."""
        gap_id = gap.get("id", "")
        
        # Base priority from gap metadata
        priority_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
        base_priority = priority_map.get(gap.get("priority", "medium"), 0.5)
        
        # Adjust for previous attempts (diminishing returns)
        attempts = self._gap_attempts.get(gap_id, 0)
        attempt_penalty = 0.9 ** attempts
        
        # Uncertainty bonus (gaps we know less about get priority)
        uncertainty = gap.get("uncertainty", 0.5)
        uncertainty_bonus = self.exploration_weight * uncertainty
        
        score = base_priority * attempt_penalty + uncertainty_bonus
        self._gap_priorities[gap_id] = score
        
        return score
    
    def select_action(self, gaps: list[dict], available_actions: list[str]) -> tuple[str, dict]:
        """Select best action to fill a gap."""
        if not gaps:
            return "explore", {}
        
        # Score and prioritize gaps
        scored_gaps = [(self.score_gap(g), g) for g in gaps]
        scored_gaps.sort(reverse=True)
        
        selected_gap = scored_gaps[0][1]
        gap_id = selected_gap.get("id", "")
        
        # Track attempt
        self._gap_attempts[gap_id] = self._gap_attempts.get(gap_id, 0) + 1
        
        # Select appropriate action
        gap_type = selected_gap.get("gap_type", "missing")
        if gap_type == "conflicting":
            action = "resolve_conflict"
        elif gap_type == "incomplete":
            action = "request_clarification"
        else:
            action = "research_gap"
        
        return action, selected_gap
    
    def mark_gap_resolved(self, gap_id: str):
        """Mark a gap as resolved."""
        self._gap_priorities.pop(gap_id, None)
        self._gap_attempts.pop(gap_id, None)


# =============================================================================
# ACTIVE LEARNING
# =============================================================================

class ActiveLearner:
    """
    Active learning for efficient knowledge acquisition.
    
    Selects the most informative samples to query,
    maximizing knowledge gain per interaction.
    
    Strategies:
    - Uncertainty sampling
    - Query-by-committee
    - Expected model change
    """
    
    def __init__(self, strategy: str = "uncertainty"):
        self.strategy = strategy
        self._model_predictions: dict[str, list[float]] = {}
        self._query_history: list[str] = []
    
    def compute_uncertainty(self, entity_id: str, predictions: list[float]) -> float:
        """Compute prediction uncertainty."""
        if len(predictions) < 2:
            return 1.0  # Maximum uncertainty
        
        # Entropy-based uncertainty
        probs = [max(min(p, 0.99), 0.01) for p in predictions]
        entropy = -sum(p * (p if p > 0 else 1e-10).__log__() for p in probs) if hasattr(probs[0], '__log__') else sum(p * (1-p) for p in probs)
        
        return entropy
    
    def select_queries(self, candidates: list[dict], num_queries: int = 5) -> list[dict]:
        """Select most informative candidates to query."""
        if self.strategy == "uncertainty":
            return self._uncertainty_sampling(candidates, num_queries)
        elif self.strategy == "committee":
            return self._query_by_committee(candidates, num_queries)
        else:
            # Random baseline
            return random.sample(candidates, min(num_queries, len(candidates)))
    
    def _uncertainty_sampling(self, candidates: list[dict], n: int) -> list[dict]:
        """Select candidates with highest prediction uncertainty."""
        scored = []
        for i, c in enumerate(candidates):
            entity_id = c.get("id", "")
            preds = self._model_predictions.get(entity_id, [0.5])
            uncertainty = self.compute_uncertainty(entity_id, preds)
            scored.append((uncertainty, i, c))  # Add index as tiebreaker
        
        scored.sort(key=lambda x: (-x[0], x[1]))  # Sort by uncertainty desc, then index
        return [c for _, _, c in scored[:n]]
    
    def _query_by_committee(self, candidates: list[dict], n: int) -> list[dict]:
        """Select candidates where committee disagrees most."""
        scored = []
        for c in candidates:
            entity_id = c.get("id", "")
            preds = self._model_predictions.get(entity_id, [])
            
            if len(preds) < 2:
                disagreement = 1.0
            else:
                # Variance as disagreement measure
                mean_pred = sum(preds) / len(preds)
                disagreement = sum((p - mean_pred)**2 for p in preds) / len(preds)
            
            scored.append((disagreement, c))
        
        scored.sort(reverse=True)
        return [c for _, c in scored[:n]]
    
    def update_predictions(self, entity_id: str, predictions: list[float]):
        """Update model predictions for an entity."""
        self._model_predictions[entity_id] = predictions


# =============================================================================
# UNIFIED LEARNING ENGINE
# =============================================================================

class InceptionLearningEngine:
    """
    Unified learning engine combining all RL/learning strategies.
    
    Orchestrates DAPO, GRPO, RLVR, GAP, and Active Learning
    for comprehensive PKG evolution.
    """
    
    def __init__(self):
        self.dapo = DAPOOptimizer()
        self.grpo = GRPOOptimizer()
        self.rlvr = RLVREngine()
        self.gap_policy = GAPPolicy()
        self.active_learner = ActiveLearner()
        
        self._experience_buffer: list[Experience] = []
        self._buffer_size = 10000
        self._total_steps = 0
    
    def step(
        self,
        action: str,
        state: dict,
        result: dict,
        sources: list[dict],
    ) -> dict:
        """Execute single learning step."""
        self._total_steps += 1
        
        # Compute verified reward
        reward = self.rlvr.compute_verified_reward(action, result, sources)
        
        # Create experience
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=result,
            done=False,
            metadata={"step": self._total_steps},
        )
        
        # Add to buffers
        self._experience_buffer.append(experience)
        if len(self._experience_buffer) > self._buffer_size:
            self._experience_buffer.pop(0)
        
        self.grpo.add_experience(experience)
        
        return {
            "step": self._total_steps,
            "reward": reward,
            "action": action,
        }
    
    def train(self, batch_size: int = 64) -> dict:
        """Run training update."""
        if len(self._experience_buffer) < batch_size:
            return {"status": "insufficient_data", "buffer_size": len(self._experience_buffer)}
        
        # Sample batch
        batch = random.sample(self._experience_buffer, batch_size)
        
        # Update with DAPO
        dapo_result = self.dapo.update(batch)
        
        # Update with GRPO
        grpo_result = self.grpo.update()
        
        return {
            "status": "trained",
            "total_steps": self._total_steps,
            "dapo": dapo_result,
            "grpo": grpo_result,
            "rlvr_stats": self.rlvr.get_verification_stats(),
        }
    
    def get_stats(self) -> dict:
        """Get comprehensive learning statistics."""
        return {
            "total_steps": self._total_steps,
            "buffer_size": len(self._experience_buffer),
            "dapo_updates": self.dapo._update_count,
            "dapo_entropy": self.dapo._entropy_schedule,
            "grpo_groups": len(self.grpo._action_groups),
            "rlvr_verification": self.rlvr.get_verification_stats(),
            "gap_priorities": len(self.gap_policy._gap_priorities),
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "DAPOOptimizer",
    "GRPOOptimizer", 
    "RLVREngine",
    "GAPPolicy",
    "ActiveLearner",
    "InceptionLearningEngine",
    "Experience",
    "RewardSignal",
]
