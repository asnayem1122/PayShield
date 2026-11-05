# PayShield Database Schema Specification

## 1. Entity Relationship Diagram

```
+------------------+       1:N       +------------------+       1:1       +------------------+
|    merchants     | --------------> |   transactions   | --------------> |  analyst_cases   |
+------------------+                 +------------------+                 +------------------+
| id (PK, UUID)    |                 | id (PK, UUID)    |                 | id (PK, UUID)    |
| name             |                 | reference (UQ)   |                 | transaction_id   |
| category         |                 | merchant_id (FK) |                 | case_status      |
| status           |                 | counterparty_name|                 | priority         |
| created_at       |                 | amount           |                 | trigger_reason   |
| updated_at       |                 | currency         |                 | assigned_analyst |
+------------------+                 | transaction_status                 | resolution_note  |
        ^                            | risk_score       |                 | created_at       |
        | 0..1                       | risk_level       |                 | updated_at       |
        |                            | recommended_action                 | resolved_at      |
+------------------+                 | channel          |                 +------------------+
|      users       |                 | device_model     |
+------------------+                 | location_city    |
| id (PK, UUID)    |                 | is_location_anom |
| email (UQ)       |                 | created_at       |
| full_name        |                 | updated_at       |
| password_hash    |                 +------------------+
| role (CHECK)     |                          |
| status (CHECK)   |                          | 1:N
| merchant_id (FK) |                          v
| failed_attempts  |                 +--------------------+
| locked_until     |                 |  risk_assessments  |
| last_login_at    |                 +--------------------+
| created_at       |                 | id (PK, UUID)      |
| updated_at       |                 | transaction_id(FK) |
+------------------+                 | base_score         |
        |                            | raw_score          |
        | 1:N                        | risk_score         |
        v                            | is_score_clamped   |
+------------------+                 | risk_level         |
|  auth_sessions   |                 | recommended_action |
+------------------+                 | scoring_method     |
| id (PK, UUID)    |                 | policy_version     |
| user_id (FK)     |                 | risk_factors(JSONB)|
| refresh_token_jti|                 | feature_contribs   |
| created_at       |                 | created_at         |
| expires_at       |                 +--------------------+
| last_used_at     |
| revoked_at       |                 +--------------------+
+------------------+                 |     audit_logs     | (Append-Only Event Store)
                                     +--------------------+
                                     | id (PK, UUID)      |
                                     | ...                |
                                     +--------------------+
```

---

## 2. Table Specifications

### 2.1. `merchants`
- **Purpose**: Registered commercial merchants in PayShield.
- **Constraints**:
  - `status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')`
  - `length(trim(name)) > 0`, `length(trim(category)) > 0`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `name` | VARCHAR(255) | NO | Merchant trade name |
| `category` | VARCHAR(100) | NO | Commercial category |
| `status` | VARCHAR(50) | NO | Operational status |
| `created_at` | TIMESTAMPTZ | NO | Audit timestamp |
| `updated_at` | TIMESTAMPTZ | NO | Audit timestamp |

---

### 2.2. `transactions`
- **Purpose**: Core payment events evaluated for fraud risk.
- **Constraints**:
  - `amount > 0.00`
  - `currency IN ('BDT')`
  - `transaction_status IN ('APPROVED', 'REVIEW', 'BLOCKED')`
  - `risk_level IN ('LOW', 'MEDIUM', 'HIGH')`
  - `recommended_action IN ('APPROVE', 'REVIEW', 'BLOCK')`
  - `risk_score BETWEEN 0 AND 100`
  - Consistency Check:
    - `0 <= risk_score <= 39` implies `risk_level = 'LOW'` and `recommended_action = 'APPROVE'`
    - `40 <= risk_score <= 74` implies `risk_level = 'MEDIUM'` and `recommended_action = 'REVIEW'`
    - `75 <= risk_score <= 100` implies `risk_level = 'HIGH'` and `recommended_action = 'BLOCK'`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `reference` | VARCHAR(64) | NO | Unique external transaction reference |
| `merchant_id` | UUID | NO | Foreign key (`merchants.id` RESTRICT) |
| `counterparty_name` | VARCHAR(255) | NO | Counterparty identifier |
| `amount` | NUMERIC(12, 2) | NO | Transaction amount |
| `currency` | VARCHAR(3) | NO | ISO 4217 Currency code (`BDT`) |
| `transaction_status` | VARCHAR(20) | NO | Workflow state (`APPROVED`, `REVIEW`, `BLOCKED`) |
| `risk_score` | INTEGER | NO | Risk score (0--100) |
| `risk_level` | VARCHAR(20) | NO | Tier (`LOW`, `MEDIUM`, `HIGH`) |
| `recommended_action` | VARCHAR(20) | NO | Policy suggestion |
| `channel` | VARCHAR(50) | NO | Channel (`MOBILE_APP`, `WEB`, `POS`, `AGENT`) |
| `device_model` | VARCHAR(100) | YES | Client device model |
| `location_city` | VARCHAR(100) | YES | Originating city |
| `is_location_anomaly` | BOOLEAN | NO | Geographic risk signal |
| `created_at` | TIMESTAMPTZ | NO | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | Last modification timestamp |

---

### 2.3. `risk_assessments`
- **Purpose**: Detailed breakdown and feature attribution for risk scoring.
- **Constraints**:
  - `scoring_method IN ('CANONICAL_SEED', 'HEURISTIC_RULES_V1')`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `transaction_id` | UUID | NO | Foreign key (`transactions.id` CASCADE) |
| `base_score` | INTEGER | NO | Baseline floor score (10) |
| `raw_score` | INTEGER | NO | Unclamped cumulative signal sum |
| `risk_score` | INTEGER | NO | Clamped score (0--100) |
| `is_score_clamped` | BOOLEAN | NO | True if raw_score > 100 |
| `risk_level` | VARCHAR(20) | NO | Risk category |
| `recommended_action` | VARCHAR(20) | NO | Policy recommendation |
| `scoring_method` | VARCHAR(50) | NO | Scoring methodology |
| `policy_version` | VARCHAR(20) | NO | Policy version string |
| `risk_factors` | JSONB | NO | Array of triggered rule codes |
| `feature_contributions` | JSONB | NO | Structured factor contributions array |
| `created_at` | TIMESTAMPTZ | NO | Audit timestamp |

---

### 2.4. `analyst_cases`
- **Purpose**: Operational workflow tracking for suspicious transactions.
- **Constraints**:
  - `case_status IN ('OPEN', 'IN_REVIEW', 'RESOLVED')`
  - `priority IN ('LOW', 'MEDIUM', 'HIGH')`
  - `trigger_reason IN ('UNUSUAL_HOUR', 'NEW_DEVICE', 'VELOCITY_WARN', 'HIGH_AMOUNT', 'DISTANCE_DELTA', 'MULTIPLE_CARDS', 'DEVICE_MISMATCH', 'NEW_ACCOUNT', 'OFF_HOURS', 'MANUAL_FLAG', 'SCORE_THRESHOLD_EXCEEDED')`
  - Resolution consistency constraint: `case_status = 'RESOLVED'` requires `resolved_at IS NOT NULL`.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `transaction_id` | UUID | NO | Foreign key (`transactions.id` CASCADE) |
| `case_status` | VARCHAR(20) | NO | Workflow state |
| `priority` | VARCHAR(20) | NO | Triage priority |
| `trigger_reason` | VARCHAR(100) | NO | Specific trigger indicator |
| `assigned_analyst` | VARCHAR(100) | YES | Assigned investigator |
| `resolution_note` | TEXT | YES | Resolution summary |
| `created_at` | TIMESTAMPTZ | NO | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | Case modification timestamp |
| `resolved_at` | TIMESTAMPTZ | YES | Resolution timestamp |

---

### 2.5. `audit_logs`
- **Purpose**: Role-restricted application-level append-only audit trail.
- **Constraints**:
  - `actor_type IN ('SYSTEM', 'ANALYST', 'MERCHANT', 'ADMIN')`
  - `length(trim(action)) > 0`, `length(trim(entity_type)) > 0`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `entity_type` | VARCHAR(50) | NO | Target entity ('transaction', 'analyst_case', 'merchant', 'USER') |
| `entity_id` | VARCHAR(100) | NO | Target entity UUID string |
| `action` | VARCHAR(100) | NO | Action verb |
| `actor_type` | VARCHAR(50) | NO | Actor category |
| `actor_id` | VARCHAR(100) | NO | Identity of the acting agent |
| `details` | JSONB | NO | JSON payload describing change |
| `ip_address` | VARCHAR(45) | YES | Client IP address |
| `idempotency_key` | VARCHAR(150) | YES | Unique idempotency token for seed/operation deduplication |
| `created_at` | TIMESTAMPTZ | NO | Immutable record timestamp |

---

### 2.6. `users`
- **Purpose**: Authenticated user accounts with credentials, role-based access control, and lockout safeguards.
- **Constraints**:
  - `role IN ('MERCHANT', 'ANALYST', 'ADMIN')`
  - `status IN ('ACTIVE', 'SUSPENDED')`
  - `length(trim(email)) > 0`, `length(trim(full_name)) > 0`
  - `failed_login_attempts >= 0`
  - Role/Merchant Matching Constraint:
    `(role = 'MERCHANT' AND merchant_id IS NOT NULL) OR (role IN ('ANALYST', 'ADMIN') AND merchant_id IS NULL)`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `email` | VARCHAR(255) | NO | Unique normalized email address (indexed) |
| `full_name` | VARCHAR(255) | NO | User display name |
| `password_hash` | VARCHAR(255) | NO | Bcrypt password hash string |
| `role` | VARCHAR(50) | NO | Role (`MERCHANT`, `ANALYST`, `ADMIN`) |
| `status` | VARCHAR(50) | NO | State (`ACTIVE`, `SUSPENDED`) |
| `merchant_id` | UUID | YES | Foreign key (`merchants.id` RESTRICT) |
| `failed_login_attempts` | INTEGER | NO | Consecutive failed login counter (default 0) |
| `locked_until` | TIMESTAMPTZ | YES | Temporal lockout expiration timestamp |
| `last_login_at` | TIMESTAMPTZ | YES | Last successful login timestamp |
| `created_at` | TIMESTAMPTZ | NO | Creation audit timestamp |
| `updated_at` | TIMESTAMPTZ | NO | Last modification timestamp |

---

### 2.7. `auth_sessions`
- **Purpose**: Active refresh token sessions for token rotation and instant revocation.
- **Constraints**:
  - `expires_at > created_at`
  - `refresh_token_jti` UNIQUE

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `user_id` | UUID | NO | Foreign key (`users.id` CASCADE) |
| `family_id` | UUID | NO | Device session family identifier for isolated token rotation (`gen_random_uuid()`) |
| `refresh_token_jti` | VARCHAR(64) | NO | Unique JWT ID string of the issued refresh token |
| `created_at` | TIMESTAMPTZ | NO | Session issuance timestamp |
| `expires_at` | TIMESTAMPTZ | NO | Expiration timestamp |
| `last_used_at` | TIMESTAMPTZ | YES | Timestamp when refreshed |
| `revoked_at` | TIMESTAMPTZ | YES | Timestamp when revoked/logged out |

---

## 3. Alembic Migration History

- **`0001_initial_schema` (`0001_initial_schema.py`)**:
  - Creates the 5 core tables with explicit check constraints, primary keys, and foreign keys.
  - Creates performance indexes (`ix_transactions_reference`, `ix_transactions_merchant_id`, `ix_risk_assessments_transaction_id`, `ix_analyst_cases_transaction_id`, `ix_audit_logs_entity_lookup`).
  - Grants least-privilege table permissions to `payshield_app`.
- **`0002_revoke_analyst_update` (`0002_revoke_assigned_analyst_update.py`)**:
  - Reversible forward migration (`revision = "0002_revoke_analyst_update"`).
  - Upgrade: `REVOKE UPDATE (assigned_analyst) ON TABLE analyst_cases FROM payshield_app`.
  - Downgrade: `GRANT UPDATE (assigned_analyst) ON TABLE analyst_cases TO payshield_app`.
- **`0003_create_users_table` (`0003_create_users_table.py`)**:
  - Reversible forward migration (`revision = "0003_create_users_table"`).
  - Creates `users` and `auth_sessions` tables with RBAC check constraints.
  - Grants least-privilege permissions to `payshield_app`:
    - `SELECT, INSERT` on `users`
    - Column-level `UPDATE` on `users(password_hash, full_name, failed_login_attempts, locked_until, last_login_at, updated_at)`
    - Denies `UPDATE` on `users(id, email, role, merchant_id, created_at)`
    - Denies `DELETE, TRUNCATE` on `users`
    - `SELECT, INSERT` on `auth_sessions`
    - Column-level `UPDATE` on `auth_sessions(last_used_at, revoked_at)`
    - Denies `DELETE, TRUNCATE` on `auth_sessions`.
- **`0004_add_session_family` (`0004_add_session_family.py`)**:
  - Reversible forward migration (`revision = "0004_add_session_family"`).
  - Adds `family_id: UUID` (NOT NULL, default `gen_random_uuid()`) with index `ix_auth_sessions_family_id` to `auth_sessions`.
  - Enables device session family isolation for token rotation and selective replay termination.
  - Reaffirms least-privilege permissions for `payshield_app`.
