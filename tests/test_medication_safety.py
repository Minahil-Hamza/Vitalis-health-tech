"""Phase 4 tests: drug interaction and allergy safety checks on medication add."""
from fastapi.testclient import TestClient

from app.models.allergy import Allergy, Severity
from app.models.audit_log import AuditAction, AuditLog
from app.models.drug_interaction import DrugInteraction, InteractionSeverity
from app.models.medication import Medication

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


def test_clean_pass_no_conflicts(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(
        f"/patients/{patient_id}/medications",
        json={"drug_name": "paracetamol", "dose": "500mg", "frequency": "as needed", "started_at": "2024-01-01"},
    )

    assert response.status_code == 201
    assert response.json()["warnings"] == []


def test_major_interaction_blocks_without_override(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    client.post(
        f"/patients/{patient_id}/medications",
        json={"drug_name": "warfarin", "dose": "5mg", "frequency": "once daily", "started_at": "2024-01-01"},
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

    response = client.post(
        f"/patients/{patient_id}/medications",
        json={"drug_name": "aspirin", "dose": "75mg", "frequency": "once daily", "started_at": "2024-06-01"},
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert len(detail["interactions"]) == 1
    assert detail["interactions"][0]["severity"] == "major"

    # Not saved
    assert db_session.query(Medication).filter(Medication.drug_name == "aspirin").count() == 0


def test_major_interaction_saves_with_override_and_audits(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    client.post(
        f"/patients/{patient_id}/medications",
        json={"drug_name": "warfarin", "dose": "5mg", "frequency": "once daily", "started_at": "2024-01-01"},
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

    response = client.post(
        f"/patients/{patient_id}/medications",
        json={
            "drug_name": "aspirin",
            "dose": "75mg",
            "frequency": "once daily",
            "started_at": "2024-06-01",
            "override_reason": "Cardiology approved short-term dual therapy.",
        },
    )

    assert response.status_code == 201
    medication = db_session.query(Medication).filter(Medication.drug_name == "aspirin").first()
    assert medication is not None
    assert medication.override_reason == "Cardiology approved short-term dual therapy."

    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.ADDED_MEDICATION).all()
    override_logs = [log for log in logs if log.override_reason]
    assert len(override_logs) == 1
    assert override_logs[0].override_reason == "Cardiology approved short-term dual therapy."


def test_allergy_hit_blocks_without_override(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    db_session.add(Allergy(patient_id=patient_id, substance="Penicillin", severity=Severity.SEVERE))
    db_session.commit()

    response = client.post(
        f"/patients/{patient_id}/medications",
        json={"drug_name": "penicillin", "dose": "500mg", "frequency": "three times daily", "started_at": "2024-01-01"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["allergy_hits"] == ["Penicillin"]


def test_minor_interaction_saves_immediately_with_warning(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    client.post(
        f"/patients/{patient_id}/medications",
        json={"drug_name": "metformin", "dose": "500mg", "frequency": "twice daily", "started_at": "2024-01-01"},
    )
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
        f"/patients/{patient_id}/medications",
        json={"drug_name": "ibuprofen", "dose": "200mg", "frequency": "as needed", "started_at": "2024-06-01"},
    )

    assert response.status_code == 201
    assert len(response.json()["warnings"]) == 1
    assert "metformin" in response.json()["warnings"][0]

    # Saved without needing an override
    medication = db_session.query(Medication).filter(Medication.drug_name == "ibuprofen").first()
    assert medication is not None
    assert medication.override_reason is None
