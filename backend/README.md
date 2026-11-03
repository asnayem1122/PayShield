# PayShield Backend API

Educational Payment Fraud Risk Monitoring API built with FastAPI, PostgreSQL 18, SQLAlchemy 2.x, and Alembic.

---

## 1. Architecture & Security Separation

The backend employs strict principle of least privilege across database roles:

| Role | Responsibility | Grants | DDL Rights |
|---|---|---|---|
| `payshield_migrator` | Schema Owner & Alembic Migrations | Owns schema `public`, runs migrations | Full DDL |
| `payshield_app` | Runtime Application Service | Connect, Schema Usage, Default: SELECT, INSERT only | **Zero DDL** (No CREATE, DROP, ALTER) |

- **Zero Superuser at Runtime**: Application routes connect strictly as `payshield_app`.
- **Zero Table-Level UPDATE/DELETE/TRUNCATE**: Default privileges grant `SELECT` and `INSERT` only. Unrestricted table-level `UPDATE`, `DELETE`, and `TRUNCATE` are strictly denied.
- **Controlled Column-Level Updates**: Column-level updates on `transactions(transaction_status, updated_at)` and `analyst_cases(case_status, resolved_at, resolution_note, updated_at)` are granted specifically in Phase 2 migrations.
- **Merchant Read-Only Reconciliation**: `merchants` table is read-only at runtime for `payshield_app` (`INSERT` is revoked upon table creation in Phase 2). Merchant entities are seeded only via `payshield_migrator` during controlled provisioning.
- **Secret Safety**: Pydantic Settings wraps all passwords in `SecretStr`. Connection strings are parsed with `make_url()` or built with `URL.create()`, preventing logging, exception leakage, or URL-encoding corruption.
- **RFC 9457 Readiness**: The probe at `/api/v1/readiness` tests connectivity with `SELECT 1` and returns standard Problem Details (`application/problem+json`) upon failure without exposing credentials or driver internals.

---

## 2. Prerequisites & Dependencies

- Python: `3.14.8` (or `>=3.12`)
- PostgreSQL: `18.x` running on port `5432`
- Core packages (in `pyproject.toml` and locked in `requirements.lock`):
  - `fastapi>=0.115.0,<1.0.0`
  - `uvicorn[standard]>=0.30.0,<1.0.0`
  - `pydantic>=2.8.0,<3.0.0`
  - `pydantic-settings>=2.4.0,<3.0.0`
  - `sqlalchemy>=2.0.35,<3.0.0`
  - `alembic>=1.13.0,<2.0.0`
  - `psycopg[binary]>=3.2.0,<4.0.0`

---

## 3. Local Setup & Provisioning

### A. Environment Configuration

Copy the template:

```powershell
cp .env.example .env
```

Review `.env` to verify credentials match your local PostgreSQL configuration. `.env` is ignored by Git and must never be committed.

### B. Database & Role Provisioning

Execute the idempotent admin provisioning script (runs as PostgreSQL admin `postgres`):

```powershell
.\.venv\Scripts\python.exe scripts\provision_db.py
```

This creates:
- Databases: `payshield_dev`, `payshield_test`
- Roles: `payshield_migrator`, `payshield_app`
- Least-privilege schema permissions and default privileges.

---

## 4. Running the Application

Start the local development server:

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 5. Health & Readiness Verification

### Liveness Probe (Service Process Alive)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health"
```

Expected output:
```json
{"status": "healthy", "app": "PayShield API", "version": "0.1.0", "environment": "development"}
```

### Readiness Probe (Database Connectivity Verified)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/readiness"
```

Expected output (HTTP 200):
```json
{"status": "ready", "database": "connected"}
```

If PostgreSQL is stopped or unreachable, returns HTTP 503 with RFC 9457 Problem Details:
```json
{
  "type": "https://payshield.internal/errors/database-unavailable",
  "title": "Service Unavailable",
  "status": 503,
  "detail": "Database service is unavailable",
  "instance": "/api/v1/readiness"
}
```

---

## 6. Alembic Migrations

Alembic is configured in `alembic.ini` and `alembic/env.py` to use `payshield_migrator` credentials dynamically from Pydantic Settings.

Check migration status:

```powershell
.\.venv\Scripts\alembic.exe current
```

---

## 7. Automated Testing

Run the backend test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

---

## 8. Current Scope & Known Limitations (Phase 1)

- **Schema Models**: Tables (`merchants`, `transactions`, `risk_assessments`, `analyst_cases`, `audit_logs`) will be defined and migrated in Phase 2.
- **Seeding**: Canonical dataset seeding (`v1.0.1-canonical-remediated`) will occur in Phase 3.
