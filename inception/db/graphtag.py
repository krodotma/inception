"""
Graphtag computation for content-based identity.

Graphtags are stable content hashes that provide semantic identity
for objects in the knowledge graph, independent of their storage NID.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import xxhash


def compute_graphtag(content: dict[str, Any] | str | bytes, algorithm: str = "xxh128") -> str:
    """
    Compute a graphtag (content hash) for the given content.
    
    Args:
        content: The content to hash. Can be:
            - dict: Will be JSON-serialized with sorted keys
            - str: Will be UTF-8 encoded
            - bytes: Used directly
        algorithm: Hash algorithm to use. Options:
            - "xxh128": xxHash 128-bit (default, fast)
            - "xxh64": xxHash 64-bit (faster, shorter)
            - "sha256": SHA-256 (slower, cryptographic)
    
    Returns:
        Hex-encoded hash string (graphtag)
    
    Examples:
        >>> compute_graphtag({"type": "claim", "text": "Python is great"})
        'a1b2c3d4e5f6...'
        >>> compute_graphtag("raw text content")
        'f6e5d4c3b2a1...'
    """
    # Normalize content to bytes
    if isinstance(content, dict):
        # Sort keys for deterministic serialization
        normalized = json.dumps(content, sort_keys=True, separators=(",", ":"))
        data = normalized.encode("utf-8")
    elif isinstance(content, str):
        data = content.encode("utf-8")
    else:
        data = content
    
    # Compute hash based on algorithm
    if algorithm == "xxh128":
        return xxhash.xxh128(data).hexdigest()
    elif algorithm == "xxh64":
        return xxhash.xxh64(data).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


def graphtag_to_bytes(graphtag: str) -> bytes:
    """
    Convert a graphtag hex string to bytes for storage.
    
    Args:
        graphtag: Hex-encoded graphtag string
    
    Returns:
        Raw bytes of the graphtag
    
    Examples:
        >>> graphtag_to_bytes("a1b2c3d4")
        b'\\xa1\\xb2\\xc3\\xd4'
    """
    return bytes.fromhex(graphtag)


def bytes_to_graphtag(data: bytes) -> str:
    """
    Convert graphtag bytes back to hex string.
    
    Args:
        data: Raw graphtag bytes
    
    Returns:
        Hex-encoded graphtag string
    
    Examples:
        >>> bytes_to_graphtag(b'\\xa1\\xb2\\xc3\\xd4')
        'a1b2c3d4'
    """
    return data.hex()


def compute_content_hash(data: bytes, algorithm: str = "sha256") -> str:
    """
    Compute a content hash for raw file data.
    
    This is used for artifact deduplication and integrity checking.
    
    Args:
        data: Raw bytes to hash
        algorithm: Hash algorithm ("sha256", "xxh128", "xxh64")
    
    Returns:
        Hex-encoded hash string
    """
    if algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    elif algorithm == "xxh128":
        return xxhash.xxh128(data).hexdigest()
    elif algorithm == "xxh64":
        return xxhash.xxh64(data).hexdigest()
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


def compute_file_hash(path: str, algorithm: str = "sha256", chunk_size: int = 65536) -> str:
    """
    Compute a content hash for a file.
    
    Reads the file in chunks to handle large files efficiently.
    
    Args:
        path: Path to the file
        algorithm: Hash algorithm ("sha256", "xxh128", "xxh64")
        chunk_size: Size of chunks to read
    
    Returns:
        Hex-encoded hash string
    """
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "xxh128":
        hasher = xxhash.xxh128()
    elif algorithm == "xxh64":
        hasher = xxhash.xxh64()
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    
    return hasher.hexdigest()
