# PayShield PostgreSQL Permissions & Security Hardening Specification

## 1. Security Architecture

The PayShield persistence model enforces least privilege directly in PostgreSQL 18. The application service connects under the unprivileged role `payshield_app`, while schema modifications are managed by `payshield_migrator`.

---

## 2. PostgreSQL Role Privilege Matrix

| Object | `payshield_migrator` | `payshield_app` | `PUBLIC` |
|---|---|---|---|
| **Database `payshield_*`** | `ALL PRIVILEGES` | `CONNECT` | `NO PRIVILEGES` (revoked) |
| **Schema `public`** | `ALL PRIVILEGES`, Owner | `USAGE` | `NO PRIVILEGES` (revoked) |
| **Table `merchants`** | `ALL PRIVILEGES` | `SELECT` only | `NO PRIVILEGES` |
| **Table `transactions`** | `ALL PRIVILEGES` | `SELECT`, `INSERT`, `UPDATE(transaction_status, updated_at)` | `NO PRIVILEGES` |
| **Table `risk_assessments`** | `ALL PRIVILEGES` | `SELECT`, `INSERT` (append-only) | `NO PRIVILEGES` |
| **Table `analyst_cases`** | `ALL PRIVILEGES` | `SELECT`, `INSERT`, `UPDATE(case_status, resolution_note, resolved_at, updated_at)` | `NO PRIVILEGES` |
| **Table `audit_logs`** | `ALL PRIVILEGES` | `SELECT`, `INSERT` (append-only) | `NO PRIVILEGES` |
| **Sequences** | `ALL PRIVILEGES` | `NO PRIVILEGES` (UUIDs use `gen_random_uuid()`) | `NO PRIVILEGES` |

---

## 3. SQL Permission Hardening Script

The following exact SQL commands are applied via `backend/scripts/provision_db.py` and `backend/alembic/versions/0001_initial_schema.py`:

```sql
-- Revoke PUBLIC default privileges
REVOKE ALL ON DATABASE payshield_dev FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Connect as payshield_migrator
-- Table Level Revocations
REVOKE ALL PRIVILEGES ON TABLE merchants FROM payshield_app;
REVOKE ALL PRIVILEGES ON TABLE transactions FROM payshield_app;
REVOKE ALL PRIVILEGES ON TABLE risk_assessments FROM payshield_app;
REVOKE ALL PRIVILEGES ON TABLE analyst_cases FROM payshield_app;
REVOKE ALL PRIVILEGES ON TABLE audit_logs FROM payshield_app;

-- Table SELECT Grants
GRANT SELECT ON TABLE merchants TO payshield_app;
GRANT SELECT ON TABLE transactions TO payshield_app;
GRANT SELECT ON TABLE risk_assessments TO payshield_app;
GRANT SELECT ON TABLE analyst_cases TO payshield_app;
GRANT SELECT ON TABLE audit_logs TO payshield_app;

-- Table INSERT Grants (merchants is read-only at runtime)
GRANT INSERT ON TABLE transactions TO payshield_app;
GRANT INSERT ON TABLE risk_assessments TO payshield_app;
GRANT INSERT ON TABLE analyst_cases TO payshield_app;
GRANT INSERT ON TABLE audit_logs TO payshield_app;

-- Column-Level UPDATE Grants (explicitly revoke table-level UPDATE first)
REVOKE UPDATE ON TABLE transactions FROM payshield_app;
REVOKE UPDATE ON TABLE analyst_cases FROM payshield_app;

GRANT UPDATE (transaction_status, updated_at) ON TABLE transactions TO payshield_app;
GRANT UPDATE (case_status, resolution_note, resolved_at, updated_at) ON TABLE analyst_cases TO payshield_app;
```

> **Security Note on Case Assignment Immutability:**
> In accordance with least-privilege security specifications, `assigned_analyst` is immutable at runtime for `payshield_app`. Analysts cannot alter the assigned analyst of an existing case via standard API updates. Case ownership is assigned at creation or managed exclusively via administrative/system workflows. This immutability is formally enforced via Alembic migration `0002_revoke_assigned_analyst_update.py` (`revision = "0002_revoke_analyst_update"`).

---

## 4. Alembic Migration History & Permission Reversibility

1. **`0001_initial_schema.py` (`0001_initial_schema`)**:
   - Creates the initial five core tables (`merchants`, `transactions`, `risk_assessments`, `analyst_cases`, `audit_logs`).
   - Applies initial least-privilege grants to `payshield_app` (SELECT on all tables, INSERT on transactions/assessments/cases/audit_logs, column-level UPDATE on transactions and analyst cases).
   - Preserves original historical grant containing `assigned_analyst`.

2. **`0002_revoke_assigned_analyst_update.py` (`0002_revoke_analyst_update`)**:
   - Executes `REVOKE UPDATE (assigned_analyst) ON TABLE analyst_cases FROM payshield_app;` on upgrade.
   - Executes `GRANT UPDATE (assigned_analyst) ON TABLE analyst_cases TO payshield_app;` on downgrade.
   - Tested for full reversibility (`0001` -> `0002` -> `0001` -> `base` -> `head`) with safety guards against non-disposable databases (`backend/tests/test_migrations.py`).

---

## 5. Automated Verification

Every rule in this specification is continuously verified by `backend/tests/test_permissions_phase2.py` across both `payshield_dev` and `payshield_test`:
- `pg_auth_members = 0` (no role inheritance).
- `has_database_privilege('public', current_database(), 'CREATE') = False`.
- `has_table_privilege('payshield_app', 'merchants', 'INSERT') = False`.
- `has_column_privilege('payshield_app', 'transactions', 'amount', 'UPDATE') = False`.
- `has_column_privilege('payshield_app', 'analyst_cases', 'trigger_reason', 'UPDATE') = False`.
- `DELETE` and `TRUNCATE` evaluate to `False` across all 5 tables.
