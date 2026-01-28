"""
GRPO v2 Optimizer for Inception.

Enhanced Group Relative Policy Optimization inspired by DeepSeek-R1:
- No critic network (40-60% memory reduction vs PPO)
- Multi-sample generation for group baselines
- Integrated verifiable rewards from RLVR
- Emergent reasoning through self-verification

References:
- DeepSeek-R1: Incentivizing Reasoning in LLMs (2024)
- GRPO: A Memory-Efficient Alternative to PPO
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class GRPOExperience:
    """Single experience for GRPO training."""
    prompt: str
    response: str
    reward: float
    advantage: float = 0.0
    verified: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class GRPOStepResult:
    """Result of a GRPO optimization step."""
    responses: list[str]
    rewards: list[float]
    advantages: list[float]
    best_response: str
    best_reward: float
    mean_reward: float
    verified_count: int = 0


@dataclass
class GRPOTrainResult:
    """Result of GRPO training batch."""
    loss: float
    policy_loss: float
    kl_divergence: float
    entropy: float
    experiences_used: int
    improvement: float = 0.0


class GRPOv2Optimizer:
    """
    Enhanced GRPO with verifiable rewards and emergent reasoning.
    
    Key innovations from DeepSeek-R1:
    - No value network: Uses group mean as baseline
    - Multi-sample generation: Better reward estimation
    - Verifiable rewards: Ground-truth verification signals
    - Self-verification: Emergent reasoning patterns
    
    Example:
        grpo = GRPOv2Optimizer()
        result = grpo.step(
            prompt="Extract claims from: OAuth uses tokens",
            policy_fn=lambda p: llm.generate(p),
        )
        # result.best_response = most accurate extraction
    """
    
    def __init__(
        self,
        group_size: int = 16,
        num_samples: int = 4,
        kl_coef: float = 0.04,
        clip_range: float = 0.2,
        verification_weight: float = 0.3,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 1.0,
    ):
        """
        Initialize GRPO v2 optimizer.
        
        Args:
            group_size: Number of experiences to group for relative advantages
            num_samples: Number of responses to generate per prompt
            kl_coef: KL divergence penalty coefficient
            clip_range: PPO-style clipping range
            verification_weight: Weight for verified rewards
            entropy_coef: Entropy bonus coefficient
            max_grad_norm: Maximum gradient norm for clipping
        """
        self.group_size = group_size
        self.num_samples = num_samples
        self.kl_coef = kl_coef
        self.clip_range = clip_range
        self.verification_weight = verification_weight
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        
        # Experience buffer
        self.experiences: list[GRPOExperience] = []
        self.baseline_ema = 0.0
        self.baseline_momentum = 0.9
        
        # Statistics
        self.total_steps = 0
        self.total_verifications = 0
    
    def step(
        self,
        prompt: str,
        policy_fn: Callable[[str], str],
        reward_fn: Optional[Callable[[str], float]] = None,
        verify_fn: Optional[Callable[[str], tuple[bool, float]]] = None,
    ) -> GRPOStepResult:
        """
        Execute a single GRPO step with multi-sample generation.
        
        Args:
            prompt: Input prompt
            policy_fn: Function that generates response from prompt
            reward_fn: Optional reward function
            verify_fn: Optional verification function returning (is_valid, score)
        
        Returns:
            GRPOStepResult with responses, rewards, and advantages
        """
        # Generate multiple responses
        responses = []
        for _ in range(self.num_samples):
            try:
                response = policy_fn(prompt)
                responses.append(response)
            except Exception as e:
                logger.warning(f"Response generation failed: {e}")
                responses.append("")
        
        # Compute rewards
        rewards = []
        verified_count = 0
        
        for response in responses:
            # Base reward
            if reward_fn:
                base_reward = reward_fn(response)
            else:
                base_reward = self._default_reward(response)
            
            # Verification bonus
            if verify_fn:
                try:
                    is_valid, verify_score = verify_fn(response)
                    if is_valid:
                        verified_count += 1
                        self.total_verifications += 1
                    base_reward += self.verification_weight * verify_score
                except Exception as e:
                    logger.warning(f"Verification failed: {e}")
            
            rewards.append(base_reward)
        
        # Compute group-relative advantages (no critic needed)
        advantages = self.compute_advantages(rewards)
        
        # Store experiences
        for resp, reward, adv in zip(responses, rewards, advantages):
            self.experiences.append(GRPOExperience(
                prompt=prompt,
                response=resp,
                reward=reward,
                advantage=adv,
                verified=verify_fn is not None,
            ))
        
        # Update baseline EMA
        mean_reward = np.mean(rewards)
        self.baseline_ema = (
            self.baseline_momentum * self.baseline_ema +
            (1 - self.baseline_momentum) * mean_reward
        )
        
        self.total_steps += 1
        
        # Find best response
        best_idx = np.argmax(rewards)
        
        return GRPOStepResult(
            responses=responses,
            rewards=rewards,
            advantages=advantages,
            best_response=responses[best_idx],
            best_reward=rewards[best_idx],
            mean_reward=mean_reward,
            verified_count=verified_count,
        )
    
    def compute_advantages(self, rewards: list[float]) -> list[float]:
        """
        Compute group-relative advantages without a critic network.
        
        This is the key GRPO innovation: using the group mean as baseline
        instead of a learned value function.
        
        Args:
            rewards: List of rewards for the group
        
        Returns:
            List of normalized advantages
        """
        rewards_arr = np.array(rewards)
        mean_reward = np.mean(rewards_arr)
        std_reward = max(1e-6, np.std(rewards_arr))
        
        # Normalize within group
        advantages = (rewards_arr - mean_reward) / std_reward
        
        return advantages.tolist()
    
    def train(self, batch_size: int = 64) -> Optional[GRPOTrainResult]:
        """
        Train on collected experiences.
        
        Args:
            batch_size: Number of experiences to use
        
        Returns:
            GRPOTrainResult with training metrics, or None if insufficient data
        """
        if len(self.experiences) < batch_size:
            logger.info(f"Insufficient experiences: {len(self.experiences)} < {batch_size}")
            return None
        
        # Sample batch
        batch = random.sample(self.experiences, batch_size)
        
        # Compute losses (placeholder for actual policy optimization)
        advantages = np.array([e.advantage for e in batch])
        rewards = np.array([e.reward for e in batch])
        
        # Policy loss (simplified)
        policy_loss = -np.mean(advantages)
        
        # KL divergence penalty (would need reference policy in practice)
        kl_div = 0.0
        
        # Entropy bonus (would need actual policy in practice)
        entropy = 0.0
        
        # Total loss
        total_loss = policy_loss + self.kl_coef * kl_div - self.entropy_coef * entropy
        
        # Compute improvement
        improvement = np.mean(rewards) - self.baseline_ema
        
        # Clear old experiences (keep recent for stability)
        if len(self.experiences) > batch_size * 4:
            self.experiences = self.experiences[-batch_size * 2:]
        
        return GRPOTrainResult(
            loss=total_loss,
            policy_loss=policy_loss,
            kl_divergence=kl_div,
            entropy=entropy,
            experiences_used=batch_size,
            improvement=improvement,
        )
    
    def _default_reward(self, response: str) -> float:
        """Default reward based on response quality heuristics."""
        if not response:
            return -1.0
        
        # Length penalty (prefer concise but complete)
        length_score = min(1.0, len(response) / 500) * 0.3
        
        # Structure bonus (has JSON structure, bullet points, etc.)
        structure_score = 0.0
        if "{" in response and "}" in response:
            structure_score += 0.2
        if "subject" in response.lower() or "claim" in response.lower():
            structure_score += 0.2
        
        # Coherence (no obvious errors)
        coherence_score = 0.3
        if response.count("{") != response.count("}"):
            coherence_score = 0.0
        
        return length_score + structure_score + coherence_score
    
    def get_stats(self) -> dict:
        """Get optimizer statistics."""
        return {
            "total_steps": self.total_steps,
            "total_verifications": self.total_verifications,
            "experience_buffer_size": len(self.experiences),
            "baseline_ema": self.baseline_ema,
            "verification_rate": (
                self.total_verifications / max(1, self.total_steps * self.num_samples)
            ),
        }
    
    def reset(self):
        """Reset optimizer state."""
        self.experiences = []
        self.baseline_ema = 0.0
        self.total_steps = 0
        self.total_verifications = 0


class GRPOWithRLVR(GRPOv2Optimizer):
    """
    GRPO integrated with RLVR (Reinforcement Learning with Verifiable Rewards).
    
    Extends GRPOv2 with ground-truth verification for extraction tasks.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._rlvr_engine = None
    
    def _get_rlvr(self):
        """Lazily load RLVR engine."""
        if self._rlvr_engine is None:
            try:
                from inception.enhance.learning import RLVREngine
                self._rlvr_engine = RLVREngine()
            except ImportError:
                # Use simplified verifier
                self._rlvr_engine = self._SimpleVerifier()
        return self._rlvr_engine
    
    class _SimpleVerifier:
        """Simple verifier fallback."""
        def compute_verified_reward(self, action: str, result: dict, sources: list) -> float:
            # Basic heuristic verification
            response = result.get("response", "")
            if not sources or not response:
                return 0.0
            
            # Check if key terms from sources appear in response
            source_text = " ".join(str(s) for s in sources)
            source_words = set(source_text.lower().split())
            response_words = set(response.lower().split())
            
            overlap = len(source_words & response_words)
            return min(1.0, overlap / max(1, len(response_words)))
    
    def step_with_sources(
        self,
        prompt: str,
        policy_fn: Callable[[str], str],
        sources: list[str],
    ) -> GRPOStepResult:
        """
        Execute GRPO step with source-based verification.
        
        Args:
            prompt: Input prompt
            policy_fn: Response generation function
            sources: Ground-truth sources for verification
        
        Returns:
            GRPOStepResult with verified responses
        """
        rlvr = self._get_rlvr()
        
        def verify_fn(response: str) -> tuple[bool, float]:
            score = rlvr.compute_verified_reward(
                action="extract",
                result={"response": response},
                sources=sources,
            )
            return score > 0.5, score
        
        return self.step(
            prompt=prompt,
            policy_fn=policy_fn,
            verify_fn=verify_fn,
        )
