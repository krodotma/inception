"""
Unit tests for extract/scenes.py

Tests for scene detection:
- SceneInfo, KeyframeInfo: Data classes
- SceneDetectionResult: Result class
- SceneDetector: Main detector
"""

import pytest
from pathlib import Path

try:
    from inception.extract.scenes import (
        SceneInfo,
        KeyframeInfo,
        SceneDetectionResult,
        SceneDetector,
    )
    HAS_SCENES = True
except ImportError:
    HAS_SCENES = False


@pytest.mark.skipif(not HAS_SCENES, reason="scenes module not available")
class TestSceneInfo:
    """Tests for SceneInfo dataclass."""
    
    def test_creation(self):
        """Test creating scene info."""
        scene = SceneInfo(
            scene_num=1,
            start_ms=0,
            end_ms=5000,
        )
        
        assert scene.scene_num == 1
        assert scene.start_ms == 0
    
    def test_duration_ms(self):
        """Test duration calculation."""
        scene = SceneInfo(
            scene_num=1,
            start_ms=1000,
            end_ms=6000,
        )
        
        assert scene.duration_ms == 5000  # property
    
    def test_with_keyframe(self):
        """Test scene with keyframe path."""
        scene = SceneInfo(
            scene_num=2,
            start_ms=5000,
            end_ms=10000,
            keyframe_path=Path("/frames/scene_2.jpg"),
            scene_type="slide",
        )
        
        assert scene.keyframe_path is not None
        assert scene.scene_type == "slide"


@pytest.mark.skipif(not HAS_SCENES, reason="scenes module not available")
class TestKeyframeInfo:
    """Tests for KeyframeInfo dataclass."""
    
    def test_creation(self):
        """Test creating keyframe info."""
        kf = KeyframeInfo(
            frame_num=100,
            timestamp_ms=3333,
            path=Path("/frames/frame_100.jpg"),
        )
        
        assert kf.frame_num == 100
        assert kf.timestamp_ms == 3333
    
    def test_with_quality_metrics(self):
        """Test keyframe with quality metrics."""
        kf = KeyframeInfo(
            frame_num=200,
            timestamp_ms=6666,
            path=Path("/frames/frame_200.jpg"),
            blur_score=150.0,
            brightness=0.5,
            contrast=0.7,
        )
        
        assert kf.blur_score == 150.0


@pytest.mark.skipif(not HAS_SCENES, reason="scenes module not available")
class TestSceneDetectionResult:
    """Tests for SceneDetectionResult dataclass."""
    
    def test_creation(self):
        """Test creating result."""
        result = SceneDetectionResult(video_path=Path("/video.mp4"))
        
        assert result.video_path == Path("/video.mp4")
        assert result.scene_count == 0  # property
    
    def test_with_scenes(self):
        """Test result with scenes."""
        scenes = [
            SceneInfo(scene_num=1, start_ms=0, end_ms=5000),
            SceneInfo(scene_num=2, start_ms=5000, end_ms=10000),
        ]
        result = SceneDetectionResult(
            video_path=Path("/video.mp4"),
            scenes=scenes,
            duration_ms=10000,
        )
        
        assert result.scene_count == 2


@pytest.mark.skipif(not HAS_SCENES, reason="scenes module not available")
class TestSceneDetector:
    """Tests for SceneDetector."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        detector = SceneDetector()
        
        assert detector.threshold == 27.0
    
    def test_creation_custom(self):
        """Test creating with custom params."""
        detector = SceneDetector(
            threshold=30.0,
            min_scene_length_ms=2000,
        )
        
        assert detector.threshold == 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
