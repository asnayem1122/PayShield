"""Integration tests for Analyst Cases API."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_analyst_cases():
    """Verify listing fraud analyst investigation cases."""
    response = client.get("/api/v1/cases?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 14
    assert len(data["items"]) == 10
    case = data["items"][0]
    assert "id" in case
    assert "case_status" in case
    assert "priority" in case
    assert "trigger_reason" in case


def test_get_and_update_case():
    """Verify retrieving and updating case workflow status and notes."""
    # Create an isolated flagged transaction so it creates a new case dedicated to this test
    create_payload = {
        "counterparty_name": "Case Test Target",
        "amount": "6000.00",
        "currency": "BDT",
        "channel": "MOBILE_APP",
        "device_model": "Oppo F19",
        "location_city": "Sylhet",
        "is_new_device": True,
        "has_high_velocity": True,
    }
    create_res = client.post("/api/v1/transactions", json=create_payload)
    assert create_res.status_code == 201
    tx_ref = create_res.json()["reference"]

    # List cases and find this specific newly created case
    list_res = client.get("/api/v1/cases?limit=5")
    assert list_res.status_code == 200
    cases = list_res.json()["items"]
    target_case = next(c for c in cases if c.get("transaction") and c["transaction"]["reference"] == tx_ref)
    case_id = target_case["id"]

    # Get single
    get_res = client.get(f"/api/v1/cases/{case_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == case_id

    # Update case workflow
    patch_payload = {
        "case_status": "IN_REVIEW",
        "resolution_note": "Under investigation by lead fraud analyst.",
        "actor_id": "analyst_shafiq",
    }
    patch_res = client.patch(f"/api/v1/cases/{case_id}", json=patch_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["case_status"] == "IN_REVIEW"
    assert updated["resolution_note"] == "Under investigation by lead fraud analyst."


def test_risk_indicators_endpoint():
    """Verify risk indicators metadata endpoint."""
    response = client.get("/api/v1/risk/indicators")
    assert response.status_code == 200
    data = response.json()
    assert data["scoring_method"] == "HEURISTIC_RULES_V1"
    assert data["base_score"] == 10
    assert data["max_raw_score"] == 110
    assert data["clamped_score_cap"] == 100
    assert len(data["indicators"]) == 6
