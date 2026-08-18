"""Add patient allergies. No dedicated audit action exists for this in the spec's enum."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.allergy import Allergy
from app.models.user import User
from app.schemas.allergy import AllergyCreate, AllergyOut
from app.services.patient_access import get_patient_or_404, has_consent_access
from app.services.security import get_current_user

router = APIRouter()

CONSENT_DENIED_DETAIL = "This patient has not consented to sharing with your facility"


@router.post("/patients/{patient_id}/allergies", response_model=AllergyOut, status_code=status.HTTP_201_CREATED)
def add_allergy(
    patient_id: str,
    payload: AllergyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add an allergy for a patient."""
    patient = get_patient_or_404(db, patient_id)
    if not has_consent_access(patient, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=CONSENT_DENIED_DETAIL)

    allergy = Allergy(
        patient_id=patient.id,
        substance=payload.substance,
        severity=payload.severity,
        noted_by_user_id=user.id,
    )
    db.add(allergy)
    db.commit()
    db.refresh(allergy)
    return allergy
