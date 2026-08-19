"""Phase 9 tests: adding chronic conditions, with an optional body_region for the 3D view."""
from fastapi.testclient import TestClient

from app.main import app
from app.models.condition import Condition

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


def test_add_condition_with_body_region(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(
        f"/patients/{patient_id}/conditions",
        json={"name": "Asthma", "diagnosed_date": "2018-05-01", "body_region": "chest", "notes": "Mild, exercise-induced"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Asthma"
    assert body["body_region"] == "chest"

    condition = db_session.query(Condition).filter(Condition.name == "Asthma").first()
    assert condition is not None
    assert condition.body_region.value == "chest"


def test_add_condition_without_body_region_defaults_to_none(client: TestClient, seeded_admin):
    """Systemic conditions (e.g. diabetes) aren't forced into a fake body location."""
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    response = client.post(f"/patients/{patient_id}/conditions", json={"name": "Type 2 Diabetes"})

    assert response.status_code == 201
    assert response.json()["body_region"] is None


def test_condition_appears_in_patient_json_detail(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    client.post(f"/patients/{patient_id}/conditions", json={"name": "Hypertension", "body_region": "chest"})

    response = client.get(f"/patients/{patient_id}", headers={"Accept": "application/json"})
    conditions = response.json()["conditions"]
    assert len(conditions) == 1
    assert conditions[0]["name"] == "Hypertension"
    assert conditions[0]["body_region"] == "chest"


def test_add_condition_blocked_without_consent(client: TestClient, seeded_admin, second_facility_user):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)
    response = client.post("/patients", json=dict(VALID_PATIENT, cnic="77777-7777777-7", consent_sharing=False))
    no_consent_id = response.json()["id"]

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)

    blocked = client_b.post(f"/patients/{no_consent_id}/conditions", json={"name": "Migraine", "body_region": "head"})
    assert blocked.status_code == 403
