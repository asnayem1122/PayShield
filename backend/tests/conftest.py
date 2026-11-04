"""Pytest shared fixtures for PayShield integration and security test suites."""

from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import create_access_token, create_refresh_token
from app.main import app
from app.models.merchant import Merchant
from app.models.user import User
from scripts.seed_demo_users import CANONICAL_USERS, seed_demo_users


@pytest.fixture(scope="session", autouse=True)
def ensure_demo_users_seeded():
    """Ensure canonical users exist in test database before executing tests."""
    seed_demo_users()


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
    """Authorization header dictionary for analyst."""
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest.fixture
def merchant_headers(merchant_token: str) -> dict[str, str]:
    """Authorization header dictionary for merchant."""
    return {"Authorization": f"Bearer {merchant_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    """Authorization header dictionary for admin."""
    return {"Authorization": f"Bearer {admin_token}"}
