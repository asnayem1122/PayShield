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
                                     | risk_score       |                 | created_at       |
                                     | risk_level       |                 | updated_at       |
                                     | recommended_action                 | resolved_at      |
                                     | channel          |                 +------------------+
                                     | device_model     |
                                     | location_city    |
                                     | is_location_anom |
                                     | created_at       |
                                     | updated_at       |
                                     +------------------+
                                              |
                                              | 1:N
                                              v
                                     +--------------------+
                                     |  risk_assessments  |
                                     +--------------------+
                                     | id (PK, UUID)      |
                                     | transaction_id(FK) |
                                     | base_score         |
                                     | raw_score          |
                                     | risk_score         |
                                     | is_score_clamped   |
                                     | risk_level         |
                                     | recommended_action |
                                     | scoring_method     |
                                     | policy_version     |
                                     | risk_factors(JSONB)|
                                     | feature_contribs   |
                                     | created_at         |
                                     +--------------------+

+--------------------+
|     audit_logs     | (Append-Only Event Store)
+--------------------+
| id (PK, UUID)      |
| entity_type        |
| entity_id (UUID)   |
| action             |
| actor_type         |
| actor_id           |
| details (JSONB)    |
| ip_address         |
| idempotency_key    |
| created_at         |
+--------------------+
```

---

## 2. Table Definitions & Constraints

### 2.1. `merchants`
- **Purpose**: Represents registered business entities processing payments through PayShield.
- **Runtime Access**: Strictly read-only (`SELECT` only) for `payshield_app`.

| Column | Type | Nullable | Constraints & Defaults | Description |
|---|---|---|---|---|
| `id` | UUID | NO | PK, `gen_random_uuid()` | Unique merchant identifier |
| `name` | VARCHAR(255) | NO | Unique, non-blank | Legal name of merchant entity |
| `category` | VARCHAR(100) | NO | Default `'General'` | Business classification |
| `status` | VARCHAR(20) | NO | Check `status IN ('ACTIVE', 'SUSPENDED', 'PENDING')` | Operational status |
| `created_at` | TIMESTAMPTZ | NO | Default `now()` | Registration timestamp |
| `updated_at` | TIMESTAMPTZ | NO | Default `now()` | Last modification timestamp |

---

### 2.2. `transactions`
- **Purpose**: Core financial ledger storing all evaluated payment transactions.

| Column | Type | Nullable | Constraints & Defaults | Description |
|---|---|---|---|---|
| `id` | UUID | NO | PK, `gen_random_uuid()` | Primary record identifier |
| `reference` | VARCHAR(100) | NO | Unique, non-blank | External canonical reference (`tx_app_...`) |
| `merchant_id` | UUID | NO | FK `merchants.id` ON DELETE RESTRICT | Owning merchant |
| `counterparty_name` | VARCHAR(255) | NO | Non-blank | Payer or counterparty identity |
| `amount` | NUMERIC(12, 2) | NO | Check `amount > 0.00` | Monetary value strictly in BDT |
| `currency` | VARCHAR(3) | NO | Check `currency = 'BDT'` | Fixed currency ISO code |
| `transaction_status` | VARCHAR(20) | NO | Check `status IN ('APPROVED', 'REVIEW', 'BLOCKED')` | Settlement/monitoring state |
| `device_model` | VARCHAR(100) | YES | Nullable | Device user agent or hardware model |
| `location_city` | VARCHAR(100) | YES | Nullable | Geographic settlement city |
| `is_location_anomaly`| BOOLEAN | NO | Default `false` | Geographic flag signal |
| `risk_score` | INTEGER | NO | Check `0 <= risk_score <= 100` | Clamped heuristic risk index |
| `risk_level` | VARCHAR(20) | NO | Check `risk_level IN ('LOW', 'MEDIUM', 'HIGH')` | Risk classification tier |
| `recommended_action`| VARCHAR(20) | NO | Check `action IN ('APPROVE', 'REVIEW', 'BLOCK')` | Automated policy recommendation |
| `channel` | VARCHAR(50) | NO | Default `'MOBILE_APP'` | Payment channel interface |
| `created_at` | TIMESTAMPTZ | NO | Default `now()` | Ingestion timestamp |
| `updated_at` | TIMESTAMPTZ | NO | Default `now()` | Status update timestamp |

#### Engine-Level Check Constraints:
1. `score_level_consistency`:
   - $0 \le \text{risk\_score} \le 39 \iff \text{risk\_level} = \text{'LOW'}$
   - $40 \le \text{risk\_score} \le 74 \iff \text{risk\_level} = \text{'MEDIUM'}$
   - $75 \le \text{risk\_score} \le 100 \iff \text{risk\_level} = \text{'HIGH'}$
2. `level_action_consistency`:
   - $\text{'LOW'} \iff \text{'APPROVE'}$
   - $\text{'MEDIUM'} \iff \text{'REVIEW'}$
   - $\text{'HIGH'} \iff \text{'BLOCK'}$

---

### 2.3. `risk_assessments`
- **Purpose**: Authoritative audit record of risk policy calculations. Append-only.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `transaction_id` | UUID | NO | FK `transactions.id` ON DELETE RESTRICT |
| `base_score` | INTEGER | YES | Baseline policy floor (10) |
| `raw_score` | INTEGER | YES | Unclamped cumulative score ($0\text{--}110$) |
| `risk_score` | INTEGER | NO | Clamped score ($0\text{--}100$) |
| `is_score_clamped` | BOOLEAN | YES | True if raw_score > 100 |
| `risk_level` | VARCHAR(20) | NO | LOW, MEDIUM, or HIGH |
| `recommended_action` | VARCHAR(20) | NO | APPROVE, REVIEW, or BLOCK |
| `scoring_method` | VARCHAR(50) | NO | Check `scoring_method IN ('CANONICAL_SEED', 'HEURISTIC_RULES_V1')` |
| `policy_version` | VARCHAR(20) | NO | Default `'1.0.0'` |
| `risk_factors` | JSONB | NO | Active factor codes |
| `feature_contributions`| JSONB | NO | Itemized weight breakdown |
| `created_at` | TIMESTAMPTZ | NO | Immutable calculation timestamp |

---

### 2.4. `analyst_cases`
- **Purpose**: Fraud analyst investigation workflow tracker.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `transaction_id` | UUID | NO | Unique FK `transactions.id` (1:1 with transaction) |
| `case_status` | VARCHAR(20) | NO | Check `case_status IN ('OPEN', 'IN_REVIEW', 'RESOLVED')` |
| `priority` | VARCHAR(20) | NO | Check `priority IN ('LOW', 'MEDIUM', 'HIGH')` |
| `trigger_reason` | VARCHAR(100) | NO | Controlled reason code (see below) |
| `assigned_analyst` | VARCHAR(100) | YES | Analyst username or handle |
| `resolution_note` | TEXT | YES | Analyst disposition notes |
| `created_at` | TIMESTAMPTZ | NO | Case creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | Case modification timestamp |
| `resolved_at` | TIMESTAMPTZ | YES | Resolution timestamp |

#### Controlled `trigger_reason` Codes:
- `UNUSUAL_HOUR`
- `NEW_DEVICE`
- `VELOCITY_WARN`
- `HIGH_AMOUNT`
- `DISTANCE_DELTA`
- `MULTIPLE_CARDS`
- `DEVICE_MISMATCH`
- `NEW_ACCOUNT`
- `OFF_HOURS`
- `MANUAL_FLAG`
- `SCORE_THRESHOLD_EXCEEDED`

#### Resolution Consistency Constraint:
- If `case_status = 'RESOLVED'`, then `resolved_at IS NOT NULL`.
- If `case_status <> 'RESOLVED'`, then `resolved_at IS NULL`.

---

### 2.5. `audit_logs`
- **Purpose**: Role-restricted application-level append-only audit trail.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key (`gen_random_uuid()`) |
| `entity_type` | VARCHAR(50) | NO | Target entity ('transaction', 'analyst_case', 'merchant') |
| `entity_id` | UUID | NO | Target entity UUID |
| `action` | VARCHAR(100) | NO | Action verb |
| `actor_type` | VARCHAR(20) | NO | Check `actor_type IN ('SYSTEM', 'ANALYST', 'MERCHANT', 'ADMIN')` |
| `actor_id` | VARCHAR(100) | NO | Identity of the acting agent |
| `details` | JSONB | NO | JSON payload describing change |
| `ip_address` | VARCHAR(45) | YES | Client IP address |
| `idempotency_key` | VARCHAR(150) | YES | Unique idempotency token for seed/operation deduplication |
| `created_at` | TIMESTAMPTZ | NO | Immutable record timestamp |

---

## 3. Alembic Migration History

- **`0001_initial_schema` (`0001_initial_schema.py`)**:
  - Creates the 5 core tables with explicit check constraints, primary keys, and foreign keys.
  - Creates performance indexes (`ix_transactions_reference`, `ix_transactions_merchant_id`, `ix_risk_assessments_transaction_id`, `ix_analyst_cases_transaction_id`, `ix_audit_logs_entity_lookup`).
  - Grants least-privilege table permissions to `payshield_app`.
- **`0002_revoke_analyst_update` (`0002_revoke_assigned_analyst_update.py`)**:
  - Reversible forward migration (`revision = "0002_revoke_analyst_update"` <= 32 chars).
  - Upgrade: `REVOKE UPDATE (assigned_analyst) ON TABLE analyst_cases FROM payshield_app`.
  - Downgrade: `GRANT UPDATE (assigned_analyst) ON TABLE analyst_cases TO payshield_app`.
