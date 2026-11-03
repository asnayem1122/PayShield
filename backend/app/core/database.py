"""SQLAlchemy engine, session factory, and dependency lifecycle for PayShield.

Provides synchronous session management, connection pooling, and connection readiness probes.
"""

from collections.abc import Generator
from typing import Any
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine configuration with connection pooling and pre-ping
# sqlite in-memory for testing requires check_same_thread=False
is_sqlite = str(settings.get_sqlalchemy_url()).startswith("sqlite")
engine_kwargs: dict[str, Any] = {
    "pool_pre_ping": settings.DB_POOL_PRE_PING,
}

if not is_sqlite:
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
        }
    )
else:
    engine_kwargs.update({"connect_args": {"check_same_thread": False}})

engine = create_engine(settings.get_sqlalchemy_url(), **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session scope for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> tuple[bool, str | None]:
    """Execute minimal SELECT 1 probe to verify database connectivity.

    Returns:
        Tuple of (is_healthy, error_detail).
        Does not leak connection strings or passwords in error_detail.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError:
        return False, "Database connection could not be established"
    except Exception:
        return False, "Database service is unreachable"


def dispose_engine() -> None:
    """Safely dispose of connection pool during application shutdown."""
    engine.dispose()
