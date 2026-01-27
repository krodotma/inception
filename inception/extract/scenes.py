"""
Scene detection and keyframe extraction module.

Uses PySceneDetect for detecting scene changes and extracting
representative keyframes for OCR processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

from inception.config import get_config


@dataclass
class SceneInfo:
    """Information about a detected scene."""
    
    scene_num: int
    start_ms: int
    end_ms: int
    
    # Keyframe info
    keyframe_time_ms: int | None = None
    keyframe_path: Path | None = None
    
    # Scene characteristics
    scene_type: str | None = None  # 'slide', 'video', 'screenshare', 'talking_head'
    avg_motion: float | None = None
    dominant_colors: list[tuple[int, int, int]] = field(default_factory=list)
    
    # Text detection hints
    has_text_overlay: bool = False
    text_region_ratio: float = 0.0
    
    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass
class KeyframeInfo:
    """Information about an extracted keyframe."""
    
    frame_num: int
    timestamp_ms: int
    path: Path
    
    # Image properties
    width: int = 0
    height: int = 0
    
    # Quality metrics
    blur_score: float = 0.0  # Higher is sharper
    brightness: float = 0.0
    contrast: float = 0.0
    
    # Content analysis
    scene_type: str | None = None
    text_probability: float = 0.0


@dataclass
class SceneDetectionResult:
    """Result of scene detection on a video."""
    
    video_path: Path
    scenes: list[SceneInfo] = field(default_factory=list)
    keyframes: list[KeyframeInfo] = field(default_factory=list)
    
    # Video properties
    duration_ms: int = 0
    fps: float = 0.0
    width: int = 0
    height: int = 0
    frame_count: int = 0
    
    @property
    def scene_count(self) -> int:
        return len(self.scenes)


class SceneDetector:
    """
    Scene detector using PySceneDetect.
    
    Detects scene changes and extracts representative keyframes.
    """
    
    def __init__(
        self,
        threshold: float = 27.0,
        min_scene_length_ms: int = 1000,
        adaptive_threshold: bool = True,
    ):
        """
        Initialize the scene detector.
        
        Args:
            threshold: Content detection threshold (default: 27.0)
            min_scene_length_ms: Minimum scene length in milliseconds
            adaptive_threshold: Whether to use adaptive thresholding
        """
        self.threshold = threshold
        self.min_scene_length_ms = min_scene_length_ms
        self.adaptive_threshold = adaptive_threshold
    
    def detect_scenes(
        self,
        video_path: Path | str,
        output_dir: Path | None = None,
        extract_keyframes: bool = True,
        max_keyframes: int | None = None,
    ) -> SceneDetectionResult:
        """
        Detect scenes in a video.
        
        Args:
            video_path: Path to video file
            output_dir: Directory for keyframe output
            extract_keyframes: Whether to extract keyframe images
            max_keyframes: Maximum number of keyframes to extract
        
        Returns:
            SceneDetectionResult with scenes and keyframes
        """
        from scenedetect import SceneManager, open_video
        from scenedetect.detectors import ContentDetector, AdaptiveDetector
        
        video_path = Path(video_path)
        config = get_config()
        
        if output_dir is None:
            output_dir = config.artifacts_dir / "keyframes" / video_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open video
        video = open_video(str(video_path))
        fps = video.frame_rate
        duration_ms = int(video.duration.get_seconds() * 1000)
        
        # Get video properties
        cap = cv2.VideoCapture(str(video_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        # Create scene manager
        scene_manager = SceneManager()
        
        if self.adaptive_threshold:
            scene_manager.add_detector(AdaptiveDetector(
                adaptive_threshold=self.threshold,
                min_scene_len=int(self.min_scene_length_ms * fps / 1000),
            ))
        else:
            scene_manager.add_detector(ContentDetector(
                threshold=self.threshold,
                min_scene_len=int(self.min_scene_length_ms * fps / 1000),
            ))
        
        # Detect scenes
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()
        
        # If no scenes detected, treat entire video as one scene
        if not scene_list:
            scene_list = [(video.base_timecode, video.duration)]
        
        # Convert to SceneInfo objects
        scenes: list[SceneInfo] = []
        for i, (start_time, end_time) in enumerate(scene_list):
            scene = SceneInfo(
                scene_num=i,
                start_ms=int(start_time.get_seconds() * 1000),
                end_ms=int(end_time.get_seconds() * 1000),
            )
            scenes.append(scene)
        
        # Extract keyframes
        keyframes: list[KeyframeInfo] = []
        if extract_keyframes:
            keyframes = self._extract_keyframes(
                video_path,
                scenes,
                output_dir,
                fps,
                max_keyframes,
            )
            
            # Associate keyframes with scenes
            for scene in scenes:
                for kf in keyframes:
                    if scene.start_ms <= kf.timestamp_ms <= scene.end_ms:
                        scene.keyframe_time_ms = kf.timestamp_ms
                        scene.keyframe_path = kf.path
                        break
        
        return SceneDetectionResult(
            video_path=video_path,
            scenes=scenes,
            keyframes=keyframes,
            duration_ms=duration_ms,
            fps=fps,
            width=width,
            height=height,
            frame_count=frame_count,
        )
    
    def _extract_keyframes(
        self,
        video_path: Path,
        scenes: list[SceneInfo],
        output_dir: Path,
        fps: float,
        max_keyframes: int | None = None,
    ) -> list[KeyframeInfo]:
        """Extract keyframes from detected scenes."""
        cap = cv2.VideoCapture(str(video_path))
        keyframes = []
        
        # Limit scenes if max_keyframes specified
        scenes_to_process = scenes[:max_keyframes] if max_keyframes else scenes
        
        for scene in scenes_to_process:
            # Get frame at middle of scene or 1/3 into it
            keyframe_ms = scene.start_ms + (scene.duration_ms // 3)
            frame_num = int(keyframe_ms * fps / 1000)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # Save keyframe
                keyframe_path = output_dir / f"scene_{scene.scene_num:04d}.jpg"
                cv2.imwrite(str(keyframe_path), frame)
                
                # Compute quality metrics
                blur_score = self._compute_blur_score(frame)
                brightness, contrast = self._compute_brightness_contrast(frame)
                
                keyframe = KeyframeInfo(
                    frame_num=frame_num,
                    timestamp_ms=keyframe_ms,
                    path=keyframe_path,
                    width=frame.shape[1],
                    height=frame.shape[0],
                    blur_score=blur_score,
                    brightness=brightness,
                    contrast=contrast,
                )
                keyframes.append(keyframe)
        
        cap.release()
        return keyframes
    
    def _compute_blur_score(self, frame: np.ndarray) -> float:
        """Compute blur score using Laplacian variance."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    def _compute_brightness_contrast(
        self,
        frame: np.ndarray,
    ) -> tuple[float, float]:
        """Compute brightness and contrast of frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))
        return brightness, contrast


def classify_scene_type(
    keyframe_path: Path,
    blur_threshold: float = 100.0,
    text_threshold: float = 0.3,
) -> str:
    """
    Classify a scene based on its keyframe.
    
    Args:
        keyframe_path: Path to keyframe image
        blur_threshold: Threshold for considering frame sharp
        text_threshold: Ratio of text regions to consider as slide
    
    Returns:
        Scene type: 'slide', 'screenshare', 'talking_head', 'video', 'unknown'
    """
    frame = cv2.imread(str(keyframe_path))
    if frame is None:
        return "unknown"
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Check for high text content (slides, screenshares)
    # Using simple edge detection as proxy for text
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = np.sum(edges > 0) / edges.size
    
    # Check color distribution
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    avg_saturation = np.mean(saturation)
    
    # Classify based on characteristics
    if edge_ratio > 0.1 and avg_saturation < 50:
        # High edges, low saturation = likely slide or code
        return "slide"
    elif edge_ratio > 0.1:
        return "screenshare"
    elif avg_saturation > 80:
        return "video"
    else:
        # Assume talking head for moderate saturation, low edges
        return "talking_head"


def extract_keyframes_uniform(
    video_path: Path | str,
    output_dir: Path | None = None,
    interval_ms: int = 5000,
    max_keyframes: int = 100,
) -> list[KeyframeInfo]:
    """
    Extract keyframes at uniform intervals.
    
    Args:
        video_path: Path to video file
        output_dir: Output directory for keyframes
        interval_ms: Interval between keyframes in milliseconds
        max_keyframes: Maximum number of keyframes
    
    Returns:
        List of extracted KeyframeInfo objects
    """
    video_path = Path(video_path)
    config = get_config()
    
    if output_dir is None:
        output_dir = config.artifacts_dir / "keyframes" / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_ms = int(frame_count / fps * 1000)
    
    keyframes = []
    timestamp = 0
    
    while timestamp < duration_ms and len(keyframes) < max_keyframes:
        frame_num = int(timestamp * fps / 1000)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        
        ret, frame = cap.read()
        if not ret:
            break
        
        keyframe_path = output_dir / f"frame_{timestamp:08d}.jpg"
        cv2.imwrite(str(keyframe_path), frame)
        
        keyframe = KeyframeInfo(
            frame_num=frame_num,
            timestamp_ms=timestamp,
            path=keyframe_path,
            width=frame.shape[1],
            height=frame.shape[0],
        )
        keyframes.append(keyframe)
        
        timestamp += interval_ms
    
    cap.release()
    return keyframes
