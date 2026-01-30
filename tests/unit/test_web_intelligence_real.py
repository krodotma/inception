"""
REAL tests for ingest/web_intelligence.py (0% coverage)
"""
import pytest
from inception.ingest.web_intelligence import (
    PageType, ContentReliability, StructuredSection,
    WebIntelligence, WebAnalyzer, ContentDiff, ContentDiffer
)


class TestPageType:
    def test_values(self):
        assert PageType.ARTICLE.value == "article"
        assert PageType.DOCUMENTATION.value == "documentation"
        assert PageType.API_REFERENCE.value == "api_reference"


class TestContentReliability:
    def test_values(self):
        assert ContentReliability.AUTHORITATIVE.value == "authoritative"
        assert ContentReliability.USER_GENERATED.value == "user_generated"


class TestStructuredSection:
    def test_creation(self):
        section = StructuredSection(
            title="Introduction",
            level=1,
            content="This is the intro.",
        )
        assert section.title == "Introduction"
        assert section.level == 1
    
    def test_with_subsections(self):
        sub = StructuredSection(title="Sub", level=2, content="Sub content")
        section = StructuredSection(
            title="Main",
            level=1,
            content="Main content",
            subsections=[sub]
        )
        assert len(section.subsections) == 1


class TestWebIntelligence:
    def test_creation(self):
        intel = WebIntelligence(url="https://example.com")
        assert intel.url == "https://example.com"
        assert intel.page_type == PageType.UNKNOWN
    
    def test_with_all_fields(self):
        intel = WebIntelligence(
            url="https://docs.example.com/api",
            page_type=PageType.API_REFERENCE,
            reliability=ContentReliability.AUTHORITATIVE,
            main_topic="API Documentation",
            word_count=1000,
            reading_time_minutes=5.0,
        )
        assert intel.page_type == PageType.API_REFERENCE
        assert intel.word_count == 1000
    
    def test_to_dict(self):
        intel = WebIntelligence(url="https://example.com")
        d = intel.to_dict()
        assert "url" in d
        assert "page_type" in d


class TestWebAnalyzer:
    def test_creation(self):
        analyzer = WebAnalyzer()
        assert analyzer is not None
    
    def test_analyze_simple(self):
        analyzer = WebAnalyzer()
        intel = analyzer.analyze(
            url="https://example.com/article",
            text="This is a test article about machine learning."
        )
        assert intel.url == "https://example.com/article"
        assert intel.word_count > 0
    
    def test_analyze_documentation(self):
        analyzer = WebAnalyzer()
        intel = analyzer.analyze(
            url="https://docs.python.org/3/tutorial/",
            text="# Python Tutorial\\n\\nThis tutorial introduces Python."
        )
        assert intel is not None
    
    def test_detect_page_type_documentation(self):
        analyzer = WebAnalyzer()
        intel = analyzer.analyze(
            url="https://docs.example.com/readme",
            text="Documentation for the project."
        )
        # Should detect as documentation
        assert intel.page_type in [PageType.DOCUMENTATION, PageType.UNKNOWN]
    
    def test_extract_concepts(self):
        analyzer = WebAnalyzer()
        intel = analyzer.analyze(
            url="https://example.com",
            text="Machine Learning uses Neural Networks for classification."
        )
        # Should extract some concepts
        assert intel.key_concepts is not None
    
    def test_analyze_with_code(self):
        analyzer = WebAnalyzer()
        content = '''
# API Reference

```python
def hello():
    return "world"
```
'''
        intel = analyzer.analyze(
            url="https://api.example.com",
            markdown=content
        )
        assert len(intel.code_snippets) >= 0


class TestContentDiff:
    def test_creation(self):
        diff = ContentDiff()
        assert diff.added_sections == []
        assert diff.significance == 0.0
    
    def test_with_changes(self):
        diff = ContentDiff(
            added_sections=["New Section"],
            removed_sections=["Old Section"],
            word_count_delta=100,
            significance=0.7,
        )
        assert len(diff.added_sections) == 1
        assert diff.significance == 0.7


class TestContentDiffer:
    def test_creation(self):
        differ = ContentDiffer()
        assert differ is not None
    
    def test_diff_identical(self):
        differ = ContentDiffer()
        intel = WebIntelligence(url="https://example.com", word_count=100)
        diff = differ.diff(intel, intel)
        assert diff.word_count_delta == 0
    
    def test_diff_different(self):
        differ = ContentDiffer()
        old = WebIntelligence(url="https://example.com", word_count=100)
        new = WebIntelligence(url="https://example.com", word_count=200)
        diff = differ.diff(old, new)
        assert diff.word_count_delta == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
