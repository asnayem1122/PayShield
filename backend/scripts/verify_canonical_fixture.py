"""Canonical Fixture Lineage and Arithmetic Verification Script.

Inspects the canonical transaction fixture, establishes forensic lineage for tx_app_1157,
and verifies mathematical totals using Python Decimal.
"""

from decimal import Decimal
import sys

# Approved seed amounts from Dart fixture
APPROVED_SEEDS = [
    1850, 1600, 1450, 2100, 1950, 1300, 2200, 1750, 2400, 1250,
    1900, 1700, 1550, 2050, 1800, 1400, 2150, 1650, 2300, 1350,
]

APPROVED_MERCHANTS = [
    ("TechPulse Gadgets Ltd", "Electronics"),
    ("Aarong Lifestyle", "Fashion"),
    ("Shwapno Superstore", "Grocery"),
    ("Bata Bangladesh", "Footwear"),
    ("Chaldal Express", "Grocery"),
    ("Daraz Bangladesh", "Retail"),
]

BLOCKED_TRANSACTIONS = [
    ("tx_c6b8d0f2_block", Decimal("12500.00"), 91, "BLOCKED", "HIGH", "BLOCK", "TechPulse Gadgets Ltd", "Electronics"),
    ("tx_7e9a4f10_block", Decimal("24000.00"), 88, "BLOCKED", "HIGH", "BLOCK", "Dhaka Luxe Watch Boutique", "Jewelry"),
    ("tx_3d2c1b99_block", Decimal("18500.00"), 79, "BLOCKED", "HIGH", "BLOCK", "Apex Digital Hub", "Digital Goods"),
]

REVIEW_TRANSACTIONS = [
    ("tx_rev_100", Decimal("8500.00"), 58, "REVIEW", "MEDIUM", "REVIEW", "Shwapno Superstore", "Grocery", "UNUSUAL_HOUR"),
    ("tx_rev_101", Decimal("14200.00"), 68, "REVIEW", "MEDIUM", "REVIEW", "TechPulse Gadgets Ltd", "Electronics", "NEW_DEVICE"),
    ("tx_rev_102", Decimal("9800.00"), 52, "REVIEW", "MEDIUM", "REVIEW", "Aarong Lifestyle", "Fashion", "VELOCITY_WARN"),
    ("tx_rev_103", Decimal("11500.00"), 71, "REVIEW", "MEDIUM", "REVIEW", "Yellow Clothing Ltd", "Fashion", "HIGH_AMOUNT"),
    ("tx_rev_104", Decimal("7400.00"), 48, "REVIEW", "MEDIUM", "REVIEW", "Daraz Bangladesh Express", "Retail", "DISTANCE_DELTA"),
    ("tx_rev_105", Decimal("16000.00"), 74, "REVIEW", "MEDIUM", "REVIEW", "Star Tech IT Corner", "Electronics", "MULTIPLE_CARDS"),
    ("tx_rev_106", Decimal("8900.00"), 61, "REVIEW", "MEDIUM", "REVIEW", "Ryans Computers Ltd", "Electronics", "DEVICE_MISMATCH"),
    ("tx_rev_107", Decimal("10200.00"), 55, "REVIEW", "MEDIUM", "REVIEW", "Pickaboo Mobile Store", "Electronics", "NEW_ACCOUNT"),
    ("tx_rev_108", Decimal("12800.00"), 67, "REVIEW", "MEDIUM", "REVIEW", "Chaldal Premium Store", "Grocery", "VELOCITY_WARN"),
    ("tx_rev_109", Decimal("6500.00"), 44, "REVIEW", "MEDIUM", "REVIEW", "Sailor Outlet", "Fashion", "OFF_HOURS"),
    ("tx_rev_110", Decimal("9100.00"), 59, "REVIEW", "MEDIUM", "REVIEW", "Lotto Bangladesh Ltd", "Footwear", "DISTANCE_DELTA"),
    ("tx_rev_111", Decimal("13400.00"), 72, "REVIEW", "MEDIUM", "REVIEW", "TechPulse Gadgets Ltd", "Electronics", "NEW_DEVICE"),
    ("tx_rev_112", Decimal("7800.00"), 46, "REVIEW", "MEDIUM", "REVIEW", "Agora Superstore", "Grocery", "UNUSUAL_HOUR"),
    ("tx_rev_113", Decimal("11200.00"), 65, "REVIEW", "MEDIUM", "REVIEW", "Cats Eye Fashion", "Fashion", "HIGH_AMOUNT"),
]


def run_verification() -> bool:
    print("=" * 70)
    print("PAYSHIELD CANONICAL FIXTURE VERIFICATION & LINEAGE REPORT")
    print("=" * 70)

    # 1. Unscaled Formula Evaluation
    unscaled_approved = []
    for i in range(158):
        val = Decimal(APPROVED_SEEDS[i % len(APPROVED_SEEDS)] + ((i * 37) % 700))
        unscaled_approved.append(val)

    unscaled_sum = sum(unscaled_approved)
    target_approved_sum = Decimal("280200.00")
    surplus = unscaled_sum - target_approved_sum

    print(f"1. Unscaled Generator Formula Total: {unscaled_sum} BDT")
    print(f"   Target Approved Volume:          {target_approved_sum} BDT")
    print(f"   Generator Excess Surplus:        {surplus} BDT")

    # 2. Historical Negative Row Derivation (Commit 3fb737e)
    accum_156 = sum(unscaled_approved[:157])
    v100_row157 = target_approved_sum - accum_156
    f157 = unscaled_approved[157]

    print(f"\n2. Lineage Analysis of tx_app_1157:")
    print(f"   Unscaled Formula Value (F_157):  {f157} BDT")
    print(f"   Accumulated Sum (Rows 0..156):   {accum_156} BDT")
    print(f"   v1.0.0 Remainder Subtraction:    {target_approved_sum} - {accum_156} = {v100_row157} BDT")
    print(f"   Discrepancy (F_157 - v1.0.0):    {f157 - v100_row157} BDT (Exact Excess Surplus)")

    # 3. Remediated Canonical Schedule (v1.0.1)
    remediated_approved = []
    for i in range(158):
        f_i = unscaled_approved[i]
        deduction = Decimal("346.00") if i <= 150 else Decimal("345.00")
        remediated_amt = f_i - deduction
        score = 8 + (i % 28)
        merch, cat = APPROVED_MERCHANTS[i % len(APPROVED_MERCHANTS)]
        ref = f"tx_app_{1000 + i}"
        remediated_approved.append((ref, remediated_amt, score, "APPROVED", "LOW", "APPROVE", merch, cat))

    remediated_approved_sum = sum(x[1] for x in remediated_approved)
    v101_row157 = remediated_approved[157][1]

    print(f"\n3. Remediated Canonical Schedule (v1.0.1):")
    print(f"   Deduction Schedule:              151 x 346.00 + 7 x 345.00 = 54,661.00 BDT")
    print(f"   Remediated tx_app_1157 Amount:   {f157} - 345.00 = {v101_row157} BDT")
    print(f"   Remediated Approved Sum:         {remediated_approved_sum} BDT")
    print(f"   All Approved Amounts Positive:   {all(x[1] > Decimal('0.00') for x in remediated_approved)}")
    print(f"   Min Amount:                      {min(x[1] for x in remediated_approved)} BDT")
    print(f"   Max Amount:                      {max(x[1] for x in remediated_approved)} BDT")

    # 4. Global Dataset Totals
    blocked_sum = sum(x[1] for x in BLOCKED_TRANSACTIONS)
    review_sum = sum(x[1] for x in REVIEW_TRANSACTIONS)
    total_volume = blocked_sum + review_sum + remediated_approved_sum

    all_scores = [x[2] for x in BLOCKED_TRANSACTIONS] + [x[2] for x in REVIEW_TRANSACTIONS] + [x[2] for x in remediated_approved]
    score_sum = sum(all_scores)
    exact_mean = Decimal(score_sum) / Decimal(len(all_scores))
    rounded_mean = round(exact_mean)

    all_refs = [x[0] for x in BLOCKED_TRANSACTIONS] + [x[0] for x in REVIEW_TRANSACTIONS] + [x[0] for x in remediated_approved]
    unique_refs = set(all_refs)

    print(f"\n4. Global Dataset Assertions:")
    print(f"   Total Transactions:              {len(all_refs)} (Unique: {len(unique_refs)})")
    print(f"   Blocked Volume (3 txs):          {blocked_sum} BDT")
    print(f"   Review Volume (14 txs):          {review_sum} BDT")
    print(f"   Approved Volume (158 txs):       {remediated_approved_sum} BDT")
    print(f"   Total Canonical Volume:          {total_volume} BDT")
    print(f"   Score Sum:                       {score_sum}")
    print(f"   Score Exact Mean:                {exact_mean:.8f}")
    print(f"   Score Rounded Mean:              {rounded_mean}")

    # Invariant Checks
    assert len(all_refs) == 175, "Total count must be 175"
    assert len(unique_refs) == 175, "All references must be unique"
    assert blocked_sum == Decimal("55000.00"), "Blocked volume must be 55,000.00 BDT"
    assert review_sum == Decimal("147300.00"), "Review volume must be 147,300.00 BDT"
    assert remediated_approved_sum == Decimal("280200.00"), "Approved volume must be 280,200.00 BDT"
    assert total_volume == Decimal("482500.00"), "Total volume must be 482,500.00 BDT"
    assert score_sum == 4405, "Score sum must be 4,405"
    assert rounded_mean == 25, "Rounded mean must be 25"

    print("\nALL INVARIANTS SATISFIED SUCCESSFULLY.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
