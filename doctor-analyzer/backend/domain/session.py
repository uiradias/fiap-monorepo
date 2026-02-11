"""Analysis session domain models."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

from domain.analysis import (
    AnalysisStatus,
    AudioAnalysis,
    DocumentAnalysis,
    ClinicalIndicator,
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
    documents_s3_keys: List[str] = field(default_factory=list)
    text_input: Optional[str] = None
    results_s3_key: Optional[str] = None

    # Analysis results
    video_emotions: Optional[VideoEmotionTimeline] = None
    audio_analysis: Optional[AudioAnalysis] = None
    document_analyses: List[DocumentAnalysis] = field(default_factory=list)

    # Aggregated insights
    emotion_summary: Dict[str, float] = field(default_factory=dict)
    clinical_indicators: List[ClinicalIndicator] = field(default_factory=list)
    text_sentiment: Optional[Dict] = None

    # Metadata
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def update_status(self, status: AnalysisStatus, error: Optional[str] = None) -> None:
        """Update session status."""
        self.status = status
        self.updated_at = datetime.utcnow()
        if error:
            self.error_message = error

    def add_document(self, s3_key: str) -> None:
        """Add a document S3 key to the session."""
        self.documents_s3_keys.append(s3_key)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status.value,
            "video_s3_key": self.video_s3_key,
            "documents_count": len(self.documents_s3_keys),
            "has_text_input": self.text_input is not None,
            "emotion_summary": self.emotion_summary,
            "clinical_indicators": [c.to_dict() for c in self.clinical_indicators],
            "text_sentiment": self.text_sentiment,
            "error_message": self.error_message,
        }

    def to_full_dict(self) -> dict:
        """Convert to full dictionary including all analysis results."""
        base = self.to_dict()
        base.update({
            "video_emotions": self.video_emotions.to_dict() if self.video_emotions else None,
            "audio_analysis": self.audio_analysis.to_dict() if self.audio_analysis else None,
            "document_analyses": [d.to_dict() for d in self.document_analyses],
            "documents_s3_keys": self.documents_s3_keys,
            "text_input": self.text_input,
            "results_s3_key": self.results_s3_key,
        })
        return base


# In-memory session store for development
class SessionStore:
    """Simple in-memory session store."""

    def __init__(self):
        self._sessions: Dict[str, AnalysisSession] = {}

    async def create(self, session: AnalysisSession) -> AnalysisSession:
        """Create a new session."""
        self._sessions[session.session_id] = session
        return session

    async def get(self, session_id: str) -> Optional[AnalysisSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    async def update(self, session: AnalysisSession) -> AnalysisSession:
        """Update an existing session."""
        session.updated_at = datetime.utcnow()
        self._sessions[session.session_id] = session
        return session

    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def list_all(self) -> List[AnalysisSession]:
        """List all sessions."""
        return list(self._sessions.values())
