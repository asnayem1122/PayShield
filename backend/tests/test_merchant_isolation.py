"""Tests for merchant data isolation and cross-tenant anti-enumeration (IDOR)."""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.merchant import Merchant
from app.models.transaction import Transaction


def test_merchant_only_sees_own_transactions_in_list(
    client: TestClient,
    merchant_headers: dict[str, str],
    merchant_user,
):
    """Verify merchant list query only returns transactions matching user's merchant_id."""
    res = client.get("/api/v1/transactions?limit=50", headers=merchant_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) > 0
    for item in items:
        assert item["merchant_id"] == str(merchant_user.merchant_id)


def test_merchant_cannot_access_other_merchant_transaction_returns_404(
    client: TestClient,
    merchant_headers: dict[str, str],
):
    """Verify 404 anti-enumeration when a merchant queries another merchant's transaction."""
    # Use migrator engine to provision test merchant and transaction
    migrator_url = settings.get_migration_sqlalchemy_url()
    admin_engine = create_engine(migrator_url)

    with Session(admin_engine) as session:
        other_merchant = Merchant(
            name=f"Other Shop {uuid.uuid4().hex[:6]}",
            category="Electronics",
            status="ACTIVE",
        )
        session.add(other_merchant)
        session.flush()

        other_tx = Transaction(
            reference=f"tx_iso_{uuid.uuid4().hex[:8]}",
            merchant_id=other_merchant.id,
            counterparty_name="Isolated Buyer",
            amount="2500.00",
            currency="BDT",
            transaction_status="APPROVED",
            risk_score=20,
            risk_level="LOW",
            recommended_action="APPROVE",
        )
        session.add(other_tx)
        session.commit()
        tx_ref = other_tx.reference

    # The canonical merchant queries this transaction belonging to other_merchant
    res = client.get(f"/api/v1/transactions/{tx_ref}", headers=merchant_headers)
    # Must return 404 (not 403) to prevent IDOR resource enumeration
    assert res.status_code == 404
    assert res.json()["detail"] == "Resource not found"


def test_merchant_transaction_creation_forces_merchant_ownership(
    client: TestClient,
    merchant_headers: dict[str, str],
    merchant_user,
):
    """Verify that even if merchant tries to specify another merchant_id, it is overridden."""
    fake_other_merchant_id = str(uuid.uuid4())
    payload = {
        "counterparty_name": "Tamper Test",
        "amount": "1500.00",
        "currency": "BDT",
        "channel": "MOBILE_APP",
        "merchant_id": fake_other_merchant_id,  # Spoofed merchant_id
    }
    res = client.post("/api/v1/transactions", headers=merchant_headers, json=payload)
    assert res.status_code == 201
    created_tx = res.json()
    # The server must have forced the merchant_id to the user's authentic merchant_id
    assert created_tx["merchant_id"] == str(merchant_user.merchant_id)
    assert created_tx["merchant_id"] != fake_other_merchant_id
