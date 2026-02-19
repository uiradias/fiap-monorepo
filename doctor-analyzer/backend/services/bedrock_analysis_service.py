"""Service for Bedrock-enhanced injury and clinical analysis."""

import logging
from typing import Any, Dict, List, Optional

from domain.analysis import AnalysisStatus, InjuryCheckResult
from domain.session import AnalysisSession
from infrastructure.aws.bedrock_client import BedrockClient
from infrastructure.websocket.connection_manager import ConnectionManager
from services.prompts.injury_prompts import (
    build_label_interpretation_prompt,
    build_transcript_analysis_prompt,
)
from services.prompts.aggregation_prompts import build_multimodal_aggregation_prompt

logger = logging.getLogger(__name__)


class BedrockAnalysisService:
    """Orchestrates Bedrock-enhanced analysis for all three use cases."""

    def __init__(
        self,
        bedrock: BedrockClient,
        ws_manager: ConnectionManager,
    ):
        self._bedrock = bedrock
        self._ws_manager = ws_manager

    async def enhance_injury_interpretation(
        self,
        session: AnalysisSession,
    ) -> InjuryCheckResult:
        """Use Case 1: Enhance Rekognition labels with contextual LLM interpretation.

        Takes the existing InjuryCheckResult (from Rekognition) and
        enriches it with Bedrock-derived severity, summary, and clinical
        rationale by cross-referencing labels with transcript context.
        """
        result = session.injury_check
        if not result or not result.rekognition_labels:
            logger.info("No Rekognition labels to enhance")
            return result

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_BEDROCK.value,
            progress=0.0,
            message="Enhancing injury analysis with AI...",
        )

        # Extract transcript text around the timestamps of flagged labels
        transcript_context = ""
        if session.audio_analysis and session.audio_analysis.transcription:
            timestamps_ms = [
                lb.get("timestamp_ms", 0) for lb in result.rekognition_labels
            ]
            transcript_context = self._extract_transcript_around_timestamps(
                session.audio_analysis.transcription,
                timestamps_ms,
            )

        prompt = build_label_interpretation_prompt(
            result.rekognition_labels,
            transcript_context,
        )

        parsed = await self._bedrock.invoke_model_json(prompt)
        if parsed is None:
            logger.warning("Bedrock label interpretation returned unparseable response")
            return result

        # Enrich the existing result with Bedrock findings
        result.has_signals = parsed.get("has_signals", result.has_signals)
        result.severity = parsed.get("severity")
        result.summary = parsed.get("summary", result.summary)
        result.confidence = float(parsed.get("confidence", result.confidence))
        result.clinical_rationale = parsed.get("clinical_rationale")

        return result

    async def analyze_transcript_for_injuries(
        self,
        session: AnalysisSession,
    ) -> Optional[Dict[str, Any]]:
        """Use Case 2: Scan transcript for verbal injury indicators.

        Returns a dict matching the transcript_analysis schema, or None
        if no transcript is available.
        """
        if not session.audio_analysis or not session.audio_analysis.full_transcript:
            logger.info("No transcript available for verbal injury analysis")
            return None

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_BEDROCK.value,
            progress=0.33,
            message="Analyzing transcript for verbal indicators...",
        )

        prompt = build_transcript_analysis_prompt(
            session.audio_analysis.full_transcript,
        )

        parsed = await self._bedrock.invoke_model_json(prompt)
        if parsed is None:
            logger.warning("Bedrock transcript analysis returned unparseable response")
            return None

        return {
            "has_verbal_signals": parsed.get("has_verbal_signals", False),
            "severity": parsed.get("severity", "low"),
            "findings": parsed.get("findings", []),
            "evidence_quotes": parsed.get("evidence_quotes", []),
            "confidence": float(parsed.get("confidence", 0)),
            "risk_factors_identified": parsed.get("risk_factors_identified", []),
        }

    async def generate_multimodal_aggregation(
        self,
        session: AnalysisSession,
    ) -> Optional[Dict[str, Any]]:
        """Use Case 3: Combine all signals into a unified clinical summary.

        Returns a dict with clinical_summary, risk_level,
        cross_referenced_evidence, concordant/discordant signals,
        and recommendations.
        """
        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_BEDROCK.value,
            progress=0.66,
            message="Generating multi-modal clinical summary...",
        )

        transcript_text = ""
        sentiment_result = None
        if session.audio_analysis:
            transcript_text = session.audio_analysis.full_transcript or ""
            if session.audio_analysis.overall_sentiment:
                sentiment_result = session.audio_analysis.overall_sentiment.to_dict()

        injury_check_dict = None
        if session.injury_check:
            injury_check_dict = session.injury_check.to_dict()

        indicators = [ci.to_dict() for ci in session.clinical_indicators]

        prompt = build_multimodal_aggregation_prompt(
            emotion_summary=session.emotion_summary or {},
            transcript_text=transcript_text,
            sentiment_result=sentiment_result,
            injury_check_result=injury_check_dict,
            clinical_indicators=indicators,
        )

        parsed = await self._bedrock.invoke_model_json(prompt)
        if parsed is None:
            logger.warning("Bedrock multi-modal aggregation returned unparseable response")
            return None

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_BEDROCK.value,
            progress=1.0,
            message="AI-enhanced analysis complete",
        )

        return {
            "clinical_summary": parsed.get("clinical_summary", ""),
            "risk_level": parsed.get("risk_level", "low"),
            "cross_referenced_evidence": parsed.get("cross_referenced_evidence", []),
            "concordant_signals": parsed.get("concordant_signals", []),
            "discordant_signals": parsed.get("discordant_signals", []),
            "recommendations": parsed.get("recommendations", []),
        }

    @staticmethod
    def _extract_transcript_around_timestamps(
        transcription_segments: List,
        timestamps_ms: List[int],
        window_ms: int = 10000,
    ) -> str:
        """Extract transcript text within a time window around given timestamps.

        For each flagged timestamp, finds transcription segments that fall
        within +/- window_ms and joins them.
        """
        if not timestamps_ms or not transcription_segments:
            return ""

        relevant_texts: List[str] = []
        seen_segments = set()

        for ts in timestamps_ms:
            lower = ts - window_ms
            upper = ts + window_ms
            for i, seg in enumerate(transcription_segments):
                seg_start_ms = seg.start_time * 1000
                seg_end_ms = seg.end_time * 1000
                if seg_end_ms >= lower and seg_start_ms <= upper and i not in seen_segments:
                    seen_segments.add(i)
                    relevant_texts.append(seg.text)

        return " ".join(relevant_texts) if relevant_texts else ""
