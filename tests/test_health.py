"""Phase 0 tests: app boots and the health-check endpoint works."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dummy():
    """Sanity check that pytest is wired up correctly."""
    assert 1 + 1 == 2


def test_health_check_returns_ok():
    """GET /health should report the service as ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
