"""Phase 3 tests: adding records and the cross-facility timeline view."""
from fastapi.testclient import TestClient

from app.main import app
from app.models.audit_log import AuditAction, AuditLog

ADMIN_PASSWORD = "TestPass123!"

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


def test_create_record_success_and_audited(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(
        f"/patients/{patient_id}/records",
        json={"record_type": "visit", "title": "Routine checkup", "details": "Patient in good health."},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Routine checkup"

    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.CREATED_RECORD).all()
    assert len(logs) == 1
    assert logs[0].user_id == admin.id
    assert logs[0].facility_id == facility.id
    assert logs[0].patient_id == patient_id


def test_create_record_requires_authentication(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    anon_client = TestClient(app)
    response = anon_client.post(
        f"/patients/{patient_id}/records",
        json={"record_type": "visit", "title": "Routine checkup", "details": "Should be blocked."},
    )
    assert response.status_code == 401


def test_create_record_blocked_without_consent(client: TestClient, seeded_admin, second_facility_user):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)

    # VALID_PATIENT defaults to consent_sharing=True, so create a separate non-consenting patient.
    response = client.post("/patients", json=dict(VALID_PATIENT, cnic="88888-8888888-8", consent_sharing=False))
    no_consent_id = response.json()["id"]

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)

    blocked = client_b.post(
        f"/patients/{no_consent_id}/records",
        json={"record_type": "visit", "title": "Unauthorized visit", "details": "Should be blocked."},
    )
    assert blocked.status_code == 403


def test_timeline_shows_records_from_all_facilities_newest_first(
    client: TestClient, seeded_admin, second_facility_user
):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)
    patient_id = _create_patient(client)
    client.post(
        f"/patients/{patient_id}/records",
        json={"record_type": "visit", "title": "First visit at Clinic A", "details": "..."},
    )

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)
    client_b.post(
        f"/patients/{patient_id}/records",
        json={"record_type": "lab_report", "title": "Blood test at Clinic B", "details": "..."},
    )

    timeline = client.get(f"/patients/{patient_id}/timeline")
    assert timeline.status_code == 200
    assert "First visit at Clinic A" in timeline.text
    assert "Blood test at Clinic B" in timeline.text
    # newest first: the Clinic B record was created second, so it should appear before Clinic A's
    assert timeline.text.index("Blood test at Clinic B") < timeline.text.index("First visit at Clinic A")
