# PayShield — Milestone 2 Phase 2 Final Remediation Report

**Project:** PayShield  
**Repository:** `D:\Code\PayShield`  
**Branch:** `main`  
**Target Milestone:** Milestone 2 — Phase 2: Database Schema, ORM Models, Alembic Migrations, Canonical Seed & Flutter Integration  
**Date:** November 4, 2026  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary & Defect Inventory

During the final audit and corrective remediation of Milestone 2 Phase 2, nine defect categories were identified, remediated, and verified with automated test suites:

| # | Defect Found | Severity | Resolution Summary | Status |
|---|---|---|---|---|
| **D1** | **Unprotected Seed Recovery Boundary Against Runtime Risk Assessments**: Prior recovery logic did not inspect or protect runtime-generated `RiskAssessment` records (`HEURISTIC_RULES_V1`). A recovery run could have deleted runtime risk assessments attached to canonical transactions. | **P1 (Critical)** | Implemented `assert_safe_recovery_boundary()` inspecting every risk assessment linked to canonical transactions. Any non-canonical assessment (`scoring_method != 'CANONICAL_SEED'`), multiple assessments, or runtime metadata aborts recovery with immediate atomic rollback. | **Implemented & Tested** |
| **D2** | **Loose Flutter Money Contract**: `Money` class accepted numeric inputs, lacked bounds checking for `NUMERIC(12, 2)`, lacked strict regex enforcement, and permitted zero/negative transaction amounts during deserialization. | **P1 (Critical)** | Rewrote `Money` to enforce integer minor units with strict 2-decimal string regex (`^\d{1,10}\.\d{2}$`). Strictly rejects raw JSON numbers, non-string amounts, missing fields, zero amounts, and negative amounts in `Transaction.fromJson` and constructor. Preserves legitimate zero-valued aggregates (`0.00` BDT) in `Money.fromDecimalString()`. | **Implemented & Tested** |
| **D3** | **Altered Migration History in Migration 0001**: Commit `81f8dbe` retroactively modified `backend/alembic/versions/0001_initial_schema.py` to revoke `assigned_analyst` UPDATE privileges. Retroactive changes do not apply to already-migrated databases. | **P2 (High)** | Restored `0001_initial_schema.py` to its original historical grant. Implemented forward migration `0002_revoke_assigned_analyst_update.py` (`revision = "0002_revoke_analyst_update"`, 26 chars $\le 32$) with reversible downgrade. | **Implemented & Tested** |
| **D4** | **Incomplete Seed Field Verification & Timestamp Drift**: Canonical seed verification previously checked key attributes (amount, score, status) but skipped several metadata columns (UUID types, JSONB feature contributions, UTC timestamps). Local vs UTC date interpretations between Dart and Python caused potential drift. | **P2 (Medium)** | Standardized canonical fixture timestamps to explicit UTC instants (`DateTime.utc(2026, 11, 4, 0, 0, 0)` in Dart and timezone-aware UTC datetime in Python). Implemented column-by-column verification across all 5 entities and added `--verify-only` CLI flag. Verified merchant `created_at` and `updated_at` down to the second against canonical UTC constants. | **Implemented & Tested** |
| **D5** | **Merchant Identity Discrepancy ("Shadhin Pay" vs "PayShield Demo Merchant")**: Documentation and repository docstring referenced "Shadhin Pay" while the canonical database model standardized on "PayShield Demo Merchant". | **P2 (Low)** | Standardized identity across all documentation (`CANONICAL_SEED.md`, `DATABASE_SCHEMA.md`), repository code (`merchant_repository.py`), and test suites to `PayShield Demo Merchant`. | **Implemented & Tested** |
| **D6** | **Unsafe Migration Testing Risk**: Migration tests previously lacked guards ensuring downgrade and upgrade cycles run strictly against a designated disposable database. | **P2 (Medium)** | Added `assert_disposable_migration_database` safety guard in `backend/tests/test_migrations.py` rejecting any execution unless database is exactly `payshield_migration_test`. | **Implemented & Tested** |
| **D7** | **Nullable Idempotency Key Leak in Recovery**: `AuditLog.idempotency_key` is nullable. SQL `NOT IN` with NULL evaluates to `UNKNOWN`, allowing unkeyed runtime audit logs to bypass detection. | **P1 (Critical)** | Applied `or_(idempotency_key.is_(None), idempotency_key.not_in(...))` for transaction and merchant audit checks. Unkeyed runtime audit records now strictly abort recovery. | **Implemented & Tested** |
| **D8** | **Risk Assessment Ownership Verification**: Broad deletion conditions could potentially delete modified canonical assessments. | **P1 (Critical)** | Hardened `assert_safe_recovery_boundary()` to verify every property (`scoring_method`, `policy_version`, `base_score is None`, `raw_score is None`, `is_score_clamped is None`, scores, levels, actions, factors, empty contributions, created_at). | **Implemented & Tested** |
| **D9** | **Assertion-Only Release Mode Money Risk & Wire Whitespace**: Dart `assert()` is stripped in release builds. Wire parser silently trimmed whitespace. | **P2 (High)** | Replaced `assert()` with runtime `ArgumentError` checks in `Money(this.minorUnits)` and `Money.fromMinorUnits()`. Enforced strict `^[0-9]{1,10}\.[0-9]{2}$` wire regex without `.trim()`, rejecting whitespace, negative amounts, and non-strings. Typed `Transaction.copyWith(Money? amount)`. Removed floating-point division in `toCompactBdt()`. | **Implemented & Tested** |
| **D10**| **Historical Fixture Timestamp Alignment**: Backend `seed_demo_data.py` introduced simplified interval approximations for blocked and review transactions, diverging from the authoritative Milestone 1 Flutter fixture. | **P2 (Medium)** | Aligned `seed_demo_data.py` transaction specs to the exact historical UTC offsets from the Flutter fixture (`-12m`, `-1h40m`, `-3h15m` for blocked; `-(i+1)h -(i*7)m` for review). Updated `payshield_dev` records and verified 100% exact second-level timestamp equality. | **Implemented & Tested** |

---

## 2. Exact Files Changed

### Backend Schema, Migrations & Scripts:
- `backend/alembic/versions/0001_initial_schema.py`: Restored original historical permission grant including `assigned_analyst`.
- `backend/alembic/versions/0002_revoke_assigned_analyst_update.py`: New forward migration (`revision = "0002_revoke_analyst_update"`) revoking UPDATE on `assigned_analyst` for `payshield_app` on upgrade and granting on downgrade.
- `backend/scripts/seed_demo_data.py`:
  - Added `assert_safe_recovery_boundary()` checking runtime risk assessments, runtime audit logs, active analyst case workflow state, and runtime merchant audit logs.
  - Aligned blocked and review transaction timestamp specs to exact historical Flutter offsets.
  - Implemented exact column-by-column verification covering UUIDs, strings, Decimals, JSONB payloads, and UTC timestamps.
  - Added `--verify-only` read-only CLI flag.
  - Synchronized merchant audit log timestamp with merchant `created_at`.
- `backend/app/repositories/merchant_repository.py`: Corrected docstring to `PayShield Demo Merchant`.

### Backend Tests:
- `backend/tests/test_migrations.py`: Added `assert_disposable_migration_database` guard; verified full migration lifecycle (clean downgrade $\rightarrow$ upgrade 0001 $\rightarrow$ upgrade 0002 $\rightarrow$ downgrade 0001 $\rightarrow$ downgrade base $\rightarrow$ upgrade head).
- `backend/tests/test_seed_verification.py`: Created comprehensive 15-test suite verifying exact-match integrity, timestamp equality with Flutter fixture, and drift detection across all timestamps, merchant name, transaction amounts, risk scores, case triggers, and audit logs.
- `backend/tests/test_seed_recovery.py`: Created 19-test suite validating safe recovery boundaries, NULL-key detection, atomic rollback, and exact canonical restoration.

### Mobile / Flutter Application & Tests:
- `mobile/lib/core/utils/money.dart`:
  - Enforced strict regex `^\d{1,10}\.\d{2}$` in `fromDecimalString()`.
  - Enforced `NUMERIC(12, 2)` bounds ($0.00$ to $9,999,999,999.99$ BDT / $999,999,999,999$ minor units).
  - Removed loose `fromNum(num)` helper to eliminate binary floating-point conversions.
  - Replaced floating-point division in `toCompactBdt()` with integer rounding `(minorUnits.abs() + 50) ~/ 100`.
- `mobile/lib/features/transactions/domain/transaction_model.dart`:
  - Enforced `required this.amount` (`Money`).
  - Constructor throws `ArgumentError` on non-positive amounts ($\le 0$).
  - `fromJson` strictly requires string amount, rejects JSON numbers/doubles, rejects missing fields, and rejects non-positive amounts.
  - `toJson` outputs exact 2-decimal string.
  - Standardized default merchant name to `PayShield Demo Merchant`.
- `mobile/lib/features/transactions/data/canonical_transactions_fixture.dart`: Updated canonical timestamps to explicit `DateTime.utc(2026, 11, 4, 0, 0, 0)`.
- `mobile/lib/features/dashboard/domain/dashboard_kpi.dart`: Updated to use strict `Money` value object.
- `mobile/lib/features/dashboard/presentation/dashboard_screen.dart`: Updated KPI card widgets to consume `Money`.
- `mobile/test/unit/api_client_and_integration_test.dart`: Added comprehensive unit tests for `Money`, `Transaction.fromJson`, JSON number rejection, valid zero-valued dashboard aggregates, and bounds validation.
- `mobile/test/unit/risk_constants_and_data_test.dart`: Updated amount constructors to `Money.fromMajor()`.

### Documentation:
- `docs/DATABASE_PERMISSIONS.md`: Documented migration 0002 and runtime immutability.
- `docs/CANONICAL_SEED.md`: Documented exact UTC timestamp verification, safe recovery boundaries, `PayShield Demo Merchant`, and `--verify-only`.
- `docs/DATABASE_SCHEMA.md`: Documented migration history (0001 and 0002) and column invariants.
- `docs/API_DOCUMENTATION.md`: Documented strict decimal string contract `^\d{1,10}\.\d{2}$`.
- `docs/PHASE_2_FINAL_REMEDIATION_REPORT.md`: This comprehensive remediation and verification report.

---

## 3. Recovery Safety Implementation (P1 Invariant)

The safe recovery protocol in `backend/scripts/seed_demo_data.py` (`assert_safe_recovery_boundary()`) provides deterministic safety boundaries:

```python
def assert_safe_recovery_boundary(session: Session, spec_map: dict[str, dict[str, Any]] | None = None) -> None:
    canonical_tx_subquery = select(Transaction.id).where(Transaction.reference.in_(CANONICAL_REFERENCES))

    # 1. Runtime-generated risk assessments attached to canonical transactions
    assessments = session.execute(
        select(RiskAssessment).where(RiskAssessment.transaction_id.in_(canonical_tx_subquery))
    ).scalars().all()

    ra_by_tx: dict[Any, list[RiskAssessment]] = defaultdict(list)
    for ra in assessments:
        ra_by_tx[ra.transaction_id].append(ra)

    for tx_id, ra_list in ra_by_tx.items():
        if len(ra_list) > 1:
            raise SeedIntegrityError(
                f"Recovery aborted: Transaction {tx_id} has {len(ra_list)} risk assessments. "
                "Refusing to delete records with unexpected multiple assessments."
            )
        ra = ra_list[0]
        if ra.scoring_method != "CANONICAL_SEED":
            raise SeedIntegrityError(
                f"Recovery aborted: Runtime-generated risk assessment detected for {tx_ref} "
                f"(scoring_method='{ra.scoring_method}'). Refusing to delete external runtime assessments."
            )
        # Deep field validation of canonical assessment properties...
```

---

## 4. Verification Execution Evidence

### 4.1 Backend Pytest Execution Output
```
PS D:\Code\PayShield> $env:PYTHONPATH="backend"; .\backend\.venv\Scripts\python.exe -m pytest backend/tests/
============================= test session starts =============================
platform win32 -- Python 3.14.8, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\Code\PayShield\backend
configfile: pyproject.toml
plugins: anyio-4.16.0
collected 96 items

backend\tests\test_api_analyst_cases.py ...                              [  3%]
backend\tests\test_api_dashboard.py ...                                  [  6%]
backend\tests\test_api_transactions.py .......                           [ 13%]
backend\tests\test_config.py .....                                       [ 18%]
backend\tests\test_database.py .....                                     [ 23%]
backend\tests\test_health.py ..                                          [ 26%]
backend\tests\test_migrations.py ..                                      [ 28%]
backend\tests\test_permissions.py .........                              [ 37%]
backend\tests\test_permissions_phase2.py ..................              [ 56%]
backend\tests\test_readiness.py ...                                      [ 59%]
backend\tests\test_risk_scoring.py .....                                 [ 64%]
backend\tests\test_seed_recovery.py ...................                  [ 84%]
backend\tests\test_seed_verification.py ...............                  [100%]

======================= 96 passed, 1 warning in 28.18s ========================
```

### 4.2 Canonical Lineage Verification Output
```
PS D:\Code\PayShield> .\backend\.venv\Scripts\python.exe backend/scripts/verify_canonical_fixture.py
======================================================================
PAYSHIELD CANONICAL FIXTURE VERIFICATION & LINEAGE REPORT
======================================================================
1. Unscaled Generator Formula Total: 334861 BDT
   Target Approved Volume:          280200.00 BDT
   Generator Excess Surplus:        54661.00 BDT

2. Lineage Analysis of tx_app_1157:
   Unscaled Formula Value (F_157):  1859 BDT
   Accumulated Sum (Rows 0..156):   333002 BDT
   v1.0.0 Remainder Subtraction:    280200.00 - 333002 = -52802.00 BDT
   Discrepancy (F_157 - v1.0.0):    54661.00 BDT (Exact Excess Surplus)

3. Remediated Canonical Schedule (v1.0.1):
   Deduction Schedule:              151 x 346.00 + 7 x 345.00 = 54,661.00 BDT
   Remediated tx_app_1157 Amount:   1859 - 345.00 = 1514.00 BDT
   Remediated Approved Sum:         280200.00 BDT
   All Approved Amounts Positive:   True
   Min Amount:                      1007.00 BDT
   Max Amount:                      2630.00 BDT

4. Global Dataset Assertions:
   Total Transactions:              175 (Unique: 175)
   Blocked Volume (3 txs):          55000.00 BDT
   Review Volume (14 txs):          147300.00 BDT
   Approved Volume (158 txs):       280200.00 BDT
   Total Canonical Volume:          482500.00 BDT
   Score Sum:                       4405
   Score Exact Mean:                25.17142857
   Score Rounded Mean:              25

ALL INVARIANTS SATISFIED SUCCESSFULLY.
======================================================================
```

### 4.3 Flutter Analysis and Tests Output
```
PS D:\Code\PayShield\mobile> flutter analyze; flutter test
Analyzing mobile...                                             
No issues found! (ran in 7.5s)

00:04 +38: All tests passed!
```

### 4.4 Canonical Seed Idempotency Output
```
PS D:\Code\PayShield> .\backend\.venv\Scripts\python.exe backend/scripts/seed_demo_data.py --verify-only
Connecting as payshield_migrator to verify canonical demo dataset...
100% exact match verified across all 5 canonical entity sets. Database intact.
```

### 4.5 PostgreSQL Effective Permission Verification
```
PS D:\Code\PayShield> $env:PYTHONPATH="backend"; .\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_permissions.py backend/tests/test_permissions_phase2.py
============================= test session starts =============================
collected 27 items

backend\tests\test_permissions.py .........                              [ 33%]
backend\tests\test_permissions_phase2.py ..................              [100%]

============================= 27 passed in 3.56s ==============================
```

---

## 5. Status Matrix: Implemented, Tested, Deferred

| Scope Area | Component | Implementation Status | Test Status |
|---|---|---|---|
| **Recovery Boundary** | Inspection of Risk Assessments on canonical transactions | Implemented | Tested (Scenarios 4 & 11 in `test_seed_recovery.py`) |
| **Recovery Boundary** | Multi-entity dependency checks (Audit logs, Analyst cases) | Implemented | Tested (Scenarios 5, 6, 8 in `test_seed_recovery.py`) |
| **Recovery Boundary** | Atomic rollback on boundary abort | Implemented | Tested (Scenario 9 in `test_seed_recovery.py`) |
| **Recovery Boundary** | Full exact restoration count (176 audit logs) | Implemented | Tested (Scenario 10 in `test_seed_recovery.py`) |
| **Flutter Money** | Strict `Money` class with `^\d{1,10}\.\d{2}$` | Implemented | Tested (Unit tests in `api_client_and_integration_test.dart`) |
| **Flutter Money** | Pure integer arithmetic in `toCompactBdt()` | Implemented | Tested (Unit tests in `api_client_and_integration_test.dart`) |
| **Flutter Money** | Rejection of raw JSON numbers, non-strings, whitespace in `fromJson` | Implemented | Tested (Unit tests in `api_client_and_integration_test.dart`) |
| **Flutter Money** | Rejection of zero and negative transaction amounts | Implemented | Tested (Unit tests in `api_client_and_integration_test.dart`) |
| **Timestamp Consistency** | Standardize explicit UTC instants across Dart and Python | Implemented | Tested (`test_canonical_specs_exact_timestamp_equality_with_flutter`) |
| **Seed Verification** | Field-level exact comparison across all 5 tables | Implemented | Tested (`seed_demo_data.py --verify-only` & pytest) |
| **Seed Verification** | `--verify-only` CLI flag | Implemented | Tested (CLI verification against `payshield_dev`) |
| **Alembic History** | Restore `0001` grant and add forward migration `0002` | Implemented | Tested (`test_migrations.py` upgrade/downgrade) |
| **Alembic History** | Migration test safety guard for disposable database | Implemented | Tested (`test_migrations.py`) |
| **Merchant Identity** | Standardize on "PayShield Demo Merchant" | Implemented | Tested (Repository, fixtures, docs verified) |
| **Documentation** | Permissions, Seed, Schema, and API specifications | Implemented | N/A (Doc sync verified) |
| **Phase 3 Scope** | Real payment gateway integration (bKash/Nagad APIs) | Deferred | Deferred (Milestone 3 scope) |
| **Phase 3 Scope** | Machine learning model training / inference engines | Deferred | Deferred (Milestone 3 scope) |
| **Phase 3 Scope** | Production user authentication / OAuth2 expansion | Deferred | Deferred (Milestone 3 scope) |

---

## 6. Remaining Known Limitations

1. **Single Merchant Domain (Phase 2 Canonical Scope)**:
   The database schema supports multi-tenant merchants via foreign keys, but Milestone 2 canonical demo fixtures configure a single default merchant (`PayShield Demo Merchant`). Multi-merchant dynamic provisioning is slated for Phase 3.
2. **Heuristic Rule Engine (Static Policy Version 1.0.0)**:
   The current risk evaluation engine uses deterministic heuristic scoring (`HEURISTIC_RULES_V1`). Machine learning feature stores and statistical risk models belong to Milestone 3.
3. **Database Deployment Dependency**:
   PostgreSQL 18 is required due to modern privilege modeling and `gen_random_uuid()` defaults without external extensions.
4. **Hardware Environment Boundary**:
   Android AVD emulator images were not configured on the host system; Flutter runtime verification executed across Windows desktop, web targets, and the Flutter automated widget test runner.
