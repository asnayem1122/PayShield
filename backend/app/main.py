"""PayShield FastAPI Application Entrypoint.

Exposes liveness and readiness health endpoints.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.core.database import check_database_connection, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for clean startup and shutdown."""
    yield
    dispose_engine()


app = FastAPI(
    title="PayShield API",
    description="Educational Fraud Risk Monitoring API",
    version="0.1.0",
    lifespan=lifespan,
)


def _get_health_status() -> dict[str, str]:
    """Return API process health status.

    Note: This confirms the API service process is responding (liveness probe).
    """
    return {
        "status": "healthy",
        "app": "PayShield API",
        "version": "0.1.0",
        "environment": "development",
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
    """API v1 database readiness probe.

    Executes a minimal SELECT 1 probe against the configured database.
    Returns HTTP 200 when database connectivity is verified.
    Returns HTTP 503 (RFC 9457 Problem Details) when database is unreachable.
    """
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
        content={
            "type": "https://payshield.internal/errors/database-unavailable",
            "title": "Service Unavailable",
            "status": 503,
            "detail": "Database service is unavailable",
            "instance": "/api/v1/readiness",
        },
        media_type="application/problem+json",
    )
