"""PayShield Phase 3 - PostgreSQL Permission Audit Tests for users and auth_sessions.

Verifies the least-privilege security model in PostgreSQL:
- payshield_app can SELECT and INSERT on users
- payshield_app has column-level UPDATE on mutable user fields (password_hash, full_name, etc.)
- payshield_app CANNOT UPDATE immutable or security-critical user fields (id, email, role, merchant_id)
- payshield_app CANNOT DELETE or TRUNCATE users
- payshield_app can SELECT and INSERT on auth_sessions
- payshield_app has column-level UPDATE on auth_sessions (last_used_at, revoked_at)
- payshield_app CANNOT DELETE or TRUNCATE auth_sessions
"""

import pytest
from sqlalchemy import create_engine, text
from app.core.config import settings

# Skip these tests if not running against real PostgreSQL
pytestmark = pytest.mark.skipif(
    str(settings.get_sqlalchemy_url()).startswith("sqlite"),
    reason="PostgreSQL permission verification requires real PostgreSQL instance",
)


@pytest.fixture(params=["payshield_dev"])
def db_admin_connection(request):
    """Admin/migrator connection to verify catalog and permission state."""
    db_name = request.param
    url = settings.get_migration_sqlalchemy_url().set(database=db_name)
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        yield conn, db_name
    engine.dispose()


def test_users_table_permissions(db_admin_connection):
    """Verify users table has SELECT, INSERT, no table-level UPDATE, DELETE, or TRUNCATE."""
    conn, db_name = db_admin_connection
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'users', 'SELECT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'users', 'INSERT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'users', 'UPDATE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'users', 'DELETE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'users', 'TRUNCATE')")).scalar_one() is False


def test_users_column_permissions(db_admin_connection):
    """Verify column-level UPDATE on users is granted strictly on mutable profile/security fields."""
    conn, db_name = db_admin_connection
    allowed_cols = [
        "password_hash",
        "full_name",
        "failed_login_attempts",
        "locked_until",
        "last_login_at",
        "updated_at",
    ]
    for col in allowed_cols:
        assert (
            conn.execute(
                text(f"SELECT has_column_privilege('payshield_app', 'users', '{col}', 'UPDATE')")
            ).scalar_one()
            is True
        ), f"payshield_app must have UPDATE on users.{col}"

    denied_cols = ["id", "email", "role", "merchant_id", "created_at"]
    for col in denied_cols:
        assert (
            conn.execute(
                text(f"SELECT has_column_privilege('payshield_app', 'users', '{col}', 'UPDATE')")
            ).scalar_one()
            is False
        ), f"payshield_app must NOT have UPDATE on users.{col}"


def test_auth_sessions_table_permissions(db_admin_connection):
    """Verify auth_sessions table has SELECT, INSERT, no table UPDATE, DELETE or TRUNCATE."""
    conn, db_name = db_admin_connection
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'auth_sessions', 'SELECT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'auth_sessions', 'INSERT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'auth_sessions', 'UPDATE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'auth_sessions', 'DELETE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'auth_sessions', 'TRUNCATE')")).scalar_one() is False


def test_auth_sessions_column_permissions(db_admin_connection):
    """Verify column-level UPDATE on auth_sessions is granted only on last_used_at and revoked_at."""
    conn, db_name = db_admin_connection
    allowed_cols = ["last_used_at", "revoked_at"]
    for col in allowed_cols:
        assert (
            conn.execute(
                text(f"SELECT has_column_privilege('payshield_app', 'auth_sessions', '{col}', 'UPDATE')")
            ).scalar_one()
            is True
        ), f"payshield_app must have UPDATE on auth_sessions.{col}"

    denied_cols = ["id", "user_id", "refresh_token_jti", "created_at", "expires_at"]
    for col in denied_cols:
        assert (
            conn.execute(
                text(f"SELECT has_column_privilege('payshield_app', 'auth_sessions', '{col}', 'UPDATE')")
            ).scalar_one()
            is False
        ), f"payshield_app must NOT have UPDATE on auth_sessions.{col}"
