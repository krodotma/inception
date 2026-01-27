"""
Ontology Linker - Connect entities to semantic web resources.

Design by OPUS-1: Entity linking to Wikidata, DBpedia, Schema.org.
Integration by GEMINI-PRO: SPARQL queries and federated access.
"""

from inception.enhance.synthesis.ontology.linker import OntologyLinker, LinkedEntity
from inception.enhance.synthesis.ontology.wikidata import WikidataClient
from inception.enhance.synthesis.ontology.dbpedia import DBpediaClient

__all__ = [
    "OntologyLinker",
    "LinkedEntity",
    "WikidataClient",
    "DBpediaClient",
]
