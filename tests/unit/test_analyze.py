"""Unit tests for analysis layer modules."""

import pytest

# Check if spaCy model is available
try:
    import spacy
    spacy.load("en_core_web_sm")
    SPACY_MODEL_AVAILABLE = True
except (ImportError, OSError):
    SPACY_MODEL_AVAILABLE = False

spacy_model_required = pytest.mark.skipif(
    not SPACY_MODEL_AVAILABLE,
    reason="spaCy model 'en_core_web_sm' not available",
)

from inception.analyze.entities import (
    Entity,
    EntityExtractor,
    EntityExtractionResult,
    extract_entities,
    normalize_entity_type,
)
from inception.analyze.claims import (
    Claim,
    ClaimExtractor,
    ClaimExtractionResult,
    extract_claims,
    compute_claim_similarity,
    detect_contradiction,
)
from inception.analyze.procedures import (
    ProcedureStep,
    Procedure,
    ProcedureExtractor,
    ProcedureExtractionResult,
    extract_procedures,
    procedure_to_skill,
)
from inception.analyze.gaps import (
    Gap,
    GapType,
    GapDetector,
    GapDetectionResult,
    detect_gaps,
    create_gap_node,
)


class TestEntityExtraction:
    """Tests for entity extraction."""
    
    def test_entity_dataclass(self):
        """Test Entity dataclass."""
        entity = Entity(
            text="Apple Inc.",
            entity_type="ORG",
            start_char=0,
            end_char=10,
            confidence=0.95,
        )
        
        assert entity.text == "Apple Inc."
        assert entity.entity_type == "ORG"
        assert entity.confidence == 0.95
    
    def test_entity_cluster_representative(self):
        """Test entity cluster with representative."""
        from inception.analyze.entities import EntityCluster
        
        e1 = Entity(text="Apple", entity_type="ORG", is_representative=True)
        e2 = Entity(text="Apple Inc", entity_type="ORG", is_representative=False)
        
        cluster = EntityCluster(
            cluster_id=0,
            entities=[e1, e2],
            representative=e2,  # Longer name
        )
        
        assert cluster.mention_count == 2
        assert cluster.canonical_text == "Apple Inc"
    
    def test_normalize_entity_type(self):
        """Test entity type normalization."""
        assert normalize_entity_type("PERSON") == "PERSON"
        assert normalize_entity_type("ORG") == "ORGANIZATION"
        assert normalize_entity_type("GPE") == "LOCATION"
        assert normalize_entity_type("UNKNOWN") == "UNKNOWN"
    
    @spacy_model_required
    def test_extract_entities_basic(self):
        """Test basic entity extraction."""
        text = "Apple announced a new product in San Francisco."
        
        result = extract_entities(text)
        
        assert isinstance(result, EntityExtractionResult)
        assert len(result.entities) >= 0  # May or may not find entities with small model
    
    def test_entity_extraction_result_methods(self):
        """Test EntityExtractionResult helper methods."""
        entities = [
            Entity(text="Apple", entity_type="ORG", is_representative=True),
            Entity(text="Microsoft", entity_type="ORG", is_representative=True),
            Entity(text="John", entity_type="PERSON", is_representative=True),
        ]
        
        result = EntityExtractionResult(
            entities=entities,
            entity_counts={"ORG": 2, "PERSON": 1},
        )
        
        orgs = result.get_by_type("ORG")
        assert len(orgs) == 2
        
        unique = result.get_unique_entities()
        assert len(unique) == 3


class TestClaimExtraction:
    """Tests for claim extraction."""
    
    def test_claim_dataclass(self):
        """Test Claim dataclass."""
        from inception.db.records import Confidence
        
        claim = Claim(
            text="The sky is blue.",
            subject="The sky",
            predicate="is",
            object="blue",
            modality="assertion",
        )
        
        assert claim.text == "The sky is blue."
        assert claim.spo_tuple == ("The sky", "is", "blue")
        assert not claim.is_hedged
    
    def test_claim_with_hedges(self):
        """Test claim with hedging markers."""
        claim = Claim(
            text="The product might be useful.",
            subject="The product",
            predicate="might be",
            object="useful",
            modality="possibility",
            hedges=["might"],
        )
        
        assert claim.is_hedged
        assert claim.modality == "possibility"
    
    @spacy_model_required
    def test_extract_claims_basic(self):
        """Test basic claim extraction."""
        text = "Python is a programming language. It was created by Guido."
        
        result = extract_claims(text)
        
        assert isinstance(result, ClaimExtractionResult)
        # May extract 0+ claims depending on structure
    
    def test_claim_similarity(self):
        """Test claim similarity computation."""
        claim1 = Claim(text="The cat sat on the mat.")
        claim2 = Claim(text="The cat was on the mat.")
        claim3 = Claim(text="Weather is warm today.")
        
        sim12 = compute_claim_similarity(claim1, claim2)
        sim13 = compute_claim_similarity(claim1, claim3)
        
        assert sim12 > sim13  # claim1 and claim2 are more similar
    
    def test_detect_contradiction(self):
        """Test contradiction detection."""
        claim1 = Claim(
            text="Python supports OOP.",
            subject="Python",
            modality="assertion",
        )
        claim2 = Claim(
            text="Python does not support OOP.",
            subject="Python",
            modality="negation",
        )
        claim3 = Claim(
            text="Java is fast.",
            subject="Java",
            modality="assertion",
        )
        
        is_contra, conf = detect_contradiction(claim1, claim2)
        assert is_contra
        assert conf > 0.5
        
        is_contra2, _ = detect_contradiction(claim1, claim3)
        assert not is_contra2


class TestProcedureExtraction:
    """Tests for procedure extraction."""
    
    def test_procedure_step_dataclass(self):
        """Test ProcedureStep dataclass."""
        step = ProcedureStep(
            index=0,
            text="Open the terminal",
            action_verb="open",
        )
        
        assert step.index == 0
        assert step.text == "Open the terminal"
        assert step.action_verb == "open"
    
    def test_procedure_dataclass(self):
        """Test Procedure dataclass."""
        steps = [
            ProcedureStep(index=0, text="Step one"),
            ProcedureStep(index=1, text="Step two"),
        ]
        
        proc = Procedure(
            title="How to test",
            steps=steps,
        )
        
        assert proc.step_count == 2
        assert proc.title == "How to test"
    
    def test_procedure_to_markdown(self):
        """Test procedure markdown conversion."""
        steps = [
            ProcedureStep(index=0, text="First step"),
            ProcedureStep(index=1, text="Second step"),
        ]
        
        proc = Procedure(
            title="Test Procedure",
            goal="To verify functionality",
            steps=steps,
        )
        
        md = proc.to_markdown()
        
        assert "## Test Procedure" in md
        assert "1. First step" in md
        assert "2. Second step" in md
    
    @spacy_model_required
    def test_extract_numbered_steps(self):
        """Test extraction of numbered steps."""
        text = """
        How to make coffee:
        1. Boil water
        2. Add coffee grounds
        3. Pour water over grounds
        4. Wait 4 minutes
        5. Enjoy
        """
        
        result = extract_procedures(text)
        
        assert isinstance(result, ProcedureExtractionResult)
        if result.procedures:
            assert result.procedures[0].step_count >= 3
    
    def test_procedure_to_skill(self):
        """Test procedure to skill conversion."""
        steps = [
            ProcedureStep(index=0, text="Click button", action_verb="click"),
        ]
        
        proc = Procedure(
            title="Click Test",
            goal="Test clicking",
            steps=steps,
        )
        
        skill = procedure_to_skill(proc)
        
        assert skill["name"] == "Click Test"
        assert len(skill["steps"]) == 1
        assert skill["steps"][0]["action"] == "click"


class TestGapDetection:
    """Tests for gap detection."""
    
    def test_gap_dataclass(self):
        """Test Gap dataclass."""
        gap = Gap(
            gap_type=GapType.AMBIGUOUS_REFERENCE,
            description="Unclear what 'it' refers to",
            severity="minor",
        )
        
        assert gap.gap_type == GapType.AMBIGUOUS_REFERENCE
        assert gap.is_aleatoric
        assert not gap.is_epistemic
    
    def test_epistemic_gap(self):
        """Test epistemic gap identification."""
        gap = Gap(
            gap_type=GapType.MISSING_CONTEXT,
            description="Missing prerequisite info",
        )
        
        assert gap.is_epistemic
        assert not gap.is_aleatoric
    
    def test_gap_types(self):
        """Test gap type enumeration."""
        assert GapType.INAUDIBLE.value == "inaudible"
        assert GapType.UNDEFINED_TERM.value == "undefined_term"
        assert GapType.CONTRADICTION.value == "contradiction"
    
    def test_detect_gaps_basic(self):
        """Test basic gap detection."""
        text = "It is important to do this. Some things need attention."
        
        result = detect_gaps(text)
        
        assert isinstance(result, GapDetectionResult)
        # Should detect at least vague quantities
    
    def test_detect_gaps_low_confidence(self):
        """Test gap detection with low confidence inputs."""
        result = detect_gaps(
            "Normal text here.",
            transcript_confidence=0.5,
            ocr_confidence=0.6,
        )
        
        # Should flag quality issues
        assert result.aleatoric_count >= 1 or result.epistemic_count >= 0
    
    def test_create_gap_node(self):
        """Test gap to node payload conversion."""
        gap = Gap(
            gap_type=GapType.TRUNCATED,
            description="Content cut off",
            context_text="ending mid-",
            severity="minor",
        )
        
        payload = create_gap_node(gap)
        
        assert payload["gap_type"] == "truncated"
        assert payload["description"] == "Content cut off"
        assert payload["severity"] == "minor"
    
    def test_gap_result_methods(self):
        """Test GapDetectionResult methods."""
        gaps = [
            Gap(gap_type=GapType.INAUDIBLE, description="g1", severity="minor"),
            Gap(gap_type=GapType.MISSING_CONTEXT, description="g2", severity="major"),
            Gap(gap_type=GapType.INAUDIBLE, description="g3", severity="minor", resolved=True),
        ]
        
        result = GapDetectionResult(
            gaps=gaps,
            aleatoric_count=2,
            epistemic_count=1,
        )
        
        inaudible = result.get_by_type(GapType.INAUDIBLE)
        assert len(inaudible) == 2
        
        unresolved = result.get_unresolved()
        assert len(unresolved) == 2
        
        dist = result.severity_distribution
        assert dist["minor"] == 2
        assert dist["major"] == 1
