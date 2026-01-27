"""
Web search for gap resolution.

Uses DuckDuckGo (no API key required) with rate limiting
and domain filtering per OPUS-3's safety design.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx

from inception.enhance.agency.explorer.config import ExplorationConfig

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""
    
    title: str
    url: str
    snippet: str
    domain: str
    position: int
    
    @classmethod
    def from_ddg(cls, item: dict[str, Any], position: int) -> "SearchResult":
        """Create from DuckDuckGo result."""
        url = item.get("href", "")
        domain = urlparse(url).netloc
        
        return cls(
            title=item.get("title", ""),
            url=url,
            snippet=item.get("body", ""),
            domain=domain,
            position=position,
        )


@dataclass
class SearchSession:
    """Tracks search session for rate limiting and budget."""
    
    requests_made: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    last_request_time: float = 0.0
    results_cache: dict[str, list[SearchResult]] = field(default_factory=dict)
    
    def can_make_request(self, config: ExplorationConfig) -> bool:
        """Check if we can make another request."""
        if config.offline:
            return False
        
        if self.cost_usd >= config.budget_cap_usd:
            return False
        
        if self.tokens_used >= config.max_tokens_per_session:
            return False
        
        return True
    
    def wait_for_rate_limit(self, config: ExplorationConfig) -> None:
        """Wait if needed for rate limit."""
        if self.last_request_time <= 0:
            return
        
        min_interval = 60.0 / config.max_requests_per_minute
        elapsed = time.time() - self.last_request_time
        
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)


class WebSearcher:
    """
    Web search with safety rails.
    
    Uses DuckDuckGo HTML API (no key required).
    """
    
    SEARCH_URL = "https://html.duckduckgo.com/html/"
    
    def __init__(self, config: ExplorationConfig | None = None):
        """Initialize searcher with config."""
        self.config = config or ExplorationConfig()
        self.session = SearchSession()
        self._client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; InceptionBot/1.0)"
            },
        )
    
    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """
        Search for a query.
        
        Args:
            query: Search query
            max_results: Maximum results to return
        
        Returns:
            List of filtered search results
        """
        # Check cache
        cache_key = f"{query}:{max_results}"
        if cache_key in self.session.results_cache:
            logger.debug(f"Cache hit for: {query}")
            return self.session.results_cache[cache_key]
        
        # Check if we can make request
        if not self.session.can_make_request(self.config):
            logger.warning("Budget or token limit reached")
            return []
        
        # Rate limit
        self.session.wait_for_rate_limit(self.config)
        
        try:
            # Make request
            results = self._do_search(query, max_results)
            
            # Update session
            self.session.requests_made += 1
            self.session.last_request_time = time.time()
            
            # Filter by domain
            filtered = [
                r for r in results
                if self.config.is_domain_allowed(r.domain)
            ]
            
            # Cache results
            self.session.results_cache[cache_key] = filtered
            
            return filtered
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _do_search(
        self,
        query: str,
        max_results: int,
    ) -> list[SearchResult]:
        """Execute the actual search."""
        try:
            response = self._client.post(
                self.SEARCH_URL,
                data={"q": query},
            )
            response.raise_for_status()
            
            # Parse HTML results (simplified)
            results = self._parse_ddg_html(response.text, max_results)
            return results
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during search: {e}")
            return []
    
    def _parse_ddg_html(
        self,
        html: str,
        max_results: int,
    ) -> list[SearchResult]:
        """Parse DuckDuckGo HTML response."""
        import re
        
        results = []
        
        # Simple regex-based parsing
        # Match result blocks
        pattern = r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html)
        
        for i, (url, title) in enumerate(matches[:max_results]):
            if not url.startswith("http"):
                continue
            
            domain = urlparse(url).netloc
            
            results.append(SearchResult(
                title=title.strip(),
                url=url,
                snippet="",  # Would need more parsing
                domain=domain,
                position=i + 1,
            ))
        
        return results
    
    def fetch_content(
        self,
        url: str,
        max_length: int | None = None,
    ) -> str | None:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch
            max_length: Maximum content length
        
        Returns:
            Text content or None on failure
        """
        max_length = max_length or self.config.max_content_length
        
        # Check domain
        domain = urlparse(url).netloc
        if not self.config.is_domain_allowed(domain):
            logger.warning(f"Domain blocked: {domain}")
            return None
        
        # Check HTTPS
        if self.config.require_https and not url.startswith("https://"):
            logger.warning(f"HTTPS required, got: {url}")
            return None
        
        try:
            response = self._client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            content = response.text
            
            # Check length limits
            if len(content) < self.config.min_content_length:
                logger.warning(f"Content too short: {len(content)} bytes")
                return None
            
            if len(content) > max_length:
                content = content[:max_length]
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
