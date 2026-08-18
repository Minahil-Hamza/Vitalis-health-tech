"""Phase 5 tests: facility admin dashboard - staff management and simple counts."""
from datetime import date

from fastapi.testclient import TestClient

from app.models.patient import Gender, Patient
from app.models.record import Record, RecordType
from app.models.user import Role, User

ADMIN_PASSWORD = "TestPass123!"


def _login(test_client: TestClient, email: str, password: str):
    response = test_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response


def test_admin_can_add_staff(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    response = client.post(
        "/admin/users",
        json={
            "full_name": "Dr. New",
            "email": "newdoctor@test-clinic.pk",
            "password": "NewPass123!",
            "role": "doctor",
        },
    )

    assert response.status_code == 201
    new_user = db_session.query(User).filter(User.email == "newdoctor@test-clinic.pk").first()
    assert new_user is not None
    assert new_user.facility_id == facility.id
    assert new_user.role == Role.DOCTOR


def test_add_staff_forbidden_for_non_admin(client: TestClient, nurse_user):
    _login(client, nurse_user.email, ADMIN_PASSWORD)

    response = client.post(
        "/admin/users",
        json={"full_name": "Someone", "email": "someone@test-clinic.pk", "password": "Pass123!", "role": "doctor"},
    )
    assert response.status_code == 403


def test_deactivate_staff_blocks_login(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    added = client.post(
        "/admin/users",
        json={
            "full_name": "Dr. New",
            "email": "newdoctor@test-clinic.pk",
            "password": "NewPass123!",
            "role": "doctor",
        },
    )
    new_user_id = added.json()["id"]

    deactivate = client.post(f"/admin/users/{new_user_id}/deactivate")
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    login_attempt = client.post(
        "/auth/login", json={"email": "newdoctor@test-clinic.pk", "password": "NewPass123!"}
    )
    assert login_attempt.status_code == 401


def test_admin_cannot_deactivate_self(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    response = client.post(f"/admin/users/{admin.id}/deactivate")
    assert response.status_code == 400


def test_admin_cannot_deactivate_cross_facility_user(client: TestClient, seeded_admin, second_facility_user):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, _doctor_password = second_facility_user

    _login(client, admin.email, password)
    response = client.post(f"/admin/users/{doctor.id}/deactivate")
    assert response.status_code == 404


def test_dashboard_counts(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)

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
        Record(
            patient_id=patient.id,
            facility_id=facility.id,
            author_user_id=admin.id,
            record_type=RecordType.VISIT,
            title="Visit",
            details="...",
        )
    )
    db_session.commit()

    response = client.get("/admin")
    assert response.status_code == 200
    assert "Patients created: 1" in response.text
    assert "Records this month: 1" in response.text

    json_response = client.get("/admin", headers={"Accept": "application/json"})
    assert json_response.status_code == 200
    body = json_response.json()
    assert body["patients_created"] == 1
    assert body["records_this_month"] == 1
    assert body["current_user_id"] == admin.id
    assert any(member["email"] == admin.email for member in body["staff"])


def test_admin_dashboard_json_forbidden_for_non_admin(client: TestClient, nurse_user):
    _login(client, nurse_user.email, ADMIN_PASSWORD)

    response = client.get("/admin", headers={"Accept": "application/json"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Not permitted for this role"}
