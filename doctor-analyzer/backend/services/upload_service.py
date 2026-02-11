"""Service for handling file uploads."""

from typing import Optional
from fastapi import UploadFile
from datetime import datetime
import uuid
import logging

from infrastructure.aws.s3_client import S3Client
from domain.session import AnalysisSession, SessionStore
from domain.analysis import AnalysisStatus

logger = logging.getLogger(__name__)


class UploadService:
    """Orchestrates file uploads to S3 and session management."""

    def __init__(self, s3_client: S3Client, session_store: SessionStore):
        self._s3 = s3_client
        self._sessions = session_store

    async def create_session(
        self,
        patient_id: Optional[str] = None,
    ) -> AnalysisSession:
        """Create a new analysis session."""
        session = AnalysisSession(
            session_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            status=AnalysisStatus.PENDING,
            patient_id=patient_id,
        )
        await self._sessions.create(session)
        logger.info(f"Created session {session.session_id}")
        return session

    async def upload_video(
        self,
        session_id: str,
        file: UploadFile,
    ) -> str:
        """
        Upload video file to S3.

        Args:
            session_id: Session to attach video to
            file: Video file to upload

        Returns:
            S3 key of uploaded file
        """
        session = await self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        s3_key = f"sessions/{session_id}/video/{file.filename}"

        # Get content type
        content_type = file.content_type or 'video/mp4'

        # Upload to S3
        await self._s3.upload_file(file.file, s3_key, content_type)

        # Update session
        session.video_s3_key = s3_key
        session.update_status(AnalysisStatus.UPLOADING)
        await self._sessions.update(session)

        logger.info(f"Uploaded video {file.filename} to {s3_key}")
        return s3_key

    async def upload_document(
        self,
        session_id: str,
        file: UploadFile,
    ) -> str:
        """
        Upload PDF document to S3.

        Args:
            session_id: Session to attach document to
            file: PDF file to upload

        Returns:
            S3 key of uploaded file
        """
        session = await self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        s3_key = f"sessions/{session_id}/documents/{file.filename}"

        # Upload to S3
        await self._s3.upload_file(file.file, s3_key, 'application/pdf')

        # Update session
        session.add_document(s3_key)
        await self._sessions.update(session)

        logger.info(f"Uploaded document {file.filename} to {s3_key}")
        return s3_key

    async def add_text_input(
        self,
        session_id: str,
        text: str,
    ) -> None:
        """
        Add text input to session.

        Args:
            session_id: Session to add text to
            text: Text input from doctor
        """
        session = await self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.text_input = text
        await self._sessions.update(session)

        # Also save to S3 for backup
        s3_key = f"sessions/{session_id}/text_input.txt"
        await self._s3.upload_bytes(text.encode('utf-8'), s3_key, 'text/plain')

        logger.info(f"Added text input to session {session_id}")

    async def get_session(self, session_id: str) -> Optional[AnalysisSession]:
        """Get session by ID."""
        return await self._sessions.get(session_id)

    async def get_video_url(self, session_id: str) -> Optional[str]:
        """Get presigned URL for video playback."""
        session = await self._sessions.get(session_id)
        if not session or not session.video_s3_key:
            return None

        return await self._s3.get_presigned_url(session.video_s3_key)

    async def delete_session(self, session_id: str) -> bool:
        """Delete session and all associated files."""
        session = await self._sessions.get(session_id)
        if not session:
            return False

        # Delete files from S3
        files = await self._s3.list_files(f"sessions/{session_id}/")
        for file_key in files:
            await self._s3.delete_file(file_key)

        # Delete session
        await self._sessions.delete(session_id)
        logger.info(f"Deleted session {session_id}")
        return True
