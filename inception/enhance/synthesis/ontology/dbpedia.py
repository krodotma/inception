"""
DBpedia client for entity linking via SPARQL.

DBpedia provides structured data extracted from Wikipedia.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


@dataclass
class DBpediaEntity:
    """A DBpedia entity with metadata."""
    
    uri: str                          # DBpedia URI
    label: str
    abstract: str = ""
    categories: list[str] = field(default_factory=list)
    types: list[str] = field(default_factory=list)  # rdf:type values
    properties: dict[str, Any] = field(default_factory=dict)
    
    @property
    def name(self) -> str:
        """Get entity name from URI."""
        return self.uri.split("/")[-1].replace("_", " ")
    
    @property
    def wikipedia_url(self) -> str:
        """Get Wikipedia URL."""
        name = self.uri.split("/")[-1]
        return f"https://en.wikipedia.org/wiki/{name}"


class DBpediaClient:
    """
    Client for DBpedia SPARQL endpoint.
    
    Provides:
    - Entity lookup by name
    - Entity details via SPARQL
    - Category and type queries
    """
    
    SPARQL_URL = "https://dbpedia.org/sparql"
    LOOKUP_URL = "https://lookup.dbpedia.org/api/search"
    
    def __init__(self, timeout: float = 30.0):
        """Initialize DBpedia client."""
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "InceptionBot/1.0"},
        )
        self._cache: dict[str, DBpediaEntity] = {}
    
    def lookup(
        self,
        query: str,
        limit: int = 5,
    ) -> list[DBpediaEntity]:
        """
        Lookup entities by name.
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching entities
        """
        try:
            response = self._client.get(
                self.LOOKUP_URL,
                params={
                    "query": query,
                    "maxResults": limit,
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            entities = []
            for doc in data.get("docs", []):
                entities.append(DBpediaEntity(
                    uri=doc.get("resource", [None])[0] or "",
                    label=doc.get("label", [None])[0] or "",
                    abstract=doc.get("comment", [None])[0] or "",
                    categories=doc.get("category", []),
                    types=doc.get("typeName", []),
                ))
            
            return entities
            
        except Exception as e:
            logger.error(f"DBpedia lookup failed: {e}")
            return []
    
    def get_entity(self, uri: str) -> DBpediaEntity | None:
        """
        Get entity details via SPARQL.
        
        Args:
            uri: DBpedia URI
        
        Returns:
            Entity details or None
        """
        if uri in self._cache:
            return self._cache[uri]
        
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        
        SELECT ?label ?abstract ?type WHERE {{
            <{uri}> rdfs:label ?label.
            OPTIONAL {{ <{uri}> dbo:abstract ?abstract. }}
            OPTIONAL {{ <{uri}> a ?type. }}
            FILTER(LANG(?label) = 'en')
            FILTER(!BOUND(?abstract) || LANG(?abstract) = 'en')
        }}
        LIMIT 10
        """
        
        results = self.sparql_query(query)
        
        if not results:
            return None
        
        # Aggregate results
        label = results[0].get("label", "")
        abstract = results[0].get("abstract", "")
        types = list(set(r.get("type", "") for r in results if r.get("type")))
        
        entity = DBpediaEntity(
            uri=uri,
            label=label,
            abstract=abstract,
            types=types,
        )
        
        self._cache[uri] = entity
        return entity
    
    def sparql_query(self, query: str) -> list[dict[str, Any]]:
        """
        Execute a SPARQL query.
        
        Args:
            query: SPARQL query string
        
        Returns:
            List of result bindings
        """
        try:
            response = self._client.get(
                self.SPARQL_URL,
                params={
                    "query": query,
                    "format": "application/sparql-results+json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for binding in data.get("results", {}).get("bindings", []):
                result = {}
                for var, value in binding.items():
                    result[var] = value.get("value", "")
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"DBpedia SPARQL failed: {e}")
            return []
    
    def find_by_wikipedia_title(self, title: str) -> DBpediaEntity | None:
        """
        Find entity by Wikipedia title.
        
        Args:
            title: Wikipedia article title
        
        Returns:
            Entity or None
        """
        encoded_title = quote(title.replace(" ", "_"))
        uri = f"http://dbpedia.org/resource/{encoded_title}"
        
        return self.get_entity(uri)
    
    def get_related(
        self,
        uri: str,
        property_uri: str,
        limit: int = 10,
    ) -> list[DBpediaEntity]:
        """
        Get entities related via a property.
        
        Args:
            uri: Source entity URI
            property_uri: Property to follow
            limit: Maximum results
        
        Returns:
            List of related entities
        """
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?related ?label WHERE {{
            <{uri}> <{property_uri}> ?related.
            ?related rdfs:label ?label.
            FILTER(LANG(?label) = 'en')
        }}
        LIMIT {limit}
        """
        
        results = self.sparql_query(query)
        
        return [
            DBpediaEntity(
                uri=r.get("related", ""),
                label=r.get("label", ""),
            )
            for r in results
        ]
