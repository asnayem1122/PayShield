# PayShield REST API Documentation

## 1. Overview

The PayShield FastAPI service exposes a REST API at `/api/v1` for payment transaction ingestion, risk evaluation, fraud investigation workflows, authentication, and live dashboard analytics.

- **Base URL (Local)**: `http://127.0.0.1:8000/api/v1`
- **Android Emulator Base URL**: `http://10.0.2.2:8000/api/v1`
- **CORS**: Enabled with `allow_origins=["*"]` for Flutter Web, Desktop, and Mobile clients.

---

## 2. Wire Contract & Decimal Currency Specification

### 2.1. Strict 2-Decimal String Wire Format
To prevent IEEE 754 floating-point inaccuracies, monetary amounts are transmitted over JSON strictly as strings matching the regular expression:
```regex
^\d{1,10}\.\d{2}$
```
- Raw JSON numbers (e.g. `1250.5` or `1250.0`) are strictly rejected with HTTP 422 Unprocessable Entity.
- Valid wire examples: `"1250.00"`, `"1514.00"`, `"280200.00"`.

---

## 3. Authentication & Server-Side Authorization (RBAC)

All sensitive endpoints require a JSON Web Token (JWT) transmitted via standard HTTP header:
```http
Authorization: Bearer <access_token>
```

### 3.1. Role Matrix
| Role | Scoping / Permissions | Restricted Endpoints |
|---|---|---|
| `MERCHANT` | Scoped strictly to own `merchant_id`. Can ingest own transactions, view own transactions, view own dashboard summary. | `/cases/*` (403), `/audit/*` (403), `PATCH /transactions/*/status` (403), other merchants' transactions (404 anti-enumeration). |
| `ANALYST` | System-wide visibility. Full access to `/cases/*`, `/transactions/*`, `/dashboard/*`, `/risk/*`, `/audit/*`. Can update case status and transaction status. | User management. |
| `ADMIN` | Super-administrative access across all tenant records, audit logs, system configurations. | None. |

### 3.2. Canonical Demo Accounts
- **Merchant**: `merchant@techpulse.bd` (Linked to PayShield Demo Merchant)
- **Analyst**: `analyst.shafiq@payshield.internal` (Unlinked)
- **Admin**: `admin.nayem@payshield.internal` (Unlinked)
- **Credential Provisioning**: Configured via environment variables (`PAYSHIELD_MERCHANT_PASSWORD`, `PAYSHIELD_ANALYST_PASSWORD`, `PAYSHIELD_ADMIN_PASSWORD`). No static passwords are committed to source control.

---

## 4. Endpoints

### 4.1. Authentication (`/auth`)

#### `POST /api/v1/auth/login`
Authenticate user with email and password, issuing an access and refresh token pair.
- **Request Body**:
  ```json
  {
    "email": "merchant@techpulse.bd",
    "password": "<ACCOUNT_PASSWORD>"
  }
  ```
- **Response 200**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "id": "e6f42da1-...",
      "email": "merchant@techpulse.bd",
      "full_name": "TechPulse Demo Merchant",
      "role": "MERCHANT",
      "status": "ACTIVE",
      "merchant_id": "908d0e51-...",
      "merchant_name": "PayShield Demo Merchant"
    }
  }
  ```
- **Response 401 (RFC 9457)**: Invalid credentials. Generic message (`"Invalid email or password"`) and constant-time dummy verification for unknown and suspended accounts to completely prevent account enumeration.
- **Response 423 (RFC 9457)**: Account locked due to 5 consecutive failed attempts.
- **Response 429 (RFC 9457)**: Rate limit exceeded (10 attempts per minute per IP address).

#### `GET /api/v1/auth/me`
Retrieve identity and profile for the authenticated user.
- **Headers**: `Authorization: Bearer <access_token>`
- **Response 200**: Returns `UserProfileResponse` with timestamps and merchant linkage.

#### `POST /api/v1/auth/refresh`
Exchange an active refresh token for a newly issued access token and rotated refresh token.
- **Request Body**: `{"refresh_token": "..."}`
- **Security Policy**:
  - Refresh token rotation with atomic database row lock (`with_for_update()`).
  - Session family isolation (`family_id`): Replay detection revokes only the compromised device's session lineage, keeping unrelated device sessions intact.

#### `POST /api/v1/auth/logout`
Revoke active session(s) upon logout.
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body (Optional)**: `{"refresh_token": "..."}`
- **Security Policy**: Revokes only the authenticated device's session family when a refresh token is supplied.
- **Response 200**: `{"status": "success", "message": "Successfully logged out"}`

---

### 4.2. System Health & Readiness

#### `GET /health` / `GET /api/v1/health`
Process liveness probe.
- **Response 200**:
  ```json
  {
    "status": "healthy",
    "app": "PayShield API",
    "version": "0.1.0",
    "environment": "development"
  }
  ```

#### `GET /api/v1/readiness`
Database connectivity probe.
- **Response 200**:
  ```json
  {
    "status": "ready",
    "database": "connected"
  }
  ```
- **Response 503 (RFC 9457 Problem Details)**:
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

### 4.3. Dashboard Aggregations

#### `GET /api/v1/dashboard/summary`
Calculates live database aggregations (scoped to merchant when authenticated as Merchant).
- **Headers**: `Authorization: Bearer <access_token>`
- **Response 200**:
  ```json
  {
    "total_volume": "482500.00",
    "approved_volume": "280200.00",
    "review_volume": "147300.00",
    "flagged_volume": "147300.00",
    "blocked_volume": "55000.00",
    "total_transactions": 175,
    "approved_count": 158,
    "review_count": 14,
    "flagged_count": 14,
    "blocked_count": 3,
    "open_cases_count": 14,
    "average_risk_score": 38.65,
    "high_risk_ratio": 0.0171
  }
  ```

#### `GET /api/v1/dashboard/risk-distribution`
Risk tier breakdown (LOW, MEDIUM, HIGH).
- **Headers**: `Authorization: Bearer <access_token>`
- **Response 200**:
  ```json
  {
    "low_count": 158,
    "medium_count": 14,
    "high_count": 3,
    "total_count": 175
  }
  ```

#### `GET /api/v1/dashboard/recent-transactions`
Recent transaction list (default limit 10).
- **Headers**: `Authorization: Bearer <access_token>`

---

### 4.4. Transactions

#### `GET /api/v1/transactions`
List paginated transactions. When authenticated as MERCHANT, automatically isolated to user's `merchant_id`.
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `status`: `APPROVED`, `REVIEW`, `BLOCKED`
  - `risk_level`: `LOW`, `MEDIUM`, `HIGH`
  - `query`: Text search on counterparty, reference, or city
  - `limit`: 50 (max 200)
  - `offset`: 0

#### `GET /api/v1/transactions/{reference}`
Retrieve details for a single transaction.
- **Headers**: `Authorization: Bearer <access_token>`
- **Tenant Isolation**: If requested transaction belongs to another merchant, returns 404 Not Found to prevent enumeration.

#### `POST /api/v1/transactions`
Submit a payment transaction for real-time risk assessment and ingestion.
- **Headers**: `Authorization: Bearer <access_token>`
- **Tenant Isolation**: For Merchant users, `merchant_id` is automatically forced to the user's authentic `merchant_id`.
- **Request Body**:
  ```json
  {
    "counterparty_name": "Daraz Bangladesh Ltd",
    "amount": "1250.00",
    "currency": "BDT",
    "channel": "MOBILE_APP",
    "device_model": "Samsung Galaxy A53",
    "location_city": "Dhaka",
    "is_location_anomaly": false,
    "is_new_device": false,
    "has_high_velocity": false,
    "has_prior_chargebacks": false
  }
  ```

#### `PATCH /api/v1/transactions/{reference}/status`
Update transaction status (restricted to `ANALYST` and `ADMIN`).
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
  ```json
  {
    "status": "APPROVED",
    "notes": "Verified legitimate customer transaction.",
    "actor_id": "analyst_shafiq"
  }
  ```

---

### 4.5. Analyst Cases

#### `GET /api/v1/cases`
Paginated fraud investigation cases with embedded transaction metadata (restricted to `ANALYST` and `ADMIN`).
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `status`: `OPEN`, `IN_REVIEW`, `RESOLVED`
  - `priority`: `LOW`, `MEDIUM`, `HIGH`
  - `limit`: 50
  - `offset`: 0

#### `GET /api/v1/cases/{case_id}`
Retrieve details for a specific case (restricted to `ANALYST` and `ADMIN`).
- **Headers**: `Authorization: Bearer <access_token>`

#### `PATCH /api/v1/cases/{case_id}`
Update analyst investigation workflow (restricted to `ANALYST` and `ADMIN`).
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
  ```json
  {
    "case_status": "IN_REVIEW",
    "resolution_note": "Investigating device fingerprint anomalies."
  }
  ```

---

### 4.6. Risk Policy

#### `GET /api/v1/risk/indicators`
Metadata describing heuristic scoring rules, weights, and thresholds.
- **Headers**: `Authorization: Bearer <access_token>`

#### `POST /api/v1/risk/assess`
Dry-run heuristic risk evaluation without persisting transaction.
- **Headers**: `Authorization: Bearer <access_token>`

---

### 4.7. Audit Log

#### `GET /api/v1/audit/logs`
Retrieve immutable audit trail entries (restricted to `ADMIN` and `ANALYST`).
- **Headers**: `Authorization: Bearer <access_token>`
