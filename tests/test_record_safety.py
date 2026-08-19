"""Tests for the drug-interaction/allergy safety checks on prescription-type records.

Mirrors test_medication_safety.py — the founder's Phase 4 refinement asked for the same
checks to apply to "a medication or a prescription record", not medications alone.
"""
from fastapi.testclient import TestClient

from app.main import app
from app.models.allergy import Allergy, Severity
from app.models.audit_log import AuditAction, AuditLog
from app.models.drug_interaction import DrugInteraction, InteractionSeverity
from app.models.medication import Medication
from app.models.record import Record

VALID_PATIENT = {
    "cnic": "12345-1234567-1",
    "full_name": "Test Patient",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "consent_sharing": True,
}


def _login(test_client: TestClient, email: str, password: str):
    response = test_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response


def _create_patient(test_client: TestClient, cnic="12345-1234567-1"):
    response = test_client.post("/patients", json=dict(VALID_PATIENT, cnic=cnic))
    assert response.status_code == 201
    return response.json()["id"]


def _add_active_medication(test_client: TestClient, patient_id: str, drug_name: str):
    response = test_client.post(
        f"/patients/{patient_id}/medications",
        json={"drug_name": drug_name, "dose": "5mg", "frequency": "once daily", "started_at": "2024-01-01"},
    )
    assert response.status_code == 201


def test_non_prescription_record_requires_no_drug_name(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(
        f"/patients/{patient_id}/records",
        json={"record_type": "visit", "title": "Routine checkup", "details": "All normal."},
    )
    assert response.status_code == 201


def test_prescription_record_requires_drug_name(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(
        f"/patients/{patient_id}/records",
        json={"record_type": "prescription", "title": "Prescribed antibiotics", "details": "..."},
    )
    assert response.status_code == 422


def test_drug_name_rejected_for_non_prescription_record(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(
        f"/patients/{patient_id}/records",
        json={"record_type": "visit", "title": "Routine checkup", "details": "...", "drug_name": "aspirin"},
    )
    assert response.status_code == 422


def test_prescription_record_clean_pass(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(
        f"/patients/{patient_id}/records",
        json={
            "record_type": "prescription",
            "title": "Prescribed paracetamol",
            "details": "For fever.",
            "drug_name": "paracetamol",
        },
    )

    assert response.status_code == 201
    assert response.json()["warnings"] == []
    assert response.json()["drug_name"] == "paracetamol"


def test_prescription_record_major_interaction_blocks_without_override(
    client: TestClient, seeded_admin, db_session
):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)
    _add_active_medication(client, patient_id, "warfarin")

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

    response = client.post(
        f"/patients/{patient_id}/records",
        json={
            "record_type": "prescription",
            "title": "Prescribed aspirin",
            "details": "...",
            "drug_name": "aspirin",
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert len(detail["interactions"]) == 1
    assert detail["interactions"][0]["severity"] == "major"
    assert db_session.query(Record).filter(Record.drug_name == "aspirin").count() == 0


def test_prescription_record_saves_with_override_and_audits(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)
    _add_active_medication(client, patient_id, "warfarin")

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

    response = client.post(
        f"/patients/{patient_id}/records",
        json={
            "record_type": "prescription",
            "title": "Prescribed aspirin",
            "details": "...",
            "drug_name": "aspirin",
            "override_reason": "Cardiology approved short-term dual therapy.",
        },
    )

    assert response.status_code == 201
    record = db_session.query(Record).filter(Record.drug_name == "aspirin").first()
    assert record is not None
    assert record.override_reason == "Cardiology approved short-term dual therapy."

    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.CREATED_RECORD).all()
    override_logs = [log for log in logs if log.override_reason]
    assert len(override_logs) == 1


def test_prescription_record_allergy_hit_blocks_without_override(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    db_session.add(Allergy(patient_id=patient_id, substance="Penicillin", severity=Severity.SEVERE))
    db_session.commit()

    response = client.post(
        f"/patients/{patient_id}/records",
        json={
            "record_type": "prescription",
            "title": "Prescribed penicillin",
            "details": "...",
            "drug_name": "penicillin",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["allergy_hits"] == ["Penicillin"]


def test_prescription_record_minor_interaction_saves_with_warning(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)
    _add_active_medication(client, patient_id, "metformin")

    db_session.add(
        DrugInteraction(
            drug_a="metformin",
            drug_b="ibuprofen",
            severity=InteractionSeverity.MODERATE,
            description="Minor risk of reduced kidney function.",
            recommendation="Monitor renal function.",
        )
    )
    db_session.commit()

    response = client.post(
        f"/patients/{patient_id}/records",
        json={
            "record_type": "prescription",
            "title": "Prescribed ibuprofen",
            "details": "...",
            "drug_name": "ibuprofen",
        },
    )

    assert response.status_code == 201
    assert len(response.json()["warnings"]) == 1
    record = db_session.query(Record).filter(Record.drug_name == "ibuprofen").first()
    assert record.override_reason is None


def test_prescription_record_override_reason_too_short_rejected(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    db_session.add(Allergy(patient_id=patient_id, substance="Penicillin", severity=Severity.SEVERE))
    db_session.commit()

    response = client.post(
        f"/patients/{patient_id}/records",
        json={
            "record_type": "prescription",
            "title": "Prescribed penicillin",
            "details": "...",
            "drug_name": "penicillin",
            "override_reason": "too short",
        },
    )

    assert response.status_code == 422
    assert db_session.query(Record).filter(Record.drug_name == "penicillin").count() == 0


def test_prescription_record_blocked_without_consent(client: TestClient, seeded_admin, second_facility_user):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)
    response = client.post("/patients", json=dict(VALID_PATIENT, cnic="66666-6666666-6", consent_sharing=False))
    no_consent_id = response.json()["id"]

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)

    blocked = client_b.post(
        f"/patients/{no_consent_id}/records",
        json={
            "record_type": "prescription",
            "title": "Unauthorized prescription",
            "details": "...",
            "drug_name": "paracetamol",
        },
    )
    assert blocked.status_code == 403
