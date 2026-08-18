"""Patient creation, CNIC search, the cross-facility patient summary page, and access history."""
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.allergy import Allergy
from app.models.audit_log import AuditAction, AuditLog
from app.models.condition import Condition
from app.models.facility import Facility
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.record import Record
from app.models.user import Role, User
from app.schemas.access_history import AccessHistoryEntryOut, AccessHistoryPageOut
from app.schemas.patient import PatientCreate, PatientDetailOut, PatientOut, RecordDetailOut
from app.services.audit import log_action
from app.services.content_negotiation import wants_json
from app.services.patient_access import CONSENT_DENIED_DETAIL, get_patient_or_404, has_consent_access
from app.services.security import get_current_user, require_role

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CREATE_PATIENT_ROLES = [Role.ADMIN, Role.DOCTOR, Role.PHARMACIST, Role.RECEPTIONIST]
ACCESS_HISTORY_PAGE_SIZE = 20
ACCESS_HISTORY_RESTRICTED_DETAIL = "This patient's access history is only visible to staff at the creating facility"


@router.get("/patients/new", response_class=HTMLResponse)
def new_patient_page(request: Request, user: User = Depends(require_role(CREATE_PATIENT_ROLES))):
    """Render the create-patient form."""
    return templates.TemplateResponse(request, "patient_new.html")


@router.post("/patients", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(CREATE_PATIENT_ROLES)),
):
    """Create a new patient, rejecting a CNIC that's already registered."""
    existing = db.query(Patient).filter(Patient.cnic == payload.cnic).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A patient with this CNIC already exists")

    patient = Patient(
        cnic=payload.cnic,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        blood_group=payload.blood_group,
        phone=payload.phone,
        address=payload.address,
        consent_sharing=payload.consent_sharing,
        created_by_facility_id=user.facility_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/patients/search", response_model=PatientOut)
def search_patient(cnic: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Look up a patient by exact CNIC match."""
    patient = db.query(Patient).filter(Patient.cnic == cnic).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("/patients/{patient_id}", response_class=HTMLResponse)
def patient_summary(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Render the patient summary: allergy banner, conditions, current medications, latest records.

    Returns JSON instead of HTML when the caller's Accept header prefers application/json
    (the future React app); existing HTML callers are unaffected.
    """
    patient = get_patient_or_404(db, patient_id)

    if not has_consent_access(patient, user):
        if wants_json(request):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": CONSENT_DENIED_DETAIL})
        return templates.TemplateResponse(
            request, "consent_denied.html", {"patient": patient}, status_code=status.HTTP_403_FORBIDDEN
        )

    ip_address = request.client.host if request.client else None
    log_action(
        db,
        action=AuditAction.VIEWED_SUMMARY,
        user_id=user.id,
        facility_id=user.facility_id,
        patient_id=patient.id,
        ip_address=ip_address,
    )

    allergies = db.query(Allergy).filter(Allergy.patient_id == patient.id).all()
    conditions = db.query(Condition).filter(Condition.patient_id == patient.id).all()
    active_medications = (
        db.query(Medication)
        .filter(Medication.patient_id == patient.id, Medication.stopped_at.is_(None))
        .order_by(Medication.started_at.desc())
        .all()
    )
    past_medications = (
        db.query(Medication)
        .filter(Medication.patient_id == patient.id, Medication.stopped_at.isnot(None))
        .order_by(Medication.stopped_at.desc())
        .all()
    )
    record_rows = (
        db.query(Record, Facility.name, User.full_name)
        .join(Facility, Record.facility_id == Facility.id)
        .join(User, Record.author_user_id == User.id)
        .filter(Record.patient_id == patient.id)
        .order_by(Record.created_at.desc())
        .limit(10)
        .all()
    )
    is_creating_facility = user.facility_id == patient.created_by_facility_id

    if wants_json(request):
        detail = PatientDetailOut(
            id=patient.id,
            cnic=patient.cnic,
            full_name=patient.full_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            blood_group=patient.blood_group,
            phone=patient.phone,
            address=patient.address,
            consent_sharing=patient.consent_sharing,
            created_by_facility_id=patient.created_by_facility_id,
            created_at=patient.created_at,
            is_creating_facility=is_creating_facility,
            allergies=allergies,
            conditions=conditions,
            active_medications=active_medications,
            past_medications=past_medications,
            records=[
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
            ],
        )
        return JSONResponse(content=detail.model_dump(mode="json"))

    records = [
        {"record": record, "facility_name": facility_name, "author_name": author_name}
        for record, facility_name, author_name in record_rows
    ]
    return templates.TemplateResponse(
        request,
        "patient_summary.html",
        {
            "patient": patient,
            "allergies": allergies,
            "conditions": conditions,
            "active_medications": active_medications,
            "past_medications": past_medications,
            "records": records,
            "is_creating_facility": is_creating_facility,
        },
    )


@router.get("/patients/{patient_id}/access-history", response_class=HTMLResponse)
def patient_access_history(
    patient_id: str,
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Show who has viewed or edited this patient's record. Visible only to staff at the creating facility."""
    patient = get_patient_or_404(db, patient_id)

    if user.facility_id != patient.created_by_facility_id:
        if wants_json(request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, content={"detail": ACCESS_HISTORY_RESTRICTED_DETAIL}
            )
        return templates.TemplateResponse(
            request, "access_history_restricted.html", {"patient": patient}, status_code=status.HTTP_403_FORBIDDEN
        )

    page = max(page, 1)
    total = db.query(AuditLog).filter(AuditLog.patient_id == patient.id).count()
    total_pages = max(ceil(total / ACCESS_HISTORY_PAGE_SIZE), 1)
    page = min(page, total_pages)

    rows = (
        db.query(AuditLog, User.full_name, Facility.name)
        .outerjoin(User, AuditLog.user_id == User.id)
        .outerjoin(Facility, AuditLog.facility_id == Facility.id)
        .filter(AuditLog.patient_id == patient.id)
        .order_by(AuditLog.timestamp.desc())
        .offset((page - 1) * ACCESS_HISTORY_PAGE_SIZE)
        .limit(ACCESS_HISTORY_PAGE_SIZE)
        .all()
    )

    if wants_json(request):
        page_out = AccessHistoryPageOut(
            entries=[
                AccessHistoryEntryOut(
                    id=log.id,
                    action=log.action,
                    timestamp=log.timestamp,
                    user_name=staff_name,
                    facility_name=facility_name,
                    override_reason=log.override_reason,
                )
                for log, staff_name, facility_name in rows
            ],
            page=page,
            total_pages=total_pages,
        )
        return JSONResponse(content=page_out.model_dump(mode="json"))

    entries = [
        {"log": log, "user_name": staff_name, "facility_name": facility_name}
        for log, staff_name, facility_name in rows
    ]
    return templates.TemplateResponse(
        request,
        "patient_access_history.html",
        {"patient": patient, "entries": entries, "page": page, "total_pages": total_pages},
    )
