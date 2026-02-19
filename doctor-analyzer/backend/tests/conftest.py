"""Shared test fixtures."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from domain.analysis import (
    AnalysisStatus,
    AudioAnalysis,
    InjuryCheckResult,
    SentimentResult,
    TranscriptionSegment,
)
from domain.session import AnalysisSession
from infrastructure.aws.bedrock_client import BedrockClient
from infrastructure.websocket.connection_manager import ConnectionManager


@pytest.fixture
def mock_bedrock():
    client = AsyncMock(spec=BedrockClient)
    return client


@pytest.fixture
def mock_ws_manager():
    manager = AsyncMock(spec=ConnectionManager)
    return manager


@pytest.fixture
def sample_transcription_segments():
    return [
        TranscriptionSegment(text="I've been feeling really down lately.", start_time=0.0, end_time=3.0, confidence=0.95),
        TranscriptionSegment(text="Nothing seems to matter anymore.", start_time=3.5, end_time=6.0, confidence=0.92),
        TranscriptionSegment(text="I just want to disappear sometimes.", start_time=6.5, end_time=9.5, confidence=0.90),
        TranscriptionSegment(text="My therapist says I should try journaling.", start_time=10.0, end_time=13.0, confidence=0.94),
        TranscriptionSegment(text="I guess that could help.", start_time=13.5, end_time=15.0, confidence=0.88),
    ]


@pytest.fixture
def sample_rekognition_labels():
    return [
        {"name": "Violence", "confidence": 0.72, "timestamp_ms": 5000, "parent_name": ""},
        {"name": "Visually Disturbing", "confidence": 0.55, "timestamp_ms": 7000, "parent_name": "Violence"},
    ]


@pytest.fixture
def sample_session(sample_transcription_segments, sample_rekognition_labels):
    return AnalysisSession(
        session_id="test-session-001",
        created_at=datetime.utcnow(),
        status=AnalysisStatus.PROCESSING_AUDIO,
        patient_id="patient-001",
        video_s3_key="sessions/test-session-001/video.mp4",
        audio_analysis=AudioAnalysis(
            transcription=sample_transcription_segments,
            overall_sentiment=SentimentResult(
                sentiment="NEGATIVE",
                positive_score=0.05,
                negative_score=0.70,
                neutral_score=0.15,
                mixed_score=0.10,
            ),
        ),
        injury_check=InjuryCheckResult(
            enabled=True,
            rekognition_labels=sample_rekognition_labels,
            has_signals=True,
            summary="Rekognition detected: Violence, Visually Disturbing.",
            confidence=0.72,
        ),
        emotion_summary={
            "sad": 0.45,
            "happy": 0.10,
            "fear": 0.20,
            "calm": 0.15,
            "depression": 0.40,
            "anxiety": 0.25,
            "discomfort": 0.35,
        },
    )


@pytest.fixture
def sample_session_no_signals():
    return AnalysisSession(
        session_id="test-session-002",
        created_at=datetime.utcnow(),
        status=AnalysisStatus.PROCESSING_AUDIO,
        patient_id="patient-002",
        video_s3_key="sessions/test-session-002/video.mp4",
        audio_analysis=AudioAnalysis(
            transcription=[
                TranscriptionSegment(text="Today was a good day.", start_time=0.0, end_time=2.0, confidence=0.95),
                TranscriptionSegment(text="I feel much better this week.", start_time=2.5, end_time=5.0, confidence=0.93),
            ],
            overall_sentiment=SentimentResult(
                sentiment="POSITIVE",
                positive_score=0.80,
                negative_score=0.05,
                neutral_score=0.10,
                mixed_score=0.05,
            ),
        ),
        injury_check=InjuryCheckResult(
            enabled=True,
            rekognition_labels=[],
            has_signals=False,
            summary="No concerning content detected.",
            confidence=0.0,
        ),
        emotion_summary={"happy": 0.65, "calm": 0.25, "sad": 0.05},
    )
