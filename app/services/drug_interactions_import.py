"""Shared CSV-parsing logic for the DrugInteraction reference table, used by both the
admin HTTP import endpoint and the local seed script — one place defines the columns and
the per-row error handling, so the two never drift apart."""
import csv
import io

from sqlalchemy.orm import Session

from app.models.drug_interaction import DrugInteraction, InteractionSeverity

REQUIRED_COLUMNS = {"drug_a", "drug_b", "severity", "description", "recommendation"}


def import_interactions_from_csv_text(csv_text: str, db: Session) -> dict:
    """Parse CSV text and insert DrugInteraction rows. Bad rows are skipped and reported
    rather than failing the whole import, since this table is hand-authored."""
    reader = csv.DictReader(io.StringIO(csv_text))

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
