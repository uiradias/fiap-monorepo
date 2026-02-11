"""Emotion detection domain models."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class EmotionType(str, Enum):
    """Detectable emotion types for medical analysis."""

    DISCOMFORT = "discomfort"
    DEPRESSION = "depression"
    ANXIETY = "anxiety"
    FEAR = "fear"
    CALM = "calm"
    HAPPY = "happy"
    CONFUSED = "confused"
    ANGRY = "angry"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    SAD = "sad"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class EmotionScore:
    """Individual emotion detection score."""

    emotion: EmotionType
    confidence: float  # 0.0 to 1.0

    def to_dict(self) -> dict:
        return {"emotion": self.emotion.value, "confidence": self.confidence}


@dataclass(frozen=True)
class BoundingBox:
    """Face bounding box as percentages of video dimensions."""

    left: float
    top: float
    width: float
    height: float

    def to_dict(self) -> dict:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class FaceDetection:
    """Face detection with emotions at a specific timestamp."""

    timestamp_ms: int
    bounding_box: BoundingBox
    emotions: List[EmotionScore] = field(default_factory=list)
    age_range: Optional[dict] = None
    gender: Optional[str] = None

    @property
    def primary_emotion(self) -> Optional[EmotionScore]:
        """Get the emotion with highest confidence."""
        if not self.emotions:
            return None
        return max(self.emotions, key=lambda e: e.confidence)

    def to_dict(self) -> dict:
        return {
            "timestamp_ms": self.timestamp_ms,
            "bounding_box": self.bounding_box.to_dict(),
            "emotions": [e.to_dict() for e in self.emotions],
            "primary_emotion": self.primary_emotion.to_dict() if self.primary_emotion else None,
            "age_range": self.age_range,
            "gender": self.gender,
        }


@dataclass
class VideoEmotionTimeline:
    """Complete emotion timeline for a video."""

    video_id: str
    duration_ms: int
    detections: List[FaceDetection] = field(default_factory=list)

    def add_detection(self, detection: FaceDetection) -> None:
        """Add a detection to the timeline."""
        self.detections.append(detection)

    def get_detections_at(self, timestamp_ms: int, tolerance_ms: int = 500) -> List[FaceDetection]:
        """Get detections within tolerance of timestamp."""
        return [
            d for d in self.detections
            if abs(d.timestamp_ms - timestamp_ms) <= tolerance_ms
        ]

    def get_emotion_summary(self) -> dict:
        """Calculate average confidence for each emotion across all detections."""
        emotion_scores: dict = {}
        emotion_counts: dict = {}

        for detection in self.detections:
            for score in detection.emotions:
                emotion_name = score.emotion.value
                if emotion_name not in emotion_scores:
                    emotion_scores[emotion_name] = 0.0
                    emotion_counts[emotion_name] = 0
                emotion_scores[emotion_name] += score.confidence
                emotion_counts[emotion_name] += 1

        return {
            emotion: score / emotion_counts[emotion]
            for emotion, score in emotion_scores.items()
            if emotion_counts[emotion] > 0
        }

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "duration_ms": self.duration_ms,
            "detection_count": len(self.detections),
            "emotion_summary": self.get_emotion_summary(),
        }
