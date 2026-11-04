"""Security utilities for PayShield: Bcrypt password hashing & RFC 7519 JWT handling.

Provides secure cryptographic primitives:
- Bcrypt password hashing with configurable work factor.
- JWT access and refresh token minting with standard RFC claims (sub, role, iss, aud, iat, exp, jti, type).
- Strict token validation with algorithm pinning, signature verification, and expiration enforcement.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
from uuid import UUID
import bcrypt
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from app.core.config import settings


class AuthenticationSecurityError(Exception):
    """Base exception for authentication and token security failures."""


class TokenExpiredError(AuthenticationSecurityError):
    """Raised when a JWT token has passed its expiration time."""


class TokenInvalidError(AuthenticationSecurityError):
    """Raised when a JWT token has an invalid signature, malformed payload, or invalid claims."""


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt rounds from settings.

    Rejects empty passwords and passwords exceeding 72 bytes to prevent bcrypt truncation issues.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password exceeds maximum length of 72 bytes.")

    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Returns False on hash mismatch or invalid format without leaking exception details.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    user_id: UUID | str,
    role: str,
    email: str | None = None,
    merchant_id: UUID | str | None = None,
    additional_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Mint a signed JWT access token with standard claims and 15-minute default validity."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    if email:
        payload["email"] = email
    if merchant_id:
        payload["merchant_id"] = str(merchant_id)
    if additional_claims:
        payload.update(additional_claims)

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def create_refresh_token(
    user_id: UUID | str,
    jti: str | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, str, datetime]:
    """Mint a signed JWT refresh token and return (token_str, jti, expires_at)."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    token_jti = jti or str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": token_jti,
        "type": "refresh",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, token_jti, expire


def decode_jwt_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Strictly decode and validate a JWT token against algorithm, issuer, audience, and type.

    Rejects unsigned tokens (alg=none), expired tokens, and mismatched token types.
    """
    if not token or not isinstance(token, str):
        raise TokenInvalidError("Token must be a non-empty string.")

    # Guard against alg=none and unapproved algorithms
    if settings.JWT_ALGORITHM.lower() == "none":
        raise TokenInvalidError("Insecure JWT algorithm 'none' is disallowed.")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={
                "require": ["sub", "exp", "iat", "jti", "type"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
    except ExpiredSignatureError as e:
        raise TokenExpiredError("Token has expired.") from e
    except PyJWTError as e:
        raise TokenInvalidError(f"Invalid token: {e}") from e

    token_type = payload.get("type")
    if token_type != expected_type:
        raise TokenInvalidError(
            f"Invalid token type: expected '{expected_type}', got '{token_type}'."
        )

    return payload
