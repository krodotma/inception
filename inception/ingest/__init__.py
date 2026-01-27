"""Ingestion layer for acquiring sources."""

from inception.ingest.youtube import (
    VideoMetadata,
    DownloadResult,
    parse_youtube_url,
    fetch_video_metadata,
    download_video,
    list_channel_videos,
    list_playlist_videos,
)
from inception.ingest.web import (
    WebPageContent,
    CrawlResult,
    fetch_page,
    extract_content,
    save_page,
    crawl_site,
)
from inception.ingest.documents import (
    DocumentInfo,
    PDFPage,
    PDFContent,
    SlideContent,
    PresentationContent,
    get_document_info,
    extract_pdf,
    extract_pptx,
    extract_docx,
    extract_xlsx,
    detect_document_type,
)
from inception.ingest.source_manager import (
    SourceFeed,
    IngestJob,
    SourceManager,
    parse_batch_file,
)

__all__ = [
    # YouTube
    "VideoMetadata",
    "DownloadResult",
    "parse_youtube_url",
    "fetch_video_metadata",
    "download_video",
    "list_channel_videos",
    "list_playlist_videos",
    # Web
    "WebPageContent",
    "CrawlResult",
    "fetch_page",
    "extract_content",
    "save_page",
    "crawl_site",
    # Documents
    "DocumentInfo",
    "PDFPage",
    "PDFContent",
    "SlideContent",
    "PresentationContent",
    "get_document_info",
    "extract_pdf",
    "extract_pptx",
    "extract_docx",
    "extract_xlsx",
    "detect_document_type",
    # Source Manager
    "SourceFeed",
    "IngestJob",
    "SourceManager",
    "parse_batch_file",
]
