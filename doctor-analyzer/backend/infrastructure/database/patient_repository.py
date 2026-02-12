"""PostgreSQL patient repository."""

from typing import List, Optional
import uuid

from sqlalchemy import select

from domain.patient import Patient
from infrastructure.database.engine import get_session_factory
from infrastructure.database.models import PatientModel


class PatientRepository:
    """CRUD operations for patients in PostgreSQL."""

    @staticmethod
    def _to_domain(row: PatientModel) -> Patient:
        return Patient(
            id=str(row.id),
            codename=row.codename,
            created_at=row.created_at,
        )

    async def create(self, patient: Patient) -> Patient:
        factory = get_session_factory()
        async with factory() as db:
            model = PatientModel(
                id=uuid.UUID(patient.id),
                codename=patient.codename,
                created_at=patient.created_at,
            )
            db.add(model)
            await db.commit()
            await db.refresh(model)
            return self._to_domain(model)

    async def get(self, patient_id: str) -> Optional[Patient]:
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(PatientModel, uuid.UUID(patient_id))
            return self._to_domain(row) if row else None

    async def exists(self, patient_id: str) -> bool:
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(PatientModel, uuid.UUID(patient_id))
            return row is not None

    async def list_all(self) -> List[Patient]:
        factory = get_session_factory()
        async with factory() as db:
            result = await db.execute(
                select(PatientModel).order_by(PatientModel.created_at.desc())
            )
            return [self._to_domain(r) for r in result.scalars().all()]

    async def delete(self, patient_id: str) -> bool:
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(PatientModel, uuid.UUID(patient_id))
            if row is None:
                return False
            await db.delete(row)
            await db.commit()
            return True
