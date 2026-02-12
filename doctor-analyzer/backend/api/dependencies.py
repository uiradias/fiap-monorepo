"""FastAPI dependency injection setup."""

from functools import lru_cache

from config.settings import Settings, get_settings
from infrastructure.aws.s3_client import S3Client
from infrastructure.aws.rekognition_client import RekognitionClient
from infrastructure.aws.transcribe_client import TranscribeClient
from infrastructure.aws.comprehend_client import ComprehendClient
from infrastructure.websocket.connection_manager import ConnectionManager
from domain.session import SessionStoreProtocol
from infrastructure.database.session_repository import PostgresSessionStore
from infrastructure.database.patient_repository import PatientRepository
from services.upload_service import UploadService
from services.video_analysis_service import VideoAnalysisService
from services.audio_analysis_service import AudioAnalysisService
from services.aggregation_service import AggregationService
from services.patient_service import PatientService


# Singleton instances
_connection_manager: ConnectionManager = None
_session_store: SessionStoreProtocol = None
_patient_repository: PatientRepository = None
_patient_service: PatientService = None


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


def get_session_store() -> SessionStoreProtocol:
    """Get session store singleton."""
    global _session_store
    if _session_store is None:
        _session_store = PostgresSessionStore()
    return _session_store


def get_patient_repository() -> PatientRepository:
    """Get patient repository singleton."""
    global _patient_repository
    if _patient_repository is None:
        _patient_repository = PatientRepository()
    return _patient_repository


def get_patient_service() -> PatientService:
    """Get patient service singleton."""
    global _patient_service
    if _patient_service is None:
        _patient_service = PatientService(repository=get_patient_repository())
    return _patient_service


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


def get_aggregation_service() -> AggregationService:
    """Get aggregation service."""
    return AggregationService(
        s3=get_s3_client(),
        ws_manager=get_connection_manager(),
        session_store=get_session_store(),
    )
