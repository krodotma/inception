"""Tests for vector embedding and search module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from inception.enhance.vectors.embedding import (
    EmbeddingModel,
    get_embedding_model,
    MODELS,
)
from inception.enhance.vectors.store import (
    VectorStore,
    InMemoryVectorStore,
    VectorSearchResult,
)
from inception.enhance.vectors.index import (
    VectorIndex,
    HybridSearcher,
    IndexStats,
)


class TestVectorSearchResult:
    """Tests for VectorSearchResult dataclass."""
    
    def test_creation(self):
        """Test basic result creation."""
        result = VectorSearchResult(
            nid=42,
            score=0.95,
            text="Test text",
            metadata={"node_kind": "CLAIM", "confidence": 0.8},
        )
        
        assert result.nid == 42
        assert result.score == 0.95
        assert result.text == "Test text"
    
    def test_node_kind_property(self):
        """Test node_kind extraction from metadata."""
        result = VectorSearchResult(
            nid=1,
            score=0.5,
            text="Test",
            metadata={"node_kind": "ENTITY"},
        )
        
        assert result.node_kind == "ENTITY"
    
    def test_source_nids_property(self):
        """Test source_nids extraction from metadata."""
        result = VectorSearchResult(
            nid=1,
            score=0.5,
            text="Test",
            metadata={"source_nids": [1, 2, 3]},
        )
        
        assert result.source_nids == [1, 2, 3]
    
    def test_confidence_property(self):
        """Test confidence extraction from metadata."""
        result = VectorSearchResult(
            nid=1,
            score=0.5,
            text="Test",
            metadata={"confidence": 0.75},
        )
        
        assert result.confidence == 0.75
    
    def test_missing_metadata(self):
        """Test defaults for missing metadata."""
        result = VectorSearchResult(nid=1, score=0.5, text="Test")
        
        assert result.node_kind is None
        assert result.source_nids == []
        assert result.confidence == 1.0


class TestInMemoryVectorStore:
    """Tests for InMemoryVectorStore."""
    
    @pytest.fixture
    def store(self):
        """Create a fresh in-memory store."""
        return InMemoryVectorStore()
    
    def test_add_and_count(self, store):
        """Test adding vectors and counting."""
        store.add(
            nids=[1, 2, 3],
            embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
            texts=["text1", "text2", "text3"],
        )
        
        assert store.count() == 3
    
    def test_add_with_metadata(self, store):
        """Test adding vectors with metadata."""
        store.add(
            nids=[1],
            embeddings=[[0.1, 0.2, 0.3]],
            texts=["test"],
            metadatas=[{"node_kind": "CLAIM"}],
        )
        
        assert store.count() == 1
    
    def test_search_basic(self, store):
        """Test basic similarity search."""
        # Add some vectors
        store.add(
            nids=[1, 2, 3],
            embeddings=[
                [1.0, 0.0],  # Similar to query
                [0.0, 1.0],  # Different
                [0.9, 0.1],  # Also similar
            ],
            texts=["similar1", "different", "similar2"],
        )
        
        # Search with query similar to first vector
        results = store.search(
            query_embedding=[1.0, 0.0],
            top_k=2,
        )
        
        assert len(results) == 2
        assert results[0].nid == 1  # Most similar
        assert results[0].score > results[1].score
    
    def test_search_with_filter(self, store):
        """Test search with metadata filter."""
        store.add(
            nids=[1, 2],
            embeddings=[[1.0, 0.0], [1.0, 0.0]],  # Same embedding
            texts=["claim", "entity"],
            metadatas=[
                {"node_kind": "CLAIM"},
                {"node_kind": "ENTITY"},
            ],
        )
        
        # Filter to only CLAIM
        results = store.search(
            query_embedding=[1.0, 0.0],
            top_k=10,
            filter_metadata={"node_kind": "CLAIM"},
        )
        
        assert len(results) == 1
        assert results[0].nid == 1
    
    def test_delete(self, store):
        """Test deleting vectors."""
        store.add(
            nids=[1, 2, 3],
            embeddings=[[0.1], [0.2], [0.3]],
            texts=["a", "b", "c"],
        )
        
        store.delete([1, 2])
        
        assert store.count() == 1
    
    def test_clear(self, store):
        """Test clearing all vectors."""
        store.add(
            nids=[1, 2, 3],
            embeddings=[[0.1], [0.2], [0.3]],
            texts=["a", "b", "c"],
        )
        
        store.clear()
        
        assert store.count() == 0


class TestEmbeddingModelConfig:
    """Tests for embedding model configuration."""
    
    def test_model_aliases(self):
        """Test that model aliases are defined."""
        assert "default" in MODELS
        assert "fast" in MODELS
        assert "quality" in MODELS
    
    def test_initialization(self):
        """Test model initialization (without loading)."""
        model = EmbeddingModel(model_name="default")
        
        assert model.model_name == MODELS["default"]
        assert model._model is None  # Lazy loading
    
    def test_custom_model_name(self):
        """Test using a custom model name."""
        model = EmbeddingModel(model_name="custom-model")
        
        assert model.model_name == "custom-model"


class TestVectorIndex:
    """Tests for VectorIndex."""
    
    @pytest.fixture
    def mock_embedding_model(self):
        """Create a mock embedding model."""
        model = Mock(spec=EmbeddingModel)
        model.model_name = "mock"
        model.dimension = 3
        model.encode_single.return_value = [0.1, 0.2, 0.3]
        model.encode_batch.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]
        return model
    
    @pytest.fixture
    def index(self, mock_embedding_model):
        """Create a vector index with mock embedding."""
        store = InMemoryVectorStore()
        return VectorIndex(
            store=store,
            embedding_model=mock_embedding_model,
        )
    
    def test_initialization(self, index):
        """Test index initialization."""
        assert index.store is not None
        assert index.embedding_model is not None
    
    def test_index_texts(self, index, mock_embedding_model):
        """Test indexing texts."""
        count = index.index_texts(
            nids=[1, 2],
            texts=["hello", "world"],
        )
        
        assert count == 2
        assert index.store.count() == 2
        mock_embedding_model.encode_batch.assert_called_once()
    
    def test_index_with_metadata(self, index):
        """Test indexing with metadata."""
        index.index_texts(
            nids=[1],
            texts=["test"],
            metadatas=[{"node_kind": "CLAIM"}],
        )
        
        results = index.search("test")
        assert len(results) == 1
    
    def test_search(self, index, mock_embedding_model):
        """Test searching the index."""
        # Index some texts
        index.index_texts(nids=[1, 2], texts=["hello", "world"])
        
        # Search
        results = index.search("hello", top_k=5)
        
        assert len(results) <= 5
        mock_embedding_model.encode_single.assert_called()
    
    def test_stats(self, index):
        """Test getting index stats."""
        index.index_texts(nids=[1], texts=["test"])
        
        stats = index.stats
        
        assert isinstance(stats, IndexStats)
        assert stats.total_vectors == 1
        assert stats.store_type == "InMemoryVectorStore"
    
    def test_clear(self, index):
        """Test clearing the index."""
        index.index_texts(nids=[1], texts=["test"])
        index.clear()
        
        assert index.store.count() == 0


class TestHybridSearcher:
    """Tests for HybridSearcher."""
    
    @pytest.fixture
    def mock_index(self):
        """Create a mock vector index."""
        index = Mock(spec=VectorIndex)
        index.search.return_value = [
            VectorSearchResult(
                nid=1, score=0.9, text="claim 1",
                metadata={"node_kind": "CLAIM", "confidence": 0.9},
            ),
            VectorSearchResult(
                nid=2, score=0.8, text="entity 1",
                metadata={"node_kind": "ENTITY", "confidence": 0.7},
            ),
            VectorSearchResult(
                nid=3, score=0.7, text="claim 2",
                metadata={"node_kind": "CLAIM", "confidence": 0.5},
            ),
        ]
        return index
    
    @pytest.fixture
    def searcher(self, mock_index):
        """Create a hybrid searcher."""
        return HybridSearcher(vector_index=mock_index)
    
    def test_initialization(self, searcher, mock_index):
        """Test searcher initialization."""
        assert searcher.vector_index == mock_index
    
    def test_search_no_filter(self, searcher):
        """Test search without filters."""
        results = searcher.search("query", top_k=10)
        
        assert len(results) == 3
    
    def test_search_node_kind_filter(self, searcher):
        """Test search with node kind filter."""
        results = searcher.search(
            "query",
            top_k=10,
            node_kinds=["CLAIM"],
        )
        
        assert len(results) == 2
        assert all(r.node_kind == "CLAIM" for r in results)
    
    def test_search_confidence_filter(self, searcher):
        """Test search with confidence filter."""
        results = searcher.search(
            "query",
            top_k=10,
            min_confidence=0.6,
        )
        
        assert len(results) == 2
        assert all(r.confidence >= 0.6 for r in results)
    
    def test_search_combined_filters(self, searcher):
        """Test search with multiple filters."""
        results = searcher.search(
            "query",
            top_k=10,
            node_kinds=["CLAIM"],
            min_confidence=0.8,
        )
        
        assert len(results) == 1
        assert results[0].nid == 1


class TestGetEmbeddingModel:
    """Tests for get_embedding_model factory."""
    
    def test_caching(self):
        """Test that models are cached."""
        # Clear cache first
        get_embedding_model.cache_clear()
        
        model1 = get_embedding_model("default")
        model2 = get_embedding_model("default")
        
        assert model1 is model2
    
    def test_different_models(self):
        """Test that different model names return different instances."""
        get_embedding_model.cache_clear()
        
        model1 = get_embedding_model("default")
        model2 = get_embedding_model("quality")
        
        assert model1 is not model2
