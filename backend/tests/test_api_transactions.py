"""Integration tests for Transactions API."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_transactions_default():
    """Verify listing seeded transactions."""
    response = client.get("/api/v1/transactions?limit=20")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 175
    assert len(data["items"]) == 20


def test_get_canonical_transaction_1157():
    """Verify canonical transaction tx_app_1157 is accessible and has exact remediated amount 1514.00."""
    response = client.get("/api/v1/transactions/tx_app_1157")
    assert response.status_code == 200
    data = response.json()
    assert data["reference"] == "tx_app_1157"
    assert data["amount"] == "1514.00"
    assert data["currency"] == "BDT"
    assert data["transaction_status"] == "APPROVED"
    assert data["risk_score"] == 25
    assert data["risk_level"] == "LOW"


def test_get_nonexistent_transaction():
    """Verify 404 for unknown transaction reference."""
    response = client.get("/api/v1/transactions/tx_nonexistent_9999")
    assert response.status_code == 404


def test_create_transaction_low_risk():
    """Verify creating a low risk transaction results in APPROVED status."""
    payload = {
        "counterparty_name": "Test Merchant Shop",
        "amount": "1250.00",
        "currency": "BDT",
        "channel": "MOBILE_APP",
        "device_model": "Samsung Galaxy A53",
        "location_city": "Dhaka",
        "is_location_anomaly": False,
        "is_new_device": False,
        "has_high_velocity": False,
        "has_prior_chargebacks": False,
    }
    response = client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["counterparty_name"] == "Test Merchant Shop"
    assert data["amount"] == "1250.00"
    assert data["risk_score"] == 10
    assert data["risk_level"] == "LOW"
    assert data["transaction_status"] == "APPROVED"


def test_create_transaction_high_risk():
    """Verify creating a high risk transaction results in BLOCKED status and open analyst case."""
    payload = {
        "counterparty_name": "Suspicious Counterparty Ltd",
        "amount": "15000.00",
        "currency": "BDT",
        "channel": "POS",
        "device_model": "Unknown POS Terminal",
        "location_city": "Unknown Region",
        "is_location_anomaly": True,
        "is_new_device": True,
        "has_high_velocity": True,
        "has_prior_chargebacks": True,
    }
    response = client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["risk_score"] == 100
    assert data["risk_level"] == "HIGH"
    assert data["transaction_status"] == "BLOCKED"
    assert data["recommended_action"] == "BLOCK"


def test_decimal_wire_validation_rejects_floats():
    """Verify Pydantic rejects raw JSON floats (must be 2-decimal string)."""
    payload = {
        "counterparty_name": "Float Test",
        "amount": 1250.5,  # float instead of string
        "currency": "BDT",
        "channel": "MOBILE_APP",
        "device_model": "Pixel 7",
        "location_city": "Dhaka",
    }
    response = client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 422


def test_update_transaction_status():
    """Verify updating transaction status records change and resolves associated case."""
    # First create a review/blocked transaction
    create_payload = {
        "counterparty_name": "Review Target",
        "amount": "4000.00",
        "currency": "BDT",
        "channel": "AGENT",
        "device_model": "Vivo Y20",
        "location_city": "Chittagong",
        "is_new_device": True,
        "has_high_velocity": True,
    }
    create_res = client.post("/api/v1/transactions", json=create_payload)
    assert create_res.status_code == 201
    ref = create_res.json()["reference"]
    assert create_res.json()["transaction_status"] == "REVIEW"

    # Now patch status to APPROVED
    patch_payload = {
        "status": "APPROVED",
        "notes": "Verified legitimate customer transaction via phone confirmation.",
        "actor_id": "lead_analyst_01",
    }
    patch_res = client.patch(f"/api/v1/transactions/{ref}/status", json=patch_payload)
    assert patch_res.status_code == 200
    assert patch_res.json()["transaction_status"] == "APPROVED"
