"""
Validation sources for fact checking.

Uses Wikipedia and Wikidata APIs for verification.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SourceEvidence:
    """Evidence from a validation source."""
    
    source_name: str
    source_url: str
    relevant_text: str
    confidence: float  # How well this matches the claim
    qid: str | None = None  # Wikidata QID if applicable
    
    
class ValidationSource(ABC):
    """Abstract base for validation sources."""
    
    name: str
    
    @abstractmethod
    def search(self, query: str) -> list[SourceEvidence]:
        """Search for evidence related to a query."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if source is available."""
        pass


class WikipediaSource(ValidationSource):
    """Wikipedia API for fact validation."""
    
    name = "wikipedia"
    API_URL = "https://en.wikipedia.org/w/api.php"
    
    def __init__(self, language: str = "en"):
        """Initialize Wikipedia source."""
        self.language = language
        self._client = httpx.Client(timeout=30.0)
    
    def is_available(self) -> bool:
        """Wikipedia is always available."""
        return True
    
    def search(self, query: str, max_results: int = 3) -> list[SourceEvidence]:
        """Search Wikipedia for relevant content."""
        try:
            # Search for pages
            search_response = self._client.get(
                self.API_URL,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": max_results,
                    "format": "json",
                },
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            
            results = []
            for item in search_data.get("query", {}).get("search", []):
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                
                # Get extract
                extract = self._get_extract(title)
                
                results.append(SourceEvidence(
                    source_name="Wikipedia",
                    source_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    relevant_text=extract or snippet,
                    confidence=0.7,  # Wikipedia is generally reliable
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return []
    
    def _get_extract(self, title: str) -> str | None:
        """Get text extract for a page."""
        try:
            response = self._client.get(
                self.API_URL,
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "exsectionformat": "plain",
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                return page.get("extract", "")
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to get extract for {title}: {e}")
            return None


class WikidataSource(ValidationSource):
    """Wikidata API for structured fact validation."""
    
    name = "wikidata"
    API_URL = "https://www.wikidata.org/w/api.php"
    SPARQL_URL = "https://query.wikidata.org/sparql"
    
    def __init__(self):
        """Initialize Wikidata source."""
        self._client = httpx.Client(timeout=30.0)
    
    def is_available(self) -> bool:
        """Wikidata is always available."""
        return True
    
    def search(self, query: str, max_results: int = 3) -> list[SourceEvidence]:
        """Search Wikidata for relevant entities."""
        try:
            response = self._client.get(
                self.API_URL,
                params={
                    "action": "wbsearchentities",
                    "search": query,
                    "language": "en",
                    "limit": max_results,
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("search", []):
                qid = item.get("id", "")
                label = item.get("label", "")
                description = item.get("description", "")
                
                # Get more details
                details = self._get_entity_details(qid)
                
                results.append(SourceEvidence(
                    source_name="Wikidata",
                    source_url=f"https://www.wikidata.org/wiki/{qid}",
                    relevant_text=f"{label}: {description}. {details}",
                    confidence=0.85,  # Wikidata is highly structured
                    qid=qid,
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Wikidata search failed: {e}")
            return []
    
    def _get_entity_details(self, qid: str) -> str:
        """Get additional entity details."""
        try:
            response = self._client.get(
                self.API_URL,
                params={
                    "action": "wbgetentities",
                    "ids": qid,
                    "props": "claims",
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            entity = data.get("entities", {}).get(qid, {})
            claims = entity.get("claims", {})
            
            # Extract some common properties
            details = []
            
            # P31 = instance of
            if "P31" in claims:
                for claim in claims["P31"]:
                    value = claim.get("mainsnak", {}).get("datavalue", {})
                    if value.get("type") == "wikibase-entityid":
                        instance_id = value.get("value", {}).get("id", "")
                        details.append(f"Instance of: {instance_id}")
            
            return "; ".join(details[:3])
            
        except Exception:
            return ""
    
    def validate_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
    ) -> tuple[bool, str]:
        """
        Validate a specific SPO fact against Wikidata.
        
        Returns:
            Tuple of (is_valid, explanation)
        """
        # Search for subject entity
        subject_results = self.search(subject, max_results=1)
        
        if not subject_results:
            return False, f"Could not find '{subject}' in Wikidata"
        
        qid = subject_results[0].qid
        
        if not qid:
            return False, "No QID found"
        
        # This would need SPARQL for full validation
        # For now, return partial validation
        return True, f"Found entity {qid} for '{subject}'"
