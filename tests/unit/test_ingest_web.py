"""
Unit tests for ingest/web.py

Tests for web ingestion:
- WebPageContent: Page data
- CrawlResult: Crawl result
"""

import pytest
from datetime import datetime

try:
    from inception.ingest.web import (
        WebPageContent,
        CrawlResult,
    )
    HAS_WEB = True
except ImportError:
    HAS_WEB = False


@pytest.mark.skipif(not HAS_WEB, reason="web module not available")
class TestWebPageContent:
    """Tests for WebPageContent dataclass."""
    
    def test_creation_minimal(self):
        """Test creating minimal page."""
        page = WebPageContent(url="https://example.com")
        
        assert page.url == "https://example.com"
    
    def test_creation_full(self):
        """Test creating full page."""
        page = WebPageContent(
            url="https://example.com/article",
            title="Test Article",
            author="John Doe",
            text="Article content here",
            markdown="# Article\n\nContent here",
        )
        
        assert page.title == "Test Article"
        assert page.author == "John Doe"
    
    def test_with_links(self):
        """Test page with links."""
        page = WebPageContent(
            url="https://example.com",
            links=[
                {"href": "/page1", "text": "Page 1"},
                {"href": "/page2", "text": "Page 2"},
            ],
        )
        
        assert len(page.links) == 2
    
    def test_with_images(self):
        """Test page with images."""
        page = WebPageContent(
            url="https://example.com",
            images=[
                {"src": "/img1.jpg", "alt": "Image 1"},
            ],
        )
        
        assert len(page.images) == 1


@pytest.mark.skipif(not HAS_WEB, reason="web module not available")
class TestCrawlResult:
    """Tests for CrawlResult dataclass."""
    
    def test_creation(self):
        """Test creating result."""
        result = CrawlResult(root_url="https://example.com")
        
        assert result.root_url == "https://example.com"
        assert result.success_count == 0  # property
    
    def test_with_pages(self):
        """Test result with pages."""
        pages = [
            WebPageContent(url="https://example.com/1"),
            WebPageContent(url="https://example.com/2"),
        ]
        result = CrawlResult(root_url="https://example.com", pages=pages)
        
        assert result.success_count == 2  # property
    
    def test_with_errors(self):
        """Test result with errors."""
        errors = [
            {"url": "https://example.com/404", "error": "Not Found"},
        ]
        result = CrawlResult(root_url="https://example.com", errors=errors)
        
        assert result.error_count == 1  # property


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
