"""Add and stop patient medications."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditAction
from app.models.medication import Medication
from app.models.user import User
from app.schemas.medication import MedicationCreate, MedicationOut
from app.services.audit import log_action
from app.services.patient_access import get_patient_or_404, has_consent_access
from app.services.security import get_current_user

router = APIRouter()

CONSENT_DENIED_DETAIL = "This patient has not consented to sharing with your facility"


@router.post("/patients/{patient_id}/medications", response_model=MedicationOut, status_code=status.HTTP_201_CREATED)
def add_medication(
    patient_id: str,
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a medication for a patient and audit it as added_medication."""
    patient = get_patient_or_404(db, patient_id)
    if not has_consent_access(patient, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=CONSENT_DENIED_DETAIL)

    medication = Medication(
        patient_id=patient.id,
        drug_name=payload.drug_name,
        brand_name=payload.brand_name,
        dose=payload.dose,
        frequency=payload.frequency,
        started_at=payload.started_at,
        prescribed_by_user_id=user.id,
        facility_id=user.facility_id,
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)

    log_action(
        db, action=AuditAction.ADDED_MEDICATION, user_id=user.id, facility_id=user.facility_id, patient_id=patient.id
    )
    return medication


@router.post("/patients/{patient_id}/medications/{medication_id}/stop", response_model=MedicationOut)
def stop_medication(
    patient_id: str,
    medication_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark a medication as stopped today, moving it out of the active list."""
    patient = get_patient_or_404(db, patient_id)
    if not has_consent_access(patient, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=CONSENT_DENIED_DETAIL)

    medication = db.get(Medication, medication_id)
    if medication is None or medication.patient_id != patient.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    if medication.stopped_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Medication is already stopped")

    medication.stopped_at = date.today()
    db.commit()
    db.refresh(medication)
    return medication
