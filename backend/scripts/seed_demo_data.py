"""Canonical Demo Seed System for PayShield.

Provides transactional, exact-match verified seeding with hardened partial recovery.
Seeds:
- 1 Demo Merchant
- 175 Transactions (158 approved, 14 review, 3 blocked)
- 175 Risk Assessments (CANONICAL_SEED)
- 14 Analyst Cases (with exact trigger_reason)
- 176 Audit Logs (exact deterministic idempotency keys)
"""

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys
from typing import Any
from sqlalchemy import String, create_engine, delete, func, select
from sqlalchemy.orm import Session

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.config import settings
from app.models import AnalystCase, AuditLog, Merchant, RiskAssessment, Transaction
from scripts.verify_canonical_fixture import (
    APPROVED_MERCHANTS,
    APPROVED_SEEDS,
    BLOCKED_TRANSACTIONS,
    REVIEW_TRANSACTIONS,
)

CANONICAL_MERCHANT_NAME = "PayShield Demo Merchant"
CANONICAL_MERCHANT_CATEGORY = "Retail"
CANONICAL_MERCHANT_AUDIT_KEY = "canonical_seeded:merchant:pay_shield_demo"

# Build canonical reference inventory
CANONICAL_REFERENCES: list[str] = (
    [x[0] for x in BLOCKED_TRANSACTIONS]
    + [x[0] for x in REVIEW_TRANSACTIONS]
    + [f"tx_app_{1000 + i}" for i in range(158)]
)
CANONICAL_REF_SET = set(CANONICAL_REFERENCES)

# Build explicitly enumerated audit keys (1 merchant + 175 transactions = 176 keys)
EXACT_AUDIT_KEYS: list[str] = [
    CANONICAL_MERCHANT_AUDIT_KEY
] + [f"canonical_seeded:tx:{ref}" for ref in CANONICAL_REFERENCES]


class SeedIntegrityError(Exception):
    """Raised when existing seed data exhibits drift, corruption, or unexpected dependencies."""


class PartialSeedAbortedError(Exception):
    """Raised when an incomplete seed state is detected and recovery was not opted into."""


def get_canonical_transaction_specs() -> list[dict[str, Any]]:
    """Build canonical transaction specification dictionary with remediated v1.0.1 amounts."""
    base_time = datetime(2026, 11, 4, 0, 0, 0, tzinfo=timezone.utc)
    specs: list[dict[str, Any]] = []

    # 1. 3 Blocked Transactions
    for i, (ref, amt, score, status, level, action, merch, cat) in enumerate(BLOCKED_TRANSACTIONS):
        specs.append(
            {
                "reference": ref,
                "counterparty_name": merch,
                "amount": amt,
                "currency": "BDT",
                "transaction_status": status,
                "device_model": "Suspicious / Emulated Device" if i == 0 else "Flagged Device",
                "location_city": "Sylhet" if i == 0 else "Chittagong",
                "is_location_anomaly": True,
                "risk_score": score,
                "risk_level": level,
                "recommended_action": action,
                "channel": "MOBILE_APP",
                "created_at": base_time - timedelta(minutes=15 * (i + 1)),
                "trigger_reason": None,
                "risk_factors": ["HIGH_VELOCITY", "SUSPICIOUS_IP", "DEVICE_MISMATCH"],
            }
        )

    # 2. 14 Review Transactions
    for i, (ref, amt, score, status, level, action, merch, cat, reason) in enumerate(REVIEW_TRANSACTIONS):
        specs.append(
            {
                "reference": ref,
                "counterparty_name": merch,
                "amount": amt,
                "currency": "BDT",
                "transaction_status": status,
                "device_model": "Samsung Galaxy A54",
                "location_city": "Dhaka" if i % 2 == 0 else "Khulna",
                "is_location_anomaly": reason == "DISTANCE_DELTA",
                "risk_score": score,
                "risk_level": level,
                "recommended_action": action,
                "channel": "MOBILE_APP",
                "created_at": base_time - timedelta(hours=i + 1, minutes=i * 5),
                "trigger_reason": reason,
                "risk_factors": [reason],
            }
        )

    # 3. 158 Approved Transactions (v1.0.1-canonical-remediated)
    for i in range(158):
        f_i = Decimal(APPROVED_SEEDS[i % len(APPROVED_SEEDS)] + ((i * 37) % 700))
        deduction = Decimal("346.00") if i <= 150 else Decimal("345.00")
        amt = f_i - deduction
        score = 8 + (i % 28)
        merch, _ = APPROVED_MERCHANTS[i % len(APPROVED_MERCHANTS)]
        ref = f"tx_app_{1000 + i}"
        specs.append(
            {
                "reference": ref,
                "counterparty_name": merch,
                "amount": amt,
                "currency": "BDT",
                "transaction_status": "APPROVED",
                "device_model": "Verified Customer Device",
                "location_city": "Dhaka",
                "is_location_anomaly": False,
                "risk_score": score,
                "risk_level": "LOW",
                "recommended_action": "APPROVE",
                "channel": "MOBILE_APP",
                "created_at": base_time - timedelta(minutes=(i + 1) * 14),
                "trigger_reason": None,
                "risk_factors": [],
            }
        )

    return specs


def verify_existing_canonical_seed(
    session: Session,
    merchant: Merchant,
    spec_map: dict[str, dict[str, Any]],
) -> None:
    """Perform rigorous, field-by-field verification of all 5 canonical entity layers."""
    # 1. Verify Merchant
    if merchant.name != CANONICAL_MERCHANT_NAME:
        raise SeedIntegrityError(f"Merchant name drift: {merchant.name} != {CANONICAL_MERCHANT_NAME}")
    if merchant.category != CANONICAL_MERCHANT_CATEGORY:
        raise SeedIntegrityError(f"Merchant category drift: {merchant.category} != {CANONICAL_MERCHANT_CATEGORY}")
    if merchant.status != "ACTIVE":
        raise SeedIntegrityError(f"Merchant status drift: {merchant.status} != ACTIVE")

    # Verify Merchant Audit Log
    merchant_log = session.execute(
        select(AuditLog).where(AuditLog.idempotency_key == CANONICAL_MERCHANT_AUDIT_KEY)
    ).scalar_one_or_none()
    if merchant_log is None:
        raise SeedIntegrityError("Merchant canonical audit log is missing")
    if merchant_log.action != "CANONICAL_RECORD_SEEDED":
        raise SeedIntegrityError(f"Merchant audit log action drift: {merchant_log.action}")
    if merchant_log.actor_type != "SYSTEM" or merchant_log.actor_id != "canonical_seed_runner":
        raise SeedIntegrityError(f"Merchant audit log actor drift: {merchant_log.actor_type}/{merchant_log.actor_id}")
    if str(merchant_log.entity_id) != str(merchant.id):
        raise SeedIntegrityError("Merchant audit log entity linkage drift")
    expected_merchant_details = {"merchant_name": merchant.name, "category": merchant.category}
    if merchant_log.details != expected_merchant_details:
        raise SeedIntegrityError(f"Merchant audit log details drift: {merchant_log.details}")

    # 2. Verify Transactions (All 175)
    txs = session.execute(
        select(Transaction).where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().all()
    if len(txs) != 175:
        raise SeedIntegrityError(f"Expected 175 canonical transactions, found {len(txs)}")

    tx_map: dict[str, Transaction] = {t.reference: t for t in txs}
    for ref, expected in spec_map.items():
        if ref not in tx_map:
            raise SeedIntegrityError(f"Missing canonical transaction {ref}")
        tx = tx_map[ref]
        if tx.merchant_id != merchant.id:
            raise SeedIntegrityError(f"Transaction {ref} merchant linkage drift")
        if tx.counterparty_name != expected["counterparty_name"]:
            raise SeedIntegrityError(f"Transaction {ref} counterparty drift: {tx.counterparty_name} != {expected['counterparty_name']}")
        if tx.amount != expected["amount"]:
            raise SeedIntegrityError(f"Transaction {ref} amount drift: {tx.amount} != {expected['amount']}")
        if tx.currency != expected["currency"]:
            raise SeedIntegrityError(f"Transaction {ref} currency drift: {tx.currency} != {expected['currency']}")
        if tx.transaction_status != expected["transaction_status"]:
            raise SeedIntegrityError(f"Transaction {ref} status drift: {tx.transaction_status} != {expected['transaction_status']}")
        if tx.device_model != expected["device_model"]:
            raise SeedIntegrityError(f"Transaction {ref} device_model drift: {tx.device_model} != {expected['device_model']}")
        if tx.location_city != expected["location_city"]:
            raise SeedIntegrityError(f"Transaction {ref} location_city drift: {tx.location_city} != {expected['location_city']}")
        if tx.is_location_anomaly != expected["is_location_anomaly"]:
            raise SeedIntegrityError(f"Transaction {ref} location anomaly drift: {tx.is_location_anomaly}")
        if tx.risk_score != expected["risk_score"]:
            raise SeedIntegrityError(f"Transaction {ref} risk_score drift: {tx.risk_score} != {expected['risk_score']}")
        if tx.risk_level != expected["risk_level"]:
            raise SeedIntegrityError(f"Transaction {ref} risk_level drift: {tx.risk_level} != {expected['risk_level']}")
        if tx.recommended_action != expected["recommended_action"]:
            raise SeedIntegrityError(f"Transaction {ref} action drift: {tx.recommended_action} != {expected['recommended_action']}")
        if tx.channel != expected["channel"]:
            raise SeedIntegrityError(f"Transaction {ref} channel drift: {tx.channel} != {expected['channel']}")

    # 3. Verify Risk Assessments (All 175)
    assessments = session.execute(
        select(RiskAssessment)
        .join(Transaction)
        .where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().all()
    if len(assessments) != 175:
        raise SeedIntegrityError(f"Expected 175 risk assessments, found {len(assessments)}")

    ra_by_tx_id = {ra.transaction_id: ra for ra in assessments}
    for ref, expected in spec_map.items():
        tx = tx_map[ref]
        if tx.id not in ra_by_tx_id:
            raise SeedIntegrityError(f"Missing risk assessment for transaction {ref}")
        ra = ra_by_tx_id[tx.id]
        if ra.scoring_method != "CANONICAL_SEED":
            raise SeedIntegrityError(f"Assessment for {ref} scoring_method drift: {ra.scoring_method}")
        if ra.policy_version != "1.0.0":
            raise SeedIntegrityError(f"Assessment for {ref} policy_version drift: {ra.policy_version}")
        if ra.risk_score != expected["risk_score"]:
            raise SeedIntegrityError(f"Assessment for {ref} risk_score drift: {ra.risk_score} != {expected['risk_score']}")
        if ra.risk_level != expected["risk_level"]:
            raise SeedIntegrityError(f"Assessment for {ref} risk_level drift: {ra.risk_level} != {expected['risk_level']}")
        if ra.recommended_action != expected["recommended_action"]:
            raise SeedIntegrityError(f"Assessment for {ref} action drift: {ra.recommended_action} != {expected['recommended_action']}")
        if ra.base_score is not None or ra.raw_score is not None or ra.is_score_clamped is not None:
            raise SeedIntegrityError(f"Assessment for {ref} non-null canonical scores")
        if ra.risk_factors != expected["risk_factors"]:
            raise SeedIntegrityError(f"Assessment for {ref} risk_factors drift: {ra.risk_factors} != {expected['risk_factors']}")
        if ra.feature_contributions != []:
            raise SeedIntegrityError(f"Assessment for {ref} non-empty feature_contributions")

    # 4. Verify Analyst Cases (All 14)
    cases = session.execute(
        select(AnalystCase)
        .join(Transaction)
        .where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().all()
    if len(cases) != 14:
        raise SeedIntegrityError(f"Expected 14 analyst cases, found {len(cases)}")

    cases_by_tx_id = {c.transaction_id: c for c in cases}
    for ref, expected in spec_map.items():
        if expected["transaction_status"] == "REVIEW":
            tx = tx_map[ref]
            if tx.id not in cases_by_tx_id:
                raise SeedIntegrityError(f"Missing analyst case for review transaction {ref}")
            c = cases_by_tx_id[tx.id]
            if c.case_status != "OPEN":
                raise SeedIntegrityError(f"Case for {ref} status drift: {c.case_status} != OPEN")
            if c.priority != "MEDIUM":
                raise SeedIntegrityError(f"Case for {ref} priority drift: {c.priority} != MEDIUM")
            if c.trigger_reason != expected["trigger_reason"]:
                raise SeedIntegrityError(f"Case for {ref} trigger_reason drift: {c.trigger_reason} != {expected['trigger_reason']}")
            if c.assigned_analyst is not None:
                raise SeedIntegrityError(f"Case for {ref} assigned_analyst is not None: {c.assigned_analyst}")
            if c.resolution_note is not None:
                raise SeedIntegrityError(f"Case for {ref} resolution_note is not None: {c.resolution_note}")
            if c.resolved_at is not None:
                raise SeedIntegrityError(f"Case for {ref} resolved_at is not None: {c.resolved_at}")

    # 5. Verify Audit Logs (All 176)
    canonical_logs = session.execute(
        select(AuditLog).where(AuditLog.idempotency_key.in_(EXACT_AUDIT_KEYS))
    ).scalars().all()
    if len(canonical_logs) != 176:
        raise SeedIntegrityError(f"Expected 176 canonical audit logs, found {len(canonical_logs)}")

    logs_by_key = {l.idempotency_key: l for l in canonical_logs}
    for ref, expected in spec_map.items():
        expected_key = f"canonical_seeded:tx:{ref}"
        if expected_key not in logs_by_key:
            raise SeedIntegrityError(f"Missing audit log for transaction {ref}")
        l = logs_by_key[expected_key]
        tx = tx_map[ref]
        if str(l.entity_id) != str(tx.id):
            raise SeedIntegrityError(f"Audit log {expected_key} entity_id linkage drift")
        if l.entity_type != "transaction":
            raise SeedIntegrityError(f"Audit log {expected_key} entity_type drift: {l.entity_type}")
        if l.action != "CANONICAL_RECORD_SEEDED":
            raise SeedIntegrityError(f"Audit log {expected_key} action drift: {l.action}")
        if l.actor_type != "SYSTEM" or l.actor_id != "canonical_seed_runner":
            raise SeedIntegrityError(f"Audit log {expected_key} actor drift: {l.actor_type}/{l.actor_id}")
        expected_details = {
            "reference": tx.reference,
            "amount": str(tx.amount),
            "status": tx.transaction_status,
            "score": tx.risk_score,
        }
        if l.details != expected_details:
            raise SeedIntegrityError(f"Audit log {expected_key} details drift: {l.details} != {expected_details}")


def assert_safe_recovery_boundary(session: Session) -> None:
    """Verify that canonical seed records have no external runtime dependencies before deletion."""
    # Check 1: Runtime audit logs referencing canonical transactions
    runtime_audit_deps = session.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "transaction",
            AuditLog.entity_id.in_(
                select(func.cast(Transaction.id, String)).where(Transaction.reference.in_(CANONICAL_REFERENCES))
            ),
            AuditLog.idempotency_key.not_in(EXACT_AUDIT_KEYS),
        )
    ).scalars().all()
    if runtime_audit_deps:
        raise SeedIntegrityError(
            f"Recovery aborted: {len(runtime_audit_deps)} runtime audit logs reference canonical transactions. "
            "Refusing to delete records with external runtime dependencies."
        )

    # Check 2: Active or modified human workflow cases
    modified_cases = session.execute(
        select(AnalystCase).where(
            AnalystCase.transaction_id.in_(
                select(Transaction.id).where(Transaction.reference.in_(CANONICAL_REFERENCES))
            ),
            (AnalystCase.case_status != "OPEN")
            | (AnalystCase.assigned_analyst.is_not(None))
            | (AnalystCase.resolution_note.is_not(None))
            | (AnalystCase.resolved_at.is_not(None)),
        )
    ).scalars().all()
    if modified_cases:
        raise SeedIntegrityError(
            f"Recovery aborted: {len(modified_cases)} analyst cases have active human workflow state. "
            "Refusing to delete records with active analyst modifications."
        )


def seed_canonical_data(
    session: Session,
    recover_partial: bool = False,
) -> dict[str, Any]:
    """Execute transactional exact-match verified seeding with safe partial recovery."""
    specs = get_canonical_transaction_specs()
    spec_map = {s["reference"]: s for s in specs}

    merchant = session.execute(
        select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)
    ).scalar_one_or_none()

    existing_txs = session.execute(
        select(Transaction).where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().all()
    existing_count = len(existing_txs)

    # Clean slate (count == 0 and merchant is None or unseeded)
    if existing_count == 0 and merchant is None:
        print("Clean slate database detected. Inserting canonical dataset...")
    elif existing_count == 175 and merchant is not None:
        if not recover_partial:
            print("Existing 175 canonical transactions detected. Verifying all fields...")
            verify_existing_canonical_seed(session, merchant, spec_map)
            print("100% exact match verified across all 5 canonical entity sets. Database intact.")
            return {"status": "VERIFIED_EXISTING", "count": 175}
        print("Existing 175 canonical transactions detected. Safe recovery/re-seed explicitly requested...")
    else:
        # Partial transaction count (0 < count < 175) or incomplete merchant state
        if not recover_partial:
            raise PartialSeedAbortedError(
                f"Detected incomplete canonical seed state ({existing_count}/175 transactions). "
                "Re-run with --recover-partial to safely remove canonical seed records and reseed."
            )
        print(f"Partial canonical seed state detected ({existing_count}/175). Initiating recovery...")

    # Execute Safe Recovery if required
    if recover_partial or existing_count > 0 or merchant is not None:
        print("Checking safety boundary for canonical records...")
        assert_safe_recovery_boundary(session)

        print("Deleting explicitly enumerated seed-owned records...")
        # 1. Delete seed-owned audit logs (explicit keys only)
        session.execute(
            delete(AuditLog).where(AuditLog.idempotency_key.in_(EXACT_AUDIT_KEYS))
        )
        # 2. Delete seed-owned analyst cases
        session.execute(
            delete(AnalystCase).where(
                AnalystCase.transaction_id.in_(
                    select(Transaction.id).where(Transaction.reference.in_(CANONICAL_REFERENCES))
                )
            )
        )
        # 3. Delete seed-owned risk assessments
        session.execute(
            delete(RiskAssessment).where(
                RiskAssessment.transaction_id.in_(
                    select(Transaction.id).where(Transaction.reference.in_(CANONICAL_REFERENCES))
                )
            )
        )
        # 4. Delete canonical transactions
        session.execute(
            delete(Transaction).where(Transaction.reference.in_(CANONICAL_REFERENCES))
        )
        session.flush()
        print("Safe deletion of canonical records complete.")

    # Reseed Merchant
    if merchant is None:
        merchant = Merchant(
            name=CANONICAL_MERCHANT_NAME,
            category=CANONICAL_MERCHANT_CATEGORY,
            status="ACTIVE",
        )
        session.add(merchant)
        session.flush()

    # Ensure Merchant Audit Log always exists (even when merchant row pre-existed)
    merchant_audit = session.execute(
        select(AuditLog).where(AuditLog.idempotency_key == CANONICAL_MERCHANT_AUDIT_KEY)
    ).scalar_one_or_none()
    if merchant_audit is None:
        session.add(
            AuditLog(
                actor_type="SYSTEM",
                actor_id="canonical_seed_runner",
                action="CANONICAL_RECORD_SEEDED",
                entity_type="merchant",
                entity_id=merchant.id,
                idempotency_key=CANONICAL_MERCHANT_AUDIT_KEY,
                details={"merchant_name": merchant.name, "category": merchant.category},
            )
        )
        session.flush()

    # Reseed 175 Transactions, Assessments, Cases, and Audit Logs
    print("Inserting 175 canonical transactions, assessments, cases, and audit logs...")
    for spec in specs:
        tx = Transaction(
            reference=spec["reference"],
            merchant_id=merchant.id,
            counterparty_name=spec["counterparty_name"],
            amount=spec["amount"],
            currency=spec["currency"],
            transaction_status=spec["transaction_status"],
            device_model=spec["device_model"],
            location_city=spec["location_city"],
            is_location_anomaly=spec["is_location_anomaly"],
            risk_score=spec["risk_score"],
            risk_level=spec["risk_level"],
            recommended_action=spec["recommended_action"],
            channel=spec["channel"],
            created_at=spec["created_at"],
            updated_at=spec["created_at"],
        )
        session.add(tx)
        session.flush()

        # Risk assessment
        ra = RiskAssessment(
            transaction_id=tx.id,
            base_score=None,
            raw_score=None,
            risk_score=tx.risk_score,
            is_score_clamped=None,
            risk_level=tx.risk_level,
            recommended_action=tx.recommended_action,
            scoring_method="CANONICAL_SEED",
            policy_version="1.0.0",
            risk_factors=spec["risk_factors"],
            feature_contributions=[],
            created_at=tx.created_at,
        )
        session.add(ra)

        # Analyst case if REVIEW transaction
        if spec["transaction_status"] == "REVIEW":
            case = AnalystCase(
                transaction_id=tx.id,
                case_status="OPEN",
                priority="MEDIUM",
                trigger_reason=spec["trigger_reason"],
                created_at=tx.created_at,
                updated_at=tx.created_at,
            )
            session.add(case)

        # Audit log for transaction
        session.add(
            AuditLog(
                actor_type="SYSTEM",
                actor_id="canonical_seed_runner",
                action="CANONICAL_RECORD_SEEDED",
                entity_type="transaction",
                entity_id=tx.id,
                idempotency_key=f"canonical_seeded:tx:{tx.reference}",
                details={
                    "reference": tx.reference,
                    "amount": str(tx.amount),
                    "status": tx.transaction_status,
                    "score": tx.risk_score,
                },
                created_at=tx.created_at,
            )
        )

    session.flush()

    # Final Exact-Match Verification of the newly seeded dataset
    verify_existing_canonical_seed(session, merchant, spec_map)
    session.commit()
    print("100% exact match verified across all 5 canonical entity sets. Database intact.")
    return {"status": "SUCCESS_SEEDED", "count": 175}


def main():
    parser = argparse.ArgumentParser(description="PayShield Canonical Demo Seed System")
    parser.add_argument(
        "--recover-partial",
        action="store_true",
        help="Safely remove partially seeded canonical records and re-seed clean dataset.",
    )
    args = parser.parse_args()

    url = settings.get_migration_sqlalchemy_url().set(database="payshield_dev")
    engine = create_engine(url)

    print("Connecting as payshield_migrator to payshield_dev on 127.0.0.1...")
    with Session(engine) as session:
        seed_canonical_data(session, recover_partial=args.recover_partial)


if __name__ == "__main__":
    main()
