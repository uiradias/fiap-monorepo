"""Service for video emotion analysis."""

import logging

from infrastructure.aws.rekognition_client import RekognitionClient
from infrastructure.aws.s3_client import S3Client
from infrastructure.websocket.connection_manager import ConnectionManager
from domain.session import AnalysisSession, SessionStore
from domain.emotion import VideoEmotionTimeline
from domain.analysis import AnalysisStatus

logger = logging.getLogger(__name__)


class VideoAnalysisService:
    """Orchestrates video upload and emotion analysis pipeline."""

    def __init__(
        self,
        rekognition: RekognitionClient,
        s3: S3Client,
        ws_manager: ConnectionManager,
        session_store: SessionStore,
    ):
        self._rekognition = rekognition
        self._s3 = s3
        self._ws_manager = ws_manager
        self._sessions = session_store

    async def analyze_video(
        self,
        session: AnalysisSession,
    ) -> VideoEmotionTimeline:
        """
        Run full video emotion analysis pipeline with real-time streaming.

        This method:
        1. Starts Rekognition face detection job
        2. Polls for results
        3. Streams each detection to connected WebSocket clients
        4. Returns complete timeline
        """
        if not session.video_s3_key:
            raise ValueError("Session has no video to analyze")

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_VIDEO.value,
            progress=0.0,
            message="Starting face detection on video...",
        )

        # Update session status
        session.update_status(AnalysisStatus.PROCESSING_VIDEO)
        await self._sessions.update(session)

        # Start the Rekognition job
        job_id = await self._rekognition.start_face_detection(
            self._s3.bucket_name,
            session.video_s3_key,
        )

        logger.info(f"Started Rekognition job {job_id} for session {session.session_id}")

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_VIDEO.value,
            progress=0.0,
            message="Waiting for Rekognition to analyze video — this may take a few minutes...",
        )

        # Create timeline to collect results
        timeline = VideoEmotionTimeline(
            video_id=session.video_s3_key,
            duration_ms=0,
        )

        # Collect detections while streaming to WebSocket
        detection_count = 0

        async for detection in self._rekognition.get_face_detection_results(job_id):
            timeline.add_detection(detection)
            detection_count += 1

            # Stream to WebSocket clients
            await self._ws_manager.send_emotion_update(
                session.session_id,
                detection.timestamp_ms,
                [e.to_dict() for e in detection.emotions],
                detection.bounding_box.to_dict(),
            )

            # Update progress periodically
            if detection_count % 10 == 0:
                await self._ws_manager.send_status_update(
                    session.session_id,
                    AnalysisStatus.PROCESSING_VIDEO.value,
                    progress=min(0.9, detection_count / 100),
                    message=f"Processing face detections... ({detection_count} detected so far)",
                )

        # Estimate duration from last detection
        if timeline.detections:
            timeline.duration_ms = max(d.timestamp_ms for d in timeline.detections) + 1000

        # Save results to S3
        results_key = f"sessions/{session.session_id}/results/video_emotions.json"
        await self._s3.upload_json(timeline.to_dict(), results_key)

        # Save individual face detections for video overlay on session review
        detections_key = f"sessions/{session.session_id}/results/face_detections.json"
        await self._s3.upload_json(
            [detection.to_dict() for detection in timeline.detections],
            detections_key,
        )

        # Update session
        session.video_emotions = timeline
        session.emotion_summary = timeline.get_emotion_summary()
        await self._sessions.update(session)

        await self._ws_manager.send_status_update(
            session.session_id,
            AnalysisStatus.PROCESSING_VIDEO.value,
            progress=1.0,
            message=f"Video emotion analysis complete — {detection_count} detections",
        )

        logger.info(f"Completed video analysis for session {session.session_id}: {detection_count} detections")
        return timeline
