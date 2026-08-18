"""Admin-only endpoints: bulk import of the drug interaction reference table."""
import csv
import io

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.drug_interaction import DrugInteraction, InteractionSeverity
from app.models.user import Role, User
from app.services.security import require_role

router = APIRouter()

REQUIRED_COLUMNS = {"drug_a", "drug_b", "severity", "description", "recommendation"}


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
