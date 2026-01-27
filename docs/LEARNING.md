# Learning Engine Guide

> DAPO, GRPO, RLVR, GAP Policy, and Active Learning for PKG evolution

The Inception Learning Engine uses advanced reinforcement learning and preference
optimization techniques to continuously improve knowledge extraction and gap resolution.

---

## Components

| Component | Full Name | Purpose |
|-----------|-----------|---------|
| **DAPO** | Dynamic Advantage Policy Optimization | Adaptive PPO with dynamic clip range |
| **GRPO** | Group Relative Policy Optimization | Within-group ranking for sparse rewards |
| **RLVR** | RL with Verifiable Rewards | Ground-truth verification signals |
| **GAP** | Gap-Aware Policy | Uncertainty-guided exploration |
| **Active** | Active Learning | Uncertainty sampling |

---

## Quick Start

```python
from inception.enhance.learning import InceptionLearningEngine

# Initialize engine
engine = InceptionLearningEngine()

# Execute learning step
result = engine.step(
    action="extract_claim",
    state={"entities": 50, "claims": 200},
    result={"statement": "OAuth is an authorization framework"},
    sources=[{"content": "RFC 6749 defines OAuth 2.0..."}]
)

print(f"Reward: {result['reward']:.2f}")
# Reward: 0.75 (verified claim)

# Train on collected experiences
train_result = engine.train(batch_size=64)
print(f"Status: {train_result['status']}")
```

---

## DAPO: Dynamic Advantage Policy Optimization

DAPO extends PPO with:
- **Dynamic clip range**: Wider clips for high-variance advantages (more exploration)
- **Entropy scheduling**: Automatic decay for exploitation
- **Advantage normalization**: Per-batch normalization

### Usage

```python
from inception.enhance.learning import DAPOOptimizer

dapo = DAPOOptimizer(
    clip_range=0.2,      # Base clip range
    entropy_coef=0.01,   # Entropy bonus coefficient
    value_coef=0.5,      # Value loss weight
)

# Compute dynamic clip based on advantage variance
advantages = [0.1, 0.5, -0.3, 0.8]
dynamic_clip = dapo.compute_dynamic_clip(advantages)
# Higher variance → wider clip → more exploration

# Get entropy bonus with scheduling
bonus = dapo.compute_entropy_bonus(policy_entropy=0.5)
# Decays over time as policy becomes confident
```

### Configuration

| Param | Default | Description |
|-------|---------|-------------|
| `clip_range` | 0.2 | Base PPO clip range |
| `entropy_coef` | 0.01 | Entropy bonus weight |
| `value_coef` | 0.5 | Value loss weight |
| `max_grad_norm` | 0.5 | Gradient clipping |

---

## GRPO: Group Relative Policy Optimization

GRPO groups experiences by action type and computes relative advantages
within each group. This is especially effective for:
- Sparse reward signals
- Heterogeneous action spaces
- Comparative ranking

### Usage

```python
from inception.enhance.learning import GRPOOptimizer, Experience
from datetime import datetime

grpo = GRPOOptimizer(
    group_size=32,       # Min group size for update
    top_k_ratio=0.25,    # Top 25% for policy update
    temperature=1.0,
)

# Add experiences (automatically grouped by action)
exp1 = Experience(
    state={},
    action="extract_claim",
    reward=0.8,
    next_state={},
    done=False
)
grpo.add_experience(exp1)

# Compute relative advantage within group
advantage = grpo.compute_group_advantage(exp1)
# Compares to group baseline, applies percentile scaling

# Run group update
results = grpo.update()
print(results["groups"]["extract_claim"]["top_k_mean_reward"])
```

### How It Works

1. Experiences added to action-specific groups
2. Group baseline = running average reward per action
3. Relative advantage = reward - baseline
4. Percentile scaling based on within-group rank
5. Top-k experiences used for policy update

---

## RLVR: Reinforcement Learning with Verifiable Rewards

RLVR provides ground-truth reward signals by verifying extractions
against source material.

### Verification Types

| Action | Verification Method | Good Reward | Bad Reward |
|--------|---------------------|-------------|------------|
| `extract_claim` | Word overlap with sources | +overlap | -0.5 |
| `resolve_gap` | Cache check | +1.0 | -0.3 |
| `extract_procedure` | Step completeness | +0.8 | +0.2 |

### Usage

```python
from inception.enhance.learning import RLVREngine

rlvr = RLVREngine()

# Verified claim extraction
claim = {"statement": "OAuth uses bearer tokens for authentication"}
sources = [{"content": "The OAuth 2.0 protocol uses bearer tokens..."}]

reward = rlvr.compute_verified_reward(
    action="extract_claim",
    result=claim,
    sources=sources
)
print(f"Verified reward: {reward}")  # Positive if claim matches sources

# Get verification statistics
stats = rlvr.get_verification_stats()
print(f"Verified rate: {stats['verified_rate']:.1%}")
```

### Custom Verifier

```python
def my_verifier(claim: dict, sources: list) -> tuple[bool, float]:
    """Custom verification logic."""
    # Your verification logic here
    return verified, confidence

rlvr = RLVREngine(verifier_fn=my_verifier)
```

---

## GAP: Gap-Aware Policy

The GAP policy prioritizes actions that fill knowledge gaps using
uncertainty-guided exploration.

### Usage

```python
from inception.enhance.learning import GAPPolicy

gap_policy = GAPPolicy(exploration_weight=0.3)

gaps = [
    {"id": "g1", "priority": "high", "gap_type": "missing", "uncertainty": 0.9},
    {"id": "g2", "priority": "low", "gap_type": "missing", "uncertainty": 0.3},
]

# Select best action for current gaps
action, selected_gap = gap_policy.select_action(
    gaps=gaps,
    available_actions=["research_gap", "resolve_conflict"]
)
print(f"Action: {action}, Gap: {selected_gap['id']}")
# High priority + high uncertainty → selected first

# Mark gap as resolved
gap_policy.mark_gap_resolved("g1")
```

### Scoring Formula

```
score = base_priority × attempt_penalty + uncertainty_bonus

where:
  base_priority = {high: 1.0, medium: 0.6, low: 0.3}
  attempt_penalty = 0.9^attempts (diminishing returns)
  uncertainty_bonus = exploration_weight × uncertainty
```

---

## Active Learning

Select the most informative samples to query, maximizing knowledge gain.

### Strategies

| Strategy | Method | Best For |
|----------|--------|----------|
| `uncertainty` | Entropy-based | Single model |
| `committee` | Variance across predictions | Ensemble models |
| `random` | Uniform sampling | Baseline |

### Usage

```python
from inception.enhance.learning import ActiveLearner

learner = ActiveLearner(strategy="uncertainty")

candidates = [
    {"id": "e1", "name": "Entity 1"},
    {"id": "e2", "name": "Entity 2"},
    {"id": "e3", "name": "Entity 3"},
]

# Select most informative samples
selected = learner.select_queries(candidates, num_queries=2)

# Update with model predictions (for future selections)
learner.update_predictions("e1", [0.2, 0.8, 0.5])
```

---

## Unified Engine

`InceptionLearningEngine` combines all components:

```python
from inception.enhance.learning import InceptionLearningEngine

engine = InceptionLearningEngine()

# Access individual components
engine.dapo      # DAPOOptimizer
engine.grpo      # GRPOOptimizer
engine.rlvr      # RLVREngine
engine.gap_policy    # GAPPolicy
engine.active_learner  # ActiveLearner

# Execute learning loop
for _ in range(100):
    result = engine.step(
        action="extract_claim",
        state={...},
        result={...},
        sources=[...]
    )

# Train
engine.train(batch_size=64)

# Get comprehensive stats
stats = engine.get_stats()
print(stats)
```

---

## API Endpoints

```bash
# Learning step
curl -X POST http://localhost:8000/api/learning/step \
  -d '{"action": "extract_claim", ...}'

# Training
curl -X POST http://localhost:8000/api/learning/train?batch_size=64

# Statistics
curl http://localhost:8000/api/learning/stats
curl http://localhost:8000/api/learning/dapo
curl http://localhost:8000/api/learning/grpo
curl http://localhost:8000/api/learning/rlvr

# Gap selection
curl -X POST http://localhost:8000/api/learning/gap/select \
  -d '{"gaps": [...], "available_actions": [...]}'

# Active learning
curl -X POST http://localhost:8000/api/learning/active/select \
  -d '{"candidates": [...], "num_queries": 5}'
```

---

## Testing

All components have extensive tests:

```bash
pytest tests/test_inception.py::TestDAPOOptimizer -v
pytest tests/test_inception.py::TestGRPOOptimizer -v
pytest tests/test_inception.py::TestRLVREngine -v
pytest tests/test_inception.py::TestGAPPolicy -v
pytest tests/test_inception.py::TestActiveLearner -v
pytest tests/test_inception.py::TestInceptionLearningEngine -v
```

---

## References

- **DAPO**: Builds on [PPO](https://arxiv.org/abs/1707.06347) with dynamic clipping
- **GRPO**: Inspired by group preference optimization techniques
- **RLVR**: Verification-based rewards for grounded RL
- **Active Learning**: [Settles (2009)](http://burrsettles.com/pub/settles.activelearning.pdf)
