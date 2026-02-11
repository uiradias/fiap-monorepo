"""Session management API endpoints."""

from fastapi import APIRouter, HTTPException, Depends

from services.upload_service import UploadService
from domain.session import SessionStore
from api.dependencies import get_upload_service, get_session_store

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
async def list_sessions(
    session_store: SessionStore = Depends(get_session_store),
):
    """List all analysis sessions."""
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
