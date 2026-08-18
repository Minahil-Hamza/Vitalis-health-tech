"""Phase 5 tests: patient access-history page (who viewed/edited, when, from which facility)."""
from datetime import datetime, timedelta, timezone

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


def _login(test_client: TestClient, email: str, password: str):
    response = test_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response


def _create_patient(test_client: TestClient, cnic="12345-1234567-1"):
    response = test_client.post("/patients", json=dict(VALID_PATIENT, cnic=cnic))
    assert response.status_code == 201
    return response.json()["id"]


def test_access_history_visible_to_creating_facility(client: TestClient, seeded_admin):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)
    client.get(f"/patients/{patient_id}")  # writes a viewed_summary row

    response = client.get(f"/patients/{patient_id}/access-history")

    assert response.status_code == 200
    assert admin.full_name in response.text
    assert "viewed_summary" in response.text
    assert facility.name in response.text


def test_access_history_blocked_for_other_facility(client: TestClient, seeded_admin, second_facility_user):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)
    # Facility B can view the summary (consent defaults to True) but not the access history.
    assert client_b.get(f"/patients/{patient_id}").status_code == 200

    response = client_b.get(f"/patients/{patient_id}/access-history")
    assert response.status_code == 403
    assert "restricted" in response.text.lower()


def test_access_history_shows_override_reason(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    db_session.add(
        AuditLog(
            action=AuditAction.ADDED_MEDICATION,
            user_id=admin.id,
            facility_id=admin.facility_id,
            patient_id=patient_id,
            override_reason="Cardiology approved short-term dual therapy",
        )
    )
    db_session.commit()

    response = client.get(f"/patients/{patient_id}/access-history")
    assert "Cardiology approved short-term dual therapy" in response.text


def test_access_history_paginates(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    patient_id = _create_patient(client)

    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(25):
        db_session.add(
            AuditLog(
                action=AuditAction.VIEWED_SUMMARY,
                user_id=admin.id,
                facility_id=facility.id,
                patient_id=patient_id,
                timestamp=base_time + timedelta(minutes=i),
            )
        )
    db_session.commit()

    page1 = client.get(f"/patients/{patient_id}/access-history")
    assert page1.status_code == 200
    assert "Page 1 of 2" in page1.text
    assert "Next" in page1.text
    assert "Previous" not in page1.text

    page2 = client.get(f"/patients/{patient_id}/access-history?page=2")
    assert "Page 2 of 2" in page2.text
    assert "Previous" in page2.text
    assert "Next" not in page2.text
