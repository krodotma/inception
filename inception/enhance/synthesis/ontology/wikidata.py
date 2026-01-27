"""
Wikidata client for entity linking and SPARQL queries.

Design by GEMINI-PRO: Federated SPARQL integration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class WikidataEntity:
    """A Wikidata entity with metadata."""
    
    qid: str                       # e.g., Q42
    label: str
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    instance_of: list[str] = field(default_factory=list)  # P31
    properties: dict[str, Any] = field(default_factory=dict)
    
    @property
    def url(self) -> str:
        """Get Wikidata URL."""
        return f"https://www.wikidata.org/wiki/{self.qid}"
    
    @property
    def wikipedia_url(self) -> str | None:
        """Get Wikipedia URL if available."""
        sitelink = self.properties.get("enwiki")
        if sitelink:
            return f"https://en.wikipedia.org/wiki/{sitelink.replace(' ', '_')}"
        return None


class WikidataClient:
    """
    Client for Wikidata API and SPARQL endpoint.
    
    Provides:
    - Entity search
    - Entity details retrieval
    - SPARQL queries
    - Property lookups
    """
    
    API_URL = "https://www.wikidata.org/w/api.php"
    SPARQL_URL = "https://query.wikidata.org/sparql"
    
    def __init__(self, timeout: float = 30.0):
        """Initialize Wikidata client."""
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "InceptionBot/1.0"},
        )
        self._cache: dict[str, WikidataEntity] = {}
    
    def search(
        self,
        query: str,
        language: str = "en",
        limit: int = 5,
    ) -> list[WikidataEntity]:
        """
        Search for entities matching query.
        
        Args:
            query: Search query
            language: Language code
            limit: Maximum results
        
        Returns:
            List of matching entities
        """
        try:
            response = self._client.get(
                self.API_URL,
                params={
                    "action": "wbsearchentities",
                    "search": query,
                    "language": language,
                    "limit": limit,
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            entities = []
            for item in data.get("search", []):
                entities.append(WikidataEntity(
                    qid=item.get("id", ""),
                    label=item.get("label", ""),
                    description=item.get("description", ""),
                    aliases=item.get("aliases", []),
                ))
            
            return entities
            
        except Exception as e:
            logger.error(f"Wikidata search failed: {e}")
            return []
    
    def get_entity(self, qid: str) -> WikidataEntity | None:
        """
        Get detailed entity information.
        
        Args:
            qid: Wikidata QID (e.g., Q42)
        
        Returns:
            Entity details or None
        """
        # Check cache
        if qid in self._cache:
            return self._cache[qid]
        
        try:
            response = self._client.get(
                self.API_URL,
                params={
                    "action": "wbgetentities",
                    "ids": qid,
                    "props": "labels|descriptions|aliases|claims|sitelinks",
                    "languages": "en",
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            entity_data = data.get("entities", {}).get(qid)
            if not entity_data:
                return None
            
            # Extract labels
            label = entity_data.get("labels", {}).get("en", {}).get("value", "")
            description = entity_data.get("descriptions", {}).get("en", {}).get("value", "")
            
            # Extract aliases
            aliases = [
                a.get("value", "")
                for a in entity_data.get("aliases", {}).get("en", [])
            ]
            
            # Extract instance_of (P31)
            instance_of = []
            claims = entity_data.get("claims", {})
            for claim in claims.get("P31", []):
                value = claim.get("mainsnak", {}).get("datavalue", {})
                if value.get("type") == "wikibase-entityid":
                    instance_of.append(value.get("value", {}).get("id", ""))
            
            # Extract sitelinks
            sitelinks = entity_data.get("sitelinks", {})
            properties = {}
            if "enwiki" in sitelinks:
                properties["enwiki"] = sitelinks["enwiki"].get("title", "")
            
            entity = WikidataEntity(
                qid=qid,
                label=label,
                description=description,
                aliases=aliases,
                instance_of=instance_of,
                properties=properties,
            )
            
            self._cache[qid] = entity
            return entity
            
        except Exception as e:
            logger.error(f"Failed to get entity {qid}: {e}")
            return None
    
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
                params={"query": query},
                headers={"Accept": "application/sparql-results+json"},
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
            logger.error(f"SPARQL query failed: {e}")
            return []
    
    def get_related_entities(
        self,
        qid: str,
        relation: str = "P31",  # Default: instance of
        limit: int = 10,
    ) -> list[WikidataEntity]:
        """
        Get entities related to a given entity.
        
        Args:
            qid: Source entity QID
            relation: Property ID for relation
            limit: Maximum results
        
        Returns:
            List of related entities
        """
        query = f"""
        SELECT ?item ?itemLabel ?itemDescription WHERE {{
            wd:{qid} wdt:{relation} ?item.
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {limit}
        """
        
        results = self.sparql_query(query)
        
        entities = []
        for result in results:
            item_uri = result.get("item", "")
            qid_match = item_uri.split("/")[-1] if "/" in item_uri else item_uri
            
            entities.append(WikidataEntity(
                qid=qid_match,
                label=result.get("itemLabel", ""),
                description=result.get("itemDescription", ""),
            ))
        
        return entities
    
    def find_entity_by_name(
        self,
        name: str,
        entity_type: str | None = None,
    ) -> WikidataEntity | None:
        """
        Find best matching entity by name.
        
        Args:
            name: Entity name
            entity_type: Optional type constraint (QID of type)
        
        Returns:
            Best matching entity or None
        """
        candidates = self.search(name, limit=5)
        
        if not candidates:
            return None
        
        if entity_type:
            # Filter by type
            for candidate in candidates:
                entity = self.get_entity(candidate.qid)
                if entity and entity_type in entity.instance_of:
                    return entity
        
        # Return first result
        return self.get_entity(candidates[0].qid)
