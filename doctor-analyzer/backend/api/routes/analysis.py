"""Analysis API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

logger = logging.getLogger(__name__)

from services.upload_service import UploadService
from services.video_analysis_service import VideoAnalysisService
from services.audio_analysis_service import AudioAnalysisService
from services.aggregation_service import AggregationService
from domain.session import SessionStore
from domain.analysis import AnalysisStatus
from infrastructure.websocket.connection_manager import ConnectionManager
from api.dependencies import (
    get_upload_service,
    get_video_analysis_service,
    get_audio_analysis_service,
    get_aggregation_service,
    get_session_store,
    get_connection_manager,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/{session_id}/start")
async def start_analysis(
    session_id: str,
    background_tasks: BackgroundTasks,
    upload_service: UploadService = Depends(get_upload_service),
    video_service: VideoAnalysisService = Depends(get_video_analysis_service),
    audio_service: AudioAnalysisService = Depends(get_audio_analysis_service),
    aggregation_service: AggregationService = Depends(get_aggregation_service),
    session_store: SessionStore = Depends(get_session_store),
):
    """
    Start the analysis pipeline for a session.

    This endpoint triggers the full analysis pipeline:
    1. Video emotion detection (Rekognition)
    2. Audio transcription and sentiment (Transcribe + Comprehend)
    3. Results aggregation

    The analysis runs in the background. Connect via WebSocket
    to receive real-time updates.
    """
    logger.info(f"Received start analysis request for session {session_id}")

    session = await upload_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Check if analysis already started
    if session.status not in [AnalysisStatus.PENDING, AnalysisStatus.UPLOADING, AnalysisStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Analysis already started. Current status: {session.status.value}",
        )

    # Start analysis in background
    ws_manager = get_connection_manager()
    logger.info(
        f"Queuing analysis pipeline for session {session_id} "
        f"(video={session.video_s3_key})"
    )
    background_tasks.add_task(
        run_analysis_pipeline,
        session_id,
        video_service,
        audio_service,
        aggregation_service,
        session_store,
        ws_manager,
    )

    return {
        "session_id": session_id,
        "status": "analysis_started",
        "message": "Connect via WebSocket to receive real-time updates",
    }


async def run_analysis_pipeline(
    session_id: str,
    video_service: VideoAnalysisService,
    audio_service: AudioAnalysisService,
    aggregation_service: AggregationService,
    session_store: SessionStore,
    ws_manager: ConnectionManager,
):
    """Run the complete analysis pipeline."""
    logger.info(f"Pipeline started for session {session_id}")

    session = await session_store.get(session_id)
    if not session:
        logger.error(f"Session {session_id} not found in store — aborting pipeline")
        await ws_manager.send_error(session_id, "Session not found")
        return

    try:
        # Run video and audio analysis (can run in parallel in future)
        if session.video_s3_key:
            logger.info(f"[{session_id}] Starting video analysis: {session.video_s3_key}")
            await video_service.analyze_video(session)
            # Refresh session after video analysis
            session = await session_store.get(session_id)

            logger.info(f"[{session_id}] Starting audio analysis")
            await audio_service.analyze_audio(session)
            # Refresh session after audio analysis
            session = await session_store.get(session_id)

        # Aggregate results
        logger.info(f"[{session_id}] Starting aggregation")
        await aggregation_service.aggregate_results(session)
        logger.info(f"[{session_id}] Pipeline completed successfully")

    except Exception as e:
        logger.exception(f"Analysis pipeline failed for session {session_id}")
        # Update session with error and notify WebSocket clients
        session = await session_store.get(session_id)
        if session:
            session.update_status(AnalysisStatus.FAILED, error=str(e))
            await session_store.update(session)
        await ws_manager.send_error(session_id, str(e))


@router.get("/{session_id}/status")
async def get_analysis_status(
    session_id: str,
    upload_service: UploadService = Depends(get_upload_service),
):
    """Get the current status of an analysis session."""
    session = await upload_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "session_id": session_id,
        "status": session.status.value,
        "error_message": session.error_message,
        "has_video": session.video_s3_key is not None,
    }


@router.get("/{session_id}/results")
async def get_analysis_results(
    session_id: str,
    upload_service: UploadService = Depends(get_upload_service),
):
    """Get the complete analysis results for a session."""
    session = await upload_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    if session.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not complete. Current status: {session.status.value}",
        )

    return session.to_full_dict()
