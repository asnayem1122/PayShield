"""Automated test suite for canonical seed verification, exact-match checking, and recovery."""

from decimal import Decimal
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AnalystCase, AuditLog, Merchant, RiskAssessment, Transaction
from scripts.seed_demo_data import (
    CANONICAL_REFERENCES,
    CANONICAL_MERCHANT_NAME,
    EXACT_AUDIT_KEYS,
    PartialSeedAbortedError,
    SeedIntegrityError,
    seed_canonical_data,
)


@pytest.fixture(scope="module")
def dev_db_session():
    """Session connected to payshield_dev as payshield_migrator."""
    engine = create_engine(settings.get_migration_sqlalchemy_url())
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_canonical_seed_integrity_mode_a(dev_db_session: Session) -> None:
    """Mode A: Verify the persistent canonical seed in payshield_dev satisfies all invariants."""
    # 1. Merchant verification
    merchant = dev_db_session.execute(
        select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)
    ).scalar_one_or_none()
    assert merchant is not None
    assert merchant.category == "Retail"
    assert merchant.status == "ACTIVE"

    # 2. Transaction counts and status distribution
    txs = dev_db_session.execute(
        select(Transaction).where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().all()
    assert len(txs) == 175

    approved_txs = [t for t in txs if t.transaction_status == "APPROVED"]
    review_txs = [t for t in txs if t.transaction_status == "REVIEW"]
    blocked_txs = [t for t in txs if t.transaction_status == "BLOCKED"]

    assert len(approved_txs) == 158
    assert len(review_txs) == 14
    assert len(blocked_txs) == 3

    # 3. Exact financial volumes
    app_vol = sum(t.amount for t in approved_txs)
    rev_vol = sum(t.amount for t in review_txs)
    blk_vol = sum(t.amount for t in blocked_txs)
    tot_vol = sum(t.amount for t in txs)

    assert app_vol == Decimal("280200.00")
    assert rev_vol == Decimal("147300.00")
    assert blk_vol == Decimal("55000.00")
    assert tot_vol == Decimal("482500.00")

    # 4. Strictly positive amounts
    assert all(t.amount > Decimal("0.00") for t in txs)
    min_app = min(t.amount for t in approved_txs)
    max_app = max(t.amount for t in approved_txs)
    assert min_app == Decimal("1007.00")
    assert max_app == Decimal("2630.00")

    # Row 157 remediation check
    tx_1157 = next(t for t in txs if t.reference == "tx_app_1157")
    assert tx_1157.amount == Decimal("1514.00")

    # 5. Risk score statistics
    score_sum = sum(t.risk_score for t in txs)
    assert score_sum == 4405
    exact_mean = Decimal(score_sum) / Decimal(len(txs))
    assert round(exact_mean) == 25

    # 6. Risk assessments verification
    assessments = dev_db_session.execute(
        select(RiskAssessment)
        .join(Transaction)
        .where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().all()
    assert len(assessments) == 175
    for ra in assessments:
        assert ra.scoring_method == "CANONICAL_SEED"
        assert ra.policy_version == "1.0.0"
        assert ra.base_score is None
        assert ra.raw_score is None
        assert ra.is_score_clamped is None

    # 7. Analyst cases verification
    cases = dev_db_session.execute(
        select(AnalystCase)
        .join(Transaction)
        .where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().all()
    assert len(cases) == 14
    for c in cases:
        assert c.case_status == "OPEN"
        assert c.priority == "MEDIUM"
        assert c.trigger_reason is not None
        assert len(c.trigger_reason) > 0
        assert c.resolved_at is None

    # 8. Audit logs verification (exact 176 keys)
    audit_logs = dev_db_session.execute(
        select(AuditLog).where(AuditLog.idempotency_key.in_(EXACT_AUDIT_KEYS))
    ).scalars().all()
    assert len(audit_logs) == 176


def test_idempotent_rerun_preserves_exact_match(dev_db_session: Session) -> None:
    """Verify that re-running seed_canonical_data verifies exact match and modifies 0 records."""
    result = seed_canonical_data(dev_db_session, recover_partial=False)
    assert result["status"] == "VERIFIED_EXISTING"
    assert result["count"] == 175
