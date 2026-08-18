"""Drug interaction and allergy safety checks run before saving a new medication."""
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.allergy import Allergy
from app.models.drug_interaction import DrugInteraction
from app.models.medication import Medication
from app.models.patient import Patient


def check_interactions(new_drug: str, patient: Patient, db: Session) -> list[DrugInteraction]:
    """Return DrugInteraction rows that conflict with the patient's active medications."""
    new_drug_lower = new_drug.strip().lower()
    active_drug_names = {
        m.drug_name.strip().lower()
        for m in db.query(Medication)
        .filter(Medication.patient_id == patient.id, Medication.stopped_at.is_(None))
        .all()
    }
    if not active_drug_names:
        return []

    return (
        db.query(DrugInteraction)
        .filter(
            or_(
                and_(DrugInteraction.drug_a == new_drug_lower, DrugInteraction.drug_b.in_(active_drug_names)),
                and_(DrugInteraction.drug_b == new_drug_lower, DrugInteraction.drug_a.in_(active_drug_names)),
            )
        )
        .all()
    )


def check_allergy(new_drug: str, patient: Patient, db: Session) -> list[Allergy]:
    """Return Allergy rows whose substance matches the new drug (exact or substring, v1)."""
    new_drug_lower = new_drug.strip().lower()
    hits = []
    for allergy in db.query(Allergy).filter(Allergy.patient_id == patient.id).all():
        substance_lower = allergy.substance.strip().lower()
        if substance_lower and (substance_lower in new_drug_lower or new_drug_lower in substance_lower):
            hits.append(allergy)
    return hits
