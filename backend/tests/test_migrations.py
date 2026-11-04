"""Destructive migration reversibility tests against disposable database only.

Verifies:
- Safe database identity check (refuses to run unless target is 'payshield_migration_test')
- alembic upgrade 0001 creates all 5 tables and grants initial column-level permissions
- alembic upgrade 0002 revokes UPDATE on assigned_analyst while preserving approved columns
- alembic downgrade to 0001 restores assigned_analyst UPDATE without dropping data/tables
- alembic downgrade to base drops all tables cleanly
- alembic upgrade head successfully re-creates schema and applies final permissions
"""

from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command

from app.core.config import settings

MIGRATION_TEST_DB = "payshield_migration_test"
BACKEND_DIR = Path(__file__).resolve().parent.parent


def get_migration_test_engine():
    """Create engine pointing to payshield_migration_test as payshield_migrator."""
    mig_url = settings.get_migration_sqlalchemy_url().set(database=MIGRATION_TEST_DB)
    return create_engine(mig_url)


def assert_disposable_migration_database(engine) -> None:
    """Enforce strict guard: refuse destructive downgrade unless target is payshield_migration_test."""
    current_db = engine.url.database
    if current_db != MIGRATION_TEST_DB:
        raise RuntimeError(
            f"SAFETY ABORT: Destructive migration tests are strictly restricted to '{MIGRATION_TEST_DB}'. "
            f"Attempted execution against '{current_db}' was aborted to protect test data."
        )


def test_safety_guard_rejects_non_disposable_database():
    """Verify safety guard raises RuntimeError if attempted on non-disposable database."""
    dev_url = settings.get_migration_sqlalchemy_url().set(database="payshield_dev")
    dev_engine = create_engine(dev_url)
    with pytest.raises(RuntimeError) as exc_info:
        assert_disposable_migration_database(dev_engine)
    assert "SAFETY ABORT" in str(exc_info.value)
    assert "payshield_dev" in str(exc_info.value)
    dev_engine.dispose()


def test_migration_upgrade_downgrade_reversibility() -> None:
    """Test full migration lifecycle (upgrade -> forward migration 0002 -> downgrade -> downgrade base) in disposable DB."""
    engine = get_migration_test_engine()
    assert_disposable_migration_database(engine)

    # Configure Alembic to use the disposable migration test database
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option(
        "sqlalchemy.url", engine.url.render_as_string(hide_password=False)
    )

    try:
        # 1. Clean slate downgrade to base if previously applied
        command.downgrade(alembic_cfg, "base")

        # 2. Upgrade to migration 0001
        command.upgrade(alembic_cfg, "0001_initial_schema")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected_tables = {
            "merchants",
            "transactions",
            "risk_assessments",
            "analyst_cases",
            "audit_logs",
        }
        assert expected_tables.issubset(tables), f"Expected tables missing: {expected_tables - tables}"

        # In 0001, assigned_analyst UPDATE was originally granted
        with engine.connect() as conn:
            priv_0001 = conn.execute(
                text("SELECT has_column_privilege('payshield_app', 'analyst_cases', 'assigned_analyst', 'UPDATE')")
            ).scalar()
            assert priv_0001 is True, "Migration 0001 should grant UPDATE on assigned_analyst"

        # 3. Upgrade forward to migration 0002 (head)
        command.upgrade(alembic_cfg, "head")

        with engine.connect() as conn:
            priv_0002 = conn.execute(
                text("SELECT has_column_privilege('payshield_app', 'analyst_cases', 'assigned_analyst', 'UPDATE')")
            ).scalar()
            assert priv_0002 is False, "Migration 0002 must revoke UPDATE on assigned_analyst"

            # Verify approved columns still have UPDATE
            for col in ["case_status", "resolution_note", "resolved_at", "updated_at"]:
                has_priv = conn.execute(
                    text(f"SELECT has_column_privilege('payshield_app', 'analyst_cases', '{col}', 'UPDATE')")
                ).scalar()
                assert has_priv is True, f"Migration 0002 must preserve UPDATE on {col}"

        # 4. Downgrade migration 0002 back to 0001
        command.downgrade(alembic_cfg, "0001_initial_schema")

        with engine.connect() as conn:
            priv_reverted = conn.execute(
                text("SELECT has_column_privilege('payshield_app', 'analyst_cases', 'assigned_analyst', 'UPDATE')")
            ).scalar()
            assert priv_reverted is True, "Downgrading 0002 must restore UPDATE on assigned_analyst"

        # 5. Full downgrade to base
        command.downgrade(alembic_cfg, "base")

        inspector_after_downgrade = inspect(engine)
        remaining_tables = set(inspector_after_downgrade.get_table_names())
        assert not remaining_tables.intersection(expected_tables), (
            f"Tables remained after downgrade: {remaining_tables.intersection(expected_tables)}"
        )

        # 6. Re-upgrade from base all the way to head
        command.upgrade(alembic_cfg, "head")

        inspector_reupgrade = inspect(engine)
        reup_tables = set(inspector_reupgrade.get_table_names())
        assert expected_tables.issubset(reup_tables), "Re-upgrade failed to restore all tables"

        with engine.connect() as conn:
            priv_final = conn.execute(
                text("SELECT has_column_privilege('payshield_app', 'analyst_cases', 'assigned_analyst', 'UPDATE')")
            ).scalar()
            assert priv_final is False, "Final head state must have UPDATE on assigned_analyst revoked"

    finally:
        engine.dispose()
