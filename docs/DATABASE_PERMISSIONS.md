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
| **Table `users`** | `ALL PRIVILEGES` | `SELECT`, `INSERT`, `UPDATE(password_hash, full_name, failed_login_attempts, locked_until, last_login_at, updated_at)` | `NO PRIVILEGES` |
| **Table `auth_sessions`** | `ALL PRIVILEGES` | `SELECT`, `INSERT`, `UPDATE(last_used_at, revoked_at)` | `NO PRIVILEGES` |
| **Sequences** | `ALL PRIVILEGES` | `NO PRIVILEGES` (UUIDs use `gen_random_uuid()`) | `NO PRIVILEGES` |

---

## 3. SQL Permission Hardening Script

The following exact SQL commands are applied via Alembic migrations (`0001_initial_schema.py`, `0002_revoke_assigned_analyst_update.py`, and `0003_create_users_table.py`):

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
REVOKE ALL PRIVILEGES ON TABLE users FROM payshield_app;
REVOKE ALL PRIVILEGES ON TABLE auth_sessions FROM payshield_app;

-- Table SELECT Grants
GRANT SELECT ON TABLE merchants TO payshield_app;
GRANT SELECT ON TABLE transactions TO payshield_app;
GRANT SELECT ON TABLE risk_assessments TO payshield_app;
GRANT SELECT ON TABLE analyst_cases TO payshield_app;
GRANT SELECT ON TABLE audit_logs TO payshield_app;
GRANT SELECT ON TABLE users TO payshield_app;
GRANT SELECT ON TABLE auth_sessions TO payshield_app;

-- Table INSERT Grants (merchants is read-only at runtime)
GRANT INSERT ON TABLE transactions TO payshield_app;
GRANT INSERT ON TABLE risk_assessments TO payshield_app;
GRANT INSERT ON TABLE analyst_cases TO payshield_app;
GRANT INSERT ON TABLE audit_logs TO payshield_app;
GRANT INSERT ON TABLE users TO payshield_app;
GRANT INSERT ON TABLE auth_sessions TO payshield_app;

-- Column-Level UPDATE Grants (explicitly revoke table-level UPDATE first)
REVOKE UPDATE ON TABLE transactions FROM payshield_app;
REVOKE UPDATE ON TABLE analyst_cases FROM payshield_app;
REVOKE UPDATE ON TABLE users FROM payshield_app;
REVOKE UPDATE ON TABLE auth_sessions FROM payshield_app;

GRANT UPDATE (transaction_status, updated_at) ON TABLE transactions TO payshield_app;
GRANT UPDATE (case_status, resolution_note, resolved_at, updated_at) ON TABLE analyst_cases TO payshield_app;
GRANT UPDATE (password_hash, full_name, failed_login_attempts, locked_until, last_login_at, updated_at) ON TABLE users TO payshield_app;
GRANT UPDATE (last_used_at, revoked_at) ON TABLE auth_sessions TO payshield_app;
```

---

## 4. Verification Evidence

The least-privilege security model is continuously validated via automated tests in `backend/tests/`:
- `test_permissions.py`: Baseline privileges and denial of DDL (CREATE/DROP TABLE).
- `test_permissions_phase2.py`: Denial of role inheritance, denial of table UPDATE/DELETE/TRUNCATE across transactions, merchants, analyst cases, risk assessments, and audit logs.
- `test_permissions_phase3.py`: Verification that `payshield_app` has column-level UPDATE strictly on mutable profile/security fields of `users` and `auth_sessions`, and is denied UPDATE on identity/role columns (`id`, `email`, `role`, `merchant_id`).
