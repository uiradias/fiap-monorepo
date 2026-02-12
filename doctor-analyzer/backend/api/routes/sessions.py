"""Session management API endpoints."""

import json
from typing import Optional

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from services.upload_service import UploadService
from infrastructure.aws.s3_client import S3Client
from domain.session import SessionStoreProtocol
from api.dependencies import get_upload_service, get_session_store, get_s3_client

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
async def list_sessions(
    patient_id: Optional[str] = Query(None),
    session_store: SessionStoreProtocol = Depends(get_session_store),
):
    """List all analysis sessions, optionally filtered by patient_id."""
    if patient_id:
        sessions = await session_store.list_by_patient(patient_id)
    else:
        sessions = await session_store.list_all()

    return {
        "sessions": [s.to_dict() for s in sessions],
        "total": len(sessions),
    }


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    upload_service: UploadService = Depends(get_upload_service),
):
    """Get details of a specific session."""
    session = await upload_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return session.to_dict()


@router.get("/{session_id}/full")
async def get_session_full(
    session_id: str,
    upload_service: UploadService = Depends(get_upload_service),
):
    """Get full details of a session including all analysis results."""
    session = await upload_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return session.to_full_dict()


@router.get("/{session_id}/video-url")
async def get_video_url(
    session_id: str,
    upload_service: UploadService = Depends(get_upload_service),
):
    """Get a presigned URL for video playback."""
    url = await upload_service.get_video_url(session_id)
    if not url:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or has no video",
        )

    return {"video_url": url}


@router.get("/{session_id}/face-detections")
async def get_face_detections(
    session_id: str,
    s3_client: S3Client = Depends(get_s3_client),
):
    """Get individual face detection records for video overlay."""
    s3_key = f"sessions/{session_id}/results/face_detections.json"
    try:
        data = await s3_client.download_file(s3_key)
        detections = json.loads(data)
        return JSONResponse(content=detections)
    except ClientError:
        raise HTTPException(
            status_code=404,
            detail=f"No face detections found for session {session_id}",
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    upload_service: UploadService = Depends(get_upload_service),
):
    """Delete a session and all associated files."""
    success = await upload_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {"status": "deleted", "session_id": session_id}
