"""Extraction layer for processing modalities."""

from inception.extract.transcription import (
    Word,
    Segment,
    TranscriptResult,
    Transcriber,
    transcribe_audio,
    parse_vtt_subtitles,
    parse_srt_subtitles,
)
from inception.extract.scenes import (
    SceneInfo,
    KeyframeInfo,
    SceneDetectionResult,
    SceneDetector,
    classify_scene_type,
    extract_keyframes_uniform,
)
from inception.extract.ocr import (
    TextBox,
    OCRResult,
    OCREngine,
    ocr_image,
    ocr_keyframes,
    merge_duplicate_boxes,
)
from inception.extract.alignment import (
    AlignedSpan,
    AlignmentResult,
    MultimodalAligner,
    align_video_content,
    compute_text_similarity,
    detect_content_change,
)

__all__ = [
    # Transcription
    "Word",
    "Segment",
    "TranscriptResult",
    "Transcriber",
    "transcribe_audio",
    "parse_vtt_subtitles",
    "parse_srt_subtitles",
    # Scenes
    "SceneInfo",
    "KeyframeInfo",
    "SceneDetectionResult",
    "SceneDetector",
    "classify_scene_type",
    "extract_keyframes_uniform",
    # OCR
    "TextBox",
    "OCRResult",
    "OCREngine",
    "ocr_image",
    "ocr_keyframes",
    "merge_duplicate_boxes",
    # Alignment
    "AlignedSpan",
    "AlignmentResult",
    "MultimodalAligner",
    "align_video_content",
    "compute_text_similarity",
    "detect_content_change",
]
