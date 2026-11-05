"""Pytest shared fixtures for PayShield integration and security test suites."""

from collections.abc import Generator
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

# Set test environment secrets prior to importing settings and running seed
os.environ.setdefault("PAYSHIELD_MERCHANT_PASSWORD", "TestMerchantSecure2026!X")
os.environ.setdefault("PAYSHIELD_ANALYST_PASSWORD", "TestAnalystSecure2026!Y")
os.environ.setdefault("PAYSHIELD_ADMIN_PASSWORD", "TestAdminSecure2026!Z")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test_secure_cryptographic_jwt_secret_key_minimum_32_bytes_long_hs256!",
)

from app.core.database import SessionLocal, get_db
from app.core.rate_limiter import login_rate_limiter
from app.core.security import create_access_token, create_refresh_token
from app.main import app
from app.models.merchant import Merchant
from app.models.user import User
from scripts.seed_demo_users import CANONICAL_USERS, rotate_demo_passwords, seed_demo_users


@pytest.fixture(scope="session", autouse=True)
def ensure_demo_users_seeded():
    """Ensure canonical users exist in test database and passwords match test secrets before executing tests."""
    seed_demo_users()
    # Ensure hashes match current test environment secrets
    rotate_demo_passwords()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the in-memory login rate limiter before each test."""
    login_rate_limiter.reset()
    yield
    login_rate_limiter.reset()


@pytest.fixture
def merchant_password() -> str:
    return os.environ["PAYSHIELD_MERCHANT_PASSWORD"]


@pytest.fixture
def analyst_password() -> str:
    return os.environ["PAYSHIELD_ANALYST_PASSWORD"]


@pytest.fixture
def admin_password() -> str:
    return os.environ["PAYSHIELD_ADMIN_PASSWORD"]


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional session for test inspections."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    """Standard unauthenticated FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def analyst_user(db_session: Session) -> User:
    """Fetch the canonical analyst user."""
    user = db_session.execute(
        select(User).where(User.email == "analyst.shafiq@payshield.internal")
    ).scalar_one()
    return user


@pytest.fixture
def merchant_user(db_session: Session) -> User:
    """Fetch the canonical merchant user."""
    user = db_session.execute(
        select(User).where(User.email == "merchant@techpulse.bd")
    ).scalar_one()
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Fetch the canonical admin user."""
    user = db_session.execute(
        select(User).where(User.email == "admin.nayem@payshield.internal")
    ).scalar_one()
    return user


@pytest.fixture
def analyst_token(analyst_user: User) -> str:
    """Generate a valid access token for the canonical analyst."""
    return create_access_token(
        user_id=analyst_user.id,
        role=analyst_user.role,
        email=analyst_user.email,
        merchant_id=analyst_user.merchant_id,
    )


@pytest.fixture
def merchant_token(merchant_user: User) -> str:
    """Generate a valid access token for the canonical merchant."""
    return create_access_token(
        user_id=merchant_user.id,
        role=merchant_user.role,
        email=merchant_user.email,
        merchant_id=merchant_user.merchant_id,
    )


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Generate a valid access token for the canonical admin."""
    return create_access_token(
        user_id=admin_user.id,
        role=admin_user.role,
        email=admin_user.email,
        merchant_id=admin_user.merchant_id,
    )


@pytest.fixture
def analyst_headers(analyst_token: str) -> dict[str, str]:
    """Authorization header dictionary for canonical analyst."""
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest.fixture
def merchant_headers(merchant_token: str) -> dict[str, str]:
    """Authorization header dictionary for canonical merchant."""
    return {"Authorization": f"Bearer {merchant_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    """Authorization header dictionary for canonical admin."""
    return {"Authorization": f"Bearer {admin_token}"}
