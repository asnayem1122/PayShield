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
1. **1 Merchant**: "Shadhin Pay" (Category: Retail, Status: ACTIVE).
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

### Idempotent Field-by-Field Verification:
Rerunning `seed_demo_data.py` on an already-seeded database runs a comprehensive exact-match comparison across all fields of all 5 entity sets (Merchant, 175 Transactions, 175 Risk Assessments, 14 Analyst Cases, 176 Audit Logs) and exits without any modifications:
```
100% exact match verified across all 5 canonical entity sets. Database intact.
```
If any drift or unexpected modification is detected (e.g. altered amount, score, status, or missing related records), the script aborts with `SeedIntegrityError`.

### Safe Partial Recovery Protocol:
If an interrupted or partial seed state is detected ($0 < \text{count} < 175$), or when explicit recovery is requested:
```bash
python -m scripts.seed_demo_data --recover-partial
```

#### Safe Recovery Boundary & Invariants:
1. **Safety Boundary Checks**:
   - Refuses deletion and rolls back if any non-seed runtime audit logs reference canonical transactions (`AuditLog.idempotency_key NOT IN EXACT_AUDIT_KEYS`).
   - Refuses deletion and rolls back if any analyst cases have active human workflow modifications (`case_status != 'OPEN'`, or non-null `assigned_analyst`, `resolution_note`, or `resolved_at`).
2. **Explicit Key Deletions**:
   - Deletions are strictly bounded to enumerated canonical primary keys (`CANONICAL_REFERENCES`) and exact audit keys (`EXACT_AUDIT_KEYS`).
   - Wildcard deletions (e.g. `LIKE 'canonical_seeded:%'`) are strictly prohibited.
3. **Merchant Audit Log Invariant**:
   - The merchant audit log (`canonical_seeded:merchant:pay_shield_demo`) is reconciled and guaranteed to exist even when the `merchants` row already pre-exists.
   - Recovery always yields exactly 176 canonical audit logs.
4. **All-or-Nothing Transaction Boundary**:
   - Deletion, re-insertion, and final field-by-field verification execute within a single atomic database transaction. If any validation fails, the entire recovery transaction is rolled back.

### Automated Recovery Test Suite:
Continuous verification of recovery and idempotency is provided in `backend/tests/test_seed_recovery.py`:
- **Scenario 1 (Empty State)**: Clean database seeds to 175 tx, 175 assessments, 14 cases, 176 audit logs.
- **Scenario 2 (Fully Seeded State)**: Idempotent run with `recover_partial=False` detects 175 records, verifies all 5 entity sets, and returns `VERIFIED_EXISTING` without mutation.
- **Scenario 3 (Partial State)**: Interrupted dataset fails standard run with `PartialSeedAbortedError` and recovers cleanly with `--recover-partial`.
- **Scenario 4 (Drifted State)**: Modified canonical record fails standard run with `SeedIntegrityError` and recovers cleanly with `--recover-partial`.
- **Scenario 5 (Runtime-Linked State)**: Runtime audit log or active analyst case modification blocks recovery with `SeedIntegrityError` and rolls back.
