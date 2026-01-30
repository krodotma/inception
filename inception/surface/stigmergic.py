"""
ENTELECHEIA+ Stigmergic Coordination Layer (AI/ML Semantics)

Stigmergy in AI/ML: Indirect coordination through shared state modifications.
NOT just a pheromone metaphor, but proper neural/symbolic coordination:

- **Marker-Based Stigmergy**: Neural traces as embeddings/activations
- **Sematectonic Stigmergy**: Modifying shared knowledge structures
- **Gradient-Compatible Traces**: Differentiable for end-to-end learning
- **Attention-Based Retrieval**: Find relevant traces via attention

References:
- Swarm Intelligence (ACO, PSO)
- Multi-Agent Reinforcement Learning (MARL)
- Graph Neural Networks (message passing as stigmergy)
- Neurosymbolic coordination patterns

Phase 3: Steps 91-120
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Protocol
import json
import hashlib
import math


# =============================================================================
# TRACE SEMANTICS (AI/ML Definition)
# =============================================================================

class TraceType(str, Enum):
    """
    Types of stigmergic traces in the AI/ML sense.
    
    Following Grassé's categories + neural extensions:
    """
    
    # Marker-based (leave information)
    MARKER = "marker"           # Information deposit (like neural activation)
    SIGNAL = "signal"           # Attention-directing (like saliency)
    GRADIENT = "gradient"       # Learning signal (for backprop)
    
    # Sematectonic (modify structure)
    STRUCTURAL = "structural"   # Modify graph/topology
    SEMANTIC = "semantic"       # Modify meaning representations
    
    # Coordination
    CLAIM = "claim"             # Exclusive access marker
    HANDOFF = "handoff"         # Transfer between agents
    BROADCAST = "broadcast"     # Multi-agent notification


# =============================================================================
# NEURAL TRACE (Embedding-Based)
# =============================================================================

@dataclass
class NeuralTrace:
    """
    A stigmergic trace with neural/symbolic representations.
    
    Unlike simple pheromone strength, this carries:
    - Vector embedding (for semantic similarity)
    - Symbolic metadata (for logical reasoning)
    - Gradient-compatible decay/reinforcement
    """
    
    trace_id: str
    trace_type: TraceType
    location: str              # Namespace/path for the trace
    agent_id: str              # Depositing agent
    
    # Neural representation (embedding)
    embedding: list[float] | None = None
    embedding_dim: int = 0
    
    # Symbolic representation
    symbols: dict[str, Any] = field(default_factory=dict)
    
    # Strength with gradient-compatible operations
    strength: float = 1.0
    strength_gradient: float = 0.0  # Accumulated gradient
    
    # Temporal
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: float = 3600.0  # Time-to-live
    
    # Coordination
    visit_count: int = 1
    visitors: list[str] = field(default_factory=list)
    attention_scores: dict[str, float] = field(default_factory=dict)
    
    # Learning
    learning_rate: float = 0.1
    momentum: float = 0.9
    _momentum_buffer: float = 0.0
    
    @classmethod
    def create(
        cls,
        trace_type: TraceType,
        location: str,
        agent_id: str,
        embedding: list[float] | None = None,
        symbols: dict[str, Any] | None = None,
        strength: float = 1.0,
    ) -> NeuralTrace:
        """Create a new trace with auto-generated ID."""
        trace_id = hashlib.md5(
            f"{trace_type.value}:{location}:{agent_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return cls(
            trace_id=trace_id,
            trace_type=trace_type,
            location=location,
            agent_id=agent_id,
            embedding=embedding,
            embedding_dim=len(embedding) if embedding else 0,
            symbols=symbols or {},
            strength=strength,
            visitors=[agent_id],
        )
    
    # -------------------------------------------------------------------------
    # Gradient-Compatible Operations
    # -------------------------------------------------------------------------
    
    def decay(self, delta_seconds: float | None = None) -> float:
        """
        Apply exponential decay (differentiable).
        
        decay(t) = strength * exp(-lambda * t)
        """
        if delta_seconds is None:
            delta_seconds = (datetime.utcnow() - self.last_updated).total_seconds()
        
        decay_rate = 1.0 / self.ttl_seconds
        decay_factor = math.exp(-decay_rate * delta_seconds)
        
        self.strength *= decay_factor
        self.strength_gradient *= decay_factor  # Decay gradient too
        
        return self.strength
    
    def reinforce(self, signal: float = 1.0, visitor_id: str | None = None) -> float:
        """
        Reinforce trace with gradient accumulation.
        
        Uses momentum for stable learning.
        """
        # Gradient update with momentum
        self._momentum_buffer = (
            self.momentum * self._momentum_buffer + 
            self.learning_rate * signal
        )
        
        self.strength += self._momentum_buffer
        self.strength = min(10.0, max(0.0, self.strength))  # Clamp
        
        self.strength_gradient += signal
        self.visit_count += 1
        self.last_updated = datetime.utcnow()
        
        if visitor_id and visitor_id not in self.visitors:
            self.visitors.append(visitor_id)
        
        return self.strength
    
    def backward(self, upstream_gradient: float = 1.0) -> dict[str, float]:
        """
        Backpropagate gradient through this trace.
        
        Returns gradients for connected traces.
        """
        # Accumulate gradient
        self.strength_gradient += upstream_gradient * self.strength
        
        # Compute gradients for attention scores
        attention_grads = {}
        for agent_id, score in self.attention_scores.items():
            attention_grads[agent_id] = upstream_gradient * score
        
        return attention_grads
    
    # -------------------------------------------------------------------------
    # Attention-Based Operations
    # -------------------------------------------------------------------------
    
    def compute_attention(self, query_embedding: list[float]) -> float:
        """
        Compute attention score between query and this trace.
        
        Uses scaled dot-product attention.
        """
        if not self.embedding or not query_embedding:
            return 0.0
        
        if len(self.embedding) != len(query_embedding):
            return 0.0
        
        # Dot product
        dot = sum(a * b for a, b in zip(self.embedding, query_embedding))
        
        # Scale by sqrt(dim)
        scale = math.sqrt(len(self.embedding))
        
        return dot / scale
    
    def update_embedding(self, new_embedding: list[float], blend: float = 0.5) -> None:
        """
        Update embedding via exponential moving average.
        """
        if not self.embedding:
            self.embedding = new_embedding
            self.embedding_dim = len(new_embedding)
            return
        
        if len(new_embedding) != len(self.embedding):
            return
        
        self.embedding = [
            blend * new + (1 - blend) * old
            for old, new in zip(self.embedding, new_embedding)
        ]
        self.last_updated = datetime.utcnow()
    
    # -------------------------------------------------------------------------
    # Symbolic Operations
    # -------------------------------------------------------------------------
    
    def add_symbol(self, key: str, value: Any) -> None:
        """Add symbolic metadata."""
        self.symbols[key] = value
        self.last_updated = datetime.utcnow()
    
    def match_symbols(self, query: dict[str, Any]) -> float:
        """
        Compute symbolic match score.
        
        Returns fraction of query keys that match.
        """
        if not query:
            return 1.0
        
        matches = sum(
            1 for k, v in query.items()
            if k in self.symbols and self.symbols[k] == v
        )
        
        return matches / len(query)
    
    # -------------------------------------------------------------------------
    # State
    # -------------------------------------------------------------------------
    
    def is_active(self) -> bool:
        """Check if trace is still active."""
        if self.strength < 0.01:
            return False
        
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age < self.ttl_seconds * 2  # Allow some grace period
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "trace_id": self.trace_id,
            "trace_type": self.trace_type.value,
            "location": self.location,
            "agent_id": self.agent_id,
            "embedding": self.embedding,
            "embedding_dim": self.embedding_dim,
            "symbols": self.symbols,
            "strength": self.strength,
            "strength_gradient": self.strength_gradient,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "visit_count": self.visit_count,
            "visitors": self.visitors,
            "attention_scores": self.attention_scores,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NeuralTrace:
        """Deserialize from dictionary."""
        trace = cls(
            trace_id=data["trace_id"],
            trace_type=TraceType(data["trace_type"]),
            location=data["location"],
            agent_id=data["agent_id"],
            embedding=data.get("embedding"),
            embedding_dim=data.get("embedding_dim", 0),
            symbols=data.get("symbols", {}),
            strength=data["strength"],
            strength_gradient=data.get("strength_gradient", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            ttl_seconds=data.get("ttl_seconds", 3600.0),
            visit_count=data["visit_count"],
            visitors=data["visitors"],
            attention_scores=data.get("attention_scores", {}),
        )
        return trace


# =============================================================================
# STIGMERGIC WORKSPACE (Shared Environment)
# =============================================================================

class StigmergicWorkspace:
    """
    A shared workspace for stigmergic coordination.
    
    This is the "environment" that agents modify indirectly.
    Implements proper AI/ML stigmergy patterns:
    
    1. **Marker-based**: Deposit neural traces
    2. **Sematectonic**: Modify structure/topology
    3. **Attention-based retrieval**: Find relevant traces
    4. **Gradient flow**: Backprop through traces
    """
    
    def __init__(
        self,
        workspace_id: str = "default",
        persist_dir: str | Path | None = None,
    ):
        self.workspace_id = workspace_id
        self.persist_dir = Path(persist_dir) if persist_dir else None
        
        # Trace storage by location (like a distributed hash table)
        self.traces: dict[str, list[NeuralTrace]] = {}
        
        # Global index for trace lookup
        self.trace_index: dict[str, NeuralTrace] = {}
        
        # Structure modifications (sematectonic)
        self.structure: dict[str, Any] = {}
        
        # Event listeners
        self._listeners: list[Callable[[str, NeuralTrace], None]] = []
        
        if self.persist_dir:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._load()
    
    # -------------------------------------------------------------------------
    # Marker-Based Stigmergy
    # -------------------------------------------------------------------------
    
    def deposit(
        self,
        trace_type: TraceType,
        location: str,
        agent_id: str,
        embedding: list[float] | None = None,
        symbols: dict[str, Any] | None = None,
        strength: float = 1.0,
    ) -> NeuralTrace:
        """
        Deposit a neural trace at a location.
        
        This is the core stigmergic operation: leave information
        that other agents can sense and respond to.
        """
        trace = NeuralTrace.create(
            trace_type=trace_type,
            location=location,
            agent_id=agent_id,
            embedding=embedding,
            symbols=symbols,
            strength=strength,
        )
        
        # Store by location
        if location not in self.traces:
            self.traces[location] = []
        self.traces[location].append(trace)
        
        # Index by ID
        self.trace_index[trace.trace_id] = trace
        
        self._emit("deposit", trace)
        self._persist_trace(trace)
        
        return trace
    
    def sense(
        self,
        location: str,
        query_embedding: list[float] | None = None,
        query_symbols: dict[str, Any] | None = None,
        trace_type: TraceType | None = None,
        top_k: int = 10,
    ) -> list[tuple[NeuralTrace, float]]:
        """
        Sense traces at a location using attention.
        
        Returns traces with their attention/relevance scores.
        """
        # Get traces at location (prefix match)
        candidates = []
        for loc, traces in self.traces.items():
            if loc.startswith(location) or location.startswith(loc):
                candidates.extend(traces)
        
        # Filter by type
        if trace_type:
            candidates = [t for t in candidates if t.trace_type == trace_type]
        
        # Apply decay and filter inactive
        active = []
        for trace in candidates:
            trace.decay()
            if trace.is_active():
                active.append(trace)
        
        if not active:
            return []
        
        # Compute attention scores
        scored = []
        for trace in active:
            # Combine neural and symbolic scores
            neural_score = 0.0
            if query_embedding and trace.embedding:
                neural_score = trace.compute_attention(query_embedding)
            
            symbolic_score = 0.0
            if query_symbols:
                symbolic_score = trace.match_symbols(query_symbols)
            
            # Weight: neural (0.7) + symbolic (0.3)
            if query_embedding and query_symbols:
                score = 0.7 * neural_score + 0.3 * symbolic_score
            elif query_embedding:
                score = neural_score
            elif query_symbols:
                score = symbolic_score
            else:
                score = trace.strength  # Fallback to strength
            
            scored.append((trace, score))
        
        # Sort by score and return top-k
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
    
    def reinforce(
        self,
        trace_id: str,
        signal: float = 1.0,
        visitor_id: str | None = None,
    ) -> float | None:
        """
        Reinforce a trace (positive or negative).
        
        The signal can be positive (reward) or negative (penalty).
        """
        trace = self.trace_index.get(trace_id)
        if not trace:
            return None
        
        new_strength = trace.reinforce(signal, visitor_id)
        self._emit("reinforce", trace)
        self._persist_trace(trace)
        
        return new_strength
    
    def backward(
        self,
        trace_id: str,
        upstream_gradient: float = 1.0,
    ) -> dict[str, float]:
        """
        Backpropagate gradient through a trace.
        
        Returns gradients for connected traces/agents.
        """
        trace = self.trace_index.get(trace_id)
        if not trace:
            return {}
        
        return trace.backward(upstream_gradient)
    
    # -------------------------------------------------------------------------
    # Sematectonic Stigmergy (Structure Modification)
    # -------------------------------------------------------------------------
    
    def modify_structure(
        self,
        key: str,
        value: Any,
        agent_id: str,
    ) -> None:
        """
        Modify shared structure (sematectonic stigmergy).
        
        This changes the "shape" of the environment itself.
        """
        self.structure[key] = {
            "value": value,
            "modified_by": agent_id,
            "modified_at": datetime.utcnow().isoformat(),
        }
    
    def read_structure(self, key: str) -> Any:
        """Read from shared structure."""
        entry = self.structure.get(key)
        return entry["value"] if entry else None
    
    # -------------------------------------------------------------------------
    # Coordination Patterns
    # -------------------------------------------------------------------------
    
    def claim(
        self,
        location: str,
        agent_id: str,
        ttl_seconds: float = 300.0,
    ) -> NeuralTrace | None:
        """
        Claim exclusive access to a location.
        
        Returns None if already claimed by another agent.
        """
        # Check existing claims
        existing = self.sense(
            location=location,
            trace_type=TraceType.CLAIM,
            top_k=1,
        )
        
        if existing:
            claim_trace, _ = existing[0]
            if claim_trace.agent_id != agent_id and claim_trace.is_active():
                return None  # Already claimed
        
        # Create claim
        return self.deposit(
            trace_type=TraceType.CLAIM,
            location=location,
            agent_id=agent_id,
            strength=5.0,
            symbols={"ttl": ttl_seconds},
        )
    
    def release(self, location: str, agent_id: str) -> bool:
        """Release a claim."""
        existing = self.sense(
            location=location,
            trace_type=TraceType.CLAIM,
            top_k=1,
        )
        
        if existing:
            claim_trace, _ = existing[0]
            if claim_trace.agent_id == agent_id:
                claim_trace.strength = 0  # Mark as inactive
                return True
        
        return False
    
    def handoff(
        self,
        location: str,
        from_agent: str,
        to_agent: str,
        context_embedding: list[float] | None = None,
        context_symbols: dict[str, Any] | None = None,
    ) -> NeuralTrace:
        """
        Hand off work from one agent to another.
        
        Includes context for continuity.
        """
        return self.deposit(
            trace_type=TraceType.HANDOFF,
            location=location,
            agent_id=from_agent,
            embedding=context_embedding,
            symbols={
                **(context_symbols or {}),
                "to_agent": to_agent,
            },
        )
    
    def broadcast(
        self,
        message_embedding: list[float] | None,
        message_symbols: dict[str, Any],
        agent_id: str,
    ) -> NeuralTrace:
        """
        Broadcast a message to all agents.
        """
        return self.deposit(
            trace_type=TraceType.BROADCAST,
            location="__broadcast__",
            agent_id=agent_id,
            embedding=message_embedding,
            symbols=message_symbols,
            strength=3.0,
        )
    
    # -------------------------------------------------------------------------
    # Topology Detection
    # -------------------------------------------------------------------------
    
    def get_topology(self) -> dict[str, Any]:
        """
        Analyze the emergent topology of traces.
        """
        # Group by location
        location_stats: dict[str, dict] = {}
        
        for location, traces in self.traces.items():
            active_traces = [t for t in traces if t.is_active()]
            if not active_traces:
                continue
            
            location_stats[location] = {
                "trace_count": len(active_traces),
                "total_strength": sum(t.strength for t in active_traces),
                "avg_embedding_dim": sum(t.embedding_dim for t in active_traces) / len(active_traces),
                "unique_agents": len(set(v for t in active_traces for v in t.visitors)),
                "types": list(set(t.trace_type.value for t in active_traces)),
            }
        
        # Sort by strength
        nodes = sorted(
            [{"location": loc, **stats} for loc, stats in location_stats.items()],
            key=lambda n: -n["total_strength"]
        )
        
        # Identify hubs (high connectivity)
        hubs = [n for n in nodes if n["trace_count"] >= 3]
        
        # Identify bridges (multiple agent types)
        bridges = [n for n in nodes if n["unique_agents"] >= 2]
        
        return {
            "total_traces": sum(len(ts) for ts in self.traces.values()),
            "active_locations": len(nodes),
            "nodes": nodes[:20],  # Top 20
            "hubs": hubs[:5],
            "bridges": bridges[:5],
        }
    
    # -------------------------------------------------------------------------
    # Event System
    # -------------------------------------------------------------------------
    
    def on(self, listener: Callable[[str, NeuralTrace], None]) -> None:
        """Register event listener."""
        self._listeners.append(listener)
    
    def _emit(self, event: str, trace: NeuralTrace) -> None:
        """Emit event to listeners."""
        for listener in self._listeners:
            try:
                listener(event, trace)
            except Exception:
                pass
    
    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------
    
    def _persist_trace(self, trace: NeuralTrace) -> None:
        """Persist trace to disk."""
        if not self.persist_dir:
            return
        
        trace_file = self.persist_dir / f"{trace.trace_id}.trace.json"
        with open(trace_file, "w") as f:
            json.dump(trace.to_dict(), f, indent=2)
    
    def _load(self) -> None:
        """Load traces from disk."""
        if not self.persist_dir:
            return
        
        for trace_file in self.persist_dir.glob("*.trace.json"):
            try:
                with open(trace_file) as f:
                    data = json.load(f)
                trace = NeuralTrace.from_dict(data)
                
                trace.decay()
                if trace.is_active():
                    if trace.location not in self.traces:
                        self.traces[trace.location] = []
                    self.traces[trace.location].append(trace)
                    self.trace_index[trace.trace_id] = trace
                else:
                    trace_file.unlink()
            except Exception:
                pass


# =============================================================================
# EMERGENT TOPOLOGY ANALYZER
# =============================================================================

class EmergentTopology:
    """
    Analyzes emergent patterns in stigmergic traces.
    
    Detects:
    - Hub formation (heavily-used locations)
    - Bridge nodes (connect different agent clusters)
    - Phase transitions (qualitative shifts)
    - Gradient flow patterns
    """
    
    def __init__(self, workspace: StigmergicWorkspace):
        self.workspace = workspace
        self._history: list[dict[str, Any]] = []
    
    def analyze(self) -> dict[str, Any]:
        """Full topology analysis."""
        topology = self.workspace.get_topology()
        
        # Compute additional metrics
        total_strength = sum(n["total_strength"] for n in topology["nodes"])
        total_gradient = sum(
            t.strength_gradient
            for traces in self.workspace.traces.values()
            for t in traces
            if t.is_active()
        )
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_traces": topology["total_traces"],
                "active_locations": topology["active_locations"],
                "total_strength": total_strength,
                "total_gradient_flow": total_gradient,
                "hub_count": len(topology["hubs"]),
                "bridge_count": len(topology["bridges"]),
            },
            "phase": self._detect_phase(topology),
            "gradient_flow": self._analyze_gradient_flow(),
            "hubs": topology["hubs"],
            "bridges": topology["bridges"],
        }
        
        self._history.append(result)
        if len(self._history) > 100:
            self._history = self._history[-100:]
        
        return result
    
    def _detect_phase(self, topology: dict) -> str:
        """Detect current phase of self-organization."""
        node_count = topology["active_locations"]
        hub_count = len(topology["hubs"])
        
        if node_count == 0:
            return "dormant"
        elif hub_count == 0:
            return "exploring"
        elif hub_count < 3:
            return "organizing"
        elif hub_count < 7:
            return "structured"
        else:
            return "crystallized"
    
    def _analyze_gradient_flow(self) -> dict[str, float]:
        """Analyze gradient flow through the workspace."""
        positive_flow = 0.0
        negative_flow = 0.0
        
        for traces in self.workspace.traces.values():
            for trace in traces:
                if trace.strength_gradient > 0:
                    positive_flow += trace.strength_gradient
                else:
                    negative_flow += abs(trace.strength_gradient)
        
        return {
            "positive": positive_flow,
            "negative": negative_flow,
            "net": positive_flow - negative_flow,
        }
    
    def visualize(self) -> str:
        """ASCII visualization of topology."""
        topology = self.workspace.get_topology()
        nodes = topology["nodes"][:10]
        
        if not nodes:
            return "No active traces in workspace"
        
        lines = [
            "ENTELECHEIA+ Stigmergic Topology (Neural)",
            "=" * 50
        ]
        
        max_strength = max(n["total_strength"] for n in nodes)
        
        for node in nodes:
            bar_len = int(25 * node["total_strength"] / max_strength)
            bar = "█" * bar_len
            
            # Icons: ⭐=hub, 🔗=bridge
            icon = ""
            if node["trace_count"] >= 3:
                icon += "⭐"
            if node["unique_agents"] >= 2:
                icon += "🔗"
            if not icon:
                icon = "  "
            
            lines.append(
                f"{icon} {node['location'][:18]:18} [{bar:25}] "
                f"s={node['total_strength']:.1f} t={node['trace_count']}"
            )
        
        lines.append("=" * 50)
        analysis = self.analyze()
        lines.append(f"Phase: {analysis['phase']}")
        lines.append(f"Gradient Flow: +{analysis['gradient_flow']['positive']:.1f} / -{analysis['gradient_flow']['negative']:.1f}")
        
        return "\n".join(lines)


# =============================================================================
# BACKWARD COMPATIBILITY ALIASES
# =============================================================================

# Keep old names for compatibility
PheromoneTrace = NeuralTrace
StigmergicCoordinator = StigmergicWorkspace
TopologyNode = dict  # Simplified
