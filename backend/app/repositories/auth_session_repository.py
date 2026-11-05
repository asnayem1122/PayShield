"""Repository for auth session lifecycle tracking and refresh token revocation."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession


class AuthSessionRepository:
    """Repository handling active sessions and token revocation."""

    @staticmethod
    def create_session(
        session: Session,
        user_id: uuid.UUID,
        refresh_token_jti: str,
        expires_at: datetime,
        family_id: uuid.UUID | None = None,
    ) -> AuthSession:
        """Register a new active refresh token session."""
        auth_session = AuthSession(
            user_id=user_id,
            family_id=family_id or uuid.uuid4(),
            refresh_token_jti=refresh_token_jti,
            expires_at=expires_at,
        )
        session.add(auth_session)
        session.flush()
        return auth_session

    @staticmethod
    def get_by_jti(session: Session, jti: str) -> AuthSession | None:
        """Find an auth session by its refresh token JTI."""
        stmt = select(AuthSession).where(AuthSession.refresh_token_jti == jti)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_jti_for_update(session: Session, jti: str) -> AuthSession | None:
        """Find an auth session by its JTI with an exclusive row lock for atomic rotation."""
        stmt = select(AuthSession).where(AuthSession.refresh_token_jti == jti).with_for_update()
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def mark_used(session: Session, auth_session: AuthSession) -> None:
        """Update last_used_at timestamp on successful token refresh."""
        auth_session.last_used_at = datetime.now(timezone.utc)
        session.flush()

    @staticmethod
    def revoke_session(session: Session, auth_session: AuthSession) -> None:
        """Revoke a specific session immediately."""
        auth_session.revoked_at = datetime.now(timezone.utc)
        session.flush()

    @staticmethod
    def revoke_family(session: Session, family_id: uuid.UUID) -> int:
        """Revoke all active sessions belonging to a specific session family (device lineage)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(AuthSession)
            .where(
                AuthSession.family_id == family_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = session.execute(stmt)
        session.flush()
        return result.rowcount

    @staticmethod
    def revoke_all_for_user(session: Session, user_id: uuid.UUID) -> int:
        """Revoke all active sessions for a user (e.g., on forced logout or password change)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = session.execute(stmt)
        session.flush()
        return result.rowcount
