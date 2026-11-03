from fastapi import FastAPI

app = FastAPI(
    title="PayShield API",
    description="Educational Fraud Risk Monitoring API",
    version="0.1.0",
)


def _get_health_status() -> dict[str, str]:
    """Return API process health status.

    Note: This confirms the API service process is responding.
    Database, ML engine, and authentication are not evaluated in Milestone 0.
    """
    return {
        "status": "healthy",
        "app": "PayShield API",
        "version": "0.1.0",
        "environment": "development",
    }


@app.get("/health", tags=["Health"])
def health_root() -> dict[str, str]:
    """Root health probe."""
    return _get_health_status()


@app.get("/api/v1/health", tags=["Health"])
def health_v1() -> dict[str, str]:
    """API v1 health probe."""
    return _get_health_status()
