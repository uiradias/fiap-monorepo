"""Patient management API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.patient_service import PatientService
from domain.session import SessionStoreProtocol
from api.dependencies import get_patient_service, get_session_store

router = APIRouter(prefix="/patients", tags=["patients"])


class CreatePatientRequest(BaseModel):
    id: str
    codename: str


@router.post("")
async def create_patient(
    body: CreatePatientRequest,
    patient_service: PatientService = Depends(get_patient_service),
):
    """Create a new patient."""
    try:
        patient = await patient_service.create_patient(body.id, body.codename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return patient.to_dict()


@router.get("")
async def list_patients(
    patient_service: PatientService = Depends(get_patient_service),
):
    """List all patients."""
    patients = await patient_service.list_patients()
    return {
        "patients": [p.to_dict() for p in patients],
        "total": len(patients),
    }


@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    patient_service: PatientService = Depends(get_patient_service),
):
    """Get a patient by ID."""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return patient.to_dict()


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    patient_service: PatientService = Depends(get_patient_service),
):
    """Delete a patient and all associated sessions."""
    success = await patient_service.delete_patient(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return {"status": "deleted", "patient_id": patient_id}


@router.get("/{patient_id}/sessions")
async def get_patient_sessions(
    patient_id: str,
    patient_service: PatientService = Depends(get_patient_service),
    session_store: SessionStoreProtocol = Depends(get_session_store),
):
    """Get all sessions for a patient."""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    sessions = await session_store.list_by_patient(patient_id)
    return {
        "sessions": [s.to_dict() for s in sessions],
        "total": len(sessions),
    }
