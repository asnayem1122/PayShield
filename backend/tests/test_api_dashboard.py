"""Integration tests for Dashboard API."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_summary():
    """Verify live database-backed dashboard aggregates."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_volume" in data
    assert "approved_volume" in data
    assert "flagged_volume" in data
    assert "blocked_volume" in data
    assert "total_transactions" in data
    assert "approved_count" in data
    assert "flagged_count" in data
    assert "blocked_count" in data
    assert "open_cases_count" in data
    assert "average_risk_score" in data
    assert "high_risk_ratio" in data

    assert data["total_transactions"] >= 175
    assert float(data["total_volume"]) >= 482500.00
    assert data["open_cases_count"] >= 14


def test_dashboard_risk_distribution():
    """Verify risk distribution breakdown."""
    response = client.get("/api/v1/dashboard/risk-distribution")
    assert response.status_code == 200
    data = response.json()
    assert "low_count" in data
    assert "medium_count" in data
    assert "high_count" in data
    assert "total_count" in data
    assert data["total_count"] == data["low_count"] + data["medium_count"] + data["high_count"]


def test_dashboard_recent_transactions():
    """Verify recent transactions endpoint returns expected limit."""
    response = client.get("/api/v1/dashboard/recent-transactions?limit=5")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) == 5
    for item in items:
        assert "reference" in item
        assert "amount" in item
        assert "risk_score" in item
