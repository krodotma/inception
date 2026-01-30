"""Tests for synthesis/ontology/* (37-43%)"""
import pytest

try:
    from inception.enhance.synthesis.ontology.dbpedia import DBpediaClient
    HAS_DBPEDIA = True
except ImportError:
    HAS_DBPEDIA = False

try:
    from inception.enhance.synthesis.ontology.wikidata import WikidataClient
    HAS_WIKIDATA = True
except ImportError:
    HAS_WIKIDATA = False


@pytest.mark.skipif(not HAS_DBPEDIA, reason="DBpedia not available")
class TestDBpediaClient:
    def test_creation(self):
        client = DBpediaClient()
        assert client is not None


@pytest.mark.skipif(not HAS_WIKIDATA, reason="Wikidata not available")
class TestWikidataClient:
    def test_creation(self):
        client = WikidataClient()
        assert client is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
