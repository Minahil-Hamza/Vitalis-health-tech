"""Add clinical records and view the full patient timeline."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditAction
from app.models.facility import Facility
from app.models.record import Record
from app.models.user import User
from app.schemas.patient import RecordDetailOut
from app.schemas.record import RecordCreate, RecordOut
from app.services.audit import log_action
from app.services.content_negotiation import wants_json
from app.services.patient_access import CONSENT_DENIED_DETAIL, get_patient_or_404, has_consent_access
from app.services.security import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/patients/{patient_id}/records", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_record(
    patient_id: str,
    payload: RecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a clinical record for a patient and audit it as created_record."""
    patient = get_patient_or_404(db, patient_id)
    if not has_consent_access(patient, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=CONSENT_DENIED_DETAIL)

    record = Record(
        patient_id=patient.id,
        facility_id=user.facility_id,
        author_user_id=user.id,
        record_type=payload.record_type,
        title=payload.title,
        details=payload.details,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_action(
        db, action=AuditAction.CREATED_RECORD, user_id=user.id, facility_id=user.facility_id, patient_id=patient.id
    )
    return record


@router.get("/patients/{patient_id}/timeline", response_class=HTMLResponse)
def patient_timeline(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Show every record for a patient, newest first, tagged with facility and author."""
    patient = get_patient_or_404(db, patient_id)
    if not has_consent_access(patient, user):
        if wants_json(request):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": CONSENT_DENIED_DETAIL})
        return templates.TemplateResponse(
            request, "consent_denied.html", {"patient": patient}, status_code=status.HTTP_403_FORBIDDEN
        )

    record_rows = (
        db.query(Record, Facility.name, User.full_name)
        .join(Facility, Record.facility_id == Facility.id)
        .join(User, Record.author_user_id == User.id)
        .filter(Record.patient_id == patient.id)
        .order_by(Record.created_at.desc())
        .all()
    )

    if wants_json(request):
        records_out = [
            RecordDetailOut(
                id=record.id,
                record_type=record.record_type,
                title=record.title,
                details=record.details,
                created_at=record.created_at,
                facility_name=facility_name,
                author_name=author_name,
            )
            for record, facility_name, author_name in record_rows
        ]
        return JSONResponse(content=[r.model_dump(mode="json") for r in records_out])

    records = [
        {"record": record, "facility_name": facility_name, "author_name": author_name}
        for record, facility_name, author_name in record_rows
    ]
    return templates.TemplateResponse(request, "patient_timeline.html", {"patient": patient, "records": records})
