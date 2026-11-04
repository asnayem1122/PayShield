"""PayShield FastAPI Application Entrypoint.

Exposes liveness and readiness health endpoints along with API v1 routes.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
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
