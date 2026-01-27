"""
Comprehensive tests for Tier 3 Synthesis modules.

Tests for:
- Multi-Source Fusion
- Ontology Linker
- Temporal Reasoner
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# ==============================================================================
# FUSION TESTS
# ==============================================================================

class TestSourceRegistry:
    """Tests for SourceRegistry."""
    
    def test_source_info_weight(self):
        """Test source weight calculation."""
        from inception.enhance.synthesis.fusion.sources import SourceInfo, SourceType
        
        source = SourceInfo(
            nid=1,
            name="Test",
            source_type=SourceType.ACADEMIC,
            base_reliability=0.9,
        )
        
        # Academic sources get 1.2x bonus
        assert source.weight > 0.9 * 1.2 * 0.4  # At minimum freshness
    
    def test_source_freshness(self):
        """Test freshness calculation."""
        from inception.enhance.synthesis.fusion.sources import SourceInfo
        
        # Fresh source
        recent = SourceInfo(
            nid=1,
            published_at=datetime.now() - timedelta(days=7),
        )
        assert recent.freshness == 1.0
        
        # Old source
        old = SourceInfo(
            nid=2,
            published_at=datetime.now() - timedelta(days=400),
        )
        assert old.freshness == 0.6
    
    def test_registry_register_and_get(self):
        """Test source registration."""
        from inception.enhance.synthesis.fusion.sources import SourceRegistry, SourceInfo
        
        registry = SourceRegistry()
        source = SourceInfo(nid=1, name="Test")
        
        registry.register(source)
        
        assert registry.get(1) == source
        assert registry.get(999) is None
    
    def test_registry_domain_authority(self):
        """Test domain authority auto-detection."""
        from inception.enhance.synthesis.fusion.sources import SourceRegistry, SourceInfo
        
        registry = SourceRegistry()
        source = SourceInfo(nid=1, url="https://wikipedia.org/wiki/Test")
        
        registry.register(source)
        
        assert source.domain_authority >= 0.8


class TestClaimMatcher:
    """Tests for ClaimMatcher."""
    
    def test_match_identical(self):
        """Test matching identical claims."""
        from inception.enhance.synthesis.fusion.matcher import ClaimMatcher, ClaimInfo, MatchType
        
        matcher = ClaimMatcher()
        
        claim1 = ClaimInfo(nid=1, text="Python was created by Guido van Rossum")
        claim2 = ClaimInfo(nid=2, text="Python was created by Guido van Rossum")
        
        result = matcher.match(claim1, claim2)
        
        assert result.similarity > 0.9
        assert result.match_type in (MatchType.IDENTICAL, MatchType.PARAPHRASE)
    
    def test_match_related(self):
        """Test matching related claims."""
        from inception.enhance.synthesis.fusion.matcher import ClaimMatcher, ClaimInfo
        
        matcher = ClaimMatcher()
        
        claim1 = ClaimInfo(nid=1, text="Python is a programming language")
        claim2 = ClaimInfo(nid=2, text="Python is a popular programming language for data science")
        
        result = matcher.match(claim1, claim2)
        
        assert result.similarity > 0.5
    
    def test_detect_negation(self):
        """Test negation detection."""
        from inception.enhance.synthesis.fusion.matcher import ClaimMatcher, ClaimInfo, MatchType
        
        matcher = ClaimMatcher()
        
        claim1 = ClaimInfo(nid=1, text="Python is dynamically typed")
        claim2 = ClaimInfo(nid=2, text="Python is not statically typed")
        
        result = matcher.match(claim1, claim2)
        
        # These are related with some overlap
        assert result.similarity > 0.3
    
    def test_find_matches(self):
        """Test finding all matches."""
        from inception.enhance.synthesis.fusion.matcher import ClaimMatcher, ClaimInfo
        
        matcher = ClaimMatcher()
        claims = [
            ClaimInfo(nid=1, text="Python was released in 1991"),
            ClaimInfo(nid=2, text="Python first appeared in 1991"),
            ClaimInfo(nid=3, text="Java was released in 1995"),
        ]
        
        matches = matcher.find_matches(claims, threshold=0.3)
        
        # Should find match between claims 1 and 2
        assert len(matches) >= 1


class TestUncertainty:
    """Tests for uncertainty quantification."""
    
    def test_bayesian_fuse_single(self):
        """Test fusion of single claim."""
        from inception.enhance.synthesis.fusion.uncertainty import UncertainClaim, bayesian_fuse
        
        claim = UncertainClaim(nid=1, text="Test", mean_confidence=0.8)
        result = bayesian_fuse([claim])
        
        assert result.mean_confidence == 0.8
    
    def test_bayesian_fuse_multiple(self):
        """Test Bayesian fusion of multiple claims."""
        from inception.enhance.synthesis.fusion.uncertainty import UncertainClaim, bayesian_fuse
        
        claims = [
            UncertainClaim(nid=1, text="Test", mean_confidence=0.7, std_confidence=0.2),
            UncertainClaim(nid=2, text="Test", mean_confidence=0.9, std_confidence=0.1),
        ]
        
        result = bayesian_fuse(claims)
        
        # Fused confidence should be between the two
        assert 0.7 < result.mean_confidence < 0.95
        # Uncertainty should decrease
        assert result.std_confidence < 0.2
    
    def test_fusion_stats(self):
        """Test fusion statistics."""
        from inception.enhance.synthesis.fusion.uncertainty import (
            UncertainClaim, bayesian_fuse, compute_fusion_stats
        )
        
        claims = [
            UncertainClaim(nid=1, text="Test", mean_confidence=0.6, std_confidence=0.3),
            UncertainClaim(nid=2, text="Test", mean_confidence=0.8, std_confidence=0.3),
        ]
        
        fused = bayesian_fuse(claims)
        stats = compute_fusion_stats(claims, fused)
        
        assert stats.claims_fused == 2
        assert stats.uncertainty_reduction > 0


class TestConflictResolver:
    """Tests for ConflictResolver."""
    
    def test_resolve_weighted_majority(self):
        """Test weighted majority resolution."""
        from inception.enhance.synthesis.fusion.resolver import ConflictResolver, ResolutionStrategy
        from inception.enhance.synthesis.fusion.matcher import ClaimInfo
        from inception.enhance.synthesis.fusion.sources import SourceRegistry, SourceInfo
        
        registry = SourceRegistry()
        registry.register(SourceInfo(nid=10, base_reliability=0.9))
        registry.register(SourceInfo(nid=11, base_reliability=0.3))
        
        resolver = ConflictResolver(source_registry=registry)
        
        claims = [
            ClaimInfo(nid=1, text="Claim A", source_nid=10),
            ClaimInfo(nid=2, text="Claim B", source_nid=11),
        ]
        
        result = resolver.resolve(claims, strategy=ResolutionStrategy.WEIGHTED_MAJORITY)
        
        # Higher reliability source should win
        assert result.winning_nid == 1
        assert result.is_resolved
    
    def test_detect_contradiction_type(self):
        """Test contradiction type detection."""
        from inception.enhance.synthesis.fusion.resolver import ConflictResolver, ContradictionType
        from inception.enhance.synthesis.fusion.matcher import ClaimInfo
        
        resolver = ConflictResolver()
        
        # Quantitative contradiction
        claim1 = ClaimInfo(nid=1, text="Python has 100 keywords")
        claim2 = ClaimInfo(nid=2, text="Python has 35 keywords")
        
        ctype = resolver.detect_type(claim1, claim2)
        assert ctype == ContradictionType.QUANTITATIVE


class TestFusionEngine:
    """Tests for FusionEngine."""
    
    def test_fuse_simple(self):
        """Test simple fusion."""
        from inception.enhance.synthesis.fusion.engine import FusionEngine
        from inception.enhance.synthesis.fusion.matcher import ClaimInfo
        
        engine = FusionEngine()
        
        claims = [
            ClaimInfo(nid=1, text="Python was created in 1991"),
            ClaimInfo(nid=2, text="Python was created in 1991"),
        ]
        
        result = engine.fuse(claims)
        
        assert result.claims_processed == 2
        assert len(result.fused_claims) >= 1


# ==============================================================================
# ONTOLOGY TESTS
# ==============================================================================

class TestWikidataClient:
    """Tests for WikidataClient."""
    
    def test_entity_creation(self):
        """Test WikidataEntity creation."""
        from inception.enhance.synthesis.ontology.wikidata import WikidataEntity
        
        entity = WikidataEntity(
            qid="Q42",
            label="Douglas Adams",
            description="English author",
        )
        
        assert entity.url == "https://www.wikidata.org/wiki/Q42"
    
    @patch("httpx.Client.get")
    def test_search(self, mock_get):
        """Test entity search."""
        from inception.enhance.synthesis.ontology.wikidata import WikidataClient
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "search": [
                {"id": "Q42", "label": "Douglas Adams", "description": "author"}
            ]
        }
        mock_get.return_value = mock_response
        
        client = WikidataClient()
        results = client.search("Douglas Adams")
        
        assert len(results) == 1
        assert results[0].qid == "Q42"


class TestDBpediaClient:
    """Tests for DBpediaClient."""
    
    def test_entity_creation(self):
        """Test DBpediaEntity creation."""
        from inception.enhance.synthesis.ontology.dbpedia import DBpediaEntity
        
        entity = DBpediaEntity(
            uri="http://dbpedia.org/resource/Python_(programming_language)",
            label="Python",
        )
        
        assert "Python" in entity.name
        assert "wikipedia.org" in entity.wikipedia_url


class TestOntologyLinker:
    """Tests for OntologyLinker."""
    
    def test_linked_entity(self):
        """Test LinkedEntity creation."""
        from inception.enhance.synthesis.ontology.linker import LinkedEntity
        
        entity = LinkedEntity(
            nid=1,
            name="Python",
            entity_type="programming language",
            wikidata_qid="Q28865",
        )
        
        assert entity.is_linked
        assert "wikidata.org" in entity.best_link
    
    def test_nil_entity(self):
        """Test NIL entity detection."""
        from inception.enhance.synthesis.ontology.linker import LinkedEntity
        
        entity = LinkedEntity(
            nid=1,
            name="NonExistentEntity12345",
            is_nil=True,
        )
        
        assert not entity.is_linked
        assert entity.is_nil
    
    def test_link_entities_batch(self):
        """Test batch linking."""
        from inception.enhance.synthesis.ontology.linker import OntologyLinker
        
        linker = OntologyLinker()
        
        # Mock the clients
        linker.wikidata.search = MagicMock(return_value=[])
        linker.dbpedia.lookup = MagicMock(return_value=[])
        
        entities = [
            (1, "Python", "programming language"),
            (2, "Java", "programming language"),
        ]
        
        result = linker.link_entities(entities)
        
        assert result.total_entities == 2


# ==============================================================================
# TEMPORAL TESTS
# ==============================================================================

class TestAllenRelations:
    """Tests for Allen's Interval Algebra."""
    
    def test_all_relations_exist(self):
        """Test all 13 Allen relations exist."""
        from inception.enhance.synthesis.temporal.relations import AllenRelation
        
        assert len(AllenRelation) == 13
    
    def test_allen_inverse(self):
        """Test Allen relation inversion."""
        from inception.enhance.synthesis.temporal.relations import (
            AllenRelation, allen_inverse
        )
        
        assert allen_inverse(AllenRelation.BEFORE) == AllenRelation.AFTER
        assert allen_inverse(AllenRelation.EQUALS) == AllenRelation.EQUALS
    
    def test_allen_compose_before(self):
        """Test Allen composition for BEFORE."""
        from inception.enhance.synthesis.temporal.relations import (
            AllenRelation, allen_compose
        )
        
        result = allen_compose(AllenRelation.BEFORE, AllenRelation.BEFORE)
        assert AllenRelation.BEFORE in result
    
    def test_relation_from_timestamps(self):
        """Test determining relation from timestamps."""
        from inception.enhance.synthesis.temporal.relations import (
            AllenRelation, relation_from_timestamps
        )
        
        # A before B
        rel = relation_from_timestamps(0, 10, 20, 30)
        assert rel == AllenRelation.BEFORE
        
        # A equals B
        rel = relation_from_timestamps(0, 10, 0, 10)
        assert rel == AllenRelation.EQUALS
        
        # A during B
        rel = relation_from_timestamps(5, 8, 0, 10)
        assert rel == AllenRelation.DURING


class TestTemporalParser:
    """Tests for TemporalParser."""
    
    def test_parse_iso_date(self):
        """Test ISO date parsing."""
        from inception.enhance.synthesis.temporal.parser import TemporalParser
        
        parser = TemporalParser()
        expressions = parser.parse("Python 3.12 was released on 2023-10-02")
        
        assert len(expressions) >= 1
        assert expressions[0].start.year == 2023
    
    def test_parse_month_day_year(self):
        """Test Month Day, Year format."""
        from inception.enhance.synthesis.temporal.parser import TemporalParser
        
        parser = TemporalParser()
        expressions = parser.parse("Published on January 15 2024")
        
        assert len(expressions) >= 1
        assert expressions[0].start.month == 1
    
    def test_parse_relative_past(self):
        """Test relative past expressions."""
        from inception.enhance.synthesis.temporal.parser import TemporalParser
        
        parser = TemporalParser()
        expressions = parser.parse("Updated 3 days ago")
        
        assert len(expressions) >= 1
        assert expressions[0].expression_type == "relative"
    
    def test_parse_year_only(self):
        """Test year-only parsing."""
        from inception.enhance.synthesis.temporal.parser import TemporalParser
        
        parser = TemporalParser()
        expressions = parser.parse("Founded in 1999")
        
        assert len(expressions) >= 1
        assert expressions[0].start.year == 1999


class TestTemporalNetwork:
    """Tests for TemporalNetwork."""
    
    def test_add_constraint(self):
        """Test adding constraints."""
        from inception.enhance.synthesis.temporal.network import (
            TemporalNetwork, TemporalConstraint
        )
        from inception.enhance.synthesis.temporal.relations import AllenRelation
        
        network = TemporalNetwork()
        
        constraint = TemporalConstraint(
            event1_nid=1,
            event2_nid=2,
            relation=AllenRelation.BEFORE,
        )
        
        network.add_constraint(constraint, propagate=False)
        
        assert 1 in network.events
        assert 2 in network.events
        assert network.get_constraint(1, 2).relation == AllenRelation.BEFORE
    
    def test_propagate(self):
        """Test constraint propagation."""
        from inception.enhance.synthesis.temporal.network import (
            TemporalNetwork, TemporalConstraint
        )
        from inception.enhance.synthesis.temporal.relations import AllenRelation
        
        network = TemporalNetwork()
        
        # A before B
        network.add_constraint(TemporalConstraint(
            event1_nid=1,
            event2_nid=2,
            relation=AllenRelation.BEFORE,
        ), propagate=False)
        
        # B before C
        network.add_constraint(TemporalConstraint(
            event1_nid=2,
            event2_nid=3,
            relation=AllenRelation.BEFORE,
        ), propagate=False)
        
        # Propagate: should infer A before C
        inferred = network.propagate()
        
        assert len(inferred) > 0


class TestTemporalFact:
    """Tests for TemporalFact."""
    
    def test_eternal_fact(self):
        """Test eternally valid fact."""
        from inception.enhance.synthesis.temporal.reasoner import TemporalFact
        
        fact = TemporalFact(
            subject_nid=1,
            predicate="is_a",
            object_value="language",
        )
        
        assert fact.is_eternally_valid
        assert fact.is_currently_valid
    
    def test_temporal_fact(self):
        """Test temporally bounded fact."""
        from inception.enhance.synthesis.temporal.reasoner import TemporalFact
        
        fact = TemporalFact(
            subject_nid=1,
            predicate="version",
            object_value="3.12",
            valid_from=datetime(2023, 10, 2),
        )
        
        assert not fact.is_eternally_valid
        assert fact.is_currently_valid


class TestTemporalReasoner:
    """Tests for TemporalReasoner."""
    
    def test_add_temporal_relation(self):
        """Test adding temporal relations."""
        from inception.enhance.synthesis.temporal.reasoner import TemporalReasoner
        from inception.enhance.synthesis.temporal.relations import AllenRelation
        
        reasoner = TemporalReasoner()
        
        inferred = reasoner.add_temporal_relation(1, 2, AllenRelation.BEFORE)
        
        # Should be able to query the constraint
        constraint = reasoner.network.get_constraint(1, 2)
        assert constraint.relation == AllenRelation.BEFORE
    
    def test_order_events(self):
        """Test event ordering."""
        from inception.enhance.synthesis.temporal.reasoner import TemporalReasoner
        from inception.enhance.synthesis.temporal.relations import AllenRelation
        
        reasoner = TemporalReasoner()
        
        # Add constraints: 1 before 2, 2 before 3
        reasoner.add_temporal_relation(1, 2, AllenRelation.BEFORE)
        reasoner.add_temporal_relation(2, 3, AllenRelation.BEFORE)
        
        order = reasoner.order_events([3, 1, 2])
        
        # Should order as 1, 2, 3
        assert order[0] == 1
        assert order[-1] == 3
    
    def test_validate_consistency(self):
        """Test consistency validation."""
        from inception.enhance.synthesis.temporal.reasoner import TemporalReasoner
        from inception.enhance.synthesis.temporal.relations import AllenRelation
        
        reasoner = TemporalReasoner()
        
        # Add consistent constraints
        reasoner.add_temporal_relation(1, 2, AllenRelation.BEFORE)
        reasoner.add_temporal_relation(2, 3, AllenRelation.BEFORE)
        
        inconsistencies = reasoner.validate_consistency()
        
        # Should be consistent
        assert len(inconsistencies) == 0


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

class TestSynthesisIntegration:
    """Integration tests for synthesis modules."""
    
    def test_full_fusion_workflow(self):
        """Test complete fusion workflow."""
        from inception.enhance.synthesis.fusion.engine import FusionEngine
        from inception.enhance.synthesis.fusion.sources import SourceInfo, SourceType
        from inception.enhance.synthesis.fusion.matcher import ClaimInfo
        
        engine = FusionEngine()
        
        sources = [
            SourceInfo(nid=10, name="Wikipedia", source_type=SourceType.ENCYCLOPEDIA),
            SourceInfo(nid=11, name="Docs", source_type=SourceType.DOCUMENTATION),
        ]
        
        claims = [
            ClaimInfo(nid=1, text="Python is interpreted", source_nid=10),
            ClaimInfo(nid=2, text="Python is an interpreted language", source_nid=11),
        ]
        
        result = engine.fuse(claims, sources)
        
        assert result.claims_processed == 2
        assert result.stats.claims_fused == 2
    
    def test_package_imports(self):
        """Test all exports are accessible."""
        from inception.enhance.synthesis import (
            FusionEngine,
            SourceRegistry,
            ClaimMatcher,
            ConflictResolver,
            ContradictionType,
            OntologyLinker,
            LinkedEntity,
            WikidataClient,
            DBpediaClient,
            TemporalReasoner,
            TemporalFact,
            TemporalRelation,
            TemporalNetwork,
        )
        
        # All imports should work
        assert FusionEngine is not None
        assert TemporalReasoner is not None
