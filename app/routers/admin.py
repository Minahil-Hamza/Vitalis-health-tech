"""Admin-only endpoints: staff management, facility counts, and drug interaction CSV import."""
import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.drug_interaction import DrugInteraction, InteractionSeverity
from app.models.patient import Patient
from app.models.record import Record
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserOut
from app.services.security import hash_password, require_role

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

REQUIRED_COLUMNS = {"drug_a", "drug_b", "severity", "description", "recommendation"}


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([Role.ADMIN])),
):
    """Show this facility's staff, simple counts, and staff management forms."""
    staff = db.query(User).filter(User.facility_id == user.facility_id).order_by(User.full_name).all()

    patients_created = db.query(Patient).filter(Patient.created_by_facility_id == user.facility_id).count()

    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    records_this_month = (
        db.query(Record)
        .filter(Record.facility_id == user.facility_id, Record.created_at >= month_start)
        .count()
    )

    return templates.TemplateResponse(
        request,
        "admin_dashboard.html",
        {
            "staff": staff,
            "patients_created": patients_created,
            "records_this_month": records_this_month,
            "current_user_id": user.id,
        },
    )


@router.post("/admin/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def add_staff(
    payload: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([Role.ADMIN])),
):
    """Add a new staff member to the admin's own facility."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")

    new_user = User(
        facility_id=user.facility_id,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/admin/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_staff(
    user_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([Role.ADMIN])),
):
    """Deactivate a staff member at the admin's own facility. An admin cannot deactivate their own account."""
    if user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account")

    target = db.get(User, user_id)
    if target is None or target.facility_id != user.facility_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    target.is_active = False
    db.commit()
    db.refresh(target)
    return target


@router.post("/admin/interactions/import", status_code=status.HTTP_201_CREATED)
async def import_interactions(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([Role.ADMIN])),
):
    """Import DrugInteraction rows from a CSV with columns: drug_a,drug_b,severity,description,recommendation.

    Bad rows are skipped and reported rather than failing the whole import, since this
    table is hand-authored.
    """
    raw = await file.read()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))

    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        return {"imported": 0, "errors": [f"CSV must have columns: {', '.join(sorted(REQUIRED_COLUMNS))}"]}

    imported = 0
    errors = []
    for line_number, row in enumerate(reader, start=2):
        try:
            interaction = DrugInteraction(
                drug_a=row["drug_a"].strip().lower(),
                drug_b=row["drug_b"].strip().lower(),
                severity=InteractionSeverity(row["severity"].strip().lower()),
                description=row["description"].strip(),
                recommendation=row["recommendation"].strip(),
            )
            db.add(interaction)
            imported += 1
        except (ValueError, KeyError, AttributeError) as exc:
            errors.append(f"Row {line_number}: {exc}")

    db.commit()
    return {"imported": imported, "errors": errors}
