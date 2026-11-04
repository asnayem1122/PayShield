# PayShield Milestone 2 — Phase 2: Complete Implementation Report

**Status**: **COMPLETE**  
**Repository**: `D:\Code\PayShield`  
**Branch**: `main`  
**Execution Environment**: Python 3.14.8, PostgreSQL 18, FastAPI, SQLAlchemy 2.x, Alembic, Flutter 3.47.8, Dart 3.13.7  
**Verification Date**: 2026-11-04  

---

## 1. Executive Summary

Milestone 2 — Phase 2 ("Database Schema, ORM, Migrations, Canonical Seed, Backend Integration & Flutter Connectivity") has been successfully implemented and verified end-to-end. All required persistence layers, least-privilege security controls, risk scoring services, REST API endpoints, canonical demo dataset seeders, and Flutter client network integrations are fully operational.

---

## 2. Completed Scope & Deliverables

### 2.1. Environment Provisioning & Database Isolation
- Updated `backend/scripts/provision_db.py` to provision and manage three isolated environments in PostgreSQL 18:
  - `payshield_dev`: Persistent development and demo database.
  - `payshield_test`: Clean automated test database.
  - `payshield_migration_test`: Disposable database for full downgrade/upgrade Alembic lifecycle verification.
- Enforced role isolation:
  - `payshield_migrator`: Schema owner with full DDL.
  - `payshield_app`: Unprivileged runtime application user with DML strictly constrained.
- Applied `REVOKE ALL ON DATABASE ... FROM PUBLIC` and `REVOKE ALL ON SCHEMA public FROM PUBLIC`.
- Revoked all sequence default privileges (UUID primary keys use PostgreSQL's internal `gen_random_uuid()` C-implementation and require no sequence grants).

### 2.2. SQLAlchemy 2.x Declarative Models (`backend/app/models/`)
Implemented all 5 core entity models:
- `Merchant`: `id`, `name`, `category`, `status`, `created_at`, `updated_at`.
- `Transaction`: `id`, `reference`, `merchant_id`, `counterparty_name`, `amount` (NUMERIC(12, 2)), `currency` ('BDT'), `transaction_status` ('APPROVED', 'REVIEW', 'BLOCKED'), `device_model`, `location_city`, `is_location_anomaly`, `risk_score` ($0\text{--}100$), `risk_level` ('LOW', 'MEDIUM', 'HIGH'), `recommended_action` ('APPROVE', 'REVIEW', 'BLOCK'), `channel`, `created_at`, `updated_at`.
  - Database check constraints enforce consistency:
    - $0\text{--}39 \iff \text{LOW} \iff \text{APPROVE}$
    - $40\text{--}74 \iff \text{MEDIUM} \iff \text{REVIEW}$
    - $75\text{--}100 \iff \text{HIGH} \iff \text{BLOCK}$
- `RiskAssessment`: Append-only authoritative risk policy calculation record (`scoring_method` strictly constrained to `'CANONICAL_SEED'` and `'HEURISTIC_RULES_V1'`).
- `AnalystCase`: Fraud workflow case tracker with `trigger_reason` constrained to 11 controlled codes (`UNUSUAL_HOUR`, `NEW_DEVICE`, `VELOCITY_WARN`, `HIGH_AMOUNT`, `DISTANCE_DELTA`, `MULTIPLE_CARDS`, `DEVICE_MISMATCH`, `NEW_ACCOUNT`, `OFF_HOURS`, `MANUAL_FLAG`, `SCORE_THRESHOLD_EXCEEDED`).
- `AuditLog`: Append-only audit trail with `idempotency_key` and actor tracking.

### 2.3. Alembic Migrations & Reversibility
- `backend/alembic/versions/0001_initial_schema.py`:
  - Creates all 5 tables with explicit foreign keys (`ON DELETE RESTRICT`) and indexes.
  - Applies least-privilege SQL permissions and column-level `UPDATE` grants for `payshield_app`.
- Verified migration reversibility via `backend/tests/test_migrations.py`:
  - `upgrade head` (5 tables created) $\rightarrow$ `downgrade base` (0 tables remaining) $\rightarrow$ `upgrade head` (5 tables restored). Passed!

### 2.4. Canonical Fixture Verification & Lineage
- Proved lineage and surplus arithmetic of row 157 (`tx_app_1157`):
  - Generator formula $F_{157} = 1650 + 209 = 1,859.00$ BDT.
  - Surplus across 158 rows reached 54,661.00 BDT. Initial negative amount `-52,802.00` BDT was caused by single-row remainder subtraction.
  - Remediated derivation distributed surplus: rows 0..150 deducted ৳ 346, rows 151..157 deducted ৳ 345.
  - Row 157 remediated: $1,859.00 - 345.00 = \mathbf{1,514.00}$ BDT.
  - Target totals matched to the exact decimal: Approved = ৳ 280,200.00; Total = ৳ 482,500.00.

### 2.5. Multi-Entity Canonical Seeding System & Safe Recovery
- Created `backend/scripts/seed_demo_data.py`:
  - Multi-entity transactional seeding: 1 merchant, 175 transactions, 175 risk assessments, 14 analyst cases, 176 audit logs.
  - Field-by-field exact-match verification: compares every single column and relationship across all 5 entity sets (Merchant name/category/status, all 12 transaction columns, all assessment scores/factors/policies, all 14 cases, and all 176 audit logs).
  - Safe recovery protocol: `--recover-partial` deletes only explicitly enumerated canonical keys (`CANONICAL_REFERENCES`, `EXACT_AUDIT_KEYS`) without wildcard deletion or affecting application data.
  - Boundary assertions: refuses deletion and rolls back if non-canonical runtime audit logs reference canonical transactions or if analyst cases have active human workflow state.
  - Merchant audit log reconciliation: guarantees exactly 176 audit logs even when the `merchants` row already pre-existed.
  - Automated recovery test suite in `backend/tests/test_seed_recovery.py`: verifies empty, fully seeded, partial, drifted, and runtime-linked states across 6 automated tests.

### 2.6. Effective PostgreSQL Permission Audit Tests
- Created `backend/tests/test_permissions_phase2.py`:
  - Verified `pg_auth_members = 0` for `payshield_app`.
  - Verified `PUBLIC` has no CREATE on database or schema.
  - Verified `merchants` is read-only (`SELECT` only).
  - Verified `transactions` allows `UPDATE` exclusively on `(transaction_status, updated_at)`.
  - Verified `analyst_cases` allows `UPDATE` exclusively on `(case_status, resolution_note, resolved_at, updated_at)`. Revoked `assigned_analyst` UPDATE grant to enforce case assignment immutability at runtime.
  - Verified `risk_assessments` and `audit_logs` are append-only.
  - Verified across both `payshield_dev` and `payshield_test`. All 18 tests passed!

### 2.7. Risk Scoring Heuristic Service (`backend/app/services/risk_scoring_service.py`)
- Heuristic Rules Engine v1:
  - Base score: 10
  - Contributions: new device (+25), velocity (+25), prior chargebacks (+25), high amount (+15), location anomaly (+10).
  - Raw score range: $0\text{--}110$, clamped to $0\text{--}100$.
  - Mapped to LOW (0-39), MEDIUM (40-74), HIGH (75-100).
  - Boundary and clamping tests in `backend/tests/test_risk_scoring.py`. All passed!

### 2.8. REST API Layer (`backend/app/api/v1/`)
- Strict decimal wire validation via Pydantic v2 (regex `^\d{1,10}\.\d{2}$`, rejects raw JSON floats).
- Endpoints implemented:
  - `GET /health` and `GET /api/v1/health`
  - `GET /api/v1/readiness` (RFC 9457 Problem Details)
  - `GET /api/v1/dashboard/summary` (Live SQL aggregates: total volume, approved/review/blocked volumes, transaction counts, open cases)
  - `GET /api/v1/dashboard/risk-distribution`
  - `GET /api/v1/dashboard/recent-transactions`
  - `GET /api/v1/transactions` (with filtering and pagination)
  - `GET /api/v1/transactions/{reference}`
  - `POST /api/v1/transactions` (with auto-assessment and case creation)
  - `PATCH /api/v1/transactions/{reference}/status` (with audit logging)
  - `GET /api/v1/cases` and `PATCH /api/v1/cases/{case_id}`
  - `GET /api/v1/risk/indicators` and `POST /api/v1/risk/assess`
  - `GET /api/v1/audit/logs`

### 2.9. Flutter Integration, Decimal-Safe Money & Zero Regression
- Implemented `Money` value object (`mobile/lib/core/utils/money.dart`) backed by integer minor units (`minorUnits` in poisha/cents):
  - Completely eliminates binary `double` floating-point arithmetic from financial volume calculations.
  - Strict 2-decimal string serialization wire contract (`toDecimalString()`, `fromDecimalString()`).
  - Seamlessly integrates with BDT formatters (`toFormattedBdt()`, `toCompactBdt()`).
- Reconciled Flutter canonical offline fallback (`canonical_transactions_fixture.dart` and `mock_transactions.dart`):
  - Removed old single-row remainder subtraction.
  - Applies identical uniform surplus deduction ($151 \times 346 + 7 \times 345 = 54,661$ BDT).
  - All 158 approved amounts strictly positive (৳ 1,007.00 to ৳ 2,630.00).
  - Row 157 (`tx_app_1157`) is exactly ৳ 1,514.00.
  - Exact totals: Approved ৳ 280,200.00; Review ৳ 147,300.00; Blocked ৳ 55,000.00; Total ৳ 482,500.00.
- Integrated `http` networking in `mobile/`.
- Implemented `ApiClient` in `mobile/lib/core/network/api_client.dart` with platform-aware base URL resolution (`10.0.2.2:8000` for Android emulator, `127.0.0.1:8000` for desktop/web).
- Enhanced `TransactionsNotifier` to live-sync with backend on startup, pull-to-refresh, case resolution, and simulated transaction creation, while seamlessly falling back to local canonical data in offline or test mode.
- Pull-to-refresh added to `DashboardScreen` and `TransactionHistoryScreen`.
- `flutter analyze`: 0 issues found.
- `flutter test`: 29/29 tests passed (0 failures, 0 warnings, zero UI or theme regression).

---

## 3. Automated Test Evidence

### 3.1. Backend Pytest Suite
```
collected 69 items

backend/tests/test_api_analyst_cases.py ...                              [  4%]
backend/tests/test_api_dashboard.py ...                                  [  8%]
backend/tests/test_api_transactions.py .......                           [ 18%]
backend/tests/test_config.py .....                                       [ 26%]
backend/tests/test_database.py .....                                     [ 33%]
backend/tests/test_health.py ..                                          [ 36%]
backend/tests/test_migrations.py .                                       [ 37%]
backend/tests/test_permissions.py .........                              [ 50%]
backend/tests/test_permissions_phase2.py ..................              [ 76%]
backend/tests/test_readiness.py ...                                      [ 81%]
backend/tests/test_risk_scoring.py .....                                 [ 88%]
backend/tests/test_seed_recovery.py ......                               [ 97%]
backend/tests/test_seed_verification.py ..                               [100%]

======================= 69 passed, 1 warning in 15.91s =======================
```

### 3.2. Flutter Test Suite
```
00:00 +0: loading D:/Code/PayShield/mobile/test/unit/api_client_and_integration_test.dart
00:00 +0: D:/Code/PayShield/mobile/test/unit/api_client_and_integration_test.dart: ApiClient Unit Tests Default base URL is configured properly for platform
00:00 +1: D:/Code/PayShield/mobile/test/unit/api_client_and_integration_test.dart: ApiClient Unit Tests Allows overriding base URL
00:00 +2: D:/Code/PayShield/mobile/test/unit/api_client_and_integration_test.dart: Decimal-Safe Money Value Object Parses decimal string without floating-point conversion
00:00 +3: D:/Code/PayShield/mobile/test/unit/api_client_and_integration_test.dart: Decimal-Safe Money Value Object Rejects floating-point arithmetic errors on repeated fractional addition
00:00 +4: D:/Code/PayShield/mobile/test/unit/api_client_and_integration_test.dart: Transaction Serialization & Wire Contract Transaction.fromJson accurately parses canonical JSON payload into Money
00:00 +5: D:/Code/PayShield/mobile/test/unit/api_client_and_integration_test.dart: Transaction Serialization & Wire Contract Transaction.toJson accurately produces decimal wire format
00:00 +6: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: AppRiskConstants Unit Tests Validates score strictly between 0 and 100 with explicit ArgumentError
00:00 +7: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: AppRiskConstants Unit Tests Maps risk score to correct RiskLevel and RiskAction
00:00 +8: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: AppRiskConstants Unit Tests Transaction entity constructor rejects invalid scores with ArgumentError and accepts 0 and 100
00:00 +9: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: Canonical Mock Dataset Reconciled Consistency Dataset contains exactly 175 transactions with unique references
00:00 +10: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: Canonical Mock Dataset Reconciled Consistency Status counts match: 158 Approved, 14 Review, 3 Blocked
00:00 +11: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: Canonical Mock Dataset Reconciled Consistency All 175 transactions have strictly positive amounts
00:00 +12: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: Canonical Mock Dataset Reconciled Consistency Merchant category counts are correctly distributed
00:00 +13: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: Canonical Mock Dataset Reconciled Consistency Exact financial volumes in integer minor units without floating-point error
00:00 +14: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: Canonical Mock Dataset Reconciled Consistency tx_app_1157 specific regression test for v1.0.1 canonical remediation
00:00 +15: D:/Code/PayShield/mobile/test/unit/risk_constants_and_data_test.dart: Canonical Mock Dataset Reconciled Consistency Local mock state modification updates analyst case resolution
00:00 +16: D:/Code/PayShield/mobile/test/unit/theme_test.dart: ThemeController Unit Tests Initializes with system default when no preference is saved
00:00 +17: D:/Code/PayShield/mobile/test/unit/theme_test.dart: ThemeController Unit Tests Loads saved theme preference synchronously
00:00 +18: D:/Code/PayShield/mobile/test/unit/theme_test.dart: ThemeController Unit Tests Updates and persists theme mode selection
00:00 +19: D:/Code/PayShield/mobile/test/unit/theme_test.dart: WCAG Contrast Ratios Verification Light theme text colors satisfy WCAG AA (>= 4.5:1) against canvas
00:00 +20: D:/Code/PayShield/mobile/test/unit/theme_test.dart: WCAG Contrast Ratios Verification Light theme telemetry labels satisfy WCAG AA against canvas and card
00:00 +21: D:/Code/PayShield/mobile/test/unit/theme_test.dart: WCAG Contrast Ratios Verification Dark theme text colors satisfy WCAG AA (>= 4.5:1) against void canvas and cards
00:00 +22: D:/Code/PayShield/mobile/test/unit/theme_test.dart: WCAG Contrast Ratios Verification Dark theme telemetry labels satisfy WCAG AA against dark surfaces
00:00 +23: D:/Code/PayShield/mobile/test/widgets/screen_layout_test.dart: Small Screen (320x568 dp) Overflow Verification Dashboard renders on compact screen without overflow
00:01 +24: D:/Code/PayShield/mobile/test/widget_test.dart: PayShieldApp initial smoke test mounts Dashboard
00:01 +25: D:/Code/PayShield/mobile/test/widget_test.dart: PayShieldApp initial smoke test mounts Dashboard
00:01 +26: D:/Code/PayShield/mobile/test/widget_test.dart: PayShieldApp initial smoke test mounts Dashboard
00:01 +27: D:/Code/PayShield/mobile/test/widgets/screen_layout_test.dart: WCAG Large Text Scaling (1.5x) Verification Dashboard scales cleanly under 1.5x text scaler
00:01 +28: D:/Code/PayShield/mobile/test/widgets/screen_layout_test.dart: Accessibility & Semantics Verification RiskBadge provides explicit semantic accessibility labels
00:01 +29: All tests passed!
```

---

## 4. Invariants & Commitments Preserved

1. **Precision Sentinel Design System**: Zero UI, styling, or color regression across Light and Void Dark themes.
2. **Strict Financial Accounting**: Canonical volume remains exactly ৳ 482,500.00 across 175 transactions with row 157 at ৳ 1,514.00.
3. **No False Claims**:
   - No PCI DSS or real card charging claims.
   - Risk score ($0\text{--}100$) documented as rule-based heuristic index, NOT calibrated fraud probability.
   - Audit trail documented as "Role-Restricted Application-Level Append-Only Audit Trail", NOT cryptographic immutability.
4. **Least-Privilege Security**: `payshield_app` has zero DDL, zero DELETE/TRUNCATE, read-only access to `merchants`, and strictly constrained column-level `UPDATE` on `transactions` and `analyst_cases`.
