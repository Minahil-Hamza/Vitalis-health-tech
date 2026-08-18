"""Phase 6 tests: friendly HTML error pages for browsers, unchanged JSON for API/JS callers."""
from fastapi.testclient import TestClient

from app.main import app

ADMIN_PASSWORD = "TestPass123!"


def _login(test_client: TestClient, email: str, password: str):
    response = test_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response


def test_404_html_for_browser_navigation(client: TestClient):
    response = client.get("/this-route-does-not-exist", headers={"Accept": "text/html"})
    assert response.status_code == 404
    assert "Page not found" in response.text


def test_404_json_for_api_caller(client: TestClient):
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_patient_not_found_renders_html_page(client: TestClient, seeded_admin):
    _facility, admin, password = seeded_admin
    _login(client, admin.email, password)

    response = client.get("/patients/does-not-exist", headers={"Accept": "text/html"})
    assert response.status_code == 404
    assert "Page not found" in response.text


def test_403_html_for_browser_navigation(client: TestClient, nurse_user):
    _login(client, nurse_user.email, ADMIN_PASSWORD)

    response = client.get("/admin", headers={"Accept": "text/html"})
    assert response.status_code == 403
    assert "Access restricted" in response.text


def test_403_json_for_api_caller(client: TestClient, nurse_user):
    _login(client, nurse_user.email, ADMIN_PASSWORD)

    response = client.get("/admin")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not permitted for this role"}


def test_500_html_for_browser_navigation(monkeypatch):
    import tests.conftest as conftest_module

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(conftest_module, "TestingSessionLocal", _boom)
    test_client = TestClient(app, raise_server_exceptions=False)

    response = test_client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 500
    assert "Something went wrong" in response.text


def test_500_json_for_api_caller(monkeypatch):
    import tests.conftest as conftest_module

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(conftest_module, "TestingSessionLocal", _boom)
    test_client = TestClient(app, raise_server_exceptions=False)

    response = test_client.get("/")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
