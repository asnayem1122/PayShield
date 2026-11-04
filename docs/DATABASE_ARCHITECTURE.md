# PayShield Database Architecture Specification

## 1. System Overview

PayShield utilizes **PostgreSQL 18** as its primary persistent relational database, deployed locally on port `5432`. The persistence layer is designed with strict least-privilege security boundaries, environment isolation, and transactional integrity.

### Architectural Principles

1. **Role-Based Privilege Separation**: DDL operations are strictly isolated to `payshield_migrator`, while runtime application services operate under `payshield_app`.
2. **Environment Isolation**: Three distinct, non-overlapping databases are maintained:
   - `payshield_dev`: Persistent development and demonstration environment populated with the verified 175-transaction canonical dataset.
   - `payshield_test`: Clean test environment reserved for transactional integration tests.
   - `payshield_migration_test`: Disposable, isolated database exclusively used for full Alembic migration downgrade/upgrade reversibility tests.
3. **Immutability & Auditability**: Risk evaluations and system audit logs are architecturally append-only. No `UPDATE`, `DELETE`, or `TRUNCATE` operations are permitted on these tables.
4. **Data Integrity via PostgreSQL Constraints**: Domain invariants (such as risk score bands, status transitions, and positive monetary amounts) are enforced at the database engine level via `CHECK` constraints.

---

## 2. PostgreSQL Topology & Environments

| Environment | Database Name | Purpose | Seeding Lifecycle |
|---|---|---|---|
| Development | `payshield_dev` | Local development, interactive API, Flutter live sync | Seeded with 175 canonical transactions (exact-match verified) |
| Test | `payshield_test` | Automated integration and regression test execution | Transactional rollback test harness |
| Migration Test | `payshield_migration_test` | Alembic upgrade/downgrade full cycle verification | Disposable; created and dropped during migration testing |

---

## 3. Database Role Separation & Least Privilege Model

PostgreSQL enforces two distinct service roles:

```
+-------------------------------------------------------------------+
|                        PostgreSQL 18                              |
+-------------------------------------------------------------------+
            |                                           |
            v                                           v
[ payshield_migrator ]                         [ payshield_app ]
  - Schema Owner                                 - Runtime Application Role
  - Full DDL (CREATE, ALTER, DROP)               - Unprivileged leaf role (no memberships)
  - Full DML on all tables                       - DML strictly restricted:
  - Grants privileges to payshield_app             * merchants: SELECT only (read-only)
                                                   * transactions: SELECT, INSERT, 
                                                     UPDATE(transaction_status, updated_at) only
                                                   * analyst_cases: SELECT, INSERT,
                                                     UPDATE(case_status, assigned_analyst, 
                                                            resolution_note, resolved_at, 
                                                            updated_at) only
                                                   * risk_assessments: SELECT, INSERT (append-only)
                                                   * audit_logs: SELECT, INSERT (append-only)
                                                   * Zero DELETE, TRUNCATE, or DDL
```

---

## 4. Connection Pooling & Synchronous Lifecycle

- **Driver**: `psycopg` (Psycopg 3 binary).
- **ORM**: SQLAlchemy 2.x Declarative Base.
- **Engine Configuration**:
  - `pool_size`: 5
  - `max_overflow`: 10
  - `pool_timeout`: 30s
  - `pool_pre_ping`: True (automatically tests connection liveliness before handing to session)
- **Session Management**: Scoped per-request generator (`get_db`) with automatic commit/rollback and clean engine disposal on application shutdown.
