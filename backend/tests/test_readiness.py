"""Tests for database readiness probe and RFC 9457 Problem Details error semantics."""

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_readiness_endpoint_when_database_available() -> None:
    """Verify that GET /api/v1/readiness returns HTTP 200 when database is healthy."""
    with patch("app.main.check_database_connection", return_value=(True, None)):
        response = client.get("/api/v1/readiness")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.json() == {
            "status": "ready",
            "database": "connected",
        }


def test_readiness_endpoint_when_database_unavailable() -> None:
    """Verify that GET /api/v1/readiness returns HTTP 503 with RFC 9457 Problem Details when DB fails."""
    with patch(
        "app.main.check_database_connection",
        return_value=(False, "Database connection could not be established"),
    ):
        response = client.get("/api/v1/readiness")
        assert response.status_code == 503
        assert response.headers["content-type"] == "application/problem+json"

        problem_data = response.json()
        assert problem_data["type"] == "https://payshield.internal/errors/database-unavailable"
        assert problem_data["title"] == "Service Unavailable"
        assert problem_data["status"] == 503
        assert problem_data["detail"] == "Database service is unavailable"
        assert problem_data["instance"] == "/api/v1/readiness"

        # Verify no sensitive driver tracebacks or credentials leaked
        response_text = response.text.lower()
        assert "password" not in response_text
        assert "psycopg" not in response_text
        assert "traceback" not in response_text


def test_liveness_and_readiness_separation() -> None:
    """Verify liveness probes remain HTTP 200 even if database is unavailable."""
    with patch(
        "app.main.check_database_connection",
        return_value=(False, "Database down"),
    ):
        # Liveness checks must succeed independently of database state
        root_health = client.get("/health")
        assert root_health.status_code == 200
        assert root_health.json()["status"] == "healthy"

        v1_health = client.get("/api/v1/health")
        assert v1_health.status_code == 200
        assert v1_health.json()["status"] == "healthy"

        # Readiness fails when database is down
        readiness = client.get("/api/v1/readiness")
        assert readiness.status_code == 503
