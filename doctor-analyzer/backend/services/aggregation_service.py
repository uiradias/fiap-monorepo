"""Service for aggregating analysis results."""

import logging
from typing import Optional

from infrastructure.aws.s3_client import S3Client
from infrastructure.websocket.connection_manager import ConnectionManager
from domain.session import AnalysisSession, SessionStore
from domain.analysis import ClinicalIndicator, AnalysisStatus

logger = logging.getLogger(__name__)


class AggregationService:
    """Aggregates all analysis results and generates clinical indicators."""

    def __init__(
        self,
        s3: S3Client,
        ws_manager: ConnectionManager,
        session_store: SessionStore,
    ):
        self._s3 = s3
        self._ws_manager = ws_manager
        self._sessions = session_store

    async def aggregate_results(
        self,
        session: AnalysisSession,
    ) -> AnalysisSession:
        """
        Aggregate all analysis results and generate clinical indicators.

        This method:
        1. Combines emotion summary from video
        2. Integrates sentiment from audio and documents
        3. Generates clinical indicators
        4. Saves final report to S3
        """
        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.AGGREGATING.value,
            progress=0.0,
            message="Generating clinical indicators...",
        )

        session.update_status(AnalysisStatus.AGGREGATING)
        await self._sessions.update(session)

        # Generate clinical indicators
        indicators = self._generate_clinical_indicators(session)
        session.clinical_indicators = indicators

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.AGGREGATING.value,
            progress=0.5,
            message="Saving final report...",
        )

        # Save final report to S3
        final_report = session.to_full_dict()
        results_key = f"sessions/{session.session_id}/results/final_report.json"
        await self._s3.upload_json(final_report, results_key)
        session.results_s3_key = results_key

        # Update session status to completed
        session.update_status(AnalysisStatus.COMPLETED)
        await self._sessions.update(session)

        # Send completion message
        await self._ws_manager.send_complete(
            session.session_id,
            session.to_full_dict(),
        )

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.COMPLETED.value,
            progress=1.0,
        )

        logger.info(f"Completed aggregation for session {session.session_id}")
        return session

    def _generate_clinical_indicators(
        self,
        session: AnalysisSession,
    ) -> list:
        """Generate clinical indicators from all analysis sources."""
        indicators = []

        # Analyze video emotions for clinical indicators
        if session.emotion_summary:
            indicators.extend(self._indicators_from_emotions(session.emotion_summary))

        # Analyze audio sentiment for clinical indicators
        if session.audio_analysis and session.audio_analysis.overall_sentiment:
            indicators.extend(
                self._indicators_from_sentiment(
                    session.audio_analysis.overall_sentiment.to_dict(),
                    source="audio",
                )
            )

        # Analyze document sentiments
        for doc in session.document_analyses:
            if doc.sentiment:
                indicators.extend(
                    self._indicators_from_sentiment(
                        doc.sentiment.to_dict(),
                        source=f"document:{doc.filename}",
                    )
                )

        # Analyze text input sentiment
        if session.text_sentiment and 'sentiment' in session.text_sentiment:
            indicators.extend(
                self._indicators_from_sentiment(
                    session.text_sentiment['sentiment'],
                    source="doctor_notes",
                )
            )

        # Sort by confidence
        indicators.sort(key=lambda x: x.confidence, reverse=True)

        return indicators

    def _indicators_from_emotions(self, emotion_summary: dict) -> list:
        """Extract clinical indicators from emotion summary."""
        indicators = []
        thresholds = {
            'discomfort': 0.3,
            'depression': 0.3,
            'anxiety': 0.3,
            'fear': 0.4,
        }

        for indicator_type, threshold in thresholds.items():
            confidence = emotion_summary.get(indicator_type, 0)
            if confidence >= threshold:
                indicators.append(ClinicalIndicator(
                    indicator_type=indicator_type,
                    confidence=confidence,
                    evidence=[f"Average {indicator_type} score: {confidence:.2%}"],
                ))

        return indicators

    def _indicators_from_sentiment(
        self,
        sentiment: dict,
        source: str,
    ) -> list:
        """Extract clinical indicators from sentiment analysis."""
        indicators = []

        # High negative sentiment may indicate distress
        negative_score = sentiment.get('negative_score', 0)
        if negative_score > 0.5:
            indicators.append(ClinicalIndicator(
                indicator_type='distress',
                confidence=negative_score,
                evidence=[f"Negative sentiment in {source}: {negative_score:.2%}"],
            ))

        # Mixed sentiment may indicate confusion or uncertainty
        mixed_score = sentiment.get('mixed_score', 0)
        if mixed_score > 0.4:
            indicators.append(ClinicalIndicator(
                indicator_type='uncertainty',
                confidence=mixed_score,
                evidence=[f"Mixed sentiment in {source}: {mixed_score:.2%}"],
            ))

        return indicators
