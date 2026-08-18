"""Phase 6 test: POST /auth/login is rate-limited per IP."""
from fastapi.testclient import TestClient


def test_login_rate_limited_after_five_attempts(client: TestClient):
    """The 6th login attempt within a minute should be rejected, regardless of credentials."""
    for _ in range(5):
        response = client.post("/auth/login", json={"email": "nobody@nowhere.pk", "password": "x"})
        assert response.status_code == 401

    sixth = client.post("/auth/login", json={"email": "nobody@nowhere.pk", "password": "x"})
    assert sixth.status_code == 429
    assert "Too many attempts" in sixth.json()["detail"]
