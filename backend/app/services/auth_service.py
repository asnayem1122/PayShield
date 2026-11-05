"""Authentication service managing user login, token issuance, session rotation, and logout."""

from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    AuthenticationSecurityError,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
    UserSummaryResponse,
)

# Constant dummy hash for constant-time comparison against nonexistent users
# to mitigate timing-based user enumeration attacks.
DUMMY_BCRYPT_HASH = "$2b$12$e8Y50v8c6.fE76bIovG0A.tq5cKzE9cTfZuYp9e0Z7Qh4z9EsqK2S"


class AuthenticationError(Exception):
    """Exception raised when authentication fails."""

    def __init__(self, detail: str = "Invalid email or password", status_code: int = 401):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AccountLockedError(AuthenticationError):
    """Exception raised when account is temporarily locked out."""

    def __init__(self, detail: str = "Account is temporarily locked due to consecutive failed login attempts. Please try again later."):
        super().__init__(detail=detail, status_code=423)


class AccountSuspendedError(AuthenticationError):
    """Exception raised internally when account has been suspended."""

    def __init__(self, detail: str = "Invalid email or password"):
        # Returns generic 401 unauthenticated to prevent account enumeration
        super().__init__(detail=detail, status_code=401)


class AuthService:
    """Service orchestrating authentication workflows, JWT lifecycle, and sessions."""

    @staticmethod
    def login(
        session: Session,
        request: LoginRequest,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Authenticate user credentials, handle account lockout, and issue token pair."""
        normalized_email = request.email.strip().lower()
        user = UserRepository.get_by_email(session, normalized_email)

        if user is None:
            # Constant-time comparison to prevent timing enumeration
            verify_password("dummy_password_timing_mitigation", DUMMY_BCRYPT_HASH)
            audit = AuditLog(
                actor_type="SYSTEM",
                actor_id="anonymous",
                action="USER_LOGIN_FAILED",
                entity_type="USER",
                entity_id="unknown",
                details={"email": normalized_email, "reason": "USER_NOT_FOUND"},
                ip_address=ip_address,
            )
            AuditLogRepository.create(session, audit)
            session.commit()
            raise AuthenticationError("Invalid email or password")

        # Anti-enumeration for suspended accounts: verify password for timing consistency,
        # log internally with specific reason, but fail with generic 401
        if user.status == "SUSPENDED":
            verify_password(request.password, user.password_hash)
            audit = AuditLog(
                actor_type=user.role,
                actor_id=str(user.id),
                action="USER_LOGIN_FAILED",
                entity_type="USER",
                entity_id=str(user.id),
                details={"email": user.email, "reason": "ACCOUNT_SUSPENDED"},
                ip_address=ip_address,
            )
            AuditLogRepository.create(session, audit)
            session.commit()
            raise AuthenticationError("Invalid email or password")

        # Check temporal lockout
        now = datetime.now(timezone.utc)
        if user.locked_until is not None:
            if now < user.locked_until:
                raise AccountLockedError()
            else:
                # Lockout window has elapsed, clear lock
                user.locked_until = None
                user.failed_login_attempts = 0
                session.flush()

        # Verify password
        if not verify_password(request.password, user.password_hash):
            UserRepository.record_failed_login(
                session,
                user,
                max_attempts=settings.MAX_FAILED_LOGIN_ATTEMPTS,
                lockout_minutes=settings.ACCOUNT_LOCKOUT_MINUTES,
            )
            # Log failed login attempt
            audit = AuditLog(
                actor_type=user.role,
                actor_id=str(user.id),
                action="USER_LOGIN_FAILED",
                entity_type="USER",
                entity_id=str(user.id),
                details={
                    "email": user.email,
                    "failed_attempts": user.failed_login_attempts,
                    "locked": user.locked_until is not None,
                },
                ip_address=ip_address,
            )
            AuditLogRepository.create(session, audit)
            session.commit()

            if user.locked_until is not None:
                raise AccountLockedError()
            raise AuthenticationError("Invalid email or password")

        # Successful authentication: reset failed attempts
        UserRepository.record_successful_login(session, user)

        # Generate tokens
        access_token = create_access_token(
            user_id=user.id,
            role=user.role,
            email=user.email,
            merchant_id=user.merchant_id,
        )

        family_id = uuid.uuid4()
        refresh_jti = str(uuid.uuid4())
        refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(
            user_id=user.id,
            jti=refresh_jti,
        )

        # Persist session with refresh token JTI and isolated session family ID
        AuthSessionRepository.create_session(
            session=session,
            user_id=user.id,
            refresh_token_jti=refresh_jti,
            expires_at=refresh_expires_at,
            family_id=family_id,
        )

        # Audit log successful login
        audit = AuditLog(
            actor_type=user.role,
            actor_id=str(user.id),
            action="USER_LOGIN_SUCCESS",
            entity_type="USER",
            entity_id=str(user.id),
            details={
                "email": user.email,
                "role": user.role,
                "family_id": str(family_id),
            },
            ip_address=ip_address,
        )
        AuditLogRepository.create(session, audit)
        session.commit()

        merchant_name = user.merchant.name if user.merchant else None

        user_summary = UserSummaryResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            merchant_id=user.merchant_id,
            merchant_name=merchant_name,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary,
        )

    @staticmethod
    def refresh_tokens(
        session: Session,
        refresh_token_str: str,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Rotate refresh token: validate existing session with atomic row lock, revoke it, and issue fresh token pair."""
        try:
            payload = decode_jwt_token(refresh_token_str, expected_type="refresh")
        except (AuthenticationSecurityError, ValueError) as e:
            raise AuthenticationError(f"Invalid refresh token: {str(e)}", status_code=401)

        user_id_str = payload.get("sub")
        jti = payload.get("jti")
        if not user_id_str or not jti:
            raise AuthenticationError("Malformed refresh token claims", status_code=401)

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise AuthenticationError("Invalid user identity in token", status_code=401)

        # Atomic row lock to prevent race conditions during rotation
        auth_session = AuthSessionRepository.get_by_jti_for_update(session, jti)
        if auth_session is None:
            raise AuthenticationError("Refresh session not found or revoked", status_code=401)

        if auth_session.revoked_at is not None:
            # Token reuse detected on a revoked session! Revoke only the affected session family (device lineage)
            revoked_count = AuthSessionRepository.revoke_family(session, auth_session.family_id)
            audit = AuditLog(
                actor_type="SYSTEM",
                actor_id=str(user_id),
                action="REFRESH_TOKEN_REUSE_DETECTED",
                entity_type="AUTH_SESSION",
                entity_id=str(auth_session.id),
                details={
                    "compromised_jti": jti,
                    "family_id": str(auth_session.family_id),
                    "revoked_count": revoked_count,
                },
                ip_address=ip_address,
            )
            AuditLogRepository.create(session, audit)
            session.commit()
            raise AuthenticationError(
                "Revoked refresh token presented; session family terminated for security",
                status_code=401,
            )

        now = datetime.now(timezone.utc)
        if auth_session.expires_at < now:
            AuthSessionRepository.revoke_session(session, auth_session)
            session.commit()
            raise AuthenticationError("Refresh token has expired", status_code=401)

        user = UserRepository.get_by_id(session, user_id)
        if user is None or user.status == "SUSPENDED":
            raise AuthenticationError("User account is inactive or suspended", status_code=401)

        # Token Rotation: Revoke current session, issue new pair maintaining the SAME family_id
        AuthSessionRepository.revoke_session(session, auth_session)

        new_access_token = create_access_token(
            user_id=user.id,
            role=user.role,
            email=user.email,
            merchant_id=user.merchant_id,
        )

        new_refresh_jti = str(uuid.uuid4())
        new_refresh_token, new_refresh_jti, new_refresh_expires_at = create_refresh_token(
            user_id=user.id,
            jti=new_refresh_jti,
        )

        AuthSessionRepository.create_session(
            session=session,
            user_id=user.id,
            refresh_token_jti=new_refresh_jti,
            expires_at=new_refresh_expires_at,
            family_id=auth_session.family_id,
        )

        # Audit log token refresh
        audit = AuditLog(
            actor_type=user.role,
            actor_id=str(user.id),
            action="TOKEN_ROTATED",
            entity_type="USER",
            entity_id=str(user.id),
            details={
                "rotated_jti": jti,
                "new_jti": new_refresh_jti,
                "family_id": str(auth_session.family_id),
            },
            ip_address=ip_address,
        )
        AuditLogRepository.create(session, audit)
        session.commit()

        merchant_name = user.merchant.name if user.merchant else None

        user_summary = UserSummaryResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            merchant_id=user.merchant_id,
            merchant_name=merchant_name,
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary,
        )

    @staticmethod
    def logout(
        session: Session,
        user_id: uuid.UUID,
        refresh_token_str: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Revoke active refresh sessions upon logout."""
        user = UserRepository.get_by_id(session, user_id)
        actor_role = user.role if user else "SYSTEM"

        revoked_count = 0
        family_id_str = None
        if refresh_token_str:
            try:
                payload = decode_jwt_token(refresh_token_str, expected_type="refresh")
                jti = payload.get("jti")
                if jti:
                    auth_session = AuthSessionRepository.get_by_jti_for_update(session, jti)
                    if auth_session and auth_session.user_id == user_id:
                        # Revoke only the session family associated with this client/device
                        family_id_str = str(auth_session.family_id)
                        revoked_count = AuthSessionRepository.revoke_family(
                            session, auth_session.family_id
                        )
            except Exception:
                # If token decode or lookup fails, fallback to revoking all sessions for user
                revoked_count = AuthSessionRepository.revoke_all_for_user(session, user_id)
        else:
            revoked_count = AuthSessionRepository.revoke_all_for_user(session, user_id)

        # Audit log logout event
        audit = AuditLog(
            actor_type=actor_role,
            actor_id=str(user_id),
            action="USER_LOGOUT",
            entity_type="USER",
            entity_id=str(user_id),
            details={
                "revoked": True,
                "revoked_sessions": revoked_count,
                "family_id": family_id_str,
            },
            ip_address=ip_address,
        )
        AuditLogRepository.create(session, audit)
        session.commit()

    @staticmethod
    def get_user_profile(session: Session, user_id: uuid.UUID) -> UserProfileResponse:
        """Retrieve full profile details for the authenticated user."""
        user = UserRepository.get_by_id(session, user_id)
        if user is None:
            raise AuthenticationError("User not found", status_code=404)

        merchant_name = user.merchant.name if user.merchant else None

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            merchant_id=user.merchant_id,
            merchant_name=merchant_name,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
