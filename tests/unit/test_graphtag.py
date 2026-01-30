"""
Unit tests for graphtag computation.
"""

import pytest
from inception.db.graphtag import (
    compute_graphtag,
    graphtag_to_bytes,
    bytes_to_graphtag,
    compute_content_hash,
    compute_file_hash,
)


class TestComputeGraphtag:
    """Tests for graphtag computation."""
    
    def test_dict_input(self):
        """Test graphtag for dict input."""
        content = {"type": "claim", "text": "Python is great"}
        tag = compute_graphtag(content)
        assert isinstance(tag, str)
        assert len(tag) == 32  # xxh128 produces 32 hex chars
    
    def test_string_input(self):
        """Test graphtag for string input."""
        tag = compute_graphtag("hello world")
        assert isinstance(tag, str)
        assert len(tag) == 32
    
    def test_bytes_input(self):
        """Test graphtag for bytes input."""
        tag = compute_graphtag(b"hello world")
        assert isinstance(tag, str)
        assert len(tag) == 32
    
    def test_determinism(self):
        """Test that same input produces same output."""
        content = {"a": 1, "b": 2}
        tag1 = compute_graphtag(content)
        tag2 = compute_graphtag(content)
        assert tag1 == tag2
    
    def test_dict_key_order_independent(self):
        """Test that dict key order doesn't affect hash."""
        content1 = {"a": 1, "b": 2}
        content2 = {"b": 2, "a": 1}
        assert compute_graphtag(content1) == compute_graphtag(content2)
    
    def test_different_content_different_hash(self):
        """Test that different content produces different hash."""
        tag1 = compute_graphtag("hello")
        tag2 = compute_graphtag("world")
        assert tag1 != tag2
    
    def test_xxh64_algorithm(self):
        """Test xxh64 algorithm option."""
        tag = compute_graphtag("hello", algorithm="xxh64")
        assert len(tag) == 16  # xxh64 produces 16 hex chars
    
    def test_sha256_algorithm(self):
        """Test sha256 algorithm option."""
        tag = compute_graphtag("hello", algorithm="sha256")
        assert len(tag) == 64  # sha256 produces 64 hex chars
    
    def test_invalid_algorithm(self):
        """Test that invalid algorithm raises error."""
        with pytest.raises(ValueError):
            compute_graphtag("hello", algorithm="md5")


class TestGraphtagBytes:
    """Tests for graphtag byte conversion."""
    
    def test_to_bytes_roundtrip(self):
        """Test conversion to bytes and back."""
        original = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        as_bytes = graphtag_to_bytes(original)
        back = bytes_to_graphtag(as_bytes)
        assert back == original
    
    def test_bytes_length(self):
        """Test that bytes have correct length."""
        tag = compute_graphtag("test")
        as_bytes = graphtag_to_bytes(tag)
        assert len(as_bytes) == 16  # 32 hex chars = 16 bytes


class TestContentHash:
    """Tests for content hashing."""
    
    def test_sha256_hash(self):
        """Test SHA256 content hash."""
        data = b"hello world"
        hash_val = compute_content_hash(data, algorithm="sha256")
        assert len(hash_val) == 64
    
    def test_xxh128_hash(self):
        """Test xxh128 content hash."""
        data = b"hello world"
        hash_val = compute_content_hash(data, algorithm="xxh128")
        assert len(hash_val) == 32
    
    def test_determinism(self):
        """Test that same data produces same hash."""
        data = b"test data"
        hash1 = compute_content_hash(data)
        hash2 = compute_content_hash(data)
        assert hash1 == hash2
    
    def test_xxh64_hash(self):
        """Test xxh64 content hash."""
        data = b"hello world"
        hash_val = compute_content_hash(data, algorithm="xxh64")
        assert len(hash_val) == 16  # xxh64 produces 16 hex chars
    
    def test_invalid_algorithm(self):
        """Test that invalid algorithm raises error."""
        with pytest.raises(ValueError):
            compute_content_hash(b"test", algorithm="md5")


class TestFileHash:
    """Tests for file hashing."""
    
    def test_file_hash_sha256(self, tmp_path):
        """Test SHA256 file hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"hello world")
        
        hash_val = compute_file_hash(str(test_file), algorithm="sha256")
        assert len(hash_val) == 64
    
    def test_file_hash_xxh128(self, tmp_path):
        """Test xxh128 file hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"hello world")
        
        hash_val = compute_file_hash(str(test_file), algorithm="xxh128")
        assert len(hash_val) == 32
    
    def test_file_hash_xxh64(self, tmp_path):
        """Test xxh64 file hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"hello world")
        
        hash_val = compute_file_hash(str(test_file), algorithm="xxh64")
        assert len(hash_val) == 16
    
    def test_file_hash_determinism(self, tmp_path):
        """Test that same file produces same hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"consistent content")
        
        hash1 = compute_file_hash(str(test_file))
        hash2 = compute_file_hash(str(test_file))
        assert hash1 == hash2
    
    def test_file_hash_invalid_algorithm(self, tmp_path):
        """Test that invalid algorithm raises error."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")
        
        with pytest.raises(ValueError):
            compute_file_hash(str(test_file), algorithm="md5")
    
    def test_large_file_chunked(self, tmp_path):
        """Test hashing large file in chunks."""
        test_file = tmp_path / "large.bin"
        # Create a file larger than default chunk size
        test_file.write_bytes(b"x" * 100000)
        
        hash_val = compute_file_hash(str(test_file), algorithm="sha256", chunk_size=1024)
        assert len(hash_val) == 64

