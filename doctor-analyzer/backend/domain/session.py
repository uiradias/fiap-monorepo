"""Analysis session domain models."""

import abc
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

from domain.analysis import (
    AnalysisStatus,
    AudioAnalysis,
    ClinicalIndicator,
    InjuryCheckResult,
)
from domain.emotion import VideoEmotionTimeline


@dataclass
class AnalysisSession:
    """Complete analysis session aggregating all results."""

    session_id: str
    created_at: datetime
    status: AnalysisStatus = AnalysisStatus.PENDING
    patient_id: Optional[str] = None

    # S3 locations
    video_s3_key: Optional[str] = None
    results_s3_key: Optional[str] = None

    # Analysis results
    video_emotions: Optional[VideoEmotionTimeline] = None
    audio_analysis: Optional[AudioAnalysis] = None
    injury_check: Optional[InjuryCheckResult] = None

    # Aggregated insights
    emotion_summary: Dict[str, float] = field(default_factory=dict)
    clinical_indicators: List[ClinicalIndicator] = field(default_factory=list)
    bedrock_aggregation: Optional[Dict] = None

    # Metadata
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def update_status(self, status: AnalysisStatus, error: Optional[str] = None) -> None:
        """Update session status."""
        self.status = status
        self.updated_at = datetime.utcnow()
        if error:
            self.error_message = error

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status.value,
            "video_s3_key": self.video_s3_key,
            "emotion_summary": self.emotion_summary,
            "clinical_indicators": [c.to_dict() for c in self.clinical_indicators],
            "error_message": self.error_message,
            "injury_check": self.injury_check.to_dict() if self.injury_check else None,
            "bedrock_aggregation": self.bedrock_aggregation,
        }

    def to_full_dict(self) -> dict:
        """Convert to full dictionary including all analysis results."""
        base = self.to_dict()
        base.update({
            "video_emotions": self.video_emotions.to_dict() if self.video_emotions else None,
            "audio_analysis": self.audio_analysis.to_dict() if self.audio_analysis else None,
            "results_s3_key": self.results_s3_key,
        })
        return base


class SessionStoreProtocol(abc.ABC):
    """Abstract interface for session persistence."""

    @abc.abstractmethod
    async def create(self, session: AnalysisSession) -> AnalysisSession: ...

    @abc.abstractmethod
    async def get(self, session_id: str) -> Optional[AnalysisSession]: ...

    @abc.abstractmethod
    async def update(self, session: AnalysisSession) -> AnalysisSession: ...

    @abc.abstractmethod
    async def delete(self, session_id: str) -> bool: ...

    @abc.abstractmethod
    async def list_all(self) -> List[AnalysisSession]: ...

    @abc.abstractmethod
    async def list_by_patient(self, patient_id: str) -> List[AnalysisSession]: ...


class InMemorySessionStore(SessionStoreProtocol):
    """Simple in-memory session store."""

    def __init__(self):
        self._sessions: Dict[str, AnalysisSession] = {}

    async def create(self, session: AnalysisSession) -> AnalysisSession:
        self._sessions[session.session_id] = session
        return session

    async def get(self, session_id: str) -> Optional[AnalysisSession]:
        return self._sessions.get(session_id)

    async def update(self, session: AnalysisSession) -> AnalysisSession:
        session.updated_at = datetime.utcnow()
        self._sessions[session.session_id] = session
        return session

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def list_all(self) -> List[AnalysisSession]:
        return list(self._sessions.values())

    async def list_by_patient(self, patient_id: str) -> List[AnalysisSession]:
        return [s for s in self._sessions.values() if s.patient_id == patient_id]


# Backward-compatible alias
SessionStore = InMemorySessionStore
