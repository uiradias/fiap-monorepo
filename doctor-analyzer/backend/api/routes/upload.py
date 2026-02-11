"""Upload API endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional

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


@router.post("/documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    session_id: str = Form(...),
    upload_service: UploadService = Depends(get_upload_service),
):
    """
    Upload PDF documents to an existing session.

    Documents will be analyzed for text content and sentiment.
    """
    # Verify session exists
    session = await upload_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    s3_keys = []
    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files allowed. Got: {file.content_type}",
            )

        try:
            s3_key = await upload_service.upload_document(session_id, file)
            s3_keys.append(s3_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    return {
        "session_id": session_id,
        "document_keys": s3_keys,
        "documents_count": len(s3_keys),
    }


@router.post("/text")
async def add_text_input(
    session_id: str = Form(...),
    text: str = Form(...),
    upload_service: UploadService = Depends(get_upload_service),
):
    """
    Add text input (doctor's notes) to an existing session.

    Text will be analyzed for sentiment and key phrases.
    """
    # Verify session exists
    session = await upload_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        await upload_service.add_text_input(session_id, text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add text: {str(e)}")

    return {
        "session_id": session_id,
        "text_length": len(text),
        "status": "added",
    }
