"""Automated test suite for canonical seed verification, exact-match checking, and drift detection."""

from datetime import timedelta
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
    SeedIntegrityError,
    seed_canonical_data,
    verify_existing_canonical_seed,
    get_canonical_transaction_specs,
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


# -----------------------------------------------------------------------------
# Drift Detection Tests (Section 4)
# -----------------------------------------------------------------------------


def _get_spec_map():
    specs = get_canonical_transaction_specs()
    return {s["reference"]: s for s in specs}


def test_drift_transaction_created_at_timestamp(dev_db_session: Session) -> None:
    """Exact-match verification detects drift in transaction created_at timestamp."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    tx = dev_db_session.execute(select(Transaction).where(Transaction.reference == "tx_app_1001")).scalar_one()
    orig = tx.created_at
    try:
        tx.created_at = orig - timedelta(hours=2)
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "created_at timestamp drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_transaction_updated_at_timestamp(dev_db_session: Session) -> None:
    """Exact-match verification detects drift in transaction updated_at timestamp."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    tx = dev_db_session.execute(select(Transaction).where(Transaction.reference == "tx_app_1001")).scalar_one()
    orig = tx.updated_at
    try:
        tx.updated_at = orig + timedelta(minutes=10)
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "updated_at timestamp drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_risk_assessment_created_at_timestamp(dev_db_session: Session) -> None:
    """Exact-match verification detects drift in risk assessment created_at timestamp."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    tx = dev_db_session.execute(select(Transaction).where(Transaction.reference == "tx_app_1001")).scalar_one()
    ra = dev_db_session.execute(select(RiskAssessment).where(RiskAssessment.transaction_id == tx.id)).scalar_one()
    orig = ra.created_at
    try:
        ra.created_at = orig - timedelta(days=1)
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "created_at timestamp drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_analyst_case_created_at_timestamp(dev_db_session: Session) -> None:
    """Exact-match verification detects drift in canonical analyst case created_at timestamp."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    case = dev_db_session.execute(
        select(AnalystCase).join(Transaction).where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().first()
    assert case is not None
    orig = case.created_at
    try:
        case.created_at = orig - timedelta(minutes=45)
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "created_at timestamp drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_audit_log_created_at_timestamp(dev_db_session: Session) -> None:
    """Exact-match verification detects drift in audit log created_at timestamp."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    audit_log = dev_db_session.execute(
        select(AuditLog).where(AuditLog.idempotency_key == "canonical_seeded:tx:tx_app_1001")
    ).scalar_one()
    orig = audit_log.created_at
    try:
        audit_log.created_at = orig - timedelta(minutes=15)
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "created_at timestamp drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_merchant_name(dev_db_session: Session) -> None:
    """Exact-match verification detects changed merchant name."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    orig = merchant.name
    try:
        merchant.name = "Altered Merchant Name"
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "Merchant name drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_transaction_amount(dev_db_session: Session) -> None:
    """Exact-match verification detects changed transaction amount."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    tx = dev_db_session.execute(select(Transaction).where(Transaction.reference == "tx_app_1001")).scalar_one()
    orig = tx.amount
    try:
        tx.amount = Decimal("9999.00")
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "amount drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_risk_metadata_score(dev_db_session: Session) -> None:
    """Exact-match verification detects changed risk metadata score within allowed CHECK range."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    tx = dev_db_session.execute(select(Transaction).where(Transaction.reference == "tx_app_1001")).scalar_one()
    ra = dev_db_session.execute(select(RiskAssessment).where(RiskAssessment.transaction_id == tx.id)).scalar_one()
    orig = ra.risk_score
    try:
        ra.risk_score = 30  # Still LOW (0-39) to satisfy check constraint, but drifts from canonical 9
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "risk_score drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_analyst_case_trigger_reason(dev_db_session: Session) -> None:
    """Exact-match verification detects changed analyst case trigger reason."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    case = dev_db_session.execute(
        select(AnalystCase).join(Transaction).where(Transaction.reference.in_(CANONICAL_REFERENCES))
    ).scalars().first()
    orig = case.trigger_reason
    try:
        case.trigger_reason = "NEW_ACCOUNT"  # Valid in CHECK constraint, but drifts from canonical reason
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "trigger_reason drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_merchant_created_at_timestamp(dev_db_session: Session) -> None:
    """Exact-match verification detects drift in merchant created_at timestamp."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    orig = merchant.created_at
    try:
        merchant.created_at = orig - timedelta(hours=3)
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "Merchant created_at timestamp drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_merchant_updated_at_timestamp(dev_db_session: Session) -> None:
    """Exact-match verification detects drift in merchant updated_at timestamp."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    orig = merchant.updated_at
    try:
        merchant.updated_at = orig + timedelta(hours=1)
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "Merchant updated_at timestamp drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_drift_audit_log_details(dev_db_session: Session) -> None:
    """Exact-match verification detects tampered audit log details."""
    merchant = dev_db_session.execute(select(Merchant).where(Merchant.name == CANONICAL_MERCHANT_NAME)).scalar_one()
    audit_log = dev_db_session.execute(
        select(AuditLog).where(AuditLog.idempotency_key == "canonical_seeded:tx:tx_app_1001")
    ).scalar_one()
    orig = audit_log.details
    try:
        audit_log.details = {"reference": "tx_app_1001", "amount": "99999.00", "status": "APPROVED", "score": 25}
        dev_db_session.flush()
        with pytest.raises(SeedIntegrityError) as exc_info:
            verify_existing_canonical_seed(dev_db_session, merchant, _get_spec_map())
        assert "details drift" in str(exc_info.value)
    finally:
        dev_db_session.rollback()


def test_canonical_specs_exact_timestamp_equality_with_flutter() -> None:
    """Verify that all 175 transaction specs have exact UTC instants matching the Flutter fixture."""
    from datetime import datetime, timezone
    specs = get_canonical_transaction_specs()
    spec_map = {s["reference"]: s for s in specs}

    base_time = datetime(2026, 11, 4, 0, 0, 0, tzinfo=timezone.utc)

    # 1. 3 Blocked transactions
    assert spec_map["tx_c6b8d0f2_block"]["created_at"] == base_time - timedelta(minutes=12)
    assert spec_map["tx_7e9a4f10_block"]["created_at"] == base_time - timedelta(hours=1, minutes=40)
    assert spec_map["tx_3d2c1b99_block"]["created_at"] == base_time - timedelta(hours=3, minutes=15)

    # 2. 14 Review transactions
    for i in range(14):
        ref = f"tx_rev_{100 + i}"
        expected_dt = base_time - timedelta(hours=i + 1, minutes=i * 7)
        assert spec_map[ref]["created_at"] == expected_dt, f"Drift in {ref} timestamp"

    # 3. 158 Approved transactions
    for i in range(158):
        ref = f"tx_app_{1000 + i}"
        expected_dt = base_time - timedelta(minutes=(i + 1) * 14)
        assert spec_map[ref]["created_at"] == expected_dt, f"Drift in {ref} timestamp"
