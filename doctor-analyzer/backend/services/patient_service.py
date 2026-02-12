"""Patient business logic."""

from datetime import datetime, timezone
from typing import List, Optional

from domain.patient import Patient
from infrastructure.database.patient_repository import PatientRepository


class PatientService:
    """Service layer for patient operations."""

    def __init__(self, repository: PatientRepository):
        self._repo = repository

    async def create_patient(self, patient_id: str, codename: str) -> Patient:
        patient = Patient(
            id=patient_id,
            codename=codename,
            created_at=datetime.now(timezone.utc),
        )
        return await self._repo.create(patient)

    async def get_patient(self, patient_id: str) -> Optional[Patient]:
        return await self._repo.get(patient_id)

    async def patient_exists(self, patient_id: str) -> bool:
        return await self._repo.exists(patient_id)

    async def list_patients(self) -> List[Patient]:
        return await self._repo.list_all()

    async def delete_patient(self, patient_id: str) -> bool:
        return await self._repo.delete(patient_id)
