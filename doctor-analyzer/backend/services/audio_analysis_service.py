"""Service for audio extraction and analysis."""

import logging
import uuid

from infrastructure.aws.transcribe_client import TranscribeClient
from infrastructure.aws.comprehend_client import ComprehendClient
from infrastructure.aws.s3_client import S3Client
from infrastructure.websocket.connection_manager import ConnectionManager
from domain.session import AnalysisSession, SessionStore
from domain.analysis import AudioAnalysis, AnalysisStatus

logger = logging.getLogger(__name__)


class AudioAnalysisService:
    """Orchestrates audio extraction, transcription, and sentiment analysis."""

    def __init__(
        self,
        transcribe: TranscribeClient,
        comprehend: ComprehendClient,
        s3: S3Client,
        ws_manager: ConnectionManager,
        session_store: SessionStore,
    ):
        self._transcribe = transcribe
        self._comprehend = comprehend
        self._s3 = s3
        self._ws_manager = ws_manager
        self._sessions = session_store

    async def analyze_audio(
        self,
        session: AnalysisSession,
    ) -> AudioAnalysis:
        """
        Extract audio from video and perform transcription + sentiment analysis.

        This method:
        1. Uses the video file directly (Transcribe can extract audio)
        2. Transcribes audio to text
        3. Analyzes sentiment of transcription
        4. Streams results to WebSocket clients
        """
        if not session.video_s3_key:
            raise ValueError("Session has no video to analyze")

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_AUDIO.value,
            progress=0.0,
            message="Starting audio transcription...",
        )

        # Update session status
        session.update_status(AnalysisStatus.PROCESSING_AUDIO)
        await self._sessions.update(session)

        # Create unique job name
        job_name = f"doctor-analyzer-{session.session_id}-{uuid.uuid4().hex[:8]}"

        # Start transcription job (Transcribe can handle video files directly)
        s3_uri = f"s3://{self._s3.bucket_name}/{session.video_s3_key}"
        await self._transcribe.start_transcription_job(
            job_name=job_name,
            s3_uri=s3_uri,
            output_bucket=self._s3.bucket_name,
        )

        logger.info(f"Started transcription job {job_name} for session {session.session_id}")

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_AUDIO.value,
            progress=0.0,
            message="Waiting for transcription to complete...",
        )

        # Wait for transcription and get segments
        try:
            segments = await self._transcribe.wait_for_transcription(job_name)
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

        # Stream transcription segments to WebSocket
        for segment in segments:
            await self._ws_manager.send_transcription_update(
                session.session_id,
                segment.text,
                segment.start_time,
                segment.end_time,
            )

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_AUDIO.value,
            progress=0.5,
            message="Transcription complete — analyzing sentiment...",
        )

        # Build AudioAnalysis result
        audio_analysis = AudioAnalysis(transcription=segments)

        # Analyze sentiment of full transcript
        if audio_analysis.full_transcript:
            overall_sentiment = await self._comprehend.detect_sentiment(
                audio_analysis.full_transcript
            )
            audio_analysis.overall_sentiment = overall_sentiment

            # Analyze sentiment of individual segments for detailed analysis
            segment_texts = [s.text for s in segments if len(s.text) > 20]
            if segment_texts:
                segment_sentiments = await self._comprehend.batch_detect_sentiment(
                    segment_texts[:25]  # Limit to 25 for batch
                )
                audio_analysis.segment_sentiments = segment_sentiments

        # Save results to S3
        results_key = f"sessions/{session.session_id}/results/transcription.json"
        await self._s3.upload_json(audio_analysis.to_dict(), results_key)

        # Update session
        session.audio_analysis = audio_analysis
        await self._sessions.update(session)

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_AUDIO.value,
            progress=1.0,
            message="Audio analysis complete",
        )

        # Clean up transcription job
        await self._transcribe.delete_transcription_job(job_name)

        logger.info(f"Completed audio analysis for session {session.session_id}")
        return audio_analysis
