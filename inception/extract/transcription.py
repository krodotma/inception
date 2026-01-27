"""
Audio transcription module using faster-whisper.

Handles transcription of audio files with word-level timestamps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from inception.config import get_config


@dataclass
class Word:
    """A single transcribed word with timing."""
    
    text: str
    start_ms: int
    end_ms: int
    probability: float = 1.0
    
    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass
class Segment:
    """A segment of transcription (usually a sentence or phrase)."""
    
    id: int
    text: str
    start_ms: int
    end_ms: int
    words: list[Word] = field(default_factory=list)
    
    # Quality metrics
    avg_log_prob: float | None = None
    no_speech_prob: float | None = None
    compression_ratio: float | None = None
    
    # Speaker info (if diarization enabled)
    speaker: str | None = None
    
    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms
    
    @property
    def word_count(self) -> int:
        return len(self.words) if self.words else len(self.text.split())


@dataclass
class TranscriptResult:
    """Full transcription result."""
    
    audio_path: Path
    segments: list[Segment] = field(default_factory=list)
    
    # Metadata
    language: str | None = None
    language_probability: float | None = None
    duration_seconds: float | None = None
    
    # Processing info
    model_name: str | None = None
    processing_time_seconds: float | None = None
    
    @property
    def full_text(self) -> str:
        """Get full transcript as a single string."""
        return " ".join(seg.text for seg in self.segments)
    
    @property
    def word_count(self) -> int:
        return sum(seg.word_count for seg in self.segments)
    
    def get_text_at_time(self, timestamp_ms: int) -> str | None:
        """Get the word/segment at a specific timestamp."""
        for segment in self.segments:
            if segment.start_ms <= timestamp_ms <= segment.end_ms:
                if segment.words:
                    for word in segment.words:
                        if word.start_ms <= timestamp_ms <= word.end_ms:
                            return word.text
                return segment.text
        return None
    
    def get_segments_in_range(
        self,
        start_ms: int,
        end_ms: int,
    ) -> list[Segment]:
        """Get segments overlapping a time range."""
        return [
            seg for seg in self.segments
            if seg.start_ms < end_ms and seg.end_ms > start_ms
        ]


class Transcriber:
    """
    Transcriber using faster-whisper.
    
    Provides word-level timestamps and multiple quality metrics.
    """
    
    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cpu, cuda, auto)
            compute_type: Compute type (int8, float16, float32)
        """
        config = get_config()
        
        self.model_size = model_size or config.whisper.model_size
        self.device = device or config.whisper.device
        self.compute_type = compute_type or config.whisper.compute_type
        
        self._model = None
    
    def _get_model(self):
        """Lazy-load the faster-whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel
            
            # Determine device
            device = self.device
            if device == "auto":
                try:
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    device = "cpu"
            
            self._model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=self.compute_type,
            )
        
        return self._model
    
    def transcribe(
        self,
        audio_path: Path | str,
        language: str | None = None,
        word_timestamps: bool = True,
        vad_filter: bool = True,
    ) -> TranscriptResult:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to audio file
            language: Target language code (None for auto-detect)
            word_timestamps: Whether to compute word-level timestamps
            vad_filter: Whether to use Voice Activity Detection
        
        Returns:
            TranscriptResult with segments and words
        """
        import time
        
        audio_path = Path(audio_path)
        model = self._get_model()
        
        start_time = time.time()
        
        segments_gen, info = model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=word_timestamps,
            vad_filter=vad_filter,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400,
            ),
        )
        
        segments = []
        for i, seg in enumerate(segments_gen):
            words = []
            if word_timestamps and seg.words:
                for w in seg.words:
                    words.append(Word(
                        text=w.word.strip(),
                        start_ms=int(w.start * 1000),
                        end_ms=int(w.end * 1000),
                        probability=w.probability,
                    ))
            
            segment = Segment(
                id=i,
                text=seg.text.strip(),
                start_ms=int(seg.start * 1000),
                end_ms=int(seg.end * 1000),
                words=words,
                avg_log_prob=seg.avg_logprob,
                no_speech_prob=seg.no_speech_prob,
                compression_ratio=seg.compression_ratio,
            )
            segments.append(segment)
        
        processing_time = time.time() - start_time
        
        return TranscriptResult(
            audio_path=audio_path,
            segments=segments,
            language=info.language,
            language_probability=info.language_probability,
            duration_seconds=info.duration,
            model_name=self.model_size,
            processing_time_seconds=processing_time,
        )
    
    def transcribe_streaming(
        self,
        audio_path: Path | str,
        language: str | None = None,
    ) -> Iterator[Segment]:
        """
        Transcribe audio and yield segments as they're processed.
        
        Args:
            audio_path: Path to audio file
            language: Target language code
        
        Yields:
            Segment objects as they're transcribed
        """
        model = self._get_model()
        
        segments_gen, info = model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
        )
        
        for i, seg in enumerate(segments_gen):
            words = []
            if seg.words:
                for w in seg.words:
                    words.append(Word(
                        text=w.word.strip(),
                        start_ms=int(w.start * 1000),
                        end_ms=int(w.end * 1000),
                        probability=w.probability,
                    ))
            
            yield Segment(
                id=i,
                text=seg.text.strip(),
                start_ms=int(seg.start * 1000),
                end_ms=int(seg.end * 1000),
                words=words,
                avg_log_prob=seg.avg_logprob,
                no_speech_prob=seg.no_speech_prob,
            )


def transcribe_audio(
    audio_path: Path | str,
    model_size: str | None = None,
    language: str | None = None,
) -> TranscriptResult:
    """
    Convenience function to transcribe an audio file.
    
    Args:
        audio_path: Path to audio file
        model_size: Optional model size override
        language: Optional language code
    
    Returns:
        TranscriptResult
    """
    transcriber = Transcriber(model_size=model_size)
    return transcriber.transcribe(audio_path, language=language)


def parse_vtt_subtitles(vtt_path: Path | str) -> TranscriptResult:
    """
    Parse VTT subtitle file as a transcript.
    
    Args:
        vtt_path: Path to VTT file
    
    Returns:
        TranscriptResult parsed from subtitles
    """
    import webvtt
    
    vtt_path = Path(vtt_path)
    vtt = webvtt.read(str(vtt_path))
    
    segments = []
    for i, caption in enumerate(vtt):
        # Parse timestamps
        start_parts = caption.start.split(":")
        end_parts = caption.end.split(":")
        
        start_ms = _parse_timestamp_to_ms(caption.start)
        end_ms = _parse_timestamp_to_ms(caption.end)
        
        segment = Segment(
            id=i,
            text=caption.text.strip(),
            start_ms=start_ms,
            end_ms=end_ms,
        )
        segments.append(segment)
    
    return TranscriptResult(
        audio_path=vtt_path,
        segments=segments,
    )


def parse_srt_subtitles(srt_path: Path | str) -> TranscriptResult:
    """
    Parse SRT subtitle file as a transcript.
    
    Args:
        srt_path: Path to SRT file
    
    Returns:
        TranscriptResult parsed from subtitles
    """
    import re
    
    srt_path = Path(srt_path)
    
    with open(srt_path, encoding="utf-8") as f:
        content = f.read()
    
    # Parse SRT format
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?:\n\n|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)
    
    segments = []
    for match in matches:
        idx, start, end, text = match
        
        # Convert SRT timestamp to ms
        start_ms = _parse_srt_timestamp_to_ms(start)
        end_ms = _parse_srt_timestamp_to_ms(end)
        
        segment = Segment(
            id=int(idx) - 1,
            text=text.strip().replace("\n", " "),
            start_ms=start_ms,
            end_ms=end_ms,
        )
        segments.append(segment)
    
    return TranscriptResult(
        audio_path=srt_path,
        segments=segments,
    )


def _parse_timestamp_to_ms(timestamp: str) -> int:
    """Parse VTT/SRT timestamp (HH:MM:SS.mmm) to milliseconds."""
    parts = timestamp.replace(",", ".").split(":")
    
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_and_ms = parts[2].split(".")
        seconds = int(seconds_and_ms[0])
        ms = int(seconds_and_ms[1]) if len(seconds_and_ms) > 1 else 0
        
        return (hours * 3600 + minutes * 60 + seconds) * 1000 + ms
    
    return 0


def _parse_srt_timestamp_to_ms(timestamp: str) -> int:
    """Parse SRT timestamp (HH:MM:SS,mmm) to milliseconds."""
    return _parse_timestamp_to_ms(timestamp.replace(",", "."))
