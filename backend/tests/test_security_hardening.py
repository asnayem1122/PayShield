"""Security hardening tests covering credentials, session family isolation, anti-enumeration, and rate limiting."""

import os
import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.core.rate_limiter import login_rate_limiter
from app.models.auth_session import AuthSession
from app.models.user import User
from app.repositories.auth_session_repository import AuthSessionRepository
from scripts.seed_demo_users import (
    get_validated_passwords,
    rotate_demo_passwords,
    seed_demo_users,
)


def test_jwt_secret_validation_short_key_rejected():
    """Verify settings validation rejects JWT keys shorter than 32 characters."""
    with pytest.raises(ValueError, match="at least 32 characters long"):
        Settings(
            ENVIRONMENT="development",
            JWT_SECRET_KEY=SecretStr("short_secret_key_1234"),
        )


def test_jwt_secret_validation_production_insecure_placeholder_rejected():
    """Verify settings fail closed in production when given insecure placeholder keys."""
    with pytest.raises(ValueError, match="cannot contain insecure placeholder"):
        Settings(
            ENVIRONMENT="production",
            POSTGRES_PASSWORD=SecretStr("prod_strong_app_password_98765"),
            MIGRATION_POSTGRES_PASSWORD=SecretStr("prod_strong_mig_password_98765"),
            JWT_SECRET_KEY=SecretStr("insecure_production_jwt_placeholder_key_over_32_chars!"),
        )


def test_database_password_validation_production_default_password_rejected():
    """Verify settings fail closed in production when default dev DB passwords are used."""
    with pytest.raises(ValueError, match="database passwords must not use default"):
        Settings(
            ENVIRONMENT="production",
            POSTGRES_PASSWORD=SecretStr("payshield_app_insecure_dev_password"),
            MIGRATION_POSTGRES_PASSWORD=SecretStr("payshield_migrator_insecure_dev_password"),
            JWT_SECRET_KEY=SecretStr("a_very_strong_cryptographic_random_key_for_testing_abcdefghij!"),
        )


def test_seed_script_fails_closed_when_env_vars_missing(monkeypatch):
    """Verify get_validated_passwords fails closed when required environment variables are absent."""
    monkeypatch.delenv("PAYSHIELD_MERCHANT_PASSWORD", raising=False)
    monkeypatch.delenv("PAYSHIELD_ANALYST_PASSWORD", raising=False)
    monkeypatch.delenv("PAYSHIELD_ADMIN_PASSWORD", raising=False)

    passwords = get_validated_passwords()
    assert passwords is None


def test_password_rotation_workflow(client: TestClient, db_session: Session, monkeypatch):
    """Verify --rotate-passwords updates hashes, revokes sessions, and allows authentication with new password."""
    # 1. Login with initial password
    orig_pw = os.environ["PAYSHIELD_ANALYST_PASSWORD"]
    res1 = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst.shafiq@payshield.internal", "password": orig_pw},
    )
    assert res1.status_code == 200
    orig_refresh = res1.json()["refresh_token"]

    # 2. Set rotated password in environment
    new_pw = "RotatedSecurePassword2026!Analyst#New"
    monkeypatch.setenv("PAYSHIELD_ANALYST_PASSWORD", new_pw)

    # 3. Execute password rotation
    rotated = rotate_demo_passwords()
    assert rotated is True

    # 4. Old refresh token must now be invalid / revoked
    refresh_old = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": orig_refresh},
    )
    assert refresh_old.status_code == 401

    # 5. Old password must fail
    login_old = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst.shafiq@payshield.internal", "password": orig_pw},
    )
    assert login_old.status_code == 401

    # 6. New password must succeed
    login_new = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst.shafiq@payshield.internal", "password": new_pw},
    )
    assert login_new.status_code == 200

    # Teardown: rotate back to original test password
    monkeypatch.setenv("PAYSHIELD_ANALYST_PASSWORD", orig_pw)
    rotate_demo_passwords()


def test_session_family_isolation_on_compromised_token_reuse(client: TestClient, analyst_password: str):
    """Verify token reuse revokes only the compromised device's session family, leaving other devices active."""
    # Device A (e.g. Mobile) login
    login_device_a = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst.shafiq@payshield.internal", "password": analyst_password},
    )
    assert login_device_a.status_code == 200
    tokens_a = login_device_a.json()
    refresh_a_v1 = tokens_a["refresh_token"]

    # Device B (e.g. Web) login
    login_device_b = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst.shafiq@payshield.internal", "password": analyst_password},
    )
    assert login_device_b.status_code == 200
    tokens_b = login_device_b.json()
    refresh_b_v1 = tokens_b["refresh_token"]

    # Device A rotates token: refresh_a_v1 -> refresh_a_v2
    rotate_a = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_a_v1},
    )
    assert rotate_a.status_code == 200
    tokens_a_v2 = rotate_a.json()
    refresh_a_v2 = tokens_a_v2["refresh_token"]

    # Attacker replays revoked refresh_a_v1 on Device A's lineage
    replay_attack = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_a_v1},
    )
    assert replay_attack.status_code == 401
    assert "terminated" in replay_attack.json()["detail"].lower()

    # Now Device A's current token refresh_a_v2 must ALSO be revoked (family terminated)
    blocked_a = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_a_v2},
    )
    assert blocked_a.status_code == 401

    # CRITICAL: Device B's session was in an isolated family and MUST REMAIN VALID!
    valid_b = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_b_v1},
    )
    assert valid_b.status_code == 200
    assert "access_token" in valid_b.json()


def test_anti_account_enumeration_suspended_user_returns_generic_401(
    client: TestClient, analyst_password: str
):
    """Verify suspended accounts receive generic 401 with identical body to unknown accounts."""
    migrator_engine = create_engine(settings.get_migration_sqlalchemy_url())
    with Session(migrator_engine) as mig_session:
        user = mig_session.execute(
            select(User).where(User.email == "analyst.shafiq@payshield.internal")
        ).scalar_one()
        orig_status = user.status
        user.status = "SUSPENDED"
        mig_session.commit()

    try:
        # Request with suspended user
        res_suspended = client.post(
            "/api/v1/auth/login",
            json={"email": "analyst.shafiq@payshield.internal", "password": analyst_password},
        )
        assert res_suspended.status_code == 401
        data_suspended = res_suspended.json()
        assert data_suspended["detail"] == "Invalid email or password"

        # Request with nonexistent user
        res_nonexistent = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent.analyst@payshield.internal", "password": analyst_password},
        )
        assert res_nonexistent.status_code == 401
        data_nonexistent = res_nonexistent.json()
        assert data_nonexistent["detail"] == "Invalid email or password"

        # Both responses must be identical
        assert data_suspended["status"] == data_nonexistent["status"]
        assert data_suspended["detail"] == data_nonexistent["detail"]
        assert data_suspended["title"] == data_nonexistent["title"]
    finally:
        with Session(migrator_engine) as mig_session:
            user = mig_session.execute(
                select(User).where(User.email == "analyst.shafiq@payshield.internal")
            ).scalar_one()
            user.status = orig_status
            mig_session.commit()


def test_login_rate_limiting(client: TestClient):
    """Verify IP rate limiting returns RFC 9457 Problem Detail with HTTP 429 when threshold exceeded."""
    login_rate_limiter.reset()

    # Make 10 attempts (within limit)
    for _ in range(10):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "random@nonexistent.domain", "password": "WrongPassword123!"},
        )
        assert res.status_code == 401

    # 11th attempt must exceed limit and return 429
    res_limited = client.post(
        "/api/v1/auth/login",
        json={"email": "random@nonexistent.domain", "password": "WrongPassword123!"},
    )
    assert res_limited.status_code == 429
    assert res_limited.headers["content-type"].startswith("application/problem+json")
    data = res_limited.json()
    assert data["status"] == 429
    assert data["title"] == "Too Many Requests"
    assert "rate" in data["detail"].lower() or "too many" in data["detail"].lower()

    # Resetting restores functionality
    login_rate_limiter.reset()
    res_restored = client.post(
        "/api/v1/auth/login",
        json={"email": "random@nonexistent.domain", "password": "WrongPassword123!"},
    )
    assert res_restored.status_code == 401
