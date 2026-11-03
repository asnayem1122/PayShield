"""Database and role provisioning script for PayShield.

Provisions payshield_dev, payshield_test databases and payshield_migrator,
payshield_app roles with least-privilege permission boundaries.
"""

import os
import psycopg
from psycopg import sql

POSTGRES_HOST = os.getenv("POSTGRES_SERVER", "127.0.0.1")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
ADMIN_USER = os.getenv("ADMIN_POSTGRES_USER", "postgres")
ADMIN_PASSWORD = os.getenv("ADMIN_POSTGRES_PASSWORD", "")

MIGRATOR_USER = os.getenv("MIGRATION_POSTGRES_USER", "payshield_migrator")
MIGRATOR_PASSWORD = os.getenv(
    "MIGRATION_POSTGRES_PASSWORD", "payshield_migrator_insecure_dev_password"
)

APP_USER = os.getenv("POSTGRES_USER", "payshield_app")
APP_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD", "payshield_app_insecure_dev_password"
)

DATABASES = ["payshield_dev", "payshield_test"]


def run_provisioning() -> None:
    print(
        f"Connecting to PostgreSQL as admin ({ADMIN_USER}) on {POSTGRES_HOST}:{POSTGRES_PORT}..."
    )
    conn_params: dict[str, object] = {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "user": ADMIN_USER,
        "dbname": "postgres",
        "autocommit": True,
    }
    if ADMIN_PASSWORD:
        conn_params["password"] = ADMIN_PASSWORD

    with psycopg.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            # 1. Create or update migrator role
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (MIGRATOR_USER,))
            if not cur.fetchone():
                print(f"Creating role: {MIGRATOR_USER}...")
                cur.execute(
                    sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                        sql.Identifier(MIGRATOR_USER), sql.Literal(MIGRATOR_PASSWORD)
                    )
                )
            else:
                print(f"Role {MIGRATOR_USER} already exists. Updating password...")
                cur.execute(
                    sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(
                        sql.Identifier(MIGRATOR_USER), sql.Literal(MIGRATOR_PASSWORD)
                    )
                )

            # 2. Create or update app role
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (APP_USER,))
            if not cur.fetchone():
                print(f"Creating role: {APP_USER}...")
                cur.execute(
                    sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                        sql.Identifier(APP_USER), sql.Literal(APP_PASSWORD)
                    )
                )
            else:
                print(f"Role {APP_USER} already exists. Updating password...")
                cur.execute(
                    sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(
                        sql.Identifier(APP_USER), sql.Literal(APP_PASSWORD)
                    )
                )

            # 3. Create databases if not exists
            for db_name in DATABASES:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
                )
                if not cur.fetchone():
                    print(f"Creating database: {db_name} (owner: {MIGRATOR_USER})...")
                    cur.execute(
                        sql.SQL("CREATE DATABASE {} OWNER {}").format(
                            sql.Identifier(db_name), sql.Identifier(MIGRATOR_USER)
                        )
                    )
                else:
                    print(f"Database {db_name} already exists.")
                    cur.execute(
                        sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                            sql.Identifier(db_name), sql.Identifier(MIGRATOR_USER)
                        )
                    )

    # 4. Configure permissions in each target database
    for db_name in DATABASES:
        print(f"Configuring permissions on {db_name}...")
        db_conn_params = dict(conn_params)
        db_conn_params["dbname"] = db_name
        with psycopg.connect(**db_conn_params) as db_conn:
            with db_conn.cursor() as cur:
                # Revoke all from PUBLIC on public schema
                cur.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")

                # Connect privilege on DB
                cur.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                        sql.Identifier(db_name), sql.Identifier(MIGRATOR_USER)
                    )
                )
                cur.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                        sql.Identifier(db_name), sql.Identifier(APP_USER)
                    )
                )

                # Migrator schema grants
                cur.execute(
                    sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(
                        sql.Identifier(MIGRATOR_USER)
                    )
                )

                # App role schema grants (USAGE only, explicitly no CREATE)
                cur.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(
                        sql.Identifier(APP_USER)
                    )
                )
                cur.execute(
                    sql.SQL("REVOKE CREATE ON SCHEMA public FROM {}").format(
                        sql.Identifier(APP_USER)
                    )
                )

                # Default privileges for tables and sequences created by migrator:
                # 1. Reset any existing default privileges on tables to avoid permission drift
                cur.execute(
                    sql.SQL("""
                        ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public
                        REVOKE ALL ON TABLES FROM {}
                    """).format(
                        sql.Identifier(MIGRATOR_USER), sql.Identifier(APP_USER)
                    )
                )

                # 2. Grant ONLY SELECT and INSERT on future tables.
                # Strictly NO table-level UPDATE, DELETE, or TRUNCATE.
                # Note: Specific column-level UPDATE on 'transactions' and 'analyst_cases',
                # and runtime read-only lock (REVOKE INSERT) on 'merchants' are applied
                # post-migration in Phase 2 once table catalog objects exist.
                cur.execute(
                    sql.SQL("""
                        ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public
                        GRANT SELECT, INSERT ON TABLES TO {}
                    """).format(
                        sql.Identifier(MIGRATOR_USER), sql.Identifier(APP_USER)
                    )
                )

                # 3. Grant sequence USAGE and SELECT for autoincrementing ID generation
                cur.execute(
                    sql.SQL("""
                        ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public
                        GRANT USAGE, SELECT ON SEQUENCES TO {}
                    """).format(
                        sql.Identifier(MIGRATOR_USER), sql.Identifier(APP_USER)
                    )
                )

    print("PostgreSQL provisioning completed successfully.")


if __name__ == "__main__":
    run_provisioning()
