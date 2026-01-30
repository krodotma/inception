"""
ENTELECHEIA+ Learning & Adaptation Layer

Implements trace-based learning, weight adjustment,
and topology evolution for continuous improvement.

Trace-Based Learning:
- Learn from successful paths
- Adapt from failures
- Generalize patterns

Weight Learning:
- Adjust co-object relevance
- Tune routing thresholds
- Optimize hybrid reasoning

Topology Evolution:
- Prune weak connections
- Strengthen frequent paths
- Emerge new structure

Phase 7: Steps 211-240
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import math
import random


# =============================================================================
# LEARNING SIGNALS
# =============================================================================

class LearningSignal(str, Enum):
    """Types of learning signals."""
    
    SUCCESS = "success"     # Positive reinforcement
    FAILURE = "failure"     # Negative feedback
    OVERRIDE = "override"   # Human correction
    TIMEOUT = "timeout"     # Action took too long
    QUALITY = "quality"     # Performance metric


@dataclass
class LearningEvent:
    """An event that triggers learning."""
    
    event_id: str
    signal: LearningSignal
    
    # Context
    source: str          # What generated this event
    action: str          # What action was taken
    confidence: float    # Confidence at decision time
    
    # Outcome
    outcome_value: float  # -1.0 to 1.0
    
    # Additional data
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# TRACE-BASED LEARNER (Steps 211-220)
# =============================================================================

class TraceLearner:
    """
    Learns from stigmergic traces and their outcomes.
    
    Implements:
    - Path value estimation
    - Experience replay
    - Temporal difference learning
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        exploration_rate: float = 0.1,
    ):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        
        # State-action values
        self.q_values: dict[str, dict[str, float]] = {}
        
        # Experience buffer
        self.experiences: list[dict[str, Any]] = []
        self.max_experiences = 10000
        
        # Statistics
        self._total_updates = 0
        self._total_reward = 0.0
    
    def observe(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str | None,
    ) -> None:
        """
        Observe a state-action-reward-state transition.
        """
        # Store experience
        experience = {
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.experiences.append(experience)
        
        # Limit buffer size
        if len(self.experiences) > self.max_experiences:
            self.experiences = self.experiences[-self.max_experiences:]
        
        # Update Q-value (TD learning)
        self._update_q_value(state, action, reward, next_state)
        
        self._total_updates += 1
        self._total_reward += reward
    
    def _update_q_value(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str | None,
    ) -> None:
        """
        Update Q-value using temporal difference.
        
        Q(s,a) ← Q(s,a) + α[r + γ·max_a'Q(s',a') - Q(s,a)]
        """
        # Initialize if needed
        if state not in self.q_values:
            self.q_values[state] = {}
        if action not in self.q_values[state]:
            self.q_values[state][action] = 0.0
        
        current_q = self.q_values[state][action]
        
        # Future value
        if next_state and next_state in self.q_values:
            next_q = max(self.q_values[next_state].values()) if self.q_values[next_state] else 0.0
        else:
            next_q = 0.0
        
        # TD update
        td_target = reward + self.discount_factor * next_q
        td_error = td_target - current_q
        
        self.q_values[state][action] = current_q + self.learning_rate * td_error
    
    def select_action(
        self,
        state: str,
        available_actions: list[str],
    ) -> str:
        """
        Select action using epsilon-greedy.
        """
        if not available_actions:
            return ""
        
        # Exploration
        if random.random() < self.exploration_rate:
            return random.choice(available_actions)
        
        # Exploitation
        if state not in self.q_values:
            return random.choice(available_actions)
        
        state_values = self.q_values[state]
        
        # Get Q-values for available actions
        action_values = [
            (action, state_values.get(action, 0.0))
            for action in available_actions
        ]
        
        # Return best action
        return max(action_values, key=lambda x: x[1])[0]
    
    def replay(self, batch_size: int = 32) -> int:
        """
        Experience replay: learn from random past experiences.
        """
        if len(self.experiences) < batch_size:
            batch = self.experiences
        else:
            batch = random.sample(self.experiences, batch_size)
        
        for exp in batch:
            self._update_q_value(
                exp["state"],
                exp["action"],
                exp["reward"],
                exp["next_state"],
            )
        
        return len(batch)
    
    def get_state_value(self, state: str) -> float:
        """Get the value of a state (max Q-value)."""
        if state not in self.q_values or not self.q_values[state]:
            return 0.0
        return max(self.q_values[state].values())
    
    def get_statistics(self) -> dict[str, Any]:
        """Get learning statistics."""
        return {
            "total_updates": self._total_updates,
            "total_reward": self._total_reward,
            "average_reward": self._total_reward / max(1, self._total_updates),
            "states_learned": len(self.q_values),
            "experience_buffer_size": len(self.experiences),
            "exploration_rate": self.exploration_rate,
        }


# =============================================================================
# CO-OBJECT WEIGHT LEARNER (Steps 221-230)
# =============================================================================

class CoObjectWeightLearner:
    """
    Learns optimal weights for co-object relationships.
    
    Adjusts relevance scores based on usage outcomes.
    """
    
    def __init__(self, base_weight: float = 1.0):
        self.base_weight = base_weight
        
        # Learned weights: (source, target, relation) → weight
        self.weights: dict[tuple[str, str, str], float] = {}
        
        # Usage counts
        self.usage_counts: dict[tuple[str, str, str], int] = {}
        
        # Success rates
        self.success_counts: dict[tuple[str, str, str], int] = {}
    
    def observe_usage(
        self,
        source: str,
        target: str,
        relation: str,
        was_successful: bool,
    ) -> None:
        """Record usage of a co-object relationship."""
        key = (source, target, relation)
        
        # Update counts
        self.usage_counts[key] = self.usage_counts.get(key, 0) + 1
        if was_successful:
            self.success_counts[key] = self.success_counts.get(key, 0) + 1
        
        # Update weight
        self._update_weight(key)
    
    def _update_weight(self, key: tuple[str, str, str]) -> None:
        """
        Update weight based on success rate.
        
        Uses Bayesian update with smoothing.
        """
        usage = self.usage_counts.get(key, 0)
        success = self.success_counts.get(key, 0)
        
        if usage == 0:
            self.weights[key] = self.base_weight
            return
        
        # Beta distribution posterior mean with prior (1, 1)
        alpha = success + 1
        beta = (usage - success) + 1
        
        # Success rate estimate
        success_rate = alpha / (alpha + beta)
        
        # Scale to weight
        self.weights[key] = self.base_weight * (0.5 + success_rate)
    
    def get_weight(
        self,
        source: str,
        target: str,
        relation: str,
    ) -> float:
        """Get the learned weight for a relationship."""
        key = (source, target, relation)
        return self.weights.get(key, self.base_weight)
    
    def get_top_relationships(
        self,
        n: int = 10,
    ) -> list[tuple[tuple[str, str, str], float]]:
        """Get the highest-weighted relationships."""
        sorted_weights = sorted(
            self.weights.items(),
            key=lambda x: -x[1]
        )
        return sorted_weights[:n]
    
    def prune_low_performers(self, min_weight: float = 0.3) -> int:
        """Remove relationships with very low weights."""
        to_remove = [
            key for key, weight in self.weights.items()
            if weight < min_weight
        ]
        
        for key in to_remove:
            del self.weights[key]
            if key in self.usage_counts:
                del self.usage_counts[key]
            if key in self.success_counts:
                del self.success_counts[key]
        
        return len(to_remove)


# =============================================================================
# TOPOLOGY EVOLVER (Steps 231-240)
# =============================================================================

@dataclass
class TopologyMutation:
    """A mutation in the topology."""
    
    mutation_type: str  # "add_edge", "remove_edge", "strengthen", "weaken"
    source: str
    target: str
    weight_delta: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class TopologyEvolver:
    """
    Evolves the knowledge topology over time.
    
    Implements:
    - Hebbian learning (fire together → wire together)
    - Pruning of unused connections
    - Emergence of new connections
    """
    
    def __init__(
        self,
        strengthen_rate: float = 0.1,
        weaken_rate: float = 0.05,
        emergence_threshold: int = 3,
    ):
        self.strengthen_rate = strengthen_rate
        self.weaken_rate = weaken_rate
        self.emergence_threshold = emergence_threshold
        
        # Topology: (source, target) → weight
        self.edges: dict[tuple[str, str], float] = {}
        
        # Activation history
        self.activations: dict[str, list[datetime]] = {}
        
        # Co-activation counts (for Hebbian)
        self.co_activations: dict[tuple[str, str], int] = {}
        
        # Mutation log
        self.mutations: list[TopologyMutation] = []
    
    def activate(self, node: str) -> None:
        """Record activation of a node."""
        now = datetime.utcnow()
        
        if node not in self.activations:
            self.activations[node] = []
        
        self.activations[node].append(now)
        
        # Keep only recent activations (last hour)
        one_hour_ago = now.timestamp() - 3600
        self.activations[node] = [
            t for t in self.activations[node]
            if t.timestamp() > one_hour_ago
        ]
    
    def record_co_activation(self, node_a: str, node_b: str) -> None:
        """
        Record co-activation of two nodes.
        
        This is the basis for Hebbian learning.
        """
        key = tuple(sorted([node_a, node_b]))
        self.co_activations[key] = self.co_activations.get(key, 0) + 1
        
        # Check for emergence
        if self.co_activations[key] >= self.emergence_threshold:
            if key not in self.edges:
                self._emerge_edge(node_a, node_b)
    
    def _emerge_edge(self, source: str, target: str) -> None:
        """Create a new edge from co-activation."""
        key = (source, target)
        
        if key not in self.edges:
            self.edges[key] = 0.5  # Initial weight
            
            self.mutations.append(TopologyMutation(
                mutation_type="add_edge",
                source=source,
                target=target,
                weight_delta=0.5,
                reason=f"Emerged from {self.co_activations.get(tuple(sorted([source, target])), 0)} co-activations",
            ))
    
    def strengthen(self, source: str, target: str, factor: float = 1.0) -> None:
        """
        Strengthen an edge (positive feedback).
        """
        key = (source, target)
        
        if key not in self.edges:
            self.edges[key] = 0.5
        
        delta = self.strengthen_rate * factor
        self.edges[key] = min(1.0, self.edges[key] + delta)
        
        self.mutations.append(TopologyMutation(
            mutation_type="strengthen",
            source=source,
            target=target,
            weight_delta=delta,
            reason="Positive feedback",
        ))
    
    def weaken(self, source: str, target: str, factor: float = 1.0) -> None:
        """
        Weaken an edge (negative feedback or decay).
        """
        key = (source, target)
        
        if key not in self.edges:
            return
        
        delta = self.weaken_rate * factor
        self.edges[key] = max(0.0, self.edges[key] - delta)
        
        self.mutations.append(TopologyMutation(
            mutation_type="weaken",
            source=source,
            target=target,
            weight_delta=-delta,
            reason="Negative feedback or decay",
        ))
        
        # Prune if too weak
        if self.edges[key] < 0.05:
            del self.edges[key]
            self.mutations.append(TopologyMutation(
                mutation_type="remove_edge",
                source=source,
                target=target,
                weight_delta=-self.edges.get(key, 0),
                reason="Pruned due to low weight",
            ))
    
    def decay_all(self, factor: float = 0.01) -> int:
        """
        Apply global decay to all edges.
        
        Edges that aren't reinforced will eventually disappear.
        """
        pruned = 0
        to_remove = []
        
        for key in self.edges:
            self.edges[key] -= factor
            if self.edges[key] < 0.05:
                to_remove.append(key)
        
        for key in to_remove:
            del self.edges[key]
            pruned += 1
        
        return pruned
    
    def get_neighbors(self, node: str) -> list[tuple[str, float]]:
        """Get all neighbors of a node with edge weights."""
        neighbors = []
        
        for (source, target), weight in self.edges.items():
            if source == node:
                neighbors.append((target, weight))
            elif target == node:
                neighbors.append((source, weight))
        
        return sorted(neighbors, key=lambda x: -x[1])
    
    def get_topology_stats(self) -> dict[str, Any]:
        """Get statistics about the topology."""
        if not self.edges:
            return {
                "edge_count": 0,
                "node_count": 0,
                "avg_weight": 0,
                "mutations": len(self.mutations),
            }
        
        nodes = set()
        for source, target in self.edges.keys():
            nodes.add(source)
            nodes.add(target)
        
        weights = list(self.edges.values())
        
        return {
            "edge_count": len(self.edges),
            "node_count": len(nodes),
            "avg_weight": sum(weights) / len(weights),
            "max_weight": max(weights),
            "min_weight": min(weights),
            "mutations": len(self.mutations),
        }


# =============================================================================
# UNIFIED LEARNER
# =============================================================================

class UnifiedLearner:
    """
    Unified learning interface combining all learning components.
    """
    
    def __init__(self):
        self.trace_learner = TraceLearner()
        self.weight_learner = CoObjectWeightLearner()
        self.topology_evolver = TopologyEvolver()
        
        self._events: list[LearningEvent] = []
    
    def process_event(self, event: LearningEvent) -> None:
        """Process a learning event across all learners."""
        self._events.append(event)
        
        # Map signal to reward
        reward_map = {
            LearningSignal.SUCCESS: 1.0,
            LearningSignal.FAILURE: -1.0,
            LearningSignal.OVERRIDE: -0.5,
            LearningSignal.TIMEOUT: -0.3,
            LearningSignal.QUALITY: event.outcome_value,
        }
        reward = reward_map.get(event.signal, 0.0)
        
        # Update trace learner
        state = event.context.get("state", event.source)
        next_state = event.context.get("next_state")
        self.trace_learner.observe(state, event.action, reward, next_state)
        
        # Update weight learner if co-objects involved
        if "source_concept" in event.context and "target_concept" in event.context:
            self.weight_learner.observe_usage(
                event.context["source_concept"],
                event.context["target_concept"],
                event.context.get("relation", "unknown"),
                event.signal == LearningSignal.SUCCESS,
            )
        
        # Update topology
        if event.signal == LearningSignal.SUCCESS:
            if "concepts" in event.context:
                concepts = event.context["concepts"]
                for i, c1 in enumerate(concepts):
                    for c2 in concepts[i+1:]:
                        self.topology_evolver.record_co_activation(c1, c2)
                        self.topology_evolver.strengthen(c1, c2, 0.5)
        elif event.signal == LearningSignal.FAILURE:
            if "concepts" in event.context:
                concepts = event.context["concepts"]
                for i, c1 in enumerate(concepts):
                    for c2 in concepts[i+1:]:
                        self.topology_evolver.weaken(c1, c2, 0.5)
    
    def get_unified_stats(self) -> dict[str, Any]:
        """Get combined statistics."""
        return {
            "events_processed": len(self._events),
            "trace_learning": self.trace_learner.get_statistics(),
            "topology": self.topology_evolver.get_topology_stats(),
            "weight_learner_relationships": len(self.weight_learner.weights),
        }
