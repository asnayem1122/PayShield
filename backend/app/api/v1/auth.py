"""Authentication API endpoints: login, token refresh, current profile, and logout."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limiter import login_rate_limiter
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    ProblemDetail,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.services.auth_service import (
    AccountLockedError,
    AccountSuspendedError,
    AuthenticationError,
    AuthService,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


def _problem_response(
    status_code: int,
    title: str,
    detail: str,
    instance: str,
    error_type: str = "about:blank",
) -> JSONResponse:
    """Helper to return an RFC 9457 problem detail JSON response."""
    return JSONResponse(
        status_code=status_code,
        media_type="application/problem+json",
        content={
            "type": error_type,
            "title": title,
            "status": status_code,
            "detail": detail,
            "instance": instance,
        },
    )


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ProblemDetail, "description": "Invalid credentials"},
        403: {"model": ProblemDetail, "description": "Account suspended"},
        423: {"model": ProblemDetail, "description": "Account temporarily locked"},
    },
)
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate with email and password, issuing an access and refresh token pair."""
    client_ip = request.client.host if request.client else "unknown"

    # Enforce rate limiting per client IP to mitigate credential brute force
    if not login_rate_limiter.is_allowed(client_ip):
        return _problem_response(
            status_code=429,
            title="Too Many Requests",
            detail="Too many login attempts. Please try again later.",
            instance="/api/v1/auth/login",
            error_type="https://payshield.internal/errors/rate-limit-exceeded",
        )

    try:
        return AuthService.login(db, payload, ip_address=client_ip)
    except AccountLockedError as e:
        return _problem_response(
            status_code=423,
            title="Account Locked",
            detail=e.detail,
            instance="/api/v1/auth/login",
            error_type="https://payshield.internal/errors/account-locked",
        )
    except AccountSuspendedError as e:
        return _problem_response(
            status_code=401,
            title="Unauthorized",
            detail=e.detail,
            instance="/api/v1/auth/login",
            error_type="https://payshield.internal/errors/invalid-credentials",
        )
    except AuthenticationError as e:
        return _problem_response(
            status_code=401,
            title="Unauthorized",
            detail=e.detail,
            instance="/api/v1/auth/login",
            error_type="https://payshield.internal/errors/invalid-credentials",
        )


@auth_router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ProblemDetail, "description": "Unauthenticated"},
        403: {"model": ProblemDetail, "description": "Forbidden"},
    },
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve identity, profile details, and role for the currently authenticated user."""
    return AuthService.get_user_profile(db, current_user.id)


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ProblemDetail, "description": "Invalid, expired, or revoked refresh token"},
    },
)
def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Exchange an unexpired refresh token for a newly issued token pair (token rotation)."""
    client_ip = request.client.host if request.client else None
    try:
        return AuthService.refresh_tokens(db, payload.refresh_token, ip_address=client_ip)
    except AuthenticationError as e:
        return _problem_response(
            status_code=e.status_code,
            title="Authentication Error",
            detail=e.detail,
            instance="/api/v1/auth/refresh",
            error_type="https://payshield.internal/errors/invalid-token",
        )


@auth_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ProblemDetail, "description": "Unauthenticated"},
    },
)
def logout(
    request: Request,
    payload: RefreshTokenRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke active refresh sessions and log out the user."""
    client_ip = request.client.host if request.client else None
    refresh_token_str = payload.refresh_token if payload else None
    AuthService.logout(
        db,
        user_id=current_user.id,
        refresh_token_str=refresh_token_str,
        ip_address=client_ip,
    )
    return {"status": "success", "message": "Successfully logged out"}
