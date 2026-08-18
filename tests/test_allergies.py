"""Phase 3 tests: adding allergies and their effect on the summary page banner."""
from fastapi.testclient import TestClient

from app.main import app

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


def test_add_allergy_success_and_shows_in_banner(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(f"/patients/{patient_id}/allergies", json={"substance": "Penicillin", "severity": "severe"})

    assert response.status_code == 201
    assert response.json()["substance"] == "Penicillin"

    summary = client.get(f"/patients/{patient_id}")
    assert "allergy-banner" in summary.text
    assert "Penicillin" in summary.text
    assert "severe" in summary.text


def test_add_allergy_blocked_without_consent(client: TestClient, seeded_admin, second_facility_user):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)
    response = client.post("/patients", json=dict(VALID_PATIENT, cnic="88888-8888888-8", consent_sharing=False))
    no_consent_id = response.json()["id"]

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)

    blocked = client_b.post(
        f"/patients/{no_consent_id}/allergies", json={"substance": "Aspirin", "severity": "mild"}
    )
    assert blocked.status_code == 403
