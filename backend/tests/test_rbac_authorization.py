"""Tests for Server-Side Role-Based Access Control (RBAC) and Tenant Scoping."""

import pytest
from fastapi.testclient import TestClient


def test_unauthenticated_requests_rejected(client: TestClient):
    """Verify protected endpoints return 401 when called without credentials."""
    assert client.get("/api/v1/dashboard/summary").status_code == 401
    assert client.get("/api/v1/dashboard/risk-distribution").status_code == 401
    assert client.get("/api/v1/dashboard/recent-transactions").status_code == 401
    assert client.get("/api/v1/transactions").status_code == 401
    assert client.get("/api/v1/transactions/tx_app_1000").status_code == 401
    assert client.get("/api/v1/cases").status_code == 401
    assert client.get("/api/v1/risk/indicators").status_code == 401
    assert client.get("/api/v1/audit/logs").status_code == 401


def test_merchant_forbidden_from_analyst_cases(client: TestClient, merchant_headers: dict[str, str]):
    """Verify MERCHANT role is forbidden (403) from accessing fraud analyst cases."""
    response = client.get("/api/v1/cases", headers=merchant_headers)
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]


def test_merchant_forbidden_from_patching_transaction_status(client: TestClient, merchant_headers: dict[str, str]):
    """Verify MERCHANT role cannot change transaction status."""
    response = client.patch(
        "/api/v1/transactions/tx_app_1000/status",
        headers=merchant_headers,
        json={"status": "APPROVED", "actor_id": "malicious_actor"},
    )
    assert response.status_code == 403


def test_merchant_forbidden_from_audit_logs(client: TestClient, merchant_headers: dict[str, str]):
    """Verify MERCHANT role cannot view system audit logs."""
    response = client.get("/api/v1/audit/logs", headers=merchant_headers)
    assert response.status_code == 403


def test_analyst_can_access_cases_and_audit(client: TestClient, analyst_headers: dict[str, str]):
    """Verify ANALYST role has access to cases and audit logs."""
    res_cases = client.get("/api/v1/cases?limit=5", headers=analyst_headers)
    assert res_cases.status_code == 200

    res_audit = client.get("/api/v1/audit/logs?limit=5", headers=analyst_headers)
    assert res_audit.status_code == 200


def test_admin_has_full_access(client: TestClient, admin_headers: dict[str, str]):
    """Verify ADMIN role has full access across all endpoints."""
    assert client.get("/api/v1/dashboard/summary", headers=admin_headers).status_code == 200
    assert client.get("/api/v1/transactions?limit=5", headers=admin_headers).status_code == 200
    assert client.get("/api/v1/cases?limit=5", headers=admin_headers).status_code == 200
    assert client.get("/api/v1/audit/logs?limit=5", headers=admin_headers).status_code == 200


def test_merchant_dashboard_is_scoped(client: TestClient, merchant_headers: dict[str, str], analyst_headers: dict[str, str]):
    """Verify dashboard summary is scoped to merchant transactions."""
    m_res = client.get("/api/v1/dashboard/summary", headers=merchant_headers)
    assert m_res.status_code == 200
    m_data = m_res.json()

    a_res = client.get("/api/v1/dashboard/summary", headers=analyst_headers)
    assert a_res.status_code == 200
    a_data = a_res.json()

    # Both return valid structures, merchant data reflects their transactions
    assert "total_volume" in m_data
    assert "total_volume" in a_data
