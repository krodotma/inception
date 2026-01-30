"""
ENTELECHEIA+ Knowledge Compilation Layer

Compiles reactive knowledge into executable forms.
The surface detects structure, then compiles to actionable output.

Surface Structure Detection:
- Patterns in the reactive surface
- Emergent topology from traces
- Concept clusters from co-objects

Executable Form Generation:
- Skills: Executable procedures
- Rules: Conditional logic
- Plans: Step sequences
- Queries: Knowledge retrieval

Phase 5: Steps 151-180
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import re


# =============================================================================
# EXECUTABLE FORM TYPES
# =============================================================================

class ExecutableType(str, Enum):
    """Types of executable forms the compiler produces."""
    
    SKILL = "skill"           # Procedural skill
    RULE = "rule"             # Conditional rule
    PLAN = "plan"             # Sequential plan
    QUERY = "query"           # Knowledge query
    WORKFLOW = "workflow"     # Multi-step workflow
    TRANSFORMATION = "transformation"  # Data transformation
    CONSTRAINT = "constraint" # Invariant/constraint


# =============================================================================
# SURFACE STRUCTURE (Steps 151-160)
# =============================================================================

@dataclass
class SurfacePattern:
    """A pattern detected in the reactive surface."""
    
    pattern_id: str
    pattern_type: str  # "cluster", "chain", "hub", "bridge", "cycle"
    
    # Nodes involved
    nodes: list[str]
    
    # Pattern strength/confidence
    strength: float
    confidence: float
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)


class SurfaceStructureDetector:
    """
    Detects structural patterns in the reactive surface.
    
    Patterns:
    - Clusters: Dense groups of related concepts
    - Chains: Linear causal/temporal sequences
    - Hubs: Central nodes with many connections
    - Bridges: Nodes connecting different clusters
    - Cycles: Feedback loops
    """
    
    def detect_clusters(
        self,
        nodes: list[str],
        edges: list[tuple[str, str, float]],
        min_size: int = 3,
    ) -> list[SurfacePattern]:
        """
        Detect concept clusters using connectivity.
        """
        # Build adjacency
        adjacency: dict[str, list[str]] = {n: [] for n in nodes}
        for src, tgt, _ in edges:
            if src in adjacency:
                adjacency[src].append(tgt)
            if tgt in adjacency:
                adjacency[tgt].append(src)
        
        # Simple connected component detection
        visited = set()
        clusters = []
        
        for node in nodes:
            if node in visited:
                continue
            
            # BFS to find connected component
            component = []
            queue = [node]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                
                for neighbor in adjacency.get(current, []):
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if len(component) >= min_size:
                clusters.append(SurfacePattern(
                    pattern_id=f"cluster_{len(clusters)}",
                    pattern_type="cluster",
                    nodes=component,
                    strength=len(component) / len(nodes) if nodes else 0,
                    confidence=0.8,
                    metadata={"size": len(component)},
                ))
        
        return clusters
    
    def detect_chains(
        self,
        edges: list[tuple[str, str, float]],
        min_length: int = 3,
    ) -> list[SurfacePattern]:
        """
        Detect causal/sequential chains.
        """
        # Build forward adjacency (directed)
        forward: dict[str, list[str]] = {}
        for src, tgt, _ in edges:
            if src not in forward:
                forward[src] = []
            forward[src].append(tgt)
        
        # Find chain starting points (no incoming edges)
        has_incoming = set(tgt for _, tgt, _ in edges)
        starts = [src for src, _, _ in edges if src not in has_incoming]
        
        chains = []
        for start in starts:
            chain = [start]
            current = start
            
            while current in forward and len(forward[current]) == 1:
                next_node = forward[current][0]
                if next_node in chain:  # Cycle detection
                    break
                chain.append(next_node)
                current = next_node
            
            if len(chain) >= min_length:
                chains.append(SurfacePattern(
                    pattern_id=f"chain_{len(chains)}",
                    pattern_type="chain",
                    nodes=chain,
                    strength=len(chain) / 10,  # Normalize
                    confidence=0.75,
                    metadata={"length": len(chain)},
                ))
        
        return chains
    
    def detect_hubs(
        self,
        nodes: list[str],
        edges: list[tuple[str, str, float]],
        min_connections: int = 4,
    ) -> list[SurfacePattern]:
        """
        Detect hub nodes (high connectivity).
        """
        # Count connections per node
        connections: dict[str, int] = {n: 0 for n in nodes}
        for src, tgt, _ in edges:
            if src in connections:
                connections[src] += 1
            if tgt in connections:
                connections[tgt] += 1
        
        hubs = []
        for node, count in connections.items():
            if count >= min_connections:
                hubs.append(SurfacePattern(
                    pattern_id=f"hub_{len(hubs)}",
                    pattern_type="hub",
                    nodes=[node],
                    strength=count / 10,
                    confidence=0.85,
                    metadata={"connection_count": count},
                ))
        
        return sorted(hubs, key=lambda h: -h.strength)
    
    def detect_all(
        self,
        nodes: list[str],
        edges: list[tuple[str, str, float]],
    ) -> dict[str, list[SurfacePattern]]:
        """Detect all pattern types."""
        return {
            "clusters": self.detect_clusters(nodes, edges),
            "chains": self.detect_chains(edges),
            "hubs": self.detect_hubs(nodes, edges),
        }


# =============================================================================
# EXECUTABLE FORM (Steps 161-170)
# =============================================================================

@dataclass
class ExecutableForm:
    """
    An executable form compiled from knowledge.
    """
    
    form_id: str
    form_type: ExecutableType
    name: str
    description: str
    
    # The executable content
    content: dict[str, Any]
    
    # Source pattern(s)
    source_patterns: list[str] = field(default_factory=list)
    
    # Execution metadata
    confidence: float = 0.0
    priority: int = 0
    
    # Timestamps
    compiled_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_skill_script(self) -> str:
        """Generate shell script for skill-type forms."""
        if self.form_type != ExecutableType.SKILL:
            raise ValueError("Only SKILL types can generate scripts")
        
        steps = self.content.get("steps", [])
        
        lines = [
            "#!/bin/bash",
            f"# ENTELECHEIA+ Skill: {self.name}",
            f"# {self.description}",
            f"# Confidence: {self.confidence:.2f}",
            "",
        ]
        
        for i, step in enumerate(steps):
            lines.append(f"# Step {i+1}: {step.get('description', '')}")
            if "command" in step:
                lines.append(step["command"])
            lines.append("")
        
        return "\n".join(lines)
    
    def to_plan_yaml(self) -> str:
        """Generate YAML for plan-type forms."""
        if self.form_type != ExecutableType.PLAN:
            raise ValueError("Only PLAN types can generate YAML")
        
        steps = self.content.get("steps", [])
        
        lines = [
            f"# ENTELECHEIA+ Plan: {self.name}",
            f"name: {self.name}",
            f"description: {self.description}",
            f"confidence: {self.confidence}",
            "steps:",
        ]
        
        for i, step in enumerate(steps):
            lines.append(f"  - id: step_{i+1}")
            lines.append(f"    action: {step.get('action', 'unknown')}")
            if "params" in step:
                lines.append("    params:")
                for k, v in step["params"].items():
                    lines.append(f"      {k}: {v}")
        
        return "\n".join(lines)


@dataclass
class ExecutableRule:
    """
    A compiled rule (if-then logic).
    """
    
    rule_id: str
    name: str
    
    # Conditions (conjunctive)
    conditions: list[dict[str, Any]]
    
    # Consequent
    consequent: dict[str, Any]
    
    # Priority/weight
    priority: int = 0
    confidence: float = 0.8
    
    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate if conditions are met.
        """
        for condition in self.conditions:
            key = condition.get("key")
            operator = condition.get("op", "==")
            value = condition.get("value")
            
            actual = context.get(key)
            
            if operator == "==":
                if actual != value:
                    return False
            elif operator == "!=":
                if actual == value:
                    return False
            elif operator == ">":
                if not (actual and actual > value):
                    return False
            elif operator == "<":
                if not (actual and actual < value):
                    return False
            elif operator == "contains":
                if not (actual and value in actual):
                    return False
            elif operator == "exists":
                if actual is None:
                    return False
        
        return True
    
    def fire(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Fire the rule and return the consequent.
        """
        if not self.evaluate(context):
            return {}
        
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "consequent": self.consequent,
            "confidence": self.confidence,
        }


# =============================================================================
# KNOWLEDGE COMPILER (Steps 171-180)
# =============================================================================

class KnowledgeCompiler:
    """
    Compiles knowledge surface patterns into executable forms.
    
    Input: Surface patterns, traces, co-object graphs
    Output: Skills, rules, plans, workflows
    """
    
    def __init__(self):
        self.detector = SurfaceStructureDetector()
        self._form_counter = 0
    
    def _next_id(self) -> str:
        self._form_counter += 1
        return f"form_{self._form_counter:04d}"
    
    def compile_cluster_to_skill(
        self,
        cluster: SurfacePattern,
        concept_details: dict[str, dict[str, Any]] | None = None,
    ) -> ExecutableForm:
        """
        Compile a concept cluster into a skill.
        """
        concept_details = concept_details or {}
        
        # Extract concepts from cluster
        concepts = cluster.nodes
        
        # Generate skill steps from concepts
        steps = []
        for concept in concepts:
            details = concept_details.get(concept, {})
            steps.append({
                "description": f"Apply {concept}",
                "action": details.get("action", concept),
                "params": details.get("params", {}),
            })
        
        return ExecutableForm(
            form_id=self._next_id(),
            form_type=ExecutableType.SKILL,
            name=f"Skill: {concepts[0]} cluster",
            description=f"Skill derived from {len(concepts)} related concepts",
            content={"steps": steps, "concepts": concepts},
            source_patterns=[cluster.pattern_id],
            confidence=cluster.confidence,
        )
    
    def compile_chain_to_plan(
        self,
        chain: SurfacePattern,
        step_details: dict[str, dict[str, Any]] | None = None,
    ) -> ExecutableForm:
        """
        Compile a causal chain into a sequential plan.
        """
        step_details = step_details or {}
        
        steps = []
        for i, node in enumerate(chain.nodes):
            details = step_details.get(node, {})
            steps.append({
                "sequence": i + 1,
                "action": node,
                "description": details.get("description", f"Execute {node}"),
                "params": details.get("params", {}),
            })
        
        return ExecutableForm(
            form_id=self._next_id(),
            form_type=ExecutableType.PLAN,
            name=f"Plan: {chain.nodes[0]} → {chain.nodes[-1]}",
            description=f"Sequential plan with {len(steps)} steps",
            content={"steps": steps, "chain": chain.nodes},
            source_patterns=[chain.pattern_id],
            confidence=chain.confidence,
        )
    
    def compile_hub_to_workflow(
        self,
        hub: SurfacePattern,
        connected_nodes: list[str],
    ) -> ExecutableForm:
        """
        Compile a hub pattern into a workflow with branching.
        """
        hub_node = hub.nodes[0]
        
        # Create workflow with central dispatch
        branches = [
            {"target": node, "condition": f"needs_{node}"}
            for node in connected_nodes[:5]  # Limit branches
        ]
        
        return ExecutableForm(
            form_id=self._next_id(),
            form_type=ExecutableType.WORKFLOW,
            name=f"Workflow: {hub_node} dispatcher",
            description=f"Workflow centered on {hub_node} with {len(branches)} branches",
            content={
                "hub": hub_node,
                "branches": branches,
            },
            source_patterns=[hub.pattern_id],
            confidence=hub.confidence,
        )
    
    def compile_patterns_to_rules(
        self,
        patterns: list[SurfacePattern],
    ) -> list[ExecutableRule]:
        """
        Compile patterns into rules.
        """
        rules = []
        
        for pattern in patterns:
            if pattern.pattern_type == "chain" and len(pattern.nodes) >= 2:
                # Chain → if A then B rule
                for i in range(len(pattern.nodes) - 1):
                    rules.append(ExecutableRule(
                        rule_id=f"rule_{pattern.pattern_id}_{i}",
                        name=f"Rule: {pattern.nodes[i]} → {pattern.nodes[i+1]}",
                        conditions=[
                            {"key": "current", "op": "==", "value": pattern.nodes[i]},
                        ],
                        consequent={"next": pattern.nodes[i+1]},
                        confidence=pattern.confidence,
                    ))
            
            elif pattern.pattern_type == "hub":
                # Hub → dispatch rule
                hub_node = pattern.nodes[0]
                rules.append(ExecutableRule(
                    rule_id=f"rule_{pattern.pattern_id}_dispatch",
                    name=f"Rule: {hub_node} dispatch",
                    conditions=[
                        {"key": "at_hub", "op": "==", "value": hub_node},
                    ],
                    consequent={"action": "dispatch"},
                    priority=pattern.metadata.get("connection_count", 0),
                    confidence=pattern.confidence,
                ))
        
        return rules
    
    def compile_all(
        self,
        nodes: list[str],
        edges: list[tuple[str, str, float]],
    ) -> dict[str, list]:
        """
        Compile all detected patterns into executable forms.
        """
        # Detect patterns
        patterns = self.detector.detect_all(nodes, edges)
        
        results = {
            "skills": [],
            "plans": [],
            "workflows": [],
            "rules": [],
        }
        
        # Compile clusters → skills
        for cluster in patterns.get("clusters", []):
            skill = self.compile_cluster_to_skill(cluster)
            results["skills"].append(skill)
        
        # Compile chains → plans
        for chain in patterns.get("chains", []):
            plan = self.compile_chain_to_plan(chain)
            results["plans"].append(plan)
        
        # Compile hubs → workflows
        for hub in patterns.get("hubs", []):
            # Get connected nodes from edges
            hub_node = hub.nodes[0]
            connected = [
                tgt for src, tgt, _ in edges if src == hub_node
            ] + [
                src for src, tgt, _ in edges if tgt == hub_node
            ]
            
            workflow = self.compile_hub_to_workflow(hub, list(set(connected)))
            results["workflows"].append(workflow)
        
        # Compile all patterns → rules
        all_patterns = (
            patterns.get("clusters", []) +
            patterns.get("chains", []) +
            patterns.get("hubs", [])
        )
        rules = self.compile_patterns_to_rules(all_patterns)
        results["rules"] = rules
        
        return results
