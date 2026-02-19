"""Analysis API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

logger = logging.getLogger(__name__)

from services.upload_service import UploadService
from services.video_analysis_service import VideoAnalysisService
from services.audio_analysis_service import AudioAnalysisService
from services.aggregation_service import AggregationService
from services.injury_check_service import InjuryCheckService
from services.bedrock_analysis_service import BedrockAnalysisService
from domain.session import SessionStore
from domain.analysis import AnalysisStatus, InjuryCheckResult
from infrastructure.websocket.connection_manager import ConnectionManager
from api.dependencies import (
    get_upload_service,
    get_video_analysis_service,
    get_audio_analysis_service,
    get_aggregation_service,
    get_injury_check_service,
    get_bedrock_analysis_service,
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
    injury_check_service: InjuryCheckService = Depends(get_injury_check_service),
    bedrock_analysis_service: BedrockAnalysisService = Depends(get_bedrock_analysis_service),
    session_store: SessionStore = Depends(get_session_store),
):
    """
    Start the analysis pipeline for a session.

    Pipeline: video emotion (Rekognition), injury check (Rekognition content moderation),
    audio transcription/sentiment, aggregation.
    """
    logger.info(f"Received start analysis request for session {session_id}")

    session = await upload_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    if session.status not in [AnalysisStatus.PENDING, AnalysisStatus.UPLOADING, AnalysisStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Analysis already started. Current status: {session.status.value}",
        )

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
        injury_check_service,
        bedrock_analysis_service,
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
    injury_check_service: InjuryCheckService,
    bedrock_service: BedrockAnalysisService,
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
        if session.video_s3_key:
            logger.info(f"[{session_id}] Starting video analysis: {session.video_s3_key}")
            await video_service.analyze_video(session)
            session = await session_store.get(session_id)

            logger.info(f"[{session_id}] Running injury check (Rekognition)")
            try:
                result = await injury_check_service.run_injury_check(session)
                session.injury_check = result
                await session_store.update(session)
            except Exception as e:
                logger.exception(f"Injury check failed for session {session_id}: %s", e)
                session.injury_check = InjuryCheckResult(
                    enabled=True,
                    rekognition_labels=[],
                    has_signals=False,
                    summary="",
                    confidence=0.0,
                    error_message=str(e),
                )
                await session_store.update(session)
            session = await session_store.get(session_id)

            logger.info(f"[{session_id}] Starting audio analysis")
            await audio_service.analyze_audio(session)
            session = await session_store.get(session_id)

        # Bedrock enhancement (after audio so transcript is available)
        if session.injury_check:
            try:
                logger.info(f"[{session_id}] Running Bedrock-enhanced injury interpretation")
                enhanced = await bedrock_service.enhance_injury_interpretation(session)
                session.injury_check = enhanced
                transcript_analysis = await bedrock_service.analyze_transcript_for_injuries(session)
                if transcript_analysis:
                    session.injury_check.transcript_analysis = transcript_analysis
                await session_store.update(session)
                session = await session_store.get(session_id)
            except Exception as e:
                logger.exception(f"Bedrock injury enhancement failed for {session_id}, keeping Rekognition results: %s", e)

        try:
            logger.info(f"[{session_id}] Running Bedrock multi-modal aggregation")
            aggregation = await bedrock_service.generate_multimodal_aggregation(session)
            if aggregation:
                session.bedrock_aggregation = aggregation
                await session_store.update(session)
                session = await session_store.get(session_id)
        except Exception as e:
            logger.exception(f"Bedrock aggregation failed for {session_id}, proceeding with rule-based: %s", e)

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
