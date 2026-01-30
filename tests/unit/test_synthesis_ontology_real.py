"""Tests for enhance/synthesis/ontology/* modules"""
import pytest

try:
    from inception.enhance.synthesis.ontology.wikidata import WikidataLinker
    HAS_WIKIDATA = True
except ImportError:
    HAS_WIKIDATA = False

try:
    from inception.enhance.synthesis.ontology.dbpedia import DBpediaLinker
    HAS_DBPEDIA = True
except ImportError:
    HAS_DBPEDIA = False

try:
    from inception.enhance.synthesis.ontology.linker import OntologyLinker
    HAS_LINKER = True
except ImportError:
    HAS_LINKER = False


@pytest.mark.skipif(not HAS_WIKIDATA, reason="WikidataLinker not available")
class TestWikidataLinker:
    def test_creation(self):
        linker = WikidataLinker()
        assert linker is not None


@pytest.mark.skipif(not HAS_DBPEDIA, reason="DBpediaLinker not available")
class TestDBpediaLinker:
    def test_creation(self):
        linker = DBpediaLinker()
        assert linker is not None


@pytest.mark.skipif(not HAS_LINKER, reason="OntologyLinker not available")
class TestOntologyLinker:
    def test_creation(self):
        linker = OntologyLinker()
        assert linker is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
