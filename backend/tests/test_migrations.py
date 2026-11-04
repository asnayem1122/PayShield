"""Destructive migration reversibility tests against disposable database only.

Verifies:
- Safe database identity check (refuses to run unless target is 'payshield_migration_test')
- alembic upgrade head creates all 5 tables and constraints
- alembic downgrade base drops all tables cleanly
- alembic upgrade head successfully re-creates schema
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


def test_migration_upgrade_downgrade_reversibility() -> None:
    """Test full migration lifecycle (upgrade -> downgrade -> upgrade) in disposable DB."""
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

        # 2. Upgrade to head
        command.upgrade(alembic_cfg, "head")

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

        # 3. Verify check constraints exist on transactions
        check_constraints = [ck["name"] for ck in inspector.get_check_constraints("transactions")]
        assert any("score_level" in ck for ck in check_constraints), f"score_level constraint missing in {check_constraints}"
        assert any("level_action" in ck for ck in check_constraints), f"level_action constraint missing in {check_constraints}"

        # 4. Destructive downgrade to base
        command.downgrade(alembic_cfg, "base")

        inspector_after_downgrade = inspect(engine)
        remaining_tables = set(inspector_after_downgrade.get_table_names())
        assert not remaining_tables.intersection(expected_tables), (
            f"Tables remained after downgrade: {remaining_tables.intersection(expected_tables)}"
        )

        # 5. Re-upgrade to head
        command.upgrade(alembic_cfg, "head")

        inspector_reupgrade = inspect(engine)
        reup_tables = set(inspector_reupgrade.get_table_names())
        assert expected_tables.issubset(reup_tables), "Re-upgrade failed to restore all tables"

    finally:
        engine.dispose()
