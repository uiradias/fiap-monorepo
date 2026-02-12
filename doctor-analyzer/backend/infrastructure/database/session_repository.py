"""PostgreSQL session store implementation."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import select

from domain.analysis import AnalysisStatus, ClinicalIndicator
from domain.session import AnalysisSession, SessionStoreProtocol
from infrastructure.database.engine import get_session_factory
from infrastructure.database.models import AnalysisSessionModel


class PostgresSessionStore(SessionStoreProtocol):
    """Persists sessions to PostgreSQL."""

    # ── helpers ──────────────────────────────────────────────

    @staticmethod
    def _to_domain(row: AnalysisSessionModel) -> AnalysisSession:
        return AnalysisSession(
            session_id=str(row.session_id),
            patient_id=str(row.patient_id),
            created_at=row.created_at,
            updated_at=row.updated_at,
            status=AnalysisStatus(row.status),
            video_s3_key=row.video_s3_key,
            results_s3_key=row.results_s3_key,
            emotion_summary=row.emotion_summary or {},
            clinical_indicators=[
                ClinicalIndicator(**ci) for ci in (row.clinical_indicators or [])
            ],
            error_message=row.error_message,
            # These stay None — populated in-memory during pipeline, persisted to S3
            video_emotions=None,
            audio_analysis=None,
        )

    @staticmethod
    def _to_model(session: AnalysisSession) -> AnalysisSessionModel:
        return AnalysisSessionModel(
            session_id=uuid.UUID(session.session_id),
            patient_id=uuid.UUID(session.patient_id),
            created_at=session.created_at,
            updated_at=session.updated_at,
            status=session.status.value if isinstance(session.status, AnalysisStatus) else session.status,
            video_s3_key=session.video_s3_key,
            results_s3_key=session.results_s3_key,
            emotion_summary=session.emotion_summary or {},
            clinical_indicators=[ci.to_dict() for ci in session.clinical_indicators],
            error_message=session.error_message,
        )

    # ── interface ────────────────────────────────────────────

    async def create(self, session: AnalysisSession) -> AnalysisSession:
        factory = get_session_factory()
        async with factory() as db:
            model = self._to_model(session)
            db.add(model)
            await db.commit()
            await db.refresh(model)
            return self._to_domain(model)

    async def get(self, session_id: str) -> Optional[AnalysisSession]:
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(AnalysisSessionModel, uuid.UUID(session_id))
            return self._to_domain(row) if row else None

    async def update(self, session: AnalysisSession) -> AnalysisSession:
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(AnalysisSessionModel, uuid.UUID(session.session_id))
            if row is None:
                raise ValueError(f"Session {session.session_id} not found")
            row.patient_id = uuid.UUID(session.patient_id)
            row.status = session.status.value if isinstance(session.status, AnalysisStatus) else session.status
            row.updated_at = datetime.now(timezone.utc)
            row.video_s3_key = session.video_s3_key
            row.results_s3_key = session.results_s3_key
            row.emotion_summary = session.emotion_summary or {}
            row.clinical_indicators = [ci.to_dict() for ci in session.clinical_indicators]
            row.error_message = session.error_message
            await db.commit()
            await db.refresh(row)
            return self._to_domain(row)

    async def delete(self, session_id: str) -> bool:
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(AnalysisSessionModel, uuid.UUID(session_id))
            if row is None:
                return False
            await db.delete(row)
            await db.commit()
            return True

    async def list_all(self) -> List[AnalysisSession]:
        factory = get_session_factory()
        async with factory() as db:
            result = await db.execute(
                select(AnalysisSessionModel).order_by(AnalysisSessionModel.created_at.desc())
            )
            return [self._to_domain(r) for r in result.scalars().all()]

    async def list_by_patient(self, patient_id: str) -> List[AnalysisSession]:
        factory = get_session_factory()
        async with factory() as db:
            result = await db.execute(
                select(AnalysisSessionModel)
                .where(AnalysisSessionModel.patient_id == uuid.UUID(patient_id))
                .order_by(AnalysisSessionModel.created_at.desc())
            )
            return [self._to_domain(r) for r in result.scalars().all()]
