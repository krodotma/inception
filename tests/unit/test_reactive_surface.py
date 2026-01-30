"""
Unit tests for ENTELECHEIA+ Reactive Surface

Tests blob detection, classification, and the ReactiveSurface + operator.
"""

import pytest
from inception.surface.reactive import (
    BlobType,
    BlobClassifier,
    URLDetector,
    RepositoryDetector,
    VideoDetector,
    ReactiveSurface,
    InputNormalizer,
)
from inception.surface.coobject import (
    RheoTransformer,
    CoObjectInferrer,
    CoObjectGraph,
    CoObjectRelation,
)


# =============================================================================
# BLOB DETECTION TESTS
# =============================================================================

class TestBlobDetection:
    """Tests for individual blob detectors."""
    
    def test_url_detection(self):
        """Test URL detection."""
        detector = URLDetector()
        
        # Valid URLs
        assert detector.detect("https://example.com") is not None
        assert detector.detect("http://foo.bar/baz") is not None
        
        # Invalid
        assert detector.detect("not a url") is None
        assert detector.detect("ftp://foo.bar") is None
    
    def test_repository_detection(self):
        """Test repository detection."""
        detector = RepositoryDetector()
        
        # GitHub
        result = detector.detect("https://github.com/user/repo")
        assert result is not None
        assert result.blob_type == BlobType.REPOSITORY
        assert result.metadata["platform"] == "github"
        
        # GitLab
        result = detector.detect("https://gitlab.com/user/repo")
        assert result is not None
        assert result.metadata["platform"] == "gitlab"
    
    def test_video_detection(self):
        """Test video URL detection."""
        detector = VideoDetector()
        
        # YouTube
        result = detector.detect("https://youtube.com/watch?v=abc123")
        assert result is not None
        assert result.blob_type == BlobType.VIDEO
        assert result.metadata["platform"] == "youtube"
        
        # Short URL
        result = detector.detect("https://youtu.be/abc123")
        assert result is not None


class TestBlobClassifier:
    """Tests for the unified classifier."""
    
    def test_classification_priority(self):
        """Repository should take priority over URL."""
        classifier = BlobClassifier()
        
        # Repo URL should be classified as REPOSITORY, not URL
        result = classifier.classify("https://github.com/user/repo")
        assert result.blob_type == BlobType.REPOSITORY
    
    def test_video_priority(self):
        """Video should take priority over URL."""
        classifier = BlobClassifier()
        
        result = classifier.classify("https://youtube.com/watch?v=abc")
        assert result.blob_type == BlobType.VIDEO
    
    def test_idea_fallback(self):
        """Short text should fall back to idea."""
        classifier = BlobClassifier()
        
        result = classifier.classify("What if we could fly?")
        assert result.blob_type == BlobType.IDEA
    
    def test_classify_all_returns_multiple(self):
        """classify_all should return all matches."""
        classifier = BlobClassifier()
        
        # This matches both URL and repo patterns
        results = classifier.classify_all("https://github.com/user/repo")
        
        # Should have at least repo detection
        assert len(results) >= 1
        assert results[0].blob_type == BlobType.REPOSITORY


# =============================================================================
# REACTIVE SURFACE TESTS
# =============================================================================

class TestReactiveSurface:
    """Tests for the ReactiveSurface class."""
    
    def test_add_blob(self):
        """Test adding a blob to the surface."""
        surface = ReactiveSurface()
        
        blob = surface.add("https://github.com/user/repo")
        
        assert blob.blob_type == BlobType.REPOSITORY
        assert blob.blob_id is not None
        assert blob.state == "pending"
    
    def test_plus_operator(self):
        """Test the + operator for adding blobs."""
        surface = ReactiveSurface()
        
        # Use + operator
        blob = surface + "https://youtube.com/watch?v=abc123"
        
        assert blob.blob_type == BlobType.VIDEO
    
    def test_event_emission(self):
        """Test that events are emitted when blobs are added."""
        surface = ReactiveSurface()
        events = []
        
        surface.on(lambda e: events.append(e))
        surface.add("test idea")
        
        assert len(events) == 1
        assert events[0].event_type == "blob_added"
    
    def test_get_state(self):
        """Test surface state retrieval."""
        surface = ReactiveSurface()
        
        surface.add("https://github.com/a/b")
        surface.add("https://github.com/c/d")
        surface.add("Some idea here")
        
        state = surface.get_state()
        
        assert state["blob_count"] == 3
        assert "REPOSITORY" in state["type_distribution"]


class TestInputNormalizer:
    """Tests for input normalization."""
    
    def test_url_normalization(self):
        """Test URL normalization."""
        normalizer = InputNormalizer()
        
        from inception.surface.reactive import DetectionResult
        
        detection = DetectionResult(
            blob_type=BlobType.URL,
            confidence=0.9,
        )
        
        blob = normalizer.normalize("http://example.com/", detection)
        
        # Should convert to https and remove trailing slash
        assert blob.normalized_content == "https://example.com"
    
    def test_repo_normalization(self):
        """Test repository normalization."""
        normalizer = InputNormalizer()
        
        from inception.surface.reactive import DetectionResult
        
        detection = DetectionResult(
            blob_type=BlobType.REPOSITORY,
            confidence=0.9,
        )
        
        blob = normalizer.normalize("https://github.com/user/repo", detection)
        
        assert blob.normalized_content == "github:user/repo"


# =============================================================================
# RHEOMODE TRANSFORMER TESTS
# =============================================================================

class TestRheoTransformer:
    """Tests for Bohm's Rheomode transformation."""
    
    def test_static_to_flowing(self):
        """Test noun to gerund transformation."""
        transformer = RheoTransformer()
        
        result = transformer.static_to_flowing("the thought")
        assert "thinking" in result
    
    def test_get_flowing_form(self):
        """Test getting gerund form."""
        transformer = RheoTransformer()
        
        assert transformer.get_flowing_form("code") == "coding"
        assert transformer.get_flowing_form("design") == "designing"
        assert transformer.get_flowing_form("unknown") == "unknowning"
    
    def test_extract_frozen_concepts(self):
        """Test extracting transformable nouns."""
        transformer = RheoTransformer()
        
        frozen = transformer.extract_frozen_concepts(
            "The thought about code design"
        )
        
        assert "thought" in frozen
        assert "code" in frozen
        assert "design" in frozen


# =============================================================================
# CO-OBJECT INFERENCE TESTS
# =============================================================================

class TestCoObjectInferrer:
    """Tests for co-object inference."""
    
    def test_semantic_inference(self):
        """Test semantic co-object inference."""
        inferrer = CoObjectInferrer()
        
        # Use base noun "code" which get_flowing_form converts to "coding"
        coobjects = inferrer.infer_semantic("code")
        
        assert len(coobjects) > 0
        assert all(co.relation == CoObjectRelation.SEMANTIC for co in coobjects)
    
    def test_causal_inference(self):
        """Test causal co-object inference."""
        inferrer = CoObjectInferrer()
        
        # Use base noun "test" which get_flowing_form converts to "testing"
        coobjects = inferrer.infer_causal("test")
        
        # Testing causes debugging
        concepts = [co.concept for co in coobjects]
        assert "debugging" in concepts
    
    def test_dialectical_inference(self):
        """Test dialectical co-object inference."""
        inferrer = CoObjectInferrer()
        
        coobjects = inferrer.infer_dialectical("theory")
        
        concepts = [co.concept for co in coobjects]
        assert "practice" in concepts
    
    def test_infer_all(self):
        """Test combined inference."""
        inferrer = CoObjectInferrer()
        
        # Use base noun "design" which get_flowing_form converts to "designing"
        coobjects = inferrer.infer_all("design")
        
        # Should have multiple types
        relations = {co.relation for co in coobjects}
        assert len(relations) >= 2


class TestCoObjectGraph:
    """Tests for co-object graph construction."""
    
    def test_add_concept(self):
        """Test adding concepts to graph."""
        graph = CoObjectGraph()
        
        node_id = graph.add_concept("coding")
        
        assert node_id == "coding"
        assert "coding" in graph.nodes
    
    def test_expand_with_coobjects(self):
        """Test graph expansion."""
        graph = CoObjectGraph()
        
        # Use base noun "design" which get_flowing_form converts to "designing"
        new_nodes = graph.expand_with_coobjects("design", depth=1)
        
        assert len(new_nodes) > 0
        assert len(graph.edges) > 0
    
    def test_get_subgraph(self):
        """Test subgraph extraction."""
        graph = CoObjectGraph()
        graph.expand_with_coobjects("coding", depth=2)
        
        subgraph = graph.get_subgraph("coding", max_depth=1)
        
        assert subgraph["root"] == "coding"
        assert subgraph["node_count"] > 0
