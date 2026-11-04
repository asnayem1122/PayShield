"""
PayShield Phase 2 - Effective PostgreSQL Permission Audit Tests.

Verifies the least-privilege security model in PostgreSQL 18:
- payshield_app has no inherited roles (pg_auth_members = 0)
- PUBLIC has no CREATE privileges on database or schema
- payshield_app has NO table-level UPDATE, DELETE, or TRUNCATE on any table
- merchants is strictly read-only (SELECT only) for payshield_app
- transactions has column-level UPDATE granted exclusively on transaction_status
- analyst_cases has column-level UPDATE granted on case_status, assigned_analyst,
  analyst_notes, resolution_reason, resolved_at (and denied on trigger_reason, transaction_id)
- risk_assessments and audit_logs are append-only (SELECT, INSERT only)
- Verified across payshield_dev and payshield_test databases
"""

import pytest
from sqlalchemy import create_engine, text
from app.core.config import settings

# Skip these tests if not running against real PostgreSQL (e.g. SQLite override)
pytestmark = pytest.mark.skipif(
    str(settings.get_sqlalchemy_url()).startswith("sqlite"),
    reason="PostgreSQL permission verification requires real PostgreSQL instance",
)


@pytest.fixture(params=["payshield_dev", "payshield_test"])
def db_admin_connection(request):
    """Admin/migrator connection to verify catalog and permission state."""
    db_name = request.param
    url = settings.get_migration_sqlalchemy_url().set(database=db_name)
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        yield conn, db_name
    engine.dispose()


def test_payshield_app_has_no_inherited_roles(db_admin_connection):
    """Verify payshield_app is an unprivileged leaf role without superuser or role memberships."""
    conn, db_name = db_admin_connection
    res = conn.execute(
        text(
            """
            SELECT count(*) 
            FROM pg_auth_members m
            JOIN pg_roles r ON m.member = r.oid
            WHERE r.rolname = 'payshield_app'
            """
        )
    ).scalar_one()
    assert res == 0, f"payshield_app must have 0 role memberships in {db_name}, found {res}"

    # Verify not superuser
    is_super = conn.execute(
        text("SELECT rolsuper FROM pg_roles WHERE rolname = 'payshield_app'")
    ).scalar_one()
    assert is_super is False, f"payshield_app must not be superuser in {db_name}"


def test_public_has_no_create_privilege(db_admin_connection):
    """Verify PUBLIC role has no CREATE privileges on database or schema."""
    conn, db_name = db_admin_connection
    has_db_create = conn.execute(
        text("SELECT has_database_privilege('public', current_database(), 'CREATE')")
    ).scalar_one()
    assert has_db_create is False, f"PUBLIC has CREATE privilege on database {db_name}"

    has_schema_create = conn.execute(
        text("SELECT has_schema_privilege('public', 'public', 'CREATE')")
    ).scalar_one()
    assert has_schema_create is False, f"PUBLIC has CREATE privilege on schema public in {db_name}"


def test_merchants_table_permissions(db_admin_connection):
    """Verify merchants table is strictly SELECT-only for payshield_app."""
    conn, db_name = db_admin_connection
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'merchants', 'SELECT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'merchants', 'INSERT')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'merchants', 'UPDATE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'merchants', 'DELETE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'merchants', 'TRUNCATE')")).scalar_one() is False


def test_transactions_table_permissions(db_admin_connection):
    """Verify transactions table has SELECT, INSERT, no table UPDATE, DELETE or TRUNCATE."""
    conn, db_name = db_admin_connection
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'transactions', 'SELECT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'transactions', 'INSERT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'transactions', 'UPDATE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'transactions', 'DELETE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'transactions', 'TRUNCATE')")).scalar_one() is False


def test_transactions_column_permissions(db_admin_connection):
    """Verify column-level UPDATE on transactions is granted only on transaction_status and updated_at."""
    conn, db_name = db_admin_connection
    assert conn.execute(text("SELECT has_column_privilege('payshield_app', 'transactions', 'transaction_status', 'UPDATE')")).scalar_one() is True
    assert conn.execute(text("SELECT has_column_privilege('payshield_app', 'transactions', 'updated_at', 'UPDATE')")).scalar_one() is True

    denied_cols = ["amount", "reference", "risk_score", "merchant_id", "counterparty_name", "currency", "risk_level"]
    for col in denied_cols:
        assert conn.execute(text(f"SELECT has_column_privilege('payshield_app', 'transactions', '{col}', 'UPDATE')")).scalar_one() is False


def test_analyst_cases_table_permissions(db_admin_connection):
    """Verify analyst_cases table has SELECT, INSERT, no table UPDATE, DELETE or TRUNCATE."""
    conn, db_name = db_admin_connection
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'analyst_cases', 'SELECT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'analyst_cases', 'INSERT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'analyst_cases', 'UPDATE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'analyst_cases', 'DELETE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'analyst_cases', 'TRUNCATE')")).scalar_one() is False


def test_analyst_cases_column_permissions(db_admin_connection):
    """Verify column-level UPDATE on analyst_cases is granted only on allowed workflow columns."""
    conn, db_name = db_admin_connection
    allowed_cols = ["case_status", "assigned_analyst", "resolution_note", "resolved_at", "updated_at"]
    for col in allowed_cols:
        assert conn.execute(text(f"SELECT has_column_privilege('payshield_app', 'analyst_cases', '{col}', 'UPDATE')")).scalar_one() is True

    denied_cols = ["id", "transaction_id", "priority", "trigger_reason", "created_at"]
    for col in denied_cols:
        assert conn.execute(text(f"SELECT has_column_privilege('payshield_app', 'analyst_cases', '{col}', 'UPDATE')")).scalar_one() is False


def test_risk_assessments_table_permissions(db_admin_connection):
    """Verify risk_assessments is append-only (SELECT, INSERT only)."""
    conn, db_name = db_admin_connection
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'risk_assessments', 'SELECT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'risk_assessments', 'INSERT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'risk_assessments', 'UPDATE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'risk_assessments', 'DELETE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'risk_assessments', 'TRUNCATE')")).scalar_one() is False


def test_audit_logs_table_permissions(db_admin_connection):
    """Verify audit_logs is append-only (SELECT, INSERT only)."""
    conn, db_name = db_admin_connection
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'audit_logs', 'SELECT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'audit_logs', 'INSERT')")).scalar_one() is True
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'audit_logs', 'UPDATE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'audit_logs', 'DELETE')")).scalar_one() is False
    assert conn.execute(text("SELECT has_table_privilege('payshield_app', 'audit_logs', 'TRUNCATE')")).scalar_one() is False
