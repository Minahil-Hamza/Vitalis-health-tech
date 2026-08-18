"""Phase 1 tests: login, wrong password, and role-based route protection."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.models.audit_log import AuditAction, AuditLog
from app.models.user import Role, User
from app.services.security import require_role


def test_login_success_returns_token_and_audits(client: TestClient, seeded_admin, db_session):
    """Correct credentials return a JWT, set a cookie, and write a login audit row."""
    facility, admin, password = seeded_admin

    response = client.post("/auth/login", json={"email": admin.email, "password": password})

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.cookies.get("access_token")

    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.LOGIN).all()
    assert len(logs) == 1
    assert logs[0].user_id == admin.id
    assert logs[0].facility_id == facility.id


def test_login_wrong_password_is_rejected_and_audited(client: TestClient, seeded_admin, db_session):
    """A wrong password returns 401 and writes a login_failed row tied to the known user."""
    _facility, admin, _password = seeded_admin

    response = client.post("/auth/login", json={"email": admin.email, "password": "wrong-password"})

    assert response.status_code == 401
    assert response.cookies.get("access_token") is None

    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.LOGIN_FAILED).all()
    assert len(logs) == 1
    assert logs[0].user_id == admin.id


def test_login_unknown_email_is_rejected_and_audited(client: TestClient, db_session):
    """An unknown email still returns 401 and audits the attempt, with no user_id to link it to."""
    response = client.post("/auth/login", json={"email": "nobody@nowhere.pk", "password": "whatever"})

    assert response.status_code == 401
    logs = db_session.query(AuditLog).filter(AuditLog.action == AuditAction.LOGIN_FAILED).all()
    assert len(logs) == 1
    assert logs[0].user_id is None


def test_dashboard_requires_authentication(client: TestClient):
    """The protected landing page rejects requests with no token."""
    response = client.get("/")
    assert response.status_code == 401


def test_dashboard_accepts_valid_cookie(client: TestClient, seeded_admin):
    """After logging in, the same client (holding the cookie) can reach the protected page."""
    _facility, admin, password = seeded_admin
    client.post("/auth/login", json={"email": admin.email, "password": password})

    response = client.get("/")
    assert response.status_code == 200
    assert admin.full_name in response.text


def test_require_role_allows_listed_roles():
    """require_role's check passes a user whose role is in the allowed list."""
    checker = require_role([Role.ADMIN, Role.DOCTOR])
    fake_user = User(role=Role.ADMIN)
    assert checker(user=fake_user) is fake_user


def test_require_role_blocks_other_roles():
    """require_role's check rejects a user whose role is not in the allowed list."""
    checker = require_role([Role.ADMIN])
    fake_user = User(role=Role.NURSE)
    with pytest.raises(HTTPException) as exc_info:
        checker(user=fake_user)
    assert exc_info.value.status_code == 403


def test_auth_me_returns_profile_with_facility_name(client: TestClient, seeded_admin):
    """GET /auth/me returns the logged-in user's profile, including the facility's name."""
    facility, admin, password = seeded_admin
    client.post("/auth/login", json={"email": admin.email, "password": password})

    response = client.get("/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == admin.id
    assert body["full_name"] == admin.full_name
    assert body["role"] == "admin"
    assert body["facility_id"] == facility.id
    assert body["facility_name"] == facility.name


def test_auth_me_requires_authentication(client: TestClient):
    """GET /auth/me rejects requests with no token."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_redirects_for_browser_navigation(client: TestClient, seeded_admin):
    """A plain GET /logout (no Accept: application/json) still redirects, as before."""
    _facility, admin, password = seeded_admin
    client.post("/auth/login", json={"email": admin.email, "password": password})

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_logout_returns_json_when_requested(client: TestClient, seeded_admin):
    """GET /logout with Accept: application/json clears the cookie and returns JSON instead of redirecting."""
    _facility, admin, password = seeded_admin
    client.post("/auth/login", json={"email": admin.email, "password": password})

    response = client.get("/logout", headers={"Accept": "application/json"}, follow_redirects=False)

    assert response.status_code == 200
    assert response.json() == {"detail": "Logged out"}

    # The cookie should be cleared either way.
    protected = client.get("/auth/me")
    assert protected.status_code == 401
