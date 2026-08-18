"""Phase 3 tests: adding and stopping medications."""
from fastapi.testclient import TestClient

from app.main import app
from app.models.audit_log import AuditAction, AuditLog

VALID_PATIENT = {
    "cnic": "12345-1234567-1",
    "full_name": "Test Patient",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "consent_sharing": True,
}

VALID_MEDICATION = {
    "drug_name": "Metformin",
    "brand_name": "Glucophage",
    "dose": "500mg",
    "frequency": "twice daily",
    "started_at": "2024-01-01",
}


def _login(test_client: TestClient, email: str, password: str):
    response = test_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response


def _create_patient(test_client: TestClient, cnic="12345-1234567-1"):
    response = test_client.post("/patients", json=dict(VALID_PATIENT, cnic=cnic))
    assert response.status_code == 201
    return response.json()["id"]


def test_add_medication_success_and_audited(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(f"/patients/{patient_id}/medications", json=VALID_MEDICATION)

    assert response.status_code == 201
    assert response.json()["drug_name"] == "Metformin"
    assert response.json()["stopped_at"] is None

    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.ADDED_MEDICATION).all()
    assert len(logs) == 1
    assert logs[0].user_id == admin.id
    assert logs[0].facility_id == facility.id
    assert logs[0].patient_id == patient_id


def test_medication_appears_in_active_list_on_summary(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)
    client.post(f"/patients/{patient_id}/medications", json=VALID_MEDICATION)

    summary = client.get(f"/patients/{patient_id}")
    assert "Metformin" in summary.text
    assert "Stop" in summary.text


def test_stop_medication_moves_it_to_past(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)
    added = client.post(f"/patients/{patient_id}/medications", json=VALID_MEDICATION)
    medication_id = added.json()["id"]

    stop_response = client.post(f"/patients/{patient_id}/medications/{medication_id}/stop")
    assert stop_response.status_code == 200
    assert stop_response.json()["stopped_at"] is not None

    summary = client.get(f"/patients/{patient_id}")
    assert "No current medications." in summary.text
    assert "Past medications" in summary.text
    assert "Metformin" in summary.text


def test_stop_already_stopped_medication_rejected(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)
    added = client.post(f"/patients/{patient_id}/medications", json=VALID_MEDICATION)
    medication_id = added.json()["id"]

    client.post(f"/patients/{patient_id}/medications/{medication_id}/stop")
    second_stop = client.post(f"/patients/{patient_id}/medications/{medication_id}/stop")

    assert second_stop.status_code == 400


def test_add_medication_blocked_without_consent(client: TestClient, seeded_admin, second_facility_user):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)
    response = client.post("/patients", json=dict(VALID_PATIENT, cnic="88888-8888888-8", consent_sharing=False))
    no_consent_id = response.json()["id"]

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)

    blocked = client_b.post(f"/patients/{no_consent_id}/medications", json=VALID_MEDICATION)
    assert blocked.status_code == 403
