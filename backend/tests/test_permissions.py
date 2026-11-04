"""Automated PostgreSQL permission tests for PayShield.

Verifies least-privilege boundary for payshield_app and payshield_migrator:
- payshield_app is granted SELECT and INSERT only on future tables via default privileges.
- payshield_app is denied UPDATE, DELETE, TRUNCATE, and DDL (CREATE/DROP TABLE).
- payshield_migrator is verified as schema owner with DDL privileges.
"""

from collections.abc import Generator
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings

# Skip these tests if not running against real PostgreSQL (e.g. SQLite override)
pytestmark = pytest.mark.skipif(
    str(settings.get_sqlalchemy_url()).startswith("sqlite"),
    reason="PostgreSQL permission verification requires real PostgreSQL instance",
)


@pytest.fixture(scope="module")
def migrator_engine():
    """SQLAlchemy engine connected as payshield_migrator."""
    eng = create_engine(settings.get_migration_sqlalchemy_url())
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def app_engine():
    """SQLAlchemy engine connected as payshield_app."""
    eng = create_engine(settings.get_sqlalchemy_url())
    yield eng
    eng.dispose()


@pytest.fixture
def probe_table(migrator_engine) -> Generator[str, None, None]:
    """Create a temporary probe table using payshield_migrator to test default privileges."""
    table_name = "_perm_probe_table"
    with migrator_engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.execute(
            text(
                f"CREATE TABLE {table_name} (id uuid primary key default gen_random_uuid(), note text, counter int)"
            )
        )
        conn.execute(
            text(f"INSERT INTO {table_name} (note, counter) VALUES ('seed_data', 10)")
        )

    yield table_name

    with migrator_engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))


def test_default_privileges_catalog_entry(app_engine) -> None:
    """Verify pg_default_acl contains only SELECT (r) and INSERT (a) for payshield_app."""
    with app_engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT defaclobjtype, defaclacl::text
                FROM pg_default_acl
                WHERE defaclrole = 'payshield_migrator'::regrole
                  AND defaclnamespace = 'public'::regnamespace
                """
            )
        ).fetchall()

        # Build mapping of object type to acl string: 'r' = tables, 'S' = sequences
        acl_map = {row[0]: row[1] for row in result}

        # Table default privileges
        assert "r" in acl_map, "Expected default privileges on tables ('r')"
        table_acl = acl_map["r"]
        assert "payshield_app=ar/payshield_migrator" in table_acl
        # Explicitly verify 'w' (UPDATE), 'd' (DELETE), 'D' (TRUNCATE) are NOT granted
        priv_str = table_acl.split("=")[1].split("/")[0]
        assert "w" not in priv_str, "UPDATE ('w') must NOT be present in table default privileges"
        assert "d" not in priv_str, "DELETE ('d') must NOT be present in table default privileges"
        assert "D" not in priv_str, "TRUNCATE ('D') must NOT be present in table default privileges"

        # Sequence default privileges (UUID PKs use gen_random_uuid(), no sequences needed)
        seq_acl = acl_map.get("S", "")
        assert "payshield_app" not in seq_acl, "Sequence privileges should NOT be granted to payshield_app"


def test_test_database_default_privileges_catalog_entry() -> None:
    """Verify pg_default_acl in payshield_test contains only SELECT (r) and INSERT (a)."""
    test_db_url = settings.get_sqlalchemy_url().set(database="payshield_test")
    test_engine = create_engine(test_db_url)
    try:
        with test_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT defaclobjtype, defaclacl::text
                    FROM pg_default_acl
                    WHERE defaclrole = 'payshield_migrator'::regrole
                      AND defaclnamespace = 'public'::regnamespace
                    """
                )
            ).fetchall()

            acl_map = {row[0]: row[1] for row in result}
            assert "r" in acl_map, "Expected default privileges on tables in payshield_test"
            table_acl = acl_map["r"]
            assert "payshield_app=ar/payshield_migrator" in table_acl
            priv_str = table_acl.split("=")[1].split("/")[0]
            assert "w" not in priv_str, "UPDATE must not be in default privileges in payshield_test"
            assert "d" not in priv_str, "DELETE must not be in default privileges in payshield_test"
            assert "D" not in priv_str, "TRUNCATE must not be in default privileges in payshield_test"

            seq_acl = acl_map.get("S", "")
            assert "payshield_app" not in seq_acl, "Sequence privileges should NOT be granted to payshield_app in payshield_test"
    finally:
        test_engine.dispose()


def test_app_can_select(app_engine, probe_table: str) -> None:
    """Verify payshield_app can execute SELECT queries."""
    with app_engine.connect() as conn:
        rows = conn.execute(text(f"SELECT note, counter FROM {probe_table}")).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "seed_data"
        assert rows[0][1] == 10


def test_app_can_insert(app_engine, probe_table: str) -> None:
    """Verify payshield_app can execute INSERT queries."""
    with app_engine.begin() as conn:
        conn.execute(
            text(f"INSERT INTO {probe_table} (note, counter) VALUES ('app_insert', 20)")
        )

    with app_engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT note FROM {probe_table} WHERE note = 'app_insert'")
        ).fetchall()
        assert len(rows) == 1


def test_app_cannot_update(app_engine, probe_table: str) -> None:
    """Verify payshield_app is DENIED unrestricted table-level UPDATE."""
    with pytest.raises(ProgrammingError) as exc_info:
        with app_engine.begin() as conn:
            conn.execute(
                text(f"UPDATE {probe_table} SET note = 'unauthorized_update'")
            )
    assert "permission denied" in str(exc_info.value).lower()


def test_app_cannot_delete(app_engine, probe_table: str) -> None:
    """Verify payshield_app is DENIED DELETE queries."""
    with pytest.raises(ProgrammingError) as exc_info:
        with app_engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {probe_table}"))
    assert "permission denied" in str(exc_info.value).lower()


def test_app_cannot_truncate(app_engine, probe_table: str) -> None:
    """Verify payshield_app is DENIED TRUNCATE queries."""
    with pytest.raises(ProgrammingError) as exc_info:
        with app_engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {probe_table}"))
    assert "permission denied" in str(exc_info.value).lower()


def test_app_cannot_ddl_create_table(app_engine) -> None:
    """Verify payshield_app is DENIED CREATE TABLE DDL."""
    with pytest.raises(ProgrammingError) as exc_info:
        with app_engine.begin() as conn:
            conn.execute(text("CREATE TABLE _unauthorized_table (id int)"))
    assert "permission denied" in str(exc_info.value).lower()


def test_app_cannot_ddl_drop_table(app_engine, probe_table: str) -> None:
    """Verify payshield_app is DENIED DROP TABLE DDL."""
    with pytest.raises(ProgrammingError) as exc_info:
        with app_engine.begin() as conn:
            conn.execute(text(f"DROP TABLE {probe_table}"))
    err_str = str(exc_info.value).lower()
    assert "permission denied" in err_str or "must be owner" in err_str
