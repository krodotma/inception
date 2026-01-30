"""
Agent Mesh Coordination System
Phase 12, Steps 261-280

Implements:
- Agent mesh topology types (261)
- Star topology coordinator (262)
- Peer-debate topology (263)
- Consensus protocols (264)
- Mesh state in context (265)
- Agent handoff with context (266)
- Mesh visualization data (267)
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional, Callable
from abc import ABC, abstractmethod


# =============================================================================
# Step 261: Agent Mesh Topology Types
# =============================================================================

class TopologyType(Enum):
    """Types of agent mesh topologies."""
    STAR = "star"           # Central coordinator
    PEER = "peer"           # Peer-to-peer
    RING = "ring"           # Ring topology
    MESH = "mesh"           # Full mesh
    DEBATE = "debate"       # Structured debate
    HIERARCHICAL = "hierarchical"  # Tree structure


class AgentRole(Enum):
    """Roles within a mesh."""
    COORDINATOR = "coordinator"
    WORKER = "worker"
    SPECIALIST = "specialist"
    VALIDATOR = "validator"
    SYNTHESIZER = "synthesizer"
    OBSERVER = "observer"


class MeshState(Enum):
    """States of the mesh."""
    FORMING = "forming"
    ACTIVE = "active"
    DELIBERATING = "deliberating"
    CONSENSUS = "consensus"
    DISBANDED = "disbanded"


@dataclass
class MeshAgent:
    """An agent in the mesh."""
    id: str
    name: str
    role: AgentRole
    capabilities: list[str] = field(default_factory=list)
    state: str = "idle"  # 'idle', 'active', 'busy', 'offline'
    
    # Position in topology
    neighbors: list[str] = field(default_factory=list)
    upstream_id: Optional[str] = None
    downstream_ids: list[str] = field(default_factory=list)
    
    # Performance
    reliability: float = 1.0
    load: float = 0.0
    last_heartbeat: Optional[datetime] = None


@dataclass
class MeshMessage:
    """A message in the mesh."""
    id: str
    from_agent_id: str
    to_agent_id: Optional[str]  # None for broadcast
    message_type: str  # 'task', 'result', 'vote', 'heartbeat', 'handoff'
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: int = 5  # 1-10
    requires_ack: bool = False
    acked: bool = False


# =============================================================================
# Step 262: Star Topology Coordinator
# =============================================================================

class StarCoordinator:
    """
    Star topology: Central coordinator with worker agents.
    """
    
    def __init__(self, coordinator_id: str, coordinator_name: str):
        self.coordinator = MeshAgent(
            id=coordinator_id,
            name=coordinator_name,
            role=AgentRole.COORDINATOR,
        )
        self.workers: dict[str, MeshAgent] = {}
        self.task_queue: list[dict[str, Any]] = []
        self.results: dict[str, Any] = {}
        self.state = MeshState.FORMING
    
    def add_worker(self, worker: MeshAgent) -> bool:
        """Add a worker to the star."""
        if worker.role not in [AgentRole.WORKER, AgentRole.SPECIALIST]:
            return False
        
        self.workers[worker.id] = worker
        worker.upstream_id = self.coordinator.id
        self.coordinator.downstream_ids.append(worker.id)
        
        return True
    
    def remove_worker(self, worker_id: str) -> bool:
        """Remove a worker."""
        if worker_id in self.workers:
            del self.workers[worker_id]
            self.coordinator.downstream_ids.remove(worker_id)
            return True
        return False
    
    def distribute_task(self, task: dict[str, Any]) -> Optional[str]:
        """Distribute a task to an available worker."""
        # Find available worker
        available = [w for w in self.workers.values() if w.state == "idle"]
        
        if not available:
            self.task_queue.append(task)
            return None
        
        # Select best worker (by reliability and load)
        best_worker = max(available, key=lambda w: w.reliability * (1 - w.load))
        
        best_worker.state = "busy"
        best_worker.load = min(best_worker.load + 0.2, 1.0)
        
        return best_worker.id
    
    def receive_result(self, worker_id: str, task_id: str, result: Any) -> None:
        """Receive result from a worker."""
        self.results[task_id] = {
            "worker_id": worker_id,
            "result": result,
            "timestamp": datetime.utcnow(),
        }
        
        if worker_id in self.workers:
            self.workers[worker_id].state = "idle"
            self.workers[worker_id].load = max(self.workers[worker_id].load - 0.2, 0.0)
        
        # Process queue
        if self.task_queue:
            next_task = self.task_queue.pop(0)
            self.distribute_task(next_task)
    
    def broadcast(self, message: MeshMessage) -> list[str]:
        """Broadcast message to all workers."""
        delivered_to = []
        for worker_id in self.workers:
            # Would send message via transport
            delivered_to.append(worker_id)
        return delivered_to
    
    def get_status(self) -> dict[str, Any]:
        """Get coordinator status."""
        return {
            "state": self.state.value,
            "total_workers": len(self.workers),
            "active_workers": sum(1 for w in self.workers.values() if w.state == "busy"),
            "queued_tasks": len(self.task_queue),
            "completed_results": len(self.results),
        }


# =============================================================================
# Step 263: Peer-Debate Topology
# =============================================================================

class DebatePosition(Enum):
    """Position in a debate."""
    PROPOSER = "proposer"
    OPPONENT = "opponent"
    NEUTRAL = "neutral"
    SYNTHESIZER = "synthesizer"


@dataclass
class DebateRound:
    """A round in the debate."""
    round_number: int
    speaker_id: str
    position: DebatePosition
    argument: str
    supporting_evidence: list[str] = field(default_factory=list)
    rebuttal_to: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PeerDebateTopology:
    """
    Peer-debate topology for adversarial reasoning.
    """
    
    def __init__(self, topic: str):
        self.topic = topic
        self.agents: dict[str, MeshAgent] = {}
        self.positions: dict[str, DebatePosition] = {}
        self.rounds: list[DebateRound] = []
        self.state = MeshState.FORMING
        
        # Debate configuration
        self.max_rounds = 6
        self.current_round = 0
        self.synthesis_threshold = 0.7  # Agreement threshold
    
    def add_debater(self, agent: MeshAgent, position: DebatePosition) -> bool:
        """Add a debater."""
        self.agents[agent.id] = agent
        self.positions[agent.id] = position
        return True
    
    def start_debate(self) -> bool:
        """Start the debate."""
        # Need at least proposer and opponent
        positions = set(self.positions.values())
        if DebatePosition.PROPOSER not in positions or DebatePosition.OPPONENT not in positions:
            return False
        
        self.state = MeshState.DELIBERATING
        return True
    
    def submit_argument(self, agent_id: str, argument: str, 
                        evidence: list[str] = None, rebuttal_to: int = None) -> Optional[DebateRound]:
        """Submit an argument."""
        if agent_id not in self.agents:
            return None
        
        if self.current_round >= self.max_rounds:
            return None
        
        self.current_round += 1
        
        round_obj = DebateRound(
            round_number=self.current_round,
            speaker_id=agent_id,
            position=self.positions[agent_id],
            argument=argument,
            supporting_evidence=evidence or [],
            rebuttal_to=rebuttal_to,
        )
        
        self.rounds.append(round_obj)
        return round_obj
    
    def request_synthesis(self, synthesizer_id: str) -> Optional[str]:
        """Request synthesis from a synthesizer agent."""
        if self.positions.get(synthesizer_id) != DebatePosition.SYNTHESIZER:
            return None
        
        # Collect arguments by position
        proposer_args = [r.argument for r in self.rounds if r.position == DebatePosition.PROPOSER]
        opponent_args = [r.argument for r in self.rounds if r.position == DebatePosition.OPPONENT]
        
        # Return arguments for synthesis (would be processed by agent)
        return f"Proposer: {'; '.join(proposer_args)}\nOpponent: {'; '.join(opponent_args)}"
    
    def conclude_debate(self, synthesis: str) -> dict[str, Any]:
        """Conclude the debate with a synthesis."""
        self.state = MeshState.CONSENSUS
        
        return {
            "topic": self.topic,
            "rounds": len(self.rounds),
            "synthesis": synthesis,
            "participants": len(self.agents),
        }
    
    def get_transcript(self) -> list[dict[str, Any]]:
        """Get debate transcript."""
        return [
            {
                "round": r.round_number,
                "speaker": self.agents[r.speaker_id].name if r.speaker_id in self.agents else "unknown",
                "position": r.position.value,
                "argument": r.argument,
            }
            for r in self.rounds
        ]


# =============================================================================
# Step 264: Consensus Protocols
# =============================================================================

class ConsensusType(Enum):
    """Types of consensus protocols."""
    MAJORITY = "majority"           # Simple majority
    SUPERMAJORITY = "supermajority" # 2/3 majority
    UNANIMOUS = "unanimous"         # All agree
    WEIGHTED = "weighted"           # Weighted by reliability
    RANKED = "ranked"               # Ranked choice


@dataclass
class Vote:
    """A vote from an agent."""
    agent_id: str
    choice: str
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reasoning: Optional[str] = None


class ConsensusProtocol:
    """
    Consensus protocol for multi-agent decision making.
    """
    
    def __init__(self, consensus_type: ConsensusType = ConsensusType.MAJORITY):
        self.consensus_type = consensus_type
        self.votes: list[Vote] = []
        self.options: list[str] = []
        self.decided: bool = False
        self.decision: Optional[str] = None
    
    def set_options(self, options: list[str]) -> None:
        """Set the options to vote on."""
        self.options = options
    
    def cast_vote(self, agent_id: str, choice: str, weight: float = 1.0, 
                  reasoning: str = None) -> bool:
        """Cast a vote."""
        if choice not in self.options:
            return False
        
        # Remove previous vote if any
        self.votes = [v for v in self.votes if v.agent_id != agent_id]
        
        self.votes.append(Vote(
            agent_id=agent_id,
            choice=choice,
            weight=weight,
            reasoning=reasoning,
        ))
        
        return True
    
    def check_consensus(self) -> Optional[str]:
        """Check if consensus has been reached."""
        if not self.votes:
            return None
        
        # Count votes by option
        vote_counts = {opt: 0.0 for opt in self.options}
        
        for vote in self.votes:
            if self.consensus_type == ConsensusType.WEIGHTED:
                vote_counts[vote.choice] += vote.weight
            else:
                vote_counts[vote.choice] += 1
        
        total = sum(vote_counts.values())
        if total == 0:
            return None
        
        # Apply consensus rule
        if self.consensus_type == ConsensusType.UNANIMOUS:
            for choice, count in vote_counts.items():
                if count == total:
                    self.decided = True
                    self.decision = choice
                    return choice
        
        elif self.consensus_type == ConsensusType.SUPERMAJORITY:
            for choice, count in vote_counts.items():
                if count / total >= 2/3:
                    self.decided = True
                    self.decision = choice
                    return choice
        
        else:  # MAJORITY or WEIGHTED
            winner = max(vote_counts.items(), key=lambda x: x[1])
            if winner[1] / total > 0.5:
                self.decided = True
                self.decision = winner[0]
                return winner[0]
        
        return None
    
    def get_vote_summary(self) -> dict[str, Any]:
        """Get summary of voting."""
        vote_counts = {opt: 0 for opt in self.options}
        total_weight = 0.0
        
        for vote in self.votes:
            vote_counts[vote.choice] += 1
            total_weight += vote.weight
        
        return {
            "options": self.options,
            "votes": vote_counts,
            "total_votes": len(self.votes),
            "total_weight": total_weight,
            "decided": self.decided,
            "decision": self.decision,
        }


# =============================================================================
# Step 265-266: Mesh State and Agent Handoff
# =============================================================================

@dataclass
class MeshContext:
    """Context that can be passed between agents in a mesh."""
    context_id: str
    mesh_id: str
    
    # Task context
    task_description: str
    task_state: dict[str, Any] = field(default_factory=dict)
    
    # Conversation history
    messages: list[MeshMessage] = field(default_factory=list)
    
    # Shared knowledge
    shared_facts: list[dict[str, Any]] = field(default_factory=list)
    shared_conclusions: list[str] = field(default_factory=list)
    
    # Handoff trail
    handoff_history: list[tuple[str, str, datetime]] = field(default_factory=list)
    
    def add_message(self, message: MeshMessage) -> None:
        """Add a message to context."""
        self.messages.append(message)
    
    def add_fact(self, fact: dict[str, Any]) -> None:
        """Add a shared fact."""
        self.shared_facts.append(fact)
    
    def add_conclusion(self, conclusion: str) -> None:
        """Add a shared conclusion."""
        self.shared_conclusions.append(conclusion)


class AgentHandoff:
    """
    Manages handoffs between agents with context preservation.
    """
    
    def __init__(self):
        self.active_handoffs: dict[str, dict[str, Any]] = {}
        self.handoff_log: list[dict[str, Any]] = []
    
    def initiate_handoff(
        self,
        from_agent_id: str,
        to_agent_id: str,
        context: MeshContext,
        reason: str,
    ) -> str:
        """Initiate a handoff."""
        handoff_id = hashlib.md5(f"{from_agent_id}{to_agent_id}{datetime.utcnow()}".encode()).hexdigest()[:8]
        
        # Update context
        context.handoff_history.append((from_agent_id, to_agent_id, datetime.utcnow()))
        
        self.active_handoffs[handoff_id] = {
            "from": from_agent_id,
            "to": to_agent_id,
            "context": context,
            "reason": reason,
            "initiated_at": datetime.utcnow(),
            "completed": False,
        }
        
        return handoff_id
    
    def complete_handoff(self, handoff_id: str, success: bool = True) -> bool:
        """Complete a handoff."""
        if handoff_id not in self.active_handoffs:
            return False
        
        handoff = self.active_handoffs[handoff_id]
        handoff["completed"] = True
        handoff["success"] = success
        handoff["completed_at"] = datetime.utcnow()
        
        self.handoff_log.append(handoff)
        del self.active_handoffs[handoff_id]
        
        return True
    
    def get_context(self, handoff_id: str) -> Optional[MeshContext]:
        """Get context for a handoff."""
        if handoff_id in self.active_handoffs:
            return self.active_handoffs[handoff_id]["context"]
        return None
    
    def get_handoff_chain(self, context_id: str) -> list[str]:
        """Get the chain of agents for a context."""
        for handoff in self.handoff_log:
            if handoff["context"].context_id == context_id:
                return [h[0] for h in handoff["context"].handoff_history]
        return []


# =============================================================================
# Step 267: Mesh Visualization Data
# =============================================================================

class MeshVisualizer:
    """
    Generate visualization data for agent meshes.
    """
    
    def to_graph_data(self, agents: dict[str, MeshAgent]) -> dict[str, Any]:
        """Convert mesh to graph visualization data."""
        nodes = []
        edges = []
        
        for agent in agents.values():
            nodes.append({
                "id": agent.id,
                "label": agent.name,
                "role": agent.role.value,
                "state": agent.state,
                "reliability": agent.reliability,
                "load": agent.load,
            })
            
            # Add edges for neighbors
            for neighbor_id in agent.neighbors:
                edges.append({
                    "source": agent.id,
                    "target": neighbor_id,
                    "type": "neighbor",
                })
            
            # Add edges for hierarchy
            if agent.upstream_id:
                edges.append({
                    "source": agent.upstream_id,
                    "target": agent.id,
                    "type": "hierarchy",
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": self._suggest_layout(agents),
        }
    
    def _suggest_layout(self, agents: dict[str, MeshAgent]) -> str:
        """Suggest layout based on topology."""
        # Check for coordinator
        coordinators = [a for a in agents.values() if a.role == AgentRole.COORDINATOR]
        if coordinators:
            return "radial"  # Star with coordinator in center
        
        # Check for hierarchical
        has_hierarchy = any(a.upstream_id for a in agents.values())
        if has_hierarchy:
            return "tree"
        
        return "force"  # Default force-directed
    
    def get_status_summary(self, agents: dict[str, MeshAgent]) -> dict[str, Any]:
        """Get status summary for visualization."""
        by_state = {}
        by_role = {}
        
        for agent in agents.values():
            by_state[agent.state] = by_state.get(agent.state, 0) + 1
            by_role[agent.role.value] = by_role.get(agent.role.value, 0) + 1
        
        return {
            "total_agents": len(agents),
            "by_state": by_state,
            "by_role": by_role,
            "avg_load": sum(a.load for a in agents.values()) / len(agents) if agents else 0,
            "avg_reliability": sum(a.reliability for a in agents.values()) / len(agents) if agents else 0,
        }


# =============================================================================
# Full Mesh Coordinator
# =============================================================================

class AgentMesh:
    """
    Complete agent mesh coordination system.
    """
    
    def __init__(self, mesh_id: str, topology: TopologyType = TopologyType.STAR):
        self.mesh_id = mesh_id
        self.topology = topology
        self.agents: dict[str, MeshAgent] = {}
        self.state = MeshState.FORMING
        
        # Components
        self.star_coordinator: Optional[StarCoordinator] = None
        self.debate_topology: Optional[PeerDebateTopology] = None
        self.consensus: Optional[ConsensusProtocol] = None
        self.handoff: AgentHandoff = AgentHandoff()
        self.visualizer: MeshVisualizer = MeshVisualizer()
        
        # Message handling
        self.message_queue: list[MeshMessage] = []
        self.message_handlers: dict[str, Callable] = {}
        
        # Initialize based on topology
        if topology == TopologyType.STAR:
            self.star_coordinator = StarCoordinator(f"{mesh_id}_coord", "Coordinator")
    
    def add_agent(self, agent: MeshAgent) -> bool:
        """Add an agent to the mesh."""
        self.agents[agent.id] = agent
        
        if self.topology == TopologyType.STAR and self.star_coordinator:
            return self.star_coordinator.add_worker(agent)
        
        return True
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the mesh."""
        if agent_id not in self.agents:
            return False
        
        del self.agents[agent_id]
        
        if self.topology == TopologyType.STAR and self.star_coordinator:
            self.star_coordinator.remove_worker(agent_id)
        
        return True
    
    def send_message(self, message: MeshMessage) -> bool:
        """Send a message within the mesh."""
        self.message_queue.append(message)
        
        # Route based on topology
        if message.to_agent_id:
            # Direct message
            if handler := self.message_handlers.get(message.message_type):
                handler(message)
        else:
            # Broadcast
            if self.star_coordinator:
                self.star_coordinator.broadcast(message)
        
        return True
    
    def initiate_handoff(self, from_id: str, to_id: str, task: str) -> Optional[str]:
        """Initiate a handoff between agents."""
        context = MeshContext(
            context_id=hashlib.md5(f"{task}{datetime.utcnow()}".encode()).hexdigest()[:8],
            mesh_id=self.mesh_id,
            task_description=task,
        )
        
        return self.handoff.initiate_handoff(from_id, to_id, context, "task_handoff")
    
    def start_debate(self, topic: str) -> bool:
        """Start a debate within the mesh."""
        self.debate_topology = PeerDebateTopology(topic)
        
        for agent in self.agents.values():
            if agent.role == AgentRole.COORDINATOR:
                self.debate_topology.add_debater(agent, DebatePosition.NEUTRAL)
            elif "proposer" in agent.capabilities:
                self.debate_topology.add_debater(agent, DebatePosition.PROPOSER)
            elif "opponent" in agent.capabilities:
                self.debate_topology.add_debater(agent, DebatePosition.OPPONENT)
        
        return self.debate_topology.start_debate()
    
    def start_consensus(self, options: list[str], protocol: ConsensusType = ConsensusType.MAJORITY) -> None:
        """Start a consensus process."""
        self.consensus = ConsensusProtocol(protocol)
        self.consensus.set_options(options)
        self.state = MeshState.DELIBERATING
    
    def get_visualization_data(self) -> dict[str, Any]:
        """Get data for visualization."""
        return self.visualizer.to_graph_data(self.agents)
    
    def get_status(self) -> dict[str, Any]:
        """Get mesh status."""
        status = {
            "mesh_id": self.mesh_id,
            "topology": self.topology.value,
            "state": self.state.value,
            "agent_count": len(self.agents),
            "message_queue": len(self.message_queue),
        }
        
        if self.star_coordinator:
            status["coordinator"] = self.star_coordinator.get_status()
        
        if self.consensus:
            status["consensus"] = self.consensus.get_vote_summary()
        
        status["visualization"] = self.visualizer.get_status_summary(self.agents)
        
        return status


# =============================================================================
# Factory Functions
# =============================================================================

def create_mesh(name: str, topology: TopologyType = TopologyType.STAR) -> AgentMesh:
    """Create a new agent mesh."""
    mesh_id = hashlib.md5(f"mesh_{name}".encode()).hexdigest()[:8]
    return AgentMesh(mesh_id, topology)


def create_mesh_agent(name: str, role: AgentRole, capabilities: list[str] = None) -> MeshAgent:
    """Create a mesh agent."""
    return MeshAgent(
        id=hashlib.md5(f"agent_{name}".encode()).hexdigest()[:8],
        name=name,
        role=role,
        capabilities=capabilities or [],
    )


__all__ = [
    # Topology
    "TopologyType",
    "AgentRole",
    "MeshState",
    "MeshAgent",
    "MeshMessage",
    
    # Star
    "StarCoordinator",
    
    # Debate
    "DebatePosition",
    "DebateRound",
    "PeerDebateTopology",
    
    # Consensus
    "ConsensusType",
    "Vote",
    "ConsensusProtocol",
    
    # Context/Handoff
    "MeshContext",
    "AgentHandoff",
    
    # Visualization
    "MeshVisualizer",
    
    # Main
    "AgentMesh",
    
    # Factory
    "create_mesh",
    "create_mesh_agent",
]
