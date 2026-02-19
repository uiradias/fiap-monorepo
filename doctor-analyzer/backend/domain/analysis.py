"""Analysis result domain models."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis job status."""

    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING_VIDEO = "processing_video"
    PROCESSING_SELF_INJURY = "processing_self_injury"
    PROCESSING_AUDIO = "processing_audio"
    PROCESSING_BEDROCK = "processing_bedrock"
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


@dataclass
class SelfInjuryCheckResult:
    """Result of optional self-injury check (Rekognition content moderation + optional Bedrock enhancement)."""

    enabled: bool
    rekognition_labels: List[Dict[str, Any]]  # name, confidence, timestamp_ms, parent_name
    has_signals: bool  # derived from labels (e.g. Self-Harm, Violence above threshold)
    summary: str
    confidence: float  # max confidence of relevant labels or 0
    error_message: Optional[str] = None
    severity: Optional[str] = None  # low/moderate/high/critical (from Bedrock)
    clinical_rationale: Optional[str] = None  # from Bedrock
    transcript_analysis: Optional[Dict[str, Any]] = None  # from Bedrock verbal analysis

    def to_dict(self) -> dict:
        base = {
            "enabled": self.enabled,
            "rekognition_labels": self.rekognition_labels,
            "bedrock_has_signals": self.has_signals,
            "bedrock_summary": self.summary,
            "bedrock_confidence": self.confidence,
            "error_message": self.error_message,
        }
        if self.severity is not None:
            base["bedrock_severity"] = self.severity
        if self.clinical_rationale is not None:
            base["bedrock_clinical_rationale"] = self.clinical_rationale
        if self.transcript_analysis is not None:
            base["bedrock_transcript_analysis"] = self.transcript_analysis
        return base
