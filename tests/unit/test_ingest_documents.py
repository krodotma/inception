"""
Unit tests for ingest/documents.py

Tests for document ingestion:
- DocumentInfo, PDFPage, PDFContent: Data classes
- SlideContent, PresentationContent: Presentation data
"""

import pytest
from pathlib import Path
from datetime import datetime

try:
    from inception.ingest.documents import (
        DocumentInfo,
        PDFPage,
        PDFContent,
        SlideContent,
        PresentationContent,
        get_document_info,
        detect_document_type,
    )
    HAS_DOCUMENTS = True
except ImportError:
    HAS_DOCUMENTS = False


@pytest.mark.skipif(not HAS_DOCUMENTS, reason="documents module not available")
class TestDocumentInfo:
    """Tests for DocumentInfo dataclass."""
    
    def test_creation_minimal(self):
        """Test creating minimal info."""
        info = DocumentInfo(
            path=Path("/test/doc.pdf"),
            mime_type="application/pdf",
            size_bytes=1024,
            content_hash="abc123",
        )
        
        assert info.path == Path("/test/doc.pdf")
        assert info.mime_type == "application/pdf"
    
    def test_creation_full(self):
        """Test creating full info."""
        info = DocumentInfo(
            path=Path("/test/doc.pdf"),
            mime_type="application/pdf",
            size_bytes=2048,
            content_hash="def456",
            title="Test Document",
            author="Author Name",
            page_count=10,
            word_count=5000,
            has_images=True,
            has_tables=True,
        )
        
        assert info.title == "Test Document"
        assert info.page_count == 10


@pytest.mark.skipif(not HAS_DOCUMENTS, reason="documents module not available")
class TestPDFPage:
    """Tests for PDFPage dataclass."""
    
    def test_creation(self):
        """Test creating a page."""
        page = PDFPage(
            page_num=1,
            text="Page content here",
        )
        
        assert page.page_num == 1
        assert page.text == "Page content here"
    
    def test_with_tables(self):
        """Test page with tables."""
        page = PDFPage(
            page_num=2,
            text="Table content",
            tables=[[["A", "B"], ["C", "D"]]],
        )
        
        assert len(page.tables) == 1
    
    def test_scanned_page(self):
        """Test scanned page flags."""
        page = PDFPage(
            page_num=3,
            is_scanned=True,
            ocr_confidence=0.85,
        )
        
        assert page.is_scanned is True
        assert page.ocr_confidence == 0.85


@pytest.mark.skipif(not HAS_DOCUMENTS, reason="documents module not available")
class TestPDFContent:
    """Tests for PDFContent dataclass."""
    
    def test_creation(self):
        """Test creating PDF content."""
        info = DocumentInfo(
            path=Path("/test.pdf"),
            mime_type="application/pdf",
            size_bytes=1024,
            content_hash="hash",
        )
        content = PDFContent(path=Path("/test.pdf"), info=info)
        
        assert content.page_count == 0  # property not method
    
    def test_full_text(self):
        """Test full text extraction."""
        info = DocumentInfo(
            path=Path("/test.pdf"),
            mime_type="application/pdf",
            size_bytes=1024,
            content_hash="hash",
        )
        pages = [
            PDFPage(page_num=1, text="Page 1"),
            PDFPage(page_num=2, text="Page 2"),
        ]
        content = PDFContent(path=Path("/test.pdf"), info=info, pages=pages)
        
        full = content.full_text  # property not method
        
        assert "Page 1" in full
        assert "Page 2" in full


@pytest.mark.skipif(not HAS_DOCUMENTS, reason="documents module not available")
class TestSlideContent:
    """Tests for SlideContent dataclass."""
    
    def test_creation(self):
        """Test creating slide content."""
        slide = SlideContent(
            slide_num=1,
            title="Introduction",
            text="Welcome to the presentation",
        )
        
        assert slide.slide_num == 1
        assert slide.title == "Introduction"
    
    def test_with_notes(self):
        """Test slide with speaker notes."""
        slide = SlideContent(
            slide_num=2,
            title="Main Point",
            notes="Remember to emphasize this",
        )
        
        assert slide.notes is not None


@pytest.mark.skipif(not HAS_DOCUMENTS, reason="documents module not available")
class TestPresentationContent:
    """Tests for PresentationContent dataclass."""
    
    def test_creation(self):
        """Test creating presentation."""
        info = DocumentInfo(
            path=Path("/test.pptx"),
            mime_type="application/vnd.openxmlformats",
            size_bytes=2048,
            content_hash="hash",
        )
        pres = PresentationContent(path=Path("/test.pptx"), info=info)
        
        assert pres.slide_count == 0  # property not method
    
    def test_full_text(self):
        """Test full text from slides."""
        info = DocumentInfo(
            path=Path("/test.pptx"),
            mime_type="application/pptx",
            size_bytes=2048,
            content_hash="hash",
        )
        slides = [
            SlideContent(slide_num=1, title="Intro", text="Hello"),
            SlideContent(slide_num=2, title="End", text="Goodbye"),
        ]
        pres = PresentationContent(
            path=Path("/test.pptx"),
            info=info,
            slides=slides,
        )
        
        full = pres.full_text  # property not method
        
        assert "Hello" in full or "Goodbye" in full


@pytest.mark.skipif(not HAS_DOCUMENTS, reason="documents module not available")
class TestDocumentFunctions:
    """Tests for module-level functions."""
    
    def test_detect_document_type_pdf(self):
        """Test detecting PDF type."""
        doc_type = detect_document_type(Path("/some/file.pdf"))
        
        assert doc_type == "pdf"
    
    def test_detect_document_type_docx(self):
        """Test detecting DOCX type."""
        doc_type = detect_document_type(Path("/some/file.docx"))
        
        assert doc_type == "docx"
    
    def test_detect_document_type_pptx(self):
        """Test detecting PPTX type."""
        doc_type = detect_document_type(Path("/some/file.pptx"))
        
        assert doc_type == "pptx"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
