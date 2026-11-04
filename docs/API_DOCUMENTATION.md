# PayShield REST API Documentation

## 1. Overview

The PayShield FastAPI service exposes a REST API at `/api/v1` for payment transaction ingestion, risk evaluation, fraud investigation workflows, and live dashboard analytics.

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

## 3. Endpoints

### 3.1. System Health & Readiness

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

### 3.2. Dashboard Aggregations

#### `GET /api/v1/dashboard/summary`
Calculates live database aggregations.
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
    "average_risk_score": 25.17,
    "high_risk_ratio": 0.0171
  }
  ```

#### `GET /api/v1/dashboard/risk-distribution`
Risk tier breakdown.
- **Response 200**:
  ```json
  {
    "low_count": 158,
    "medium_count": 14,
    "high_count": 3,
    "total_count": 175
  }
  ```

#### `GET /api/v1/dashboard/recent-transactions?limit=10`
Returns the 10 most recent transactions.

---

### 3.3. Transactions

#### `GET /api/v1/transactions`
List transactions with optional filtering and pagination.
- **Query Parameters**:
  - `status`: `APPROVED`, `REVIEW`, `BLOCKED`
  - `risk_level`: `LOW`, `MEDIUM`, `HIGH`
  - `query`: Text search across reference, counterparty name, and location
  - `limit`: Default `50` (1-200)
  - `offset`: Default `0`

#### `GET /api/v1/transactions/{reference}`
Retrieve full details of a specific transaction.

#### `POST /api/v1/transactions`
Submit a payment transaction for real-time risk assessment and ingestion.
- **Request Body**:
  ```json
  {
    "counterparty_name": "Rahim Electronics",
    "amount": "15000.00",
    "currency": "BDT",
    "channel": "MOBILE_APP",
    "device_model": "Xiaomi Redmi Note 11",
    "location_city": "Dhaka",
    "is_location_anomaly": false,
    "is_new_device": true,
    "has_high_velocity": false,
    "has_prior_chargebacks": false
  }
  ```
- **Response 201**: Created `TransactionResponse` with computed `risk_score`, `risk_level`, `recommended_action`, and auto-created `AnalystCase` if reviewed/blocked.

#### `PATCH /api/v1/transactions/{reference}/status`
Update transaction status and record an append-only audit trail entry.
- **Request Body**:
  ```json
  {
    "status": "APPROVED",
    "notes": "Customer verified via phone call.",
    "actor_id": "lead_analyst_01"
  }
  ```

---

### 3.4. Analyst Cases

#### `GET /api/v1/cases`
Paginated fraud investigation cases with embedded transaction metadata.
- **Query Parameters**:
  - `status`: `OPEN`, `IN_REVIEW`, `RESOLVED`
  - `priority`: `LOW`, `MEDIUM`, `HIGH`
  - `limit`: 50
  - `offset`: 0

#### `PATCH /api/v1/cases/{case_id}`
Update analyst investigation workflow.
- **Request Body**:
  ```json
  {
    "case_status": "IN_REVIEW",
    "assigned_analyst": "analyst_shafiq",
    "resolution_note": "Investigating device fingerprint anomalies."
  }
  ```

---

### 3.5. Risk Policy

#### `GET /api/v1/risk/indicators`
Metadata describing heuristic scoring rules, weights, and thresholds.
- Baseline Floor: 10
- New Device: +25
- High Velocity: +25
- Prior Chargebacks: +25
- High Amount ($\ge \text{৳ 10,000}$): +15
- Location Anomaly: +10
- Max Raw Score: 110, Clamped Score Cap: 100
- Risk Bands: $0\text{--}39 \rightarrow \text{LOW}$, $40\text{--}74 \rightarrow \text{MEDIUM}$, $75\text{--}100 \rightarrow \text{HIGH}$

#### `POST /api/v1/risk/assess`
Dry-run heuristic risk evaluation without creating a transaction.
