"""Add chronic conditions. No dedicated audit action exists for this in the spec's enum."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.condition import Condition
from app.models.user import User
from app.schemas.condition import ConditionCreate, ConditionOut
from app.services.patient_access import CONSENT_DENIED_DETAIL, get_patient_or_404, has_consent_access
from app.services.security import get_current_user

router = APIRouter()


@router.post("/patients/{patient_id}/conditions", response_model=ConditionOut, status_code=status.HTTP_201_CREATED)
def add_condition(
    patient_id: str,
    payload: ConditionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a chronic condition for a patient."""
    patient = get_patient_or_404(db, patient_id)
    if not has_consent_access(patient, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=CONSENT_DENIED_DETAIL)

    condition = Condition(
        patient_id=patient.id,
        name=payload.name,
        diagnosed_date=payload.diagnosed_date,
        notes=payload.notes,
        body_region=payload.body_region,
    )
    db.add(condition)
    db.commit()
    db.refresh(condition)
    return condition
