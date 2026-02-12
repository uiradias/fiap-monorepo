"""Analysis result domain models."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis job status."""

    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING_VIDEO = "processing_video"
    PROCESSING_AUDIO = "processing_audio"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class SentimentResult:
    """Sentiment analysis result from Comprehend."""

    sentiment: str  # POSITIVE, NEGATIVE, NEUTRAL, MIXED
    positive_score: float
    negative_score: float
    neutral_score: float
    mixed_score: float
    source_text: str = ""

    def to_dict(self) -> dict:
        return {
            "sentiment": self.sentiment,
            "positive_score": self.positive_score,
            "negative_score": self.negative_score,
            "neutral_score": self.neutral_score,
            "mixed_score": self.mixed_score,
        }


@dataclass(frozen=True)
class TranscriptionSegment:
    """Transcription segment with timing."""

    text: str
    start_time: float  # seconds
    end_time: float
    confidence: float
    speaker_label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence,
            "speaker_label": self.speaker_label,
        }


@dataclass
class AudioAnalysis:
    """Complete audio analysis result."""

    transcription: List[TranscriptionSegment] = field(default_factory=list)
    overall_sentiment: Optional[SentimentResult] = None
    segment_sentiments: List[SentimentResult] = field(default_factory=list)

    @property
    def full_transcript(self) -> str:
        return " ".join(seg.text for seg in self.transcription)

    def to_dict(self) -> dict:
        return {
            "full_transcript": self.full_transcript,
            "segment_count": len(self.transcription),
            "overall_sentiment": self.overall_sentiment.to_dict() if self.overall_sentiment else None,
        }


@dataclass
class ClinicalIndicator:
    """Clinical indicator derived from analysis."""

    indicator_type: str  # discomfort, depression, anxiety, fear
    confidence: float
    evidence: List[str] = field(default_factory=list)
    timestamp_ranges: List[Dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "indicator_type": self.indicator_type,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "timestamp_ranges": self.timestamp_ranges,
        }
