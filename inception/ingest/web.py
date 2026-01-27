"""
Web page acquisition module.

Handles fetching and extracting content from web pages using trafilatura.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import trafilatura
from trafilatura.settings import use_config

from inception.config import get_config


@dataclass
class WebPageContent:
    """Extracted content from a web page."""
    
    url: str
    title: str | None = None
    author: str | None = None
    date: datetime | None = None
    text: str | None = None
    html: str | None = None
    markdown: str | None = None
    
    # Metadata
    description: str | None = None
    sitename: str | None = None
    language: str | None = None
    
    # Structure
    headings: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    
    # Quality
    content_hash: str | None = None
    fetch_time: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CrawlResult:
    """Result of crawling multiple pages."""
    
    root_url: str
    pages: list[WebPageContent] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    
    @property
    def success_count(self) -> int:
        return len(self.pages)
    
    @property
    def error_count(self) -> int:
        return len(self.errors)


def fetch_page(url: str, timeout: float = 30.0) -> str:
    """
    Fetch HTML content from a URL.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
    
    Returns:
        HTML content as string
    
    Raises:
        RuntimeError: If fetch fails
    """
    config = get_config()
    
    if config.pipeline.offline_mode:
        raise RuntimeError("Cannot fetch web page in offline mode")
    
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; Inception/0.1; +https://github.com/inception)"
            })
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}") from e


def extract_content(
    url: str,
    html: str | None = None,
    include_links: bool = True,
    include_images: bool = True,
    include_tables: bool = True,
    output_format: str = "markdown",
) -> WebPageContent:
    """
    Extract content from a web page.
    
    Args:
        url: URL of the page
        html: HTML content (if None, will fetch from URL)
        include_links: Whether to extract links
        include_images: Whether to extract images
        include_tables: Whether to extract tables
        output_format: Output format ('markdown', 'text', 'html')
    
    Returns:
        WebPageContent with extracted content
    """
    # Fetch if not provided
    if html is None:
        html = fetch_page(url)
    
    # Configure trafilatura
    traf_config = use_config()
    traf_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
    
    # Extract main content
    extracted = trafilatura.extract(
        html,
        url=url,
        include_links=include_links,
        include_images=include_images,
        include_tables=include_tables,
        output_format="markdown" if output_format == "markdown" else "txt",
        favor_precision=True,
        include_comments=False,
        config=traf_config,
    )
    
    # Get metadata
    metadata = trafilatura.extract_metadata(html, url=url)
    
    # Parse date if available
    page_date = None
    if metadata and metadata.date:
        try:
            page_date = datetime.fromisoformat(metadata.date)
        except ValueError:
            pass
    
    # Extract links
    links = []
    if include_links and metadata:
        # trafilatura doesn't expose links directly in metadata
        # We would need to parse HTML for comprehensive link extraction
        pass
    
    # Extract images
    images = []
    if include_images and metadata:
        # Similar for images
        pass
    
    # Compute content hash
    content_hash = None
    if extracted:
        content_hash = hashlib.sha256(extracted.encode()).hexdigest()
    
    return WebPageContent(
        url=url,
        title=metadata.title if metadata else None,
        author=metadata.author if metadata else None,
        date=page_date,
        text=extracted if output_format == "text" else None,
        markdown=extracted if output_format == "markdown" else None,
        html=html if output_format == "html" else None,
        description=metadata.description if metadata else None,
        sitename=metadata.sitename if metadata else None,
        language=metadata.language if metadata else None,
        content_hash=content_hash,
        links=links,
        images=images,
    )


def extract_from_html(
    html: str,
    url: str = "",
    output_format: str = "markdown",
) -> WebPageContent:
    """
    Extract content from HTML string (for cached/saved pages).
    
    Args:
        html: HTML content
        url: Original URL (for metadata)
        output_format: Output format
    
    Returns:
        WebPageContent
    """
    return extract_content(url, html=html, output_format=output_format)


def save_page(
    url: str,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """
    Save a web page (HTML + extracted content).
    
    Args:
        url: URL to save
        output_dir: Directory to save to (default: config artifacts dir)
    
    Returns:
        Tuple of (html_path, content_path)
    """
    config = get_config()
    
    if output_dir is None:
        output_dir = config.artifacts_dir / "web"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch HTML
    html = fetch_page(url)
    
    # Generate filename from URL hash
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    
    # Save HTML
    html_path = output_dir / f"{url_hash}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Extract and save content
    content = extract_content(url, html=html)
    content_path = output_dir / f"{url_hash}.md"
    
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(f"# {content.title or 'Untitled'}\n\n")
        f.write(f"**URL:** {url}\n")
        if content.author:
            f.write(f"**Author:** {content.author}\n")
        if content.date:
            f.write(f"**Date:** {content.date.isoformat()}\n")
        f.write("\n---\n\n")
        f.write(content.markdown or content.text or "")
    
    return html_path, content_path


def crawl_site(
    root_url: str,
    max_pages: int = 10,
    max_depth: int = 2,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> CrawlResult:
    """
    Crawl a website starting from a root URL.
    
    Args:
        root_url: Starting URL
        max_pages: Maximum number of pages to crawl
        max_depth: Maximum link depth from root
        include_patterns: URL patterns to include (regex)
        exclude_patterns: URL patterns to exclude (regex)
    
    Returns:
        CrawlResult with all extracted pages
    
    Note:
        This is a simplified implementation. For production use,
        consider using a proper crawler like Scrapy or crawl4ai.
    """
    import re
    from urllib.parse import urljoin, urlparse
    
    config = get_config()
    
    if config.pipeline.offline_mode:
        raise RuntimeError("Cannot crawl in offline mode")
    
    result = CrawlResult(root_url=root_url)
    visited: set[str] = set()
    to_visit: list[tuple[str, int]] = [(root_url, 0)]
    
    root_domain = urlparse(root_url).netloc
    
    while to_visit and len(result.pages) < max_pages:
        url, depth = to_visit.pop(0)
        
        if url in visited:
            continue
        visited.add(url)
        
        # Check depth
        if depth > max_depth:
            continue
        
        # Check domain
        if urlparse(url).netloc != root_domain:
            continue
        
        # Check include patterns
        if include_patterns:
            if not any(re.search(p, url) for p in include_patterns):
                continue
        
        # Check exclude patterns
        if exclude_patterns:
            if any(re.search(p, url) for p in exclude_patterns):
                continue
        
        try:
            content = extract_content(url, include_links=True)
            result.pages.append(content)
            
            # Extract links for further crawling
            if depth < max_depth:
                # Would need to parse HTML for proper link extraction
                # This is simplified
                pass
                
        except Exception as e:
            result.errors.append({"url": url, "error": str(e)})
    
    return result
