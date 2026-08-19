"""Drug interaction and allergy safety checks, shared by medication and prescription-record creation."""
from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.allergy import Allergy
from app.models.drug_interaction import DrugInteraction, InteractionSeverity
from app.models.medication import Medication
from app.models.patient import Patient
from app.schemas.safety import InteractionWarning, SafetyBlockedDetail


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


def evaluate_drug_safety(
    drug_name: str, patient: Patient, db: Session, override_reason: str | None
) -> tuple[str | None, list[str]]:
    """Run both safety checks for a drug being added (as a medication or a prescription record).

    Returns (accepted_override_reason, non_blocking_warnings). Raises HTTPException(409)
    if a major interaction or allergy hit exists and no override reason was given — the
    caller is expected to let that propagate as the route's response.
    """
    interactions = check_interactions(drug_name, patient, db)
    allergy_hits = check_allergy(drug_name, patient, db)
    major_interactions = [i for i in interactions if i.severity == InteractionSeverity.MAJOR]
    minor_moderate_interactions = [i for i in interactions if i.severity != InteractionSeverity.MAJOR]
    blocking = bool(major_interactions) or bool(allergy_hits)

    cleaned_override = override_reason.strip() if override_reason else None

    if blocking and not cleaned_override:
        detail = SafetyBlockedDetail(
            message="This requires an override reason due to a major interaction or a recorded allergy.",
            interactions=[
                InteractionWarning(
                    drug_a=i.drug_a,
                    drug_b=i.drug_b,
                    severity=i.severity.value,
                    description=i.description,
                    recommendation=i.recommendation,
                )
                for i in major_interactions
            ],
            allergy_hits=[a.substance for a in allergy_hits],
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail.model_dump())

    new_drug_lower = drug_name.strip().lower()
    warnings = [
        f"{i.severity.value.capitalize()} interaction with "
        f"{i.drug_b if i.drug_a == new_drug_lower else i.drug_a}: {i.description}"
        for i in minor_moderate_interactions
    ]

    return (cleaned_override if blocking else None), warnings
