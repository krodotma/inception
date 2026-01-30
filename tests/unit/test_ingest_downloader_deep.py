"""
Deep tests for ingest/downloader.py
"""
import pytest

try:
    from inception.ingest.downloader import Downloader
    HAS_DOWNLOADER = True
except ImportError:
    HAS_DOWNLOADER = False

@pytest.mark.skipif(not HAS_DOWNLOADER, reason="downloader not available")
class TestDownloaderDeep:
    def test_creation(self):
        downloader = Downloader()
        assert downloader is not None
    
    def test_has_download(self):
        assert hasattr(Downloader, "download")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
