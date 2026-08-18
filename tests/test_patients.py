"""Phase 2 tests: patient creation, CNIC search, and the cross-facility summary page."""
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models.allergy import Allergy, Severity
from app.models.audit_log import AuditAction, AuditLog
from app.models.condition import Condition
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.record import Record, RecordType

ADMIN_PASSWORD = "TestPass123!"

VALID_PATIENT = {
    "cnic": "12345-1234567-1",
    "full_name": "Test Patient",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "blood_group": "O+",
    "phone": "03001234567",
    "address": "1 Patient Rd",
    "consent_sharing": True,
}


def _login(test_client: TestClient, email: str, password: str):
    """Log in a client and confirm it worked."""
    response = test_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response


def test_create_patient_success(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    response = client.post("/patients", json=VALID_PATIENT)

    assert response.status_code == 201
    body = response.json()
    assert body["cnic"] == VALID_PATIENT["cnic"]

    patient = db_session.query(Patient).filter(Patient.cnic == VALID_PATIENT["cnic"]).first()
    assert patient is not None
    assert patient.created_by_facility_id == facility.id


def test_create_patient_invalid_cnic_format(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    bad_payload = dict(VALID_PATIENT, cnic="not-a-cnic")
    response = client.post("/patients", json=bad_payload)

    assert response.status_code == 422


def test_create_patient_duplicate_cnic_rejected(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    first = client.post("/patients", json=VALID_PATIENT)
    assert first.status_code == 201

    second = client.post("/patients", json=VALID_PATIENT)
    assert second.status_code == 409


def test_create_patient_forbidden_for_nurse(client: TestClient, nurse_user):
    _login(client, nurse_user.email, ADMIN_PASSWORD)

    response = client.post("/patients", json=dict(VALID_PATIENT, cnic="55555-5555555-5"))

    assert response.status_code == 403


def test_search_by_cnic_found_and_not_found(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)
    client.post("/patients", json=VALID_PATIENT)

    found = client.get(f"/patients/search?cnic={VALID_PATIENT['cnic']}")
    assert found.status_code == 200
    assert found.json()["cnic"] == VALID_PATIENT["cnic"]

    missing = client.get("/patients/search?cnic=99999-9999999-9")
    assert missing.status_code == 404


def test_patient_visible_across_facilities_and_audited(
    client: TestClient, seeded_admin, second_facility_user, db_session
):
    _facility_a, admin, password = seeded_admin
    facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)
    created = client.post("/patients", json=VALID_PATIENT)
    patient_id = created.json()["id"]

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)

    response = client_b.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    assert VALID_PATIENT["full_name"] in response.text

    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.VIEWED_SUMMARY).all()
    assert len(logs) == 1
    assert logs[0].user_id == doctor.id
    assert logs[0].facility_id == facility_b.id
    assert logs[0].patient_id == patient_id


def test_consent_denied_blocks_other_facility(client: TestClient, seeded_admin, second_facility_user, db_session):
    _facility_a, admin, password = seeded_admin
    _facility_b, doctor, doctor_password = second_facility_user

    _login(client, admin.email, password)
    no_consent_payload = dict(VALID_PATIENT, cnic="22222-2222222-2", consent_sharing=False)
    created = client.post("/patients", json=no_consent_payload)
    patient_id = created.json()["id"]

    client_b = TestClient(app)
    _login(client_b, doctor.email, doctor_password)

    response = client_b.get(f"/patients/{patient_id}")
    assert response.status_code == 403
    assert "consent" in response.text.lower()

    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.VIEWED_SUMMARY).all()
    assert len(logs) == 0


def test_consent_false_still_allows_same_facility(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    no_consent_payload = dict(VALID_PATIENT, cnic="33333-3333333-3", consent_sharing=False)
    created = client.post("/patients", json=no_consent_payload)
    patient_id = created.json()["id"]

    response = client.get(f"/patients/{patient_id}")
    assert response.status_code == 200


def test_allergy_banner_shown_only_when_allergies_exist(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    created = client.post("/patients", json=dict(VALID_PATIENT, cnic="44444-4444444-4"))
    patient_id = created.json()["id"]

    no_allergy_response = client.get(f"/patients/{patient_id}")
    assert "allergy-banner" not in no_allergy_response.text

    db_session.add(Allergy(patient_id=patient_id, substance="Penicillin", severity=Severity.SEVERE))
    db_session.commit()

    with_allergy_response = client.get(f"/patients/{patient_id}")
    assert "allergy-banner" in with_allergy_response.text
    assert "Penicillin" in with_allergy_response.text


def test_conditions_and_medications_render(client: TestClient, seeded_admin, db_session):
    facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    created = client.post("/patients", json=dict(VALID_PATIENT, cnic="66666-6666666-6"))
    patient_id = created.json()["id"]

    db_session.add(Condition(patient_id=patient_id, name="Type 2 Diabetes", diagnosed_date=date(2020, 1, 1)))
    db_session.add(
        Medication(
            patient_id=patient_id,
            drug_name="Metformin",
            brand_name="Glucophage",
            dose="500mg",
            frequency="twice daily",
            started_at=date(2021, 1, 1),
            facility_id=facility.id,
        )
    )
    db_session.add(
        Medication(
            patient_id=patient_id,
            drug_name="Old Drug",
            dose="10mg",
            frequency="once daily",
            started_at=date(2019, 1, 1),
            stopped_at=date(2020, 1, 1),
            facility_id=facility.id,
        )
    )
    db_session.commit()

    response = client.get(f"/patients/{patient_id}")
    assert "Type 2 Diabetes" in response.text
    assert "Metformin" in response.text
    # A stopped medication belongs in "Past medications", not the "Current medications" list.
    current_section = response.text.split("Current medications")[1].split("Past medications")[0]
    assert "Old Drug" not in current_section
    assert "Old Drug" in response.text


def test_records_from_all_facilities_limited_to_ten_latest(
    client: TestClient, seeded_admin, second_facility_user, db_session
):
    facility_a, admin, password = seeded_admin
    facility_b, doctor, _doctor_password = second_facility_user

    _login(client, admin.email, password)
    created = client.post("/patients", json=dict(VALID_PATIENT, cnic="77777-7777777-7"))
    patient_id = created.json()["id"]

    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(12):
        db_session.add(
            Record(
                patient_id=patient_id,
                facility_id=facility_a.id if i % 2 == 0 else facility_b.id,
                author_user_id=admin.id if i % 2 == 0 else doctor.id,
                record_type=RecordType.VISIT,
                title=f"Visit {i}",
                details="Routine visit.",
                created_at=base_time + timedelta(minutes=i),
            )
        )
    db_session.commit()

    response = client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    assert response.text.count("Visit ") == 10
    assert "Visit 11\n" in response.text  # newest should be present
    assert "Visit 0\n" not in response.text  # oldest two should be truncated
    assert "Visit 1\n" not in response.text
