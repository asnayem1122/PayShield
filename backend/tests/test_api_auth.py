"""Integration tests for Authentication API (/api/v1/auth/*)."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_login_success_merchant(client: TestClient, merchant_password: str):
    """Verify successful login for canonical merchant returns tokens and summary."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "merchant@techpulse.bd", "password": merchant_password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert data["user"]["email"] == "merchant@techpulse.bd"
    assert data["user"]["role"] == "MERCHANT"
    assert data["user"]["merchant_id"] is not None


def test_login_success_analyst(client: TestClient, analyst_password: str):
    """Verify successful login for canonical analyst."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst.shafiq@payshield.internal", "password": analyst_password},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "ANALYST"
    assert data["user"]["merchant_id"] is None


def test_login_invalid_password_returns_401_rfc9457(client: TestClient):
    """Verify 401 Unauthorized with RFC 9457 structure on wrong password."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst.shafiq@payshield.internal", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    data = response.json()
    assert data["status"] == 401
    assert data["title"] == "Unauthorized"
    assert "detail" in data
    assert data["instance"] == "/api/v1/auth/login"


def test_login_unknown_email_returns_generic_401(client: TestClient):
    """Verify 401 Unauthorized with identical message to prevent user enumeration."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown.user@nonexistent.domain", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    data = response.json()
    assert data["detail"] == "Invalid email or password"


def test_get_current_user_profile(client: TestClient, analyst_headers: dict[str, str]):
    """Verify GET /api/v1/auth/me returns user profile."""
    response = client.get("/api/v1/auth/me", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "analyst.shafiq@payshield.internal"
    assert data["role"] == "ANALYST"
    assert "created_at" in data


def test_get_current_user_profile_unauthenticated(client: TestClient):
    """Verify GET /api/v1/auth/me returns 401 when no token provided."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")


def test_token_rotation_on_refresh(client: TestClient, analyst_password: str):
    """Verify refresh token rotation: old session revoked, new token pair issued."""
    # 1. Login to get initial tokens
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst.shafiq@payshield.internal", "password": analyst_password},
    )
    tokens = login_res.json()
    orig_refresh = tokens["refresh_token"]

    # 2. Refresh token
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": orig_refresh},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != orig_refresh

    # 3. Attempting to reuse the revoked refresh token must be rejected
    reuse_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": orig_refresh},
    )
    assert reuse_res.status_code == 401


def test_logout_revokes_session(client: TestClient, merchant_password: str):
    """Verify logout revokes the session and subsequent refresh fails."""
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "merchant@techpulse.bd", "password": merchant_password},
    )
    tokens = login_res.json()
    auth_header = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 2. Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers=auth_header,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"

    # 3. Refresh should now fail
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_res.status_code == 401
