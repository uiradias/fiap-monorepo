"""FastAPI dependency injection setup."""

from functools import lru_cache

from config.settings import Settings, get_settings
from infrastructure.aws.s3_client import S3Client
from infrastructure.aws.rekognition_client import RekognitionClient
from infrastructure.aws.transcribe_client import TranscribeClient
from infrastructure.aws.comprehend_client import ComprehendClient
from infrastructure.aws.textract_client import TextractClient
from infrastructure.websocket.connection_manager import ConnectionManager
from domain.session import SessionStore
from services.upload_service import UploadService
from services.video_analysis_service import VideoAnalysisService
from services.audio_analysis_service import AudioAnalysisService
from services.document_analysis_service import DocumentAnalysisService
from services.aggregation_service import AggregationService


# Singleton instances
_connection_manager: ConnectionManager = None
_session_store: SessionStore = None


@lru_cache()
def get_cached_settings() -> Settings:
    """Get cached settings instance."""
    return get_settings()


def get_connection_manager() -> ConnectionManager:
    """Get WebSocket connection manager singleton."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def get_session_store() -> SessionStore:
    """Get session store singleton."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store


def get_s3_client() -> S3Client:
    """Get S3 client."""
    settings = get_cached_settings()
    return S3Client(settings.aws)


def get_rekognition_client() -> RekognitionClient:
    """Get Rekognition client."""
    settings = get_cached_settings()
    return RekognitionClient(settings.aws)


def get_transcribe_client() -> TranscribeClient:
    """Get Transcribe client."""
    settings = get_cached_settings()
    return TranscribeClient(settings.aws)


def get_comprehend_client() -> ComprehendClient:
    """Get Comprehend client."""
    settings = get_cached_settings()
    return ComprehendClient(settings.aws)


def get_textract_client() -> TextractClient:
    """Get Textract client."""
    settings = get_cached_settings()
    return TextractClient(settings.aws)


def get_upload_service() -> UploadService:
    """Get upload service."""
    return UploadService(
        s3_client=get_s3_client(),
        session_store=get_session_store(),
    )


def get_video_analysis_service() -> VideoAnalysisService:
    """Get video analysis service."""
    return VideoAnalysisService(
        rekognition=get_rekognition_client(),
        s3=get_s3_client(),
        ws_manager=get_connection_manager(),
        session_store=get_session_store(),
    )


def get_audio_analysis_service() -> AudioAnalysisService:
    """Get audio analysis service."""
    return AudioAnalysisService(
        transcribe=get_transcribe_client(),
        comprehend=get_comprehend_client(),
        s3=get_s3_client(),
        ws_manager=get_connection_manager(),
        session_store=get_session_store(),
    )


def get_document_analysis_service() -> DocumentAnalysisService:
    """Get document analysis service."""
    return DocumentAnalysisService(
        textract=get_textract_client(),
        comprehend=get_comprehend_client(),
        s3=get_s3_client(),
        ws_manager=get_connection_manager(),
        session_store=get_session_store(),
    )


def get_aggregation_service() -> AggregationService:
    """Get aggregation service."""
    return AggregationService(
        s3=get_s3_client(),
        ws_manager=get_connection_manager(),
        session_store=get_session_store(),
    )
