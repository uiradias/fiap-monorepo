"""Upload API endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional

from services.upload_service import UploadService
from api.dependencies import get_upload_service

router = APIRouter(prefix="/upload", tags=["upload"])


ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
]


@router.post("/video")
async def upload_video(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    upload_service: UploadService = Depends(get_upload_service),
):
    """
    Upload a video file for analysis.

    Creates a new session and uploads the video to S3.
    Returns session_id for tracking the analysis.
    """
    # Validate file type
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Allowed: {ALLOWED_VIDEO_TYPES}",
        )

    # Create session
    session = await upload_service.create_session(patient_id=patient_id)

    # Upload video
    try:
        s3_key = await upload_service.upload_video(session.session_id, file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    return {
        "session_id": session.session_id,
        "video_s3_key": s3_key,
        "status": session.status.value,
    }


