"""Tests for database engine, session lifecycle, and connectivity probes."""

from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import (
    check_database_connection,
    engine,
    get_db,
)


def test_engine_initialization() -> None:
    """Verify that SQLAlchemy engine is initialized with expected dialect."""
    assert engine is not None
    # Dialect name should be postgresql or sqlite
    assert engine.dialect.name in ("postgresql", "sqlite")


def test_session_lifecycle_success() -> None:
    """Verify get_db dependency yields a valid session and closes it cleanly."""
    gen = get_db()
    db = next(gen)
    assert isinstance(db, Session)
    # Complete generator to trigger finally block
    with pytest.raises(StopIteration):
        next(gen)


def test_session_lifecycle_rollback_on_exception() -> None:
    """Verify get_db dependency rolls back session if an unhandled exception occurs."""
    mock_session = MagicMock(spec=Session)

    with patch("app.core.database.SessionLocal", return_value=mock_session):
        gen = get_db()
        db = next(gen)
        assert db is mock_session

        with pytest.raises(RuntimeError, match="Simulation error"):
            gen.throw(RuntimeError("Simulation error"))

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


def test_check_database_connection_success() -> None:
    """Verify check_database_connection returns True against the running database."""
    is_healthy, error = check_database_connection()
    assert is_healthy is True
    assert error is None


def test_check_database_connection_failure() -> None:
    """Verify check_database_connection returns safe error without leaking credentials when DB fails."""
    with patch.object(
        engine, "connect", side_effect=OperationalError("connection failed", None, Exception("driver internal"))
    ):
        is_healthy, error = check_database_connection()
        assert is_healthy is False
        assert error == "Database connection could not be established"
        # Ensure driver internal or secrets are not present
        assert "driver internal" not in (error or "")
        assert "password" not in (error or "").lower()
