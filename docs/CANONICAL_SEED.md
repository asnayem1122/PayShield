# PayShield Canonical Seed Dataset & Lineage Specification

## 1. Executive Summary

PayShield includes an authoritative canonical dataset of **175 transactions** designed for realistic demonstration, testing, and UI fidelity.

### Target Financial Totals:
- **Total Monitored Volume**: **৳ 482,500.00**
- **Total Transactions**: **175**
- **Approved Transactions (158)**: **৳ 280,200.00**
- **Review Transactions (14)**: **৳ 147,300.00**
- **Blocked Transactions (3)**: **৳ 55,000.00**
- **Average Risk Score**: **25** (integer-rounded from exact mean 25.17)

---

## 2. Lineage & Remediated Discrepancy of Row 157 (`tx_app_1157`)

### Historical Investigation
In Git commit `3fb737ef5e5aa6786e39c3a006f8f017cc19951c`, the canonical synthetic generator formula for row $i \in [0..157]$ was:

$$F_i = 1650 + ((i \times 37) \pmod{981})$$

For row $i = 157$:
$$F_{157} = 1650 + ((157 \times 37) \pmod{981}) = 1650 + (5809 \pmod{981}) = 1650 + 209 = \mathbf{1,859.00 \text{ BDT}}$$

### Origin of the Negative Amount
Evaluating the generator formula across all 158 rows yielded an unconstrained sum:
$$\sum_{i=0}^{156} F_i = 333,002.00 \text{ BDT}$$
Against the target volume of 280,200.00 BDT, the generated series carried an excess surplus:
$$333,002.00 + 1,859.00 - 280,200.00 = 54,661.00 \text{ BDT}$$

In the initial implementation, row 157 was forced to absorb the entire cumulative surplus:
$$280,200.00 - 333,002.00 = \mathbf{-52,802.00 \text{ BDT}}$$
This resulted in a negative transaction amount violating the fundamental domain rule `amount > 0.00`.

### Remediated Derivation (`v1.0.1-canonical-remediated`)
To preserve all 158 rows without negative amounts, the 54,661.00 BDT surplus was uniformly distributed:
- Rows 0 through 150: deduct ৳ 346 each ($151 \times 346 = 52,246.00$)
- Rows 151 through 157: deduct ৳ 345 each ($7 \times 345 = 2,415.00$)
- Total deduction: $52,246.00 + 2,415.00 = 54,661.00 \text{ BDT}$

For row 157 (`tx_app_1157`):
$$\text{Amount}_{157} = 1,859.00 - 345.00 = \mathbf{1,514.00 \text{ BDT}}$$

### Outcome:
- All 158 approved transactions strictly positive: `1007.00` to `2630.00` BDT.
- Row 157 is strictly positive at `1,514.00` BDT.
- Approved subtotal exactly `280,200.00` BDT.
- Total volume exactly `482,500.00` BDT.
- Score sum exactly `4,405` with rounded average `25`.

---

## 3. Multi-Entity Seed Composition

Seeding `payshield_dev` inserts all 5 interrelated entity layers in a single transactional unit:
1. **1 Merchant**: "PayShield Demo Merchant" (Category: Retail, Status: ACTIVE).
2. **175 Transactions**: 158 Approved, 14 Review, 3 Blocked.
3. **175 Risk Assessments**: scoring_method `CANONICAL_SEED`, policy_version `1.0.0`.
4. **14 Analyst Cases**: 1:1 linked to the 14 review transactions, status `OPEN`, priority `MEDIUM`.
5. **176 Audit Logs**: 1 for merchant provisioning, 175 for transaction ingestion.

---

## 4. Seeding Commands & Safe Recovery

### Standard Seeding:
```bash
python -m scripts.seed_demo_data
```

### Read-Only Verification Mode:
```bash
python -m scripts.seed_demo_data --verify-only
```
Verifies 100% exact match across all fields (including exact UTC timestamps and UUIDs) without making any insertions or database mutations. Exits with exit code 0 on success, or raises `SeedIntegrityError` if drift is detected.

### Idempotent Field-by-Field Verification:
Rerunning `seed_demo_data.py` on an already-seeded database runs a comprehensive exact-match comparison across all fields of all 5 entity sets (Merchant, 175 Transactions, 175 Risk Assessments, 14 Analyst Cases, 176 Audit Logs) and exits without any modifications:
```
100% exact match verified across all 5 canonical entity sets. Database intact.
```
If any drift or unexpected modification is detected (e.g. altered amount, score, status, timestamp, or missing related records), the script aborts with `SeedIntegrityError`.

### Safe Partial Recovery Protocol:
If an interrupted or partial seed state is detected ($0 < \text{count} < 175$), or when explicit recovery is requested:
```bash
python -m scripts.seed_demo_data --recover-partial
```

#### Safe Recovery Boundary & Invariants:
1. **Safety Boundary Checks (P1 Invariant)**:
   - **Risk Assessment Ownership Verification**: Refuses deletion and aborts with atomic rollback if any canonical transaction has multiple risk assessments, or any assessment that deviates from the canonical seed specification (verifying `scoring_method == 'CANONICAL_SEED'`, `policy_version == '1.0.0'`, `base_score is None`, `raw_score is None`, `is_score_clamped is None`, expected `risk_score`, `risk_level`, `recommended_action`, `risk_factors`, empty `feature_contributions`, and exact UTC `created_at`). Runtime or modified assessments must never be deleted by recovery.
   - **Runtime Transaction Audit Logs (with NULL Key Protection)**: Refuses deletion and rolls back if any non-seed runtime audit logs reference canonical transactions (`or_(AuditLog.idempotency_key.is_(None), AuditLog.idempotency_key.not_in(EXACT_AUDIT_KEYS))`). In SQL, comparisons involving `NULL` evaluate to `UNKNOWN`; explicit `IS NULL` checks prevent unkeyed runtime events from escaping recovery detection.
   - **Runtime Merchant Audit Logs (with NULL Key Protection)**: Refuses deletion and rolls back if any non-seed runtime audit logs reference the canonical merchant (`or_(AuditLog.idempotency_key.is_(None), AuditLog.idempotency_key != CANONICAL_MERCHANT_AUDIT_KEY)`).
   - **Active Human Workflow Activity**: Refuses deletion and rolls back if any analyst cases have active human workflow modifications (`case_status != 'OPEN'`, or non-null `assigned_analyst`, `resolution_note`, or `resolved_at`).
2. **Explicit Key Deletions**:
   - Deletions are strictly bounded to enumerated canonical primary keys (`CANONICAL_REFERENCES`) and exact audit keys (`EXACT_AUDIT_KEYS`).
   - Wildcard deletions (e.g. `LIKE 'canonical_seeded:%'`) are strictly prohibited.
3. **Merchant Timestamp & Audit Log Invariants**:
   - Both `merchant.created_at` and `merchant.updated_at` are verified against `CANONICAL_MERCHANT_TIMESTAMP` (`2026-11-04T00:00:00Z`).
   - The merchant audit log (`canonical_seeded:merchant:pay_shield_demo`) is reconciled and guaranteed to exist with timestamp synchronized to `CANONICAL_MERCHANT_TIMESTAMP`.
   - Recovery always yields exactly 176 canonical audit logs.
4. **All-or-Nothing Transaction Boundary**:
   - Deletion, re-insertion, and final field-by-field verification execute within a single atomic database transaction. If any validation fails, the entire recovery transaction is rolled back.

### Automated Recovery Test Suite:
Continuous verification of recovery and idempotency is provided in `backend/tests/test_seed_recovery.py` across 18 distinct scenarios:
- **Scenario 1 (Empty State)**: Clean database seeds to 175 tx, 175 assessments, 14 cases, 176 audit logs.
- **Scenario 2 (Fully Seeded State)**: Idempotent run with `recover_partial=False` detects 175 records, verifies all 5 entity sets, and returns `VERIFIED_EXISTING` without mutation.
- **Scenario 3 (Partial State)**: Incomplete dataset (125/175) fails standard run with `PartialSeedAbortedError` and recovers cleanly with `--recover-partial`.
- **Scenario 4 (Runtime Heuristic Assessment Block)**: Mandatory test - runtime `HEURISTIC_RULES_V1` assessment attached to a canonical tx aborts recovery and preserves data.
- **Scenario 5 (Runtime Audit Event Block)**: Non-canonical runtime audit log referencing a canonical tx blocks recovery.
- **Scenario 6 (Modified Analyst Case Block)**: Analyst case with human workflow activity (`IN_REVIEW`, notes) blocks recovery.
- **Scenario 7 (Modified Canonical Record Drift & Recovery)**: Modified amount triggers `SeedIntegrityError` on standard run and recovers cleanly with `--recover-partial`.
- **Scenario 8 (Unexpected Merchant Audit Dependency Block)**: Non-seed audit log attached to merchant blocks recovery.
- **Scenario 9 (Atomic Rollback Guarantee)**: When recovery safety boundary triggers, 0 records are deleted due to atomic rollback.
- **Scenario 10 (Successful Recovery Exact Counts)**: Successful recovery restores exactly 1 merchant, 175 tx, 175 ra, 14 cases, 176 audit logs.
- **Regression 11 (Transaction Audit with NULL Key)**: Explicitly tests that an audit log with `idempotency_key = NULL` referencing a canonical transaction blocks recovery.
- **Regression 12 (Merchant Audit with NULL Key)**: Explicitly tests that an audit log with `idempotency_key = NULL` referencing the merchant blocks recovery.
- **Regression 13 (Immutability of Rows on Abort)**: Proves original transaction IDs, audit keys, and rows remain untouched after failed recovery.
- **Regression 14 (Canonical Assessment Unexpected raw_score)**: Assessment with non-null `raw_score` blocks recovery.
- **Regression 15 (Canonical Assessment Unexpected is_score_clamped)**: Assessment with non-null `is_score_clamped` blocks recovery.
- **Regression 16 (Canonical Assessment Modified feature_contributions)**: Assessment with non-empty `feature_contributions` blocks recovery.
- **Regression 17 (Canonical Assessment Modified risk_factors)**: Assessment with modified `risk_factors` blocks recovery.
- **Regression 18 (Canonical Assessment Altered Score)**: Assessment with altered `risk_score` blocks recovery.
