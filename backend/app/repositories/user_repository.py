"""Repository for user lookup, credential verification state, and lockout tracking."""

from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.user import User


class UserRepository:
    """Repository handling database operations for User entities."""

    @staticmethod
    def get_by_id(session: Session, user_id: uuid.UUID) -> User | None:
        """Fetch a user by their unique primary key with eager merchant loading."""
        stmt = (
            select(User)
            .options(joinedload(User.merchant))
            .where(User.id == user_id)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_email(session: Session, email: str) -> User | None:
        """Fetch a user by normalized lowercase email address."""
        normalized_email = email.strip().lower()
        stmt = (
            select(User)
            .options(joinedload(User.merchant))
            .where(User.email == normalized_email)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def record_failed_login(
        session: Session,
        user: User,
        max_attempts: int = 5,
        lockout_minutes: int = 15,
    ) -> User:
        """Increment failed login attempts and optionally engage temporal lockout."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=lockout_minutes
            )
        session.flush()
        return user

    @staticmethod
    def record_successful_login(session: Session, user: User) -> User:
        """Clear failed attempts and lockout timers, updating last_login_at timestamp."""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        session.flush()
        return user

    @staticmethod
    def create_user(session: Session, user: User) -> User:
        """Persist a new user account."""
        session.add(user)
        session.flush()
        return user
