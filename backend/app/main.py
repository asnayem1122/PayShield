"""PayShield FastAPI Application Entrypoint.

Exposes liveness and readiness health endpoints along with API v1 routes.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import check_database_connection, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for clean startup and shutdown."""
    yield
    dispose_engine()


app = FastAPI(
    title="PayShield API",
    description="Educational Payment Fraud-Risk Monitoring System API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for Flutter Web, Desktop, and Mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Format all HTTPExceptions according to RFC 9457 Problem Details specification."""
    title_map = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        423: "Locked",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    title = title_map.get(exc.status_code, "HTTP Error")
    headers = getattr(exc, "headers", None) or {}
    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content={
            "type": f"https://payshield.internal/errors/{exc.status_code}",
            "title": title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path,
        },
        headers=headers,
    )


def _get_health_status() -> dict[str, str]:
    """Return API process health status."""
    return {
        "status": "healthy",
        "app": "PayShield API",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
def health_root() -> dict[str, str]:
    """Root process liveness probe."""
    return _get_health_status()


@app.get("/api/v1/health", tags=["Health"])
def health_v1() -> dict[str, str]:
    """API v1 process liveness probe."""
    return _get_health_status()


@app.get("/api/v1/readiness", tags=["Health"])
def readiness_v1() -> JSONResponse:
    """API v1 database readiness probe."""
    is_healthy, _ = check_database_connection()
    if is_healthy:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "database": "connected",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        media_type="application/problem+json",
        content={
            "type": "https://payshield.internal/errors/database-unavailable",
            "title": "Service Unavailable",
            "status": 503,
            "detail": "Database service is unavailable",
            "instance": "/api/v1/readiness",
        },
    )


# Mount API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
