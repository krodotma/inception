"""
ENTELECHEIA+ Co-Object Inference Engine

Infers related co-objects using rheomode transformation.
When you give the system an object, it figures out what
other objects are implicitly needed.

Phase 2: Steps 51-90
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import re


# =============================================================================
# CO-OBJECT TYPES
# =============================================================================

class CoObjectRelation(str, Enum):
    """How a co-object relates to the primary object."""
    
    SEMANTIC = "semantic"       # Meaning-similar
    CAUSAL = "causal"           # Causes or caused by
    DIALECTICAL = "dialectical" # Opposing/complementary
    STRUCTURAL = "structural"   # Part-of or contains
    TEMPORAL = "temporal"       # Before/after/during
    DEPENDENCY = "dependency"   # Required for


@dataclass
class CoObject:
    """A co-object inferred from a primary object."""
    
    concept: str                    # The co-object concept
    relation: CoObjectRelation      # How it relates
    relevance: float                # 0.0 to 1.0
    source: str                     # What triggered inference
    rheomode_form: str | None = None  # Gerund/flowing form
    evidence: list[str] = field(default_factory=list)


# =============================================================================
# RHEOMODE TRANSFORMER (Steps 51-60)
# =============================================================================

class RheoTransformer:
    """
    Transforms static concepts into flowing meaning.
    
    Based on David Bohm's Rheomode philosophy.
    """
    
    # Noun → Gerund mappings
    GERUNDS = {
        "thought": "thinking",
        "knowledge": "knowing",
        "understanding": "understanding",
        "analysis": "analyzing",
        "creation": "creating",
        "decision": "deciding",
        "observation": "observing",
        "perception": "perceiving",
        "belief": "believing",
        "definition": "defining",
        "concept": "conceiving",
        "memory": "remembering",
        "code": "coding",
        "design": "designing",
        "test": "testing",
        "build": "building",
        "deploy": "deploying",
        "document": "documenting",
        "review": "reviewing",
        "debug": "debugging",
        "refactor": "refactoring",
        "implement": "implementing",
        "plan": "planning",
        "learn": "learning",
    }
    
    def static_to_flowing(self, text: str) -> str:
        """Transform static nouns to gerunds."""
        result = text.lower()
        
        for noun, gerund in self.GERUNDS.items():
            # Replace "the X" with "the act of X-ing"
            result = re.sub(
                rf'\bthe {noun}\b',
                f'the act of {gerund}',
                result
            )
            # Replace standalone noun
            result = re.sub(rf'\b{noun}\b', gerund, result)
        
        return result
    
    def extract_frozen_concepts(self, text: str) -> list[str]:
        """Extract nouns that could be transformed."""
        text_lower = text.lower()
        frozen = []
        
        for noun in self.GERUNDS.keys():
            if noun in text_lower:
                frozen.append(noun)
        
        return frozen
    
    def get_flowing_form(self, concept: str) -> str:
        """Get the flowing/gerund form of a concept."""
        concept_lower = concept.lower().strip()
        return self.GERUNDS.get(concept_lower, f"{concept_lower}ing")


# =============================================================================
# CO-OBJECT INFERENCE ENGINE (Steps 61-70)
# =============================================================================

class CoObjectInferrer:
    """
    Infers co-objects from primary concepts.
    
    Uses semantic, causal, and dialectical relationships.
    """
    
    # Domain → Related concepts
    DOMAIN_COOBJECTS = {
        "coding": ["testing", "debugging", "documenting", "reviewing"],
        "testing": ["debugging", "coding", "deploying"],
        "designing": ["implementing", "planning", "reviewing"],
        "learning": ["practicing", "teaching", "understanding"],
        "planning": ["executing", "reviewing", "adapting"],
        "analyzing": ["synthesizing", "deciding", "understanding"],
        "building": ["testing", "deploying", "maintaining"],
        "thinking": ["knowing", "deciding", "creating"],
    }
    
    # Dialectical oppositions
    DIALECTICAL_PAIRS = {
        "thesis": "antithesis",
        "theory": "practice",
        "abstract": "concrete",
        "general": "specific",
        "simple": "complex",
        "static": "dynamic",
        "local": "global",
        "centralized": "decentralized",
    }
    
    def __init__(self):
        self.transformer = RheoTransformer()
    
    def infer_semantic(self, concept: str) -> list[CoObject]:
        """Infer semantically related co-objects."""
        flowing = self.transformer.get_flowing_form(concept)
        
        coobjects = []
        related = self.DOMAIN_COOBJECTS.get(flowing, [])
        
        for i, rel in enumerate(related):
            coobjects.append(CoObject(
                concept=rel,
                relation=CoObjectRelation.SEMANTIC,
                relevance=0.9 - (i * 0.1),
                source=f"semantic neighbor of '{flowing}'",
                rheomode_form=rel,
                evidence=[f"In same domain as {flowing}"],
            ))
        
        return coobjects
    
    def infer_causal(self, concept: str) -> list[CoObject]:
        """Infer causally related co-objects."""
        flowing = self.transformer.get_flowing_form(concept)
        
        # Simple causal chains
        CAUSAL_CHAINS = {
            "designing": [("implementing", 0.9), ("testing", 0.8)],
            "implementing": [("testing", 0.95), ("debugging", 0.85)],
            "testing": [("debugging", 0.9), ("deploying", 0.7)],
            "planning": [("executing", 0.95), ("reviewing", 0.8)],
            "learning": [("understanding", 0.9), ("applying", 0.8)],
        }
        
        coobjects = []
        chain = CAUSAL_CHAINS.get(flowing, [])
        
        for effect, relevance in chain:
            coobjects.append(CoObject(
                concept=effect,
                relation=CoObjectRelation.CAUSAL,
                relevance=relevance,
                source=f"causal effect of '{flowing}'",
                rheomode_form=effect,
                evidence=[f"{flowing} leads to {effect}"],
            ))
        
        return coobjects
    
    def infer_dialectical(self, concept: str) -> list[CoObject]:
        """Infer dialectically opposed co-objects."""
        concept_lower = concept.lower()
        
        coobjects = []
        
        # Direct opposition
        if concept_lower in self.DIALECTICAL_PAIRS:
            opposite = self.DIALECTICAL_PAIRS[concept_lower]
            coobjects.append(CoObject(
                concept=opposite,
                relation=CoObjectRelation.DIALECTICAL,
                relevance=0.95,
                source=f"dialectical opposite of '{concept}'",
                rheomode_form=self.transformer.get_flowing_form(opposite),
                evidence=[f"{concept} ↔ {opposite}"],
            ))
        
        # Reverse lookup
        for thesis, antithesis in self.DIALECTICAL_PAIRS.items():
            if concept_lower == antithesis:
                coobjects.append(CoObject(
                    concept=thesis,
                    relation=CoObjectRelation.DIALECTICAL,
                    relevance=0.95,
                    source=f"dialectical thesis of '{concept}'",
                    rheomode_form=self.transformer.get_flowing_form(thesis),
                    evidence=[f"{antithesis} ↔ {thesis}"],
                ))
        
        return coobjects
    
    def infer_all(
        self,
        concept: str,
        max_per_type: int = 3,
    ) -> list[CoObject]:
        """Infer all types of co-objects."""
        all_coobjects = []
        
        # Semantic
        semantic = self.infer_semantic(concept)[:max_per_type]
        all_coobjects.extend(semantic)
        
        # Causal
        causal = self.infer_causal(concept)[:max_per_type]
        all_coobjects.extend(causal)
        
        # Dialectical
        dialectical = self.infer_dialectical(concept)[:max_per_type]
        all_coobjects.extend(dialectical)
        
        # Sort by relevance
        return sorted(all_coobjects, key=lambda c: -c.relevance)


# =============================================================================
# CO-OBJECT GRAPH (Steps 71-80)
# =============================================================================

@dataclass
class CoObjectEdge:
    """An edge in the co-object graph."""
    
    source: str
    target: str
    relation: CoObjectRelation
    weight: float  # Edge weight = relevance
    metadata: dict[str, Any] = field(default_factory=dict)


class CoObjectGraph:
    """
    A graph of objects and their co-objects.
    
    Supports transitive inference and subgraph extraction.
    """
    
    def __init__(self):
        self.nodes: dict[str, dict[str, Any]] = {}  # node_id → metadata
        self.edges: list[CoObjectEdge] = []
        self.inferrer = CoObjectInferrer()
    
    def add_concept(self, concept: str, metadata: dict[str, Any] | None = None) -> str:
        """Add a concept node to the graph."""
        node_id = concept.lower().replace(" ", "_")
        self.nodes[node_id] = metadata or {"concept": concept}
        return node_id
    
    def add_edge(
        self,
        source: str,
        target: str,
        relation: CoObjectRelation,
        weight: float = 1.0,
    ) -> CoObjectEdge:
        """Add an edge between nodes."""
        edge = CoObjectEdge(
            source=source,
            target=target,
            relation=relation,
            weight=weight,
        )
        self.edges.append(edge)
        return edge
    
    def expand_with_coobjects(self, concept: str, depth: int = 1) -> list[str]:
        """
        Expand a concept by inferring its co-objects.
        
        Returns list of newly added node IDs.
        """
        if depth <= 0:
            return []
        
        # Ensure source exists
        source_id = self.add_concept(concept)
        
        # Infer co-objects
        coobjects = self.inferrer.infer_all(concept)
        
        new_nodes = []
        for co in coobjects:
            target_id = self.add_concept(co.concept)
            new_nodes.append(target_id)
            
            self.add_edge(
                source=source_id,
                target=target_id,
                relation=co.relation,
                weight=co.relevance,
            )
        
        # Recursive expansion
        if depth > 1:
            for node_id in new_nodes[:3]:  # Limit expansion
                self.expand_with_coobjects(node_id, depth - 1)
        
        return new_nodes
    
    def get_neighbors(self, node_id: str) -> list[tuple[str, CoObjectEdge]]:
        """Get all neighbors of a node."""
        neighbors = []
        for edge in self.edges:
            if edge.source == node_id:
                neighbors.append((edge.target, edge))
            elif edge.target == node_id:
                neighbors.append((edge.source, edge))
        return neighbors
    
    def get_subgraph(self, root: str, max_depth: int = 2) -> dict[str, Any]:
        """Extract a subgraph centered on a node."""
        visited = set()
        nodes = []
        edges = []
        
        def traverse(node_id: str, depth: int):
            if depth > max_depth or node_id in visited:
                return
            visited.add(node_id)
            
            if node_id in self.nodes:
                nodes.append({"id": node_id, **self.nodes[node_id]})
            
            for neighbor_id, edge in self.get_neighbors(node_id):
                edges.append({
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation.value,
                    "weight": edge.weight,
                })
                traverse(neighbor_id, depth + 1)
        
        traverse(root, 0)
        
        return {
            "root": root,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
    
    def to_dict(self) -> dict[str, Any]:
        """Export graph to dictionary."""
        return {
            "nodes": list(self.nodes.keys()),
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "relation": e.relation.value,
                    "weight": e.weight,
                }
                for e in self.edges
            ],
        }
