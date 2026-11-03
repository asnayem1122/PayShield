from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_HEALTH_PAYLOAD = {
    "status": "healthy",
    "app": "PayShield API",
    "version": "0.1.0",
    "environment": "development",
}


def test_root_health_endpoint() -> None:
    """Verify that GET /health returns HTTP 200 and the expected status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == EXPECTED_HEALTH_PAYLOAD


def test_api_v1_health_endpoint() -> None:
    """Verify that GET /api/v1/health returns HTTP 200 and the expected status payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == EXPECTED_HEALTH_PAYLOAD
