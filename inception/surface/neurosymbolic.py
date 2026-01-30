"""
ENTELECHEIA+ Neurosymbolic Bridge Layer

Bidirectional transformations between neural and symbolic representations.
Enables hybrid reasoning that combines the strengths of both paradigms.

Neural → Symbolic:
- Embedding → Concept grounding
- Cluster → Category inference
- Attention → Salience extraction

Symbolic → Neural:
- Concept → Embedding mapping
- Rule → Soft constraint
- Relation → Vector operation

Hybrid Reasoning:
- Neural-first with symbolic verification
- Symbolic-first with neural fallback
- Interleaved reasoning

Phase 4: Steps 121-150
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Protocol
import math


# =============================================================================
# REASONING MODES
# =============================================================================

class ReasoningMode(str, Enum):
    """Available hybrid reasoning modes."""
    
    NEURAL_FIRST = "neural_first"       # Start neural, verify symbolic
    SYMBOLIC_FIRST = "symbolic_first"   # Start symbolic, ground neural
    INTERLEAVED = "interleaved"         # Alternate between modes
    PARALLEL = "parallel"               # Run both, reconcile
    ADAPTIVE = "adaptive"               # Choose based on confidence


# =============================================================================
# GROUNDING RESULT
# =============================================================================

@dataclass
class GroundingResult:
    """Result of neural→symbolic grounding."""
    
    success: bool
    concept: str | None
    confidence: float
    explanation: str
    intermediate_steps: list[dict[str, Any]] = field(default_factory=list)
    
    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.8


@dataclass
class EmbeddingResult:
    """Result of symbolic→neural embedding."""
    
    success: bool
    embedding: list[float] | None
    dimension: int
    explanation: str
    source_concept: str


# =============================================================================
# NEURAL → SYMBOLIC BRIDGE (Steps 121-130)
# =============================================================================

class NeuralToSymbolicBridge:
    """
    Transform neural representations to symbolic concepts.
    
    Key operations:
    - embed_to_concept: Ground embedding in concept space
    - cluster_to_category: Map neural clusters to categories
    - attention_to_salience: Extract importance from attention
    - confidence_to_probability: Neural confidence → logical probability
    """
    
    def __init__(
        self,
        concept_embeddings: dict[str, list[float]] | None = None,
        similarity_threshold: float = 0.7,
    ):
        # Concept → embedding mapping (for nearest neighbor lookup)
        self.concept_embeddings = concept_embeddings or {}
        self.similarity_threshold = similarity_threshold
        
        # Built-in concept embeddings (simplified, would be learned)
        self._init_default_concepts()
    
    def _init_default_concepts(self) -> None:
        """Initialize default concept embeddings."""
        # Simplified: use hash-based pseudo-embeddings
        # In production, these would be learned embeddings
        default_concepts = [
            "code", "test", "design", "build", "deploy",
            "analyze", "debug", "document", "review", "plan",
            "idea", "project", "domain", "article", "video",
            "theory", "practice", "abstract", "concrete",
        ]
        
        for concept in default_concepts:
            if concept not in self.concept_embeddings:
                self.concept_embeddings[concept] = self._pseudo_embed(concept)
    
    def _pseudo_embed(self, text: str, dim: int = 64) -> list[float]:
        """Generate pseudo-embedding from text (for demo purposes)."""
        # Hash-based pseudo-embedding
        import hashlib
        h = hashlib.sha256(text.lower().encode()).digest()
        
        embedding = []
        for i in range(dim):
            byte_val = h[i % len(h)]
            embedding.append((byte_val - 128) / 128.0)
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity."""
        if len(a) != len(b):
            return 0.0
        
        dot = sum(x*y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x*x for x in a))
        norm_b = math.sqrt(sum(x*x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot / (norm_a * norm_b)
    
    def embed_to_concept(
        self,
        embedding: list[float],
        top_k: int = 3,
    ) -> GroundingResult:
        """
        Ground an embedding in concept space.
        
        Finds the nearest concept(s) to the embedding.
        """
        if not embedding:
            return GroundingResult(
                success=False,
                concept=None,
                confidence=0.0,
                explanation="Empty embedding provided",
            )
        
        # Find nearest concepts
        similarities = []
        for concept, concept_emb in self.concept_embeddings.items():
            sim = self._cosine_similarity(embedding, concept_emb)
            similarities.append((concept, sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: -x[1])
        top = similarities[:top_k]
        
        if not top or top[0][1] < self.similarity_threshold:
            return GroundingResult(
                success=False,
                concept=None,
                confidence=top[0][1] if top else 0.0,
                explanation="No concept above similarity threshold",
                intermediate_steps=[
                    {"candidates": [{"concept": c, "similarity": s} for c, s in top]}
                ],
            )
        
        best_concept, best_sim = top[0]
        
        return GroundingResult(
            success=True,
            concept=best_concept,
            confidence=best_sim,
            explanation=f"Grounded to '{best_concept}' with similarity {best_sim:.3f}",
            intermediate_steps=[
                {"candidates": [{"concept": c, "similarity": s} for c, s in top]}
            ],
        )
    
    def cluster_to_category(
        self,
        cluster_embeddings: list[list[float]],
        cluster_label: str | None = None,
    ) -> GroundingResult:
        """
        Map a cluster of embeddings to a category concept.
        """
        if not cluster_embeddings:
            return GroundingResult(
                success=False,
                concept=None,
                confidence=0.0,
                explanation="Empty cluster provided",
            )
        
        # Compute centroid
        dim = len(cluster_embeddings[0])
        centroid = [0.0] * dim
        
        for emb in cluster_embeddings:
            for i, val in enumerate(emb):
                centroid[i] += val
        
        centroid = [v / len(cluster_embeddings) for v in centroid]
        
        # Ground centroid to concept
        result = self.embed_to_concept(centroid)
        result.intermediate_steps.insert(0, {
            "operation": "cluster_centroid",
            "cluster_size": len(cluster_embeddings),
        })
        
        return result
    
    def attention_to_salience(
        self,
        attention_weights: list[float],
        tokens: list[str],
        threshold: float = 0.1,
    ) -> list[tuple[str, float]]:
        """
        Extract salient tokens from attention weights.
        """
        if len(attention_weights) != len(tokens):
            return []
        
        # Normalize attention
        total = sum(attention_weights)
        if total > 0:
            normalized = [w / total for w in attention_weights]
        else:
            normalized = attention_weights
        
        # Filter by threshold and sort
        salient = [
            (token, weight)
            for token, weight in zip(tokens, normalized)
            if weight >= threshold
        ]
        
        return sorted(salient, key=lambda x: -x[1])
    
    def confidence_to_probability(
        self,
        confidence: float,
        calibration: str = "platt",
    ) -> float:
        """
        Convert neural confidence to calibrated probability.
        
        Neural networks are often overconfident; this applies calibration.
        """
        if calibration == "platt":
            # Platt scaling (simplified)
            # P = 1 / (1 + exp(A*confidence + B))
            # Using default A=-1, B=0 (identity sigmoid)
            return 1.0 / (1.0 + math.exp(-confidence))
        
        elif calibration == "temperature":
            # Temperature scaling
            temperature = 1.5  # Cool down overconfidence
            return 1.0 / (1.0 + math.exp(-confidence / temperature))
        
        else:
            # No calibration
            return confidence
    
    def register_concept(self, concept: str, embedding: list[float]) -> None:
        """Register a new concept with its embedding."""
        self.concept_embeddings[concept] = embedding


# =============================================================================
# SYMBOLIC → NEURAL BRIDGE (Steps 131-140)
# =============================================================================

class SymbolicToNeuralBridge:
    """
    Transform symbolic concepts to neural representations.
    
    Key operations:
    - concept_to_embed: Map concept to embedding
    - relation_to_operation: Symbolic relation → vector operation
    - rule_to_constraint: Logical rule → soft constraint
    - proof_to_confidence: Derivation → confidence score
    """
    
    def __init__(
        self,
        embedding_dim: int = 64,
        concept_embeddings: dict[str, list[float]] | None = None,
    ):
        self.embedding_dim = embedding_dim
        self.concept_embeddings = concept_embeddings or {}
        
        # Relation embeddings (for relation → operation)
        self.relation_embeddings: dict[str, list[float]] = {}
        self._init_default_relations()
    
    def _init_default_relations(self) -> None:
        """Initialize default relation embeddings."""
        relations = [
            "is_a", "has_a", "part_of", "causes", "follows",
            "similar_to", "opposite_of", "instance_of", "depends_on",
        ]
        
        for rel in relations:
            self.relation_embeddings[rel] = self._pseudo_embed(rel)
    
    def _pseudo_embed(self, text: str) -> list[float]:
        """Generate pseudo-embedding."""
        import hashlib
        h = hashlib.sha256(text.lower().encode()).digest()
        
        embedding = []
        for i in range(self.embedding_dim):
            byte_val = h[i % len(h)]
            embedding.append((byte_val - 128) / 128.0)
        
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def concept_to_embed(self, concept: str) -> EmbeddingResult:
        """
        Map a symbolic concept to its neural embedding.
        """
        if concept in self.concept_embeddings:
            return EmbeddingResult(
                success=True,
                embedding=self.concept_embeddings[concept],
                dimension=len(self.concept_embeddings[concept]),
                explanation=f"Retrieved cached embedding for '{concept}'",
                source_concept=concept,
            )
        
        # Generate embedding for new concept
        embedding = self._pseudo_embed(concept)
        self.concept_embeddings[concept] = embedding
        
        return EmbeddingResult(
            success=True,
            embedding=embedding,
            dimension=len(embedding),
            explanation=f"Generated new embedding for '{concept}'",
            source_concept=concept,
        )
    
    def relation_to_operation(
        self,
        subject: str,
        relation: str,
        obj: str,
    ) -> list[float]:
        """
        Convert symbolic relation to vector operation.
        
        Uses translation-based approach: subject + relation ≈ object
        (Similar to TransE in knowledge graph embeddings)
        """
        subj_emb = self.concept_to_embed(subject).embedding
        rel_emb = self.relation_embeddings.get(
            relation,
            self._pseudo_embed(relation)
        )
        
        if not subj_emb or not rel_emb:
            return []
        
        # subject + relation = expected_object
        expected_obj = [s + r for s, r in zip(subj_emb, rel_emb)]
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in expected_obj))
        if norm > 0:
            expected_obj = [x / norm for x in expected_obj]
        
        return expected_obj
    
    def rule_to_constraint(
        self,
        rule: dict[str, Any],
        weight: float = 1.0,
    ) -> dict[str, Any]:
        """
        Convert logical rule to soft constraint.
        
        Rule format: {"if": [conditions], "then": conclusion}
        Returns constraint that can be used in neural optimization.
        """
        conditions = rule.get("if", [])
        conclusion = rule.get("then")
        
        # Embed conditions and conclusion
        condition_embeddings = [
            self.concept_to_embed(c).embedding
            for c in conditions
            if isinstance(c, str)
        ]
        
        conclusion_embedding = None
        if conclusion:
            conclusion_embedding = self.concept_to_embed(conclusion).embedding
        
        return {
            "type": "soft_constraint",
            "conditions": condition_embeddings,
            "conclusion": conclusion_embedding,
            "weight": weight,
            "original_rule": rule,
        }
    
    def proof_to_confidence(
        self,
        proof_steps: list[dict[str, Any]],
        base_confidence: float = 0.9,
        decay_per_step: float = 0.02,
    ) -> float:
        """
        Convert proof derivation to confidence score.
        
        Longer proofs have slightly lower confidence.
        """
        num_steps = len(proof_steps)
        
        # Decay confidence for longer proofs
        confidence = base_confidence * (1.0 - decay_per_step * num_steps)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))
    
    def register_concept(self, concept: str, embedding: list[float]) -> None:
        """Register a concept with its embedding."""
        self.concept_embeddings[concept] = embedding


# =============================================================================
# HYBRID REASONER (Steps 141-150)
# =============================================================================

@dataclass
class ReasoningStep:
    """A step in hybrid reasoning."""
    
    step_num: int
    mode: str  # "neural" or "symbolic"
    action: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    confidence: float
    duration_ms: float = 0.0


@dataclass
class ReasoningResult:
    """Result of hybrid reasoning."""
    
    success: bool
    answer: Any
    confidence: float
    mode_used: ReasoningMode
    steps: list[ReasoningStep] = field(default_factory=list)
    explanation: str = ""


class HybridReasoner:
    """
    Hybrid reasoning combining neural and symbolic approaches.
    
    Modes:
    - NEURAL_FIRST: Start with neural, verify symbolically
    - SYMBOLIC_FIRST: Start with symbolic, ground neurally
    - INTERLEAVED: Alternate between modes
    - PARALLEL: Run both, reconcile results
    - ADAPTIVE: Choose based on query characteristics
    """
    
    def __init__(
        self,
        neural_bridge: NeuralToSymbolicBridge | None = None,
        symbolic_bridge: SymbolicToNeuralBridge | None = None,
    ):
        self.neural_bridge = neural_bridge or NeuralToSymbolicBridge()
        self.symbolic_bridge = symbolic_bridge or SymbolicToNeuralBridge()
    
    def reason(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        mode: ReasoningMode = ReasoningMode.ADAPTIVE,
        max_steps: int = 5,
    ) -> ReasoningResult:
        """
        Perform hybrid reasoning on a query.
        """
        context = context or {}
        
        # Select mode if adaptive
        if mode == ReasoningMode.ADAPTIVE:
            mode = self._select_mode(query, context)
        
        # Execute appropriate reasoning strategy
        if mode == ReasoningMode.NEURAL_FIRST:
            return self._neural_first(query, context, max_steps)
        elif mode == ReasoningMode.SYMBOLIC_FIRST:
            return self._symbolic_first(query, context, max_steps)
        elif mode == ReasoningMode.INTERLEAVED:
            return self._interleaved(query, context, max_steps)
        elif mode == ReasoningMode.PARALLEL:
            return self._parallel(query, context, max_steps)
        else:
            return self._neural_first(query, context, max_steps)
    
    def _select_mode(
        self,
        query: str,
        context: dict[str, Any],
    ) -> ReasoningMode:
        """
        Select reasoning mode based on query characteristics.
        """
        query_lower = query.lower()
        
        # Keywords suggesting symbolic reasoning
        symbolic_keywords = [
            "prove", "must", "always", "never", "if", "then",
            "exactly", "precisely", "logically", "deduce",
        ]
        
        # Keywords suggesting neural reasoning
        neural_keywords = [
            "like", "similar", "creative", "explore", "suggest",
            "might", "could", "possibly", "brainstorm",
        ]
        
        symbolic_score = sum(1 for kw in symbolic_keywords if kw in query_lower)
        neural_score = sum(1 for kw in neural_keywords if kw in query_lower)
        
        if symbolic_score > neural_score:
            return ReasoningMode.SYMBOLIC_FIRST
        elif neural_score > symbolic_score:
            return ReasoningMode.NEURAL_FIRST
        else:
            return ReasoningMode.INTERLEAVED
    
    def _neural_first(
        self,
        query: str,
        context: dict[str, Any],
        max_steps: int,
    ) -> ReasoningResult:
        """Neural-first reasoning with symbolic verification."""
        steps = []
        
        # Step 1: Embed query
        query_embedding = self.symbolic_bridge._pseudo_embed(query)
        steps.append(ReasoningStep(
            step_num=1,
            mode="neural",
            action="embed_query",
            input_data={"query": query},
            output_data={"embedding_dim": len(query_embedding)},
            confidence=0.9,
        ))
        
        # Step 2: Ground to concept
        grounding = self.neural_bridge.embed_to_concept(query_embedding)
        steps.append(ReasoningStep(
            step_num=2,
            mode="neural",
            action="ground_to_concept",
            input_data={"embedding_dim": len(query_embedding)},
            output_data={
                "concept": grounding.concept,
                "confidence": grounding.confidence,
            },
            confidence=grounding.confidence,
        ))
        
        # Step 3: Symbolic verification
        verified = grounding.success and grounding.confidence >= 0.7
        steps.append(ReasoningStep(
            step_num=3,
            mode="symbolic",
            action="verify_grounding",
            input_data={"concept": grounding.concept},
            output_data={"verified": verified},
            confidence=grounding.confidence if verified else 0.3,
        ))
        
        return ReasoningResult(
            success=verified,
            answer=grounding.concept,
            confidence=grounding.confidence if verified else 0.3,
            mode_used=ReasoningMode.NEURAL_FIRST,
            steps=steps,
            explanation=grounding.explanation,
        )
    
    def _symbolic_first(
        self,
        query: str,
        context: dict[str, Any],
        max_steps: int,
    ) -> ReasoningResult:
        """Symbolic-first reasoning with neural grounding."""
        steps = []
        
        # Step 1: Parse query symbolically
        # (Simplified: extract key terms)
        terms = [t.strip() for t in query.lower().split() if len(t) > 3]
        steps.append(ReasoningStep(
            step_num=1,
            mode="symbolic",
            action="parse_query",
            input_data={"query": query},
            output_data={"terms": terms},
            confidence=0.85,
        ))
        
        # Step 2: Get embeddings for terms
        embeddings = {}
        for term in terms[:5]:  # Limit
            result = self.symbolic_bridge.concept_to_embed(term)
            if result.success:
                embeddings[term] = result.embedding
        
        steps.append(ReasoningStep(
            step_num=2,
            mode="symbolic",
            action="embed_terms",
            input_data={"terms": terms[:5]},
            output_data={"embedded_count": len(embeddings)},
            confidence=0.8,
        ))
        
        # Step 3: Neural grounding
        if embeddings:
            # Average embeddings
            dim = len(next(iter(embeddings.values())))
            avg_emb = [0.0] * dim
            for emb in embeddings.values():
                for i, v in enumerate(emb):
                    avg_emb[i] += v
            avg_emb = [v / len(embeddings) for v in avg_emb]
            
            grounding = self.neural_bridge.embed_to_concept(avg_emb)
            final_concept = grounding.concept
            final_confidence = grounding.confidence
        else:
            final_concept = None
            final_confidence = 0.3
        
        steps.append(ReasoningStep(
            step_num=3,
            mode="neural",
            action="ground_result",
            input_data={"embedding_count": len(embeddings)},
            output_data={"concept": final_concept},
            confidence=final_confidence,
        ))
        
        return ReasoningResult(
            success=final_concept is not None,
            answer=final_concept,
            confidence=final_confidence,
            mode_used=ReasoningMode.SYMBOLIC_FIRST,
            steps=steps,
            explanation=f"Parsed into {len(terms)} terms, grounded to '{final_concept}'",
        )
    
    def _interleaved(
        self,
        query: str,
        context: dict[str, Any],
        max_steps: int,
    ) -> ReasoningResult:
        """Interleaved neural-symbolic reasoning."""
        steps = []
        current_data: dict[str, Any] = {"query": query}
        
        modes = ["neural", "symbolic"] * (max_steps // 2 + 1)
        
        for i, mode in enumerate(modes[:max_steps]):
            if mode == "neural":
                # Neural step: embed or ground
                if "embedding" not in current_data:
                    emb = self.symbolic_bridge._pseudo_embed(query)
                    current_data["embedding"] = emb
                    action = "embed"
                else:
                    grounding = self.neural_bridge.embed_to_concept(current_data["embedding"])
                    current_data["concept"] = grounding.concept
                    current_data["confidence"] = grounding.confidence
                    action = "ground"
            else:
                # Symbolic step: verify or expand
                if "concept" in current_data:
                    # Verify concept
                    current_data["verified"] = current_data["confidence"] >= 0.7
                    action = "verify"
                else:
                    # Parse terms
                    current_data["terms"] = query.split()[:5]
                    action = "parse"
            
            steps.append(ReasoningStep(
                step_num=i + 1,
                mode=mode,
                action=action,
                input_data={"keys": list(current_data.keys())},
                output_data=dict(current_data),
                confidence=current_data.get("confidence", 0.5),
            ))
        
        final_confidence = current_data.get("confidence", 0.5)
        
        return ReasoningResult(
            success=current_data.get("verified", False),
            answer=current_data.get("concept"),
            confidence=final_confidence,
            mode_used=ReasoningMode.INTERLEAVED,
            steps=steps,
            explanation=f"Interleaved {len(steps)} steps",
        )
    
    def _parallel(
        self,
        query: str,
        context: dict[str, Any],
        max_steps: int,
    ) -> ReasoningResult:
        """Run neural and symbolic in parallel, reconcile."""
        # Run both paths
        neural_result = self._neural_first(query, context, max_steps // 2)
        symbolic_result = self._symbolic_first(query, context, max_steps // 2)
        
        # Reconcile
        if neural_result.confidence >= symbolic_result.confidence:
            winner = neural_result
            loser = symbolic_result
        else:
            winner = symbolic_result
            loser = neural_result
        
        # Combine steps
        all_steps = []
        for step in winner.steps:
            step.step_num = len(all_steps) + 1
            all_steps.append(step)
        for step in loser.steps:
            step.step_num = len(all_steps) + 1
            all_steps.append(step)
        
        # Boost confidence if both agree
        final_confidence = winner.confidence
        if winner.answer == loser.answer:
            final_confidence = min(1.0, final_confidence * 1.2)
        
        return ReasoningResult(
            success=winner.success,
            answer=winner.answer,
            confidence=final_confidence,
            mode_used=ReasoningMode.PARALLEL,
            steps=all_steps,
            explanation=f"Parallel reasoning: neural={neural_result.confidence:.2f}, symbolic={symbolic_result.confidence:.2f}",
        )
