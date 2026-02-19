"""Tests for BedrockAnalysisService — all three use cases + graceful degradation."""

import pytest
from unittest.mock import AsyncMock

from services.bedrock_analysis_service import BedrockAnalysisService


# ── Use Case 1: Label Interpretation ────────────────────────────────


@pytest.mark.asyncio
async def test_enhance_injury_interpretation_updates_result(
    mock_bedrock, mock_ws_manager, sample_session,
):
    mock_bedrock.invoke_model_json.return_value = {
        "has_signals": True,
        "severity": "moderate",
        "summary": "Violence label appears contextual to discussion of past events.",
        "confidence": 0.65,
        "clinical_rationale": "Patient was describing a past traumatic event. Visual content flagged is likely gestures accompanying the narrative.",
        "label_assessments": [
            {"label": "Violence", "is_relevant": False, "reasoning": "Contextual to narrative"},
        ],
    }

    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = service.enhance_injury_interpretation(sample_session)
    result = await result

    assert result.severity == "moderate"
    assert result.confidence == 0.65
    assert result.clinical_rationale is not None
    assert "past traumatic event" in result.clinical_rationale
    mock_bedrock.invoke_model_json.assert_called_once()


@pytest.mark.asyncio
async def test_enhance_injury_no_labels_returns_original(
    mock_bedrock, mock_ws_manager, sample_session_no_signals,
):
    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = await service.enhance_injury_interpretation(sample_session_no_signals)

    assert result.has_signals is False
    assert result.severity is None
    mock_bedrock.invoke_model_json.assert_not_called()


@pytest.mark.asyncio
async def test_enhance_injury_bedrock_returns_none(
    mock_bedrock, mock_ws_manager, sample_session,
):
    """Unparseable Bedrock response should preserve original result."""
    mock_bedrock.invoke_model_json.return_value = None

    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = await service.enhance_injury_interpretation(sample_session)

    # Should keep original Rekognition values
    assert result.has_signals is True
    assert result.severity is None  # Not overwritten
    assert result.confidence == 0.72  # Original value


# ── Use Case 2: Transcript Analysis ─────────────────────────────────


@pytest.mark.asyncio
async def test_transcript_analysis_detects_verbal_signals(
    mock_bedrock, mock_ws_manager, sample_session,
):
    mock_bedrock.invoke_model_json.return_value = {
        "has_verbal_signals": True,
        "severity": "high",
        "findings": [
            "Hopelessness expressed: 'Nothing seems to matter anymore'",
            "Disappearance wish: 'I just want to disappear sometimes'",
        ],
        "evidence_quotes": [
            "Nothing seems to matter anymore.",
            "I just want to disappear sometimes.",
        ],
        "confidence": 0.82,
        "risk_factors_identified": ["hopelessness", "disappearance_wish"],
    }

    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = await service.analyze_transcript_for_injuries(sample_session)

    assert result is not None
    assert result["has_verbal_signals"] is True
    assert result["severity"] == "high"
    assert len(result["findings"]) == 2
    assert len(result["evidence_quotes"]) == 2
    assert result["confidence"] == 0.82


@pytest.mark.asyncio
async def test_transcript_analysis_no_transcript(
    mock_bedrock, mock_ws_manager,
):
    """Session without audio analysis should return None."""
    from domain.session import AnalysisSession
    from domain.analysis import AnalysisStatus, InjuryCheckResult
    from datetime import datetime

    session = AnalysisSession(
        session_id="no-audio",
        created_at=datetime.utcnow(),
        status=AnalysisStatus.PROCESSING_AUDIO,
        audio_analysis=None,
        injury_check=InjuryCheckResult(
            enabled=True, rekognition_labels=[], has_signals=False,
            summary="", confidence=0.0,
        ),
    )

    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = await service.analyze_transcript_for_injuries(session)

    assert result is None
    mock_bedrock.invoke_model_json.assert_not_called()


@pytest.mark.asyncio
async def test_transcript_analysis_bedrock_failure(
    mock_bedrock, mock_ws_manager, sample_session,
):
    mock_bedrock.invoke_model_json.return_value = None

    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = await service.analyze_transcript_for_injuries(sample_session)

    assert result is None


# ── Use Case 3: Multi-Modal Aggregation ─────────────────────────────


@pytest.mark.asyncio
async def test_multimodal_aggregation_success(
    mock_bedrock, mock_ws_manager, sample_session,
):
    mock_bedrock.invoke_model_json.return_value = {
        "clinical_summary": "Patient shows concordant distress signals across video and audio modalities.",
        "risk_level": "high",
        "cross_referenced_evidence": [
            {
                "source": "audio",
                "finding": "Expressions of hopelessness in transcript",
                "supporting_sources": ["video"],
            },
        ],
        "concordant_signals": ["Sadness in face + negative verbal content"],
        "discordant_signals": [],
        "recommendations": ["Follow-up assessment recommended", "Monitor for escalation"],
    }

    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = await service.generate_multimodal_aggregation(sample_session)

    assert result is not None
    assert result["risk_level"] == "high"
    assert len(result["recommendations"]) == 2
    assert len(result["cross_referenced_evidence"]) == 1
    assert "concordant" in result["concordant_signals"][0].lower() or len(result["concordant_signals"]) > 0


@pytest.mark.asyncio
async def test_multimodal_aggregation_low_risk(
    mock_bedrock, mock_ws_manager, sample_session_no_signals,
):
    mock_bedrock.invoke_model_json.return_value = {
        "clinical_summary": "Patient presents with generally positive affect and outlook.",
        "risk_level": "low",
        "cross_referenced_evidence": [],
        "concordant_signals": ["Positive facial expression + positive verbal content"],
        "discordant_signals": [],
        "recommendations": ["Continue current therapeutic approach"],
    }

    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = await service.generate_multimodal_aggregation(sample_session_no_signals)

    assert result is not None
    assert result["risk_level"] == "low"


@pytest.mark.asyncio
async def test_multimodal_aggregation_bedrock_failure(
    mock_bedrock, mock_ws_manager, sample_session,
):
    mock_bedrock.invoke_model_json.return_value = None

    service = BedrockAnalysisService(mock_bedrock, mock_ws_manager)
    result = await service.generate_multimodal_aggregation(sample_session)

    assert result is None


# ── Helper: Transcript extraction ────────────────────────────────────


def test_extract_transcript_around_timestamps(sample_transcription_segments):
    result = BedrockAnalysisService._extract_transcript_around_timestamps(
        sample_transcription_segments,
        timestamps_ms=[5000, 7000],
        window_ms=5000,
    )

    # Should capture segments near 5s and 7s (0-10s window, 2-12s window)
    assert "feeling really down" in result
    assert "Nothing seems to matter" in result
    assert "disappear" in result


def test_extract_transcript_empty_timestamps(sample_transcription_segments):
    result = BedrockAnalysisService._extract_transcript_around_timestamps(
        sample_transcription_segments,
        timestamps_ms=[],
    )
    assert result == ""


def test_extract_transcript_no_segments():
    result = BedrockAnalysisService._extract_transcript_around_timestamps(
        [],
        timestamps_ms=[5000],
    )
    assert result == ""
