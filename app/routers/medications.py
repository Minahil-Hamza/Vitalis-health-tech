"""Add and stop patient medications, enforcing drug-interaction and allergy safety checks."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditAction
from app.models.medication import Medication
from app.models.user import User
from app.schemas.medication import MedicationCreate, MedicationCreateResponse, MedicationOut
from app.services.audit import log_action
from app.services.interactions import evaluate_drug_safety
from app.services.patient_access import CONSENT_DENIED_DETAIL, get_patient_or_404, has_consent_access
from app.services.security import get_current_user

router = APIRouter()


@router.post(
    "/patients/{patient_id}/medications",
    response_model=MedicationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_medication(
    patient_id: str,
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a medication, blocking on a major interaction or allergy unless an override reason is given."""
    patient = get_patient_or_404(db, patient_id)
    if not has_consent_access(patient, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=CONSENT_DENIED_DETAIL)

    override_reason, warnings = evaluate_drug_safety(payload.drug_name, patient, db, payload.override_reason)

    medication = Medication(
        patient_id=patient.id,
        drug_name=payload.drug_name,
        brand_name=payload.brand_name,
        dose=payload.dose,
        frequency=payload.frequency,
        started_at=payload.started_at,
        prescribed_by_user_id=user.id,
        facility_id=user.facility_id,
        override_reason=override_reason,
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)

    log_action(
        db,
        action=AuditAction.ADDED_MEDICATION,
        user_id=user.id,
        facility_id=user.facility_id,
        patient_id=patient.id,
        override_reason=medication.override_reason,
    )

    return MedicationCreateResponse(
        id=medication.id,
        drug_name=medication.drug_name,
        dose=medication.dose,
        stopped_at=medication.stopped_at,
        warnings=warnings,
    )


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
