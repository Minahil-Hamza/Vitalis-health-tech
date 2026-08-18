"""Phase 4 tests: admin CSV import of the drug interaction reference table."""
import io

from fastapi.testclient import TestClient

from app.models.drug_interaction import DrugInteraction

GOOD_CSV = (
    "drug_a,drug_b,severity,description,recommendation\n"
    "aspirin,warfarin,major,Increased bleeding risk.,Avoid combination.\n"
    "metformin,ibuprofen,moderate,Reduced kidney function.,Monitor renal function.\n"
)

BAD_ROW_CSV = (
    "drug_a,drug_b,severity,description,recommendation\n"
    "aspirin,warfarin,major,Increased bleeding risk.,Avoid combination.\n"
    "foo,bar,not-a-severity,Bad row.,Should be skipped.\n"
)


def _login(test_client: TestClient, email: str, password: str):
    response = test_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response


def test_admin_can_import_csv(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    response = client.post(
        "/admin/interactions/import",
        files={"file": ("interactions.csv", io.BytesIO(GOOD_CSV.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 201
    assert response.json()["imported"] == 2
    assert response.json()["errors"] == []
    assert db_session.query(DrugInteraction).count() == 2


def test_import_skips_bad_rows_and_reports_them(client: TestClient, seeded_admin, db_session):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    response = client.post(
        "/admin/interactions/import",
        files={"file": ("interactions.csv", io.BytesIO(BAD_ROW_CSV.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 201
    assert response.json()["imported"] == 1
    assert len(response.json()["errors"]) == 1
    assert db_session.query(DrugInteraction).count() == 1


def test_import_forbidden_for_non_admin(client: TestClient, nurse_user):
    _login(client, nurse_user.email, "TestPass123!")

    response = client.post(
        "/admin/interactions/import",
        files={"file": ("interactions.csv", io.BytesIO(GOOD_CSV.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 403
