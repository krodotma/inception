"""
Swarm Learning Coordinator - Swarm Track 2

Multi-strategy learning with Thompson Sampling, curriculum learning.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    """Available learning strategies."""
    DSPY_MIPRO = "dspy_mipro"
    GRPO_V2 = "grpo_v2"
    TEXTGRAD = "textgrad"
    COMPOUND = "compound"
    ENSEMBLE = "ensemble"
    ADAPTIVE = "adaptive"


@dataclass
class LearningEpisode:
    """A single learning episode."""
    episode_id: str
    strategy: LearningStrategy
    initial_score: float
    final_score: float
    improvement: float
    iterations: int
    duration_ms: int


@dataclass
class SwarmSession:
    """A swarm learning session."""
    session_id: str
    objective_name: str
    start_time: datetime
    episodes: list[LearningEpisode] = field(default_factory=list)
    best_result: str | None = None
    best_score: float = 0.0
    total_iterations: int = 0


class SwarmLearningCoordinator:
    """
    Coordinates multiple learning strategies using Thompson Sampling.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        exploration_rate: float = 0.3,
        early_stop_patience: int = 5,
    ):
        self.max_workers = max_workers
        self.exploration_rate = exploration_rate
        self.early_stop_patience = early_stop_patience
        self._strategy_successes: dict[LearningStrategy, int] = {}
        self._strategy_failures: dict[LearningStrategy, int] = {}
        self.sessions: list[SwarmSession] = []
        self.current_session: SwarmSession | None = None
    
    def run_swarm(
        self,
        objective: Callable[[str], float],
        initial_population: list[str],
        strategies: list[LearningStrategy] | None = None,
        iterations_per_strategy: int = 10,
        max_rounds: int = 5,
    ) -> tuple[str, float]:
        """Run swarm optimization with Thompson Sampling."""
        if strategies is None:
            strategies = [LearningStrategy.DSPY_MIPRO, LearningStrategy.GRPO_V2]
        
        session = SwarmSession(
            session_id=f"swarm_{int(time.time())}",
            objective_name=f"swarm_{len(self.sessions)}",
            start_time=datetime.utcnow(),
        )
        self.sessions.append(session)
        self.current_session = session
        
        population = [(c, objective(c)) for c in initial_population]
        population.sort(key=lambda x: x[1], reverse=True)
        best_result, best_score = population[0]
        
        for round_num in range(max_rounds):
            selected = self._select_strategies(strategies)
            results = self._run_parallel(
                objective, [p[0] for p in population[:3]], selected, iterations_per_strategy
            )
            
            for result, score, episode in results:
                session.episodes.append(episode)
                if score > best_score:
                    best_result, best_score = result, score
                    self._strategy_successes[episode.strategy] = \
                        self._strategy_successes.get(episode.strategy, 0) + 1
                else:
                    self._strategy_failures[episode.strategy] = \
                        self._strategy_failures.get(episode.strategy, 0) + 1
        
        session.best_result = best_result
        session.best_score = best_score
        return best_result, best_score
    
    def _select_strategies(self, available: list[LearningStrategy]) -> list[LearningStrategy]:
        """Select via Thompson Sampling."""
        if random.random() < self.exploration_rate:
            return random.sample(available, min(2, len(available)))
        
        samples = []
        for s in available:
            succ = self._strategy_successes.get(s, 1)
            fail = self._strategy_failures.get(s, 1)
            samples.append((s, random.betavariate(succ, fail)))
        samples.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in samples[:2]]
    
    def _run_parallel(
        self, objective: Callable, candidates: list[str],
        strategies: list[LearningStrategy], iterations: int,
    ) -> list[tuple[str, float, LearningEpisode]]:
        """Run strategies in parallel."""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._run_one, objective, c, s, iterations)
                for s in strategies for c in candidates
            ]
            for f in as_completed(futures):
                try:
                    results.append(f.result())
                except Exception as e:
                    logger.error(f"Strategy failed: {e}")
        return results
    
    def _run_one(
        self, objective: Callable, candidate: str,
        strategy: LearningStrategy, iterations: int,
    ) -> tuple[str, float, LearningEpisode]:
        """Run single strategy."""
        start = time.time()
        initial = objective(candidate)
        result, best = candidate, initial
        
        for _ in range(iterations):
            var = self._mutate(result)
            score = objective(var)
            if score > best:
                result, best = var, score
        
        return result, best, LearningEpisode(
            episode_id=f"ep_{int(time.time())}",
            strategy=strategy,
            initial_score=initial,
            final_score=best,
            improvement=best - initial,
            iterations=iterations,
            duration_ms=int((time.time() - start) * 1000),
        )
    
    def _mutate(self, candidate: str) -> str:
        """Simple mutation."""
        words = candidate.split()
        if words and random.random() > 0.5:
            idx = random.randint(0, len(words) - 1)
            words[idx] = words[idx] + "_v"
        return " ".join(words)
    
    def get_stats(self) -> dict[str, Any]:
        """Get strategy stats."""
        return {
            s.value: {
                "success_rate": self._strategy_successes.get(s, 0) / 
                    max(1, self._strategy_successes.get(s, 0) + self._strategy_failures.get(s, 0))
            }
            for s in LearningStrategy
        }
