"""
Multimodal alignment module.

Aligns transcripts, OCR results, and scene information into
coherent temporal spans with merged content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from inception.extract.transcription import TranscriptResult, Segment, Word
from inception.extract.scenes import SceneDetectionResult, SceneInfo, KeyframeInfo
from inception.extract.ocr import OCRResult, TextBox


@dataclass
class AlignedSpan:
    """
    A temporal span with aligned multimodal content.
    
    Represents a coherent unit (e.g., a slide presentation segment,
    a talking head segment, a demonstration) across modalities.
    """
    
    start_ms: int
    end_ms: int
    
    # Content from different modalities
    transcript_text: str | None = None
    transcript_segments: list[Segment] = field(default_factory=list)
    
    ocr_text: str | None = None
    ocr_boxes: list[TextBox] = field(default_factory=list)
    
    # Scene info
    scene_info: SceneInfo | None = None
    keyframe_path: Path | None = None
    scene_type: str | None = None
    
    # Quality metrics
    transcript_confidence: float = 1.0
    ocr_confidence: float = 1.0
    alignment_confidence: float = 1.0
    
    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms
    
    @property
    def has_transcript(self) -> bool:
        return bool(self.transcript_text)
    
    @property
    def has_ocr(self) -> bool:
        return bool(self.ocr_text)
    
    @property
    def combined_text(self) -> str:
        """Get combined text from all modalities."""
        parts = []
        if self.transcript_text:
            parts.append(self.transcript_text)
        if self.ocr_text:
            parts.append(f"[Visual: {self.ocr_text}]")
        return " ".join(parts)


@dataclass
class AlignmentResult:
    """Result of multimodal alignment."""
    
    spans: list[AlignedSpan] = field(default_factory=list)
    
    # Source info
    source_path: Path | None = None
    duration_ms: int = 0
    
    # Statistics
    transcript_coverage: float = 0.0
    ocr_coverage: float = 0.0
    
    @property
    def span_count(self) -> int:
        return len(self.spans)
    
    def get_spans_at_time(self, timestamp_ms: int) -> list[AlignedSpan]:
        """Get spans that contain a timestamp."""
        return [
            span for span in self.spans
            if span.start_ms <= timestamp_ms <= span.end_ms
        ]
    
    def get_spans_in_range(
        self,
        start_ms: int,
        end_ms: int,
    ) -> list[AlignedSpan]:
        """Get spans that overlap with a time range."""
        return [
            span for span in self.spans
            if span.start_ms < end_ms and span.end_ms > start_ms
        ]


class MultimodalAligner:
    """
    Aligner for multimodal content (transcript, OCR, scenes).
    
    Produces coherent temporal spans from heterogeneous inputs.
    """
    
    def __init__(
        self,
        scene_boundary_weight: float = 0.8,
        ocr_change_weight: float = 0.3,
        transcript_pause_threshold_ms: int = 3000,
    ):
        """
        Initialize the aligner.
        
        Args:
            scene_boundary_weight: Weight for scene boundaries in span detection
            ocr_change_weight: Weight for OCR content changes
            transcript_pause_threshold_ms: Transcript pause threshold for span breaks
        """
        self.scene_boundary_weight = scene_boundary_weight
        self.ocr_change_weight = ocr_change_weight
        self.transcript_pause_threshold_ms = transcript_pause_threshold_ms
    
    def align(
        self,
        transcript: TranscriptResult | None = None,
        scenes: SceneDetectionResult | None = None,
        ocr_results: dict[int, OCRResult] | None = None,
    ) -> AlignmentResult:
        """
        Align multimodal content into coherent spans.
        
        Args:
            transcript: Transcription result with segments
            scenes: Scene detection result with scenes and keyframes
            ocr_results: Dict mapping scene_num -> OCRResult
        
        Returns:
            AlignmentResult with aligned spans
        """
        # Determine duration
        duration_ms = 0
        if scenes:
            duration_ms = scenes.duration_ms
        elif transcript:
            if transcript.segments:
                duration_ms = max(seg.end_ms for seg in transcript.segments)
        
        # Use scene boundaries as primary span boundaries
        spans: list[AlignedSpan] = []
        
        if scenes and scenes.scenes:
            for scene in scenes.scenes:
                span = AlignedSpan(
                    start_ms=scene.start_ms,
                    end_ms=scene.end_ms,
                    scene_info=scene,
                    keyframe_path=scene.keyframe_path,
                    scene_type=scene.scene_type,
                )
                
                # Align transcript segments to this span
                if transcript:
                    aligned_segments = self._align_transcript_to_span(
                        transcript, span.start_ms, span.end_ms
                    )
                    if aligned_segments:
                        span.transcript_segments = aligned_segments
                        span.transcript_text = " ".join(
                            seg.text for seg in aligned_segments
                        )
                        span.transcript_confidence = sum(
                            seg.avg_log_prob or 0 for seg in aligned_segments
                        ) / len(aligned_segments) if aligned_segments else 0
                
                # Align OCR results to this span
                if ocr_results and scene.scene_num in ocr_results:
                    ocr_result = ocr_results[scene.scene_num]
                    span.ocr_boxes = ocr_result.text_boxes
                    span.ocr_text = ocr_result.full_text
                    span.ocr_confidence = ocr_result.avg_confidence
                
                spans.append(span)
        
        elif transcript:
            # No scenes - create spans from transcript pauses
            spans = self._create_spans_from_transcript(transcript)
        
        # Compute coverage
        transcript_coverage = 0.0
        ocr_coverage = 0.0
        
        if spans:
            covered_with_transcript = sum(
                s.duration_ms for s in spans if s.has_transcript
            )
            covered_with_ocr = sum(
                s.duration_ms for s in spans if s.has_ocr
            )
            
            if duration_ms > 0:
                transcript_coverage = covered_with_transcript / duration_ms
                ocr_coverage = covered_with_ocr / duration_ms
        
        return AlignmentResult(
            spans=spans,
            source_path=transcript.audio_path if transcript else None,
            duration_ms=duration_ms,
            transcript_coverage=transcript_coverage,
            ocr_coverage=ocr_coverage,
        )
    
    def _align_transcript_to_span(
        self,
        transcript: TranscriptResult,
        start_ms: int,
        end_ms: int,
    ) -> list[Segment]:
        """Get transcript segments that overlap with a time range."""
        aligned = []
        
        for segment in transcript.segments:
            # Check overlap
            if segment.start_ms < end_ms and segment.end_ms > start_ms:
                aligned.append(segment)
        
        return aligned
    
    def _create_spans_from_transcript(
        self,
        transcript: TranscriptResult,
    ) -> list[AlignedSpan]:
        """Create spans from transcript based on pauses."""
        if not transcript.segments:
            return []
        
        spans = []
        current_start = transcript.segments[0].start_ms
        current_segments: list[Segment] = []
        
        for i, segment in enumerate(transcript.segments):
            current_segments.append(segment)
            
            # Check for pause before next segment
            is_last = i == len(transcript.segments) - 1
            has_pause = False
            
            if not is_last:
                next_segment = transcript.segments[i + 1]
                gap = next_segment.start_ms - segment.end_ms
                if gap > self.transcript_pause_threshold_ms:
                    has_pause = True
            
            if is_last or has_pause:
                # Create span
                span = AlignedSpan(
                    start_ms=current_start,
                    end_ms=segment.end_ms,
                    transcript_segments=current_segments,
                    transcript_text=" ".join(s.text for s in current_segments),
                )
                spans.append(span)
                
                # Reset for next span
                if not is_last:
                    current_start = transcript.segments[i + 1].start_ms
                    current_segments = []
        
        return spans


def align_video_content(
    transcript: TranscriptResult | None = None,
    scenes: SceneDetectionResult | None = None,
    ocr_results: dict[int, OCRResult] | None = None,
) -> AlignmentResult:
    """
    Convenience function to align video content.
    
    Args:
        transcript: Transcription result
        scenes: Scene detection result
        ocr_results: Dict of scene_num -> OCRResult
    
    Returns:
        AlignmentResult
    """
    aligner = MultimodalAligner()
    return aligner.align(transcript, scenes, ocr_results)


def compute_text_similarity(text1: str, text2: str) -> float:
    """
    Compute similarity between two text strings.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    # Simple Jaccard similarity on words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


def detect_content_change(
    ocr1: OCRResult,
    ocr2: OCRResult,
    threshold: float = 0.3,
) -> bool:
    """
    Detect if OCR content has significantly changed between frames.
    
    Args:
        ocr1: First OCR result
        ocr2: Second OCR result
        threshold: Similarity threshold below which content is considered changed
    
    Returns:
        True if content has changed significantly
    """
    similarity = compute_text_similarity(ocr1.full_text, ocr2.full_text)
    return similarity < threshold
