"""Unit tests for the check_interactions / check_allergy safety-check functions."""
from datetime import date

from app.models.allergy import Allergy, Severity
from app.models.drug_interaction import DrugInteraction, InteractionSeverity
from app.models.medication import Medication
from app.services.interactions import check_allergy, check_interactions


def test_check_interactions_finds_conflict_regardless_of_direction(db_session, seeded_admin):
    facility, admin, _password = seeded_admin
    from app.models.patient import Gender, Patient

    patient = Patient(
        cnic="12345-1234567-1",
        full_name="Test Patient",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.MALE,
        created_by_facility_id=facility.id,
    )
    db_session.add(patient)
    db_session.flush()

    db_session.add(
        Medication(
            patient_id=patient.id,
            drug_name="warfarin",
            dose="5mg",
            frequency="once daily",
            started_at=date(2024, 1, 1),
            facility_id=facility.id,
        )
    )
    db_session.add(
        DrugInteraction(
            drug_a="aspirin",
            drug_b="warfarin",
            severity=InteractionSeverity.MAJOR,
            description="Increased bleeding risk.",
            recommendation="Avoid combination.",
        )
    )
    db_session.commit()

    conflicts = check_interactions("aspirin", patient, db_session)
    assert len(conflicts) == 1
    assert conflicts[0].severity == InteractionSeverity.MAJOR

    # No conflict against an unrelated drug
    assert check_interactions("paracetamol", patient, db_session) == []


def test_check_interactions_ignores_stopped_medications(db_session, seeded_admin):
    facility, _admin, _password = seeded_admin
    from app.models.patient import Gender, Patient

    patient = Patient(
        cnic="22222-2222222-2",
        full_name="Test Patient 2",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.MALE,
        created_by_facility_id=facility.id,
    )
    db_session.add(patient)
    db_session.flush()

    db_session.add(
        Medication(
            patient_id=patient.id,
            drug_name="warfarin",
            dose="5mg",
            frequency="once daily",
            started_at=date(2020, 1, 1),
            stopped_at=date(2021, 1, 1),
            facility_id=facility.id,
        )
    )
    db_session.add(
        DrugInteraction(
            drug_a="aspirin",
            drug_b="warfarin",
            severity=InteractionSeverity.MAJOR,
            description="Increased bleeding risk.",
            recommendation="Avoid combination.",
        )
    )
    db_session.commit()

    assert check_interactions("aspirin", patient, db_session) == []


def test_check_allergy_matches_exact_and_substring(db_session, seeded_admin):
    facility, _admin, _password = seeded_admin
    from app.models.patient import Gender, Patient

    patient = Patient(
        cnic="33333-3333333-3",
        full_name="Test Patient 3",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.MALE,
        created_by_facility_id=facility.id,
    )
    db_session.add(patient)
    db_session.flush()
    db_session.add(Allergy(patient_id=patient.id, substance="Penicillin", severity=Severity.SEVERE))
    db_session.commit()

    assert len(check_allergy("penicillin", patient, db_session)) == 1  # exact (case-insensitive)
    assert len(check_allergy("amoxicillin-penicillin combo", patient, db_session)) == 1  # substring
    assert check_allergy("ibuprofen", patient, db_session) == []  # no match
