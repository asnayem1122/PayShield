"""
PayShield Phase 2 - Canonical Seed Verification and Safe Recovery Test Suite.

Verifies all ten required recovery scenarios against PostgreSQL (payshield_test):
1. Empty database recovery.
2. Normal canonical seed recovery (idempotent verification).
3. Partial canonical seed recovery.
4. Runtime heuristic assessment attached to a canonical transaction blocks recovery (mandatory).
5. Runtime audit event attached to a canonical transaction blocks recovery.
6. Modified analyst case blocks recovery.
7. Modified canonical transaction triggers drift error on standard run and recovers cleanly.
8. Unexpected runtime audit log on merchant blocks recovery.
9. Failed recovery guarantees atomic database rollback.
10. Successful recovery restores exact canonical counts across all 5 layers (176 audit logs).
"""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, delete, func, select
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
    get_canonical_transaction_specs,
)


@pytest.fixture(scope="module")
def test_db_session():
    """Admin/migrator session connected to payshield_test."""
    url = settings.get_migration_sqlalchemy_url().set(database="payshield_test")
    engine = create_engine(url)
    with Session(engine) as session:
        _clean_test_db(session)
        yield session
        _clean_test_db(session)
    engine.dispose()


def _clean_test_db(session: Session) -> None:
    """Helper to remove all records from payshield_test in dependency order."""
    session.rollback()
    session.execute(delete(AuditLog))
    session.execute(delete(AnalystCase))
    session.execute(delete(RiskAssessment))
    session.execute(delete(Transaction))
    session.execute(delete(Merchant))
    session.commit()


def _ensure_clean_seed(session: Session) -> None:
    """Helper to reset database to 100% clean canonical state."""
    _clean_test_db(session)
    seed_canonical_data(session, recover_partial=False)


def test_scenario_1_empty_state_seeding(test_db_session: Session):
    """Scenario 1: Fresh/empty database seeds to full canonical specification."""
    _clean_test_db(test_db_session)

    res = seed_canonical_data(test_db_session, recover_partial=False)
    assert res["status"] == "SUCCESS_SEEDED"
    assert res["count"] == 175

    # Verify counts
    merchant = test_db_session.execute(select(Merchant)).scalar_one()
    assert merchant.name == CANONICAL_MERCHANT_NAME

    tx_count = test_db_session.execute(select(func.count(Transaction.id))).scalar()
    ra_count = test_db_session.execute(select(func.count(RiskAssessment.id))).scalar()
    case_count = test_db_session.execute(select(func.count(AnalystCase.id))).scalar()
    audit_count = test_db_session.execute(select(func.count(AuditLog.id))).scalar()

    assert tx_count == 175
    assert ra_count == 175
    assert case_count == 14
    assert audit_count == 176


def test_scenario_2_fully_seeded_idempotency(test_db_session: Session):
    """Scenario 2: Rerunning seed on fully intact database verifies without modifying records."""
    res = seed_canonical_data(test_db_session, recover_partial=False)
    assert res["status"] == "VERIFIED_EXISTING"
    assert res["count"] == 175


def test_scenario_3_partial_state_recovery(test_db_session: Session):
    """Scenario 3: Incomplete dataset fails standard run and recovers cleanly with recover_partial."""
    test_db_session.rollback()
    subset_refs = CANONICAL_REFERENCES[:50]
    sub_tx_ids = test_db_session.execute(
        select(Transaction.id).where(Transaction.reference.in_(subset_refs))
    ).scalars().all()

    test_db_session.execute(
        delete(AuditLog).where(AuditLog.idempotency_key.in_([f"canonical_seeded:tx:{r}" for r in subset_refs]))
    )
    test_db_session.execute(
        delete(AnalystCase).where(AnalystCase.transaction_id.in_(sub_tx_ids))
    )
    test_db_session.execute(
        delete(RiskAssessment).where(RiskAssessment.transaction_id.in_(sub_tx_ids))
    )
    test_db_session.execute(
        delete(Transaction).where(Transaction.id.in_(sub_tx_ids))
    )
    test_db_session.commit()

    # Verify count is now 125
    remaining_tx = test_db_session.execute(select(func.count(Transaction.id))).scalar()
    assert remaining_tx == 125

    # Standard run must abort with PartialSeedAbortedError
    with pytest.raises(PartialSeedAbortedError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=False)
    assert "125/175" in str(exc_info.value)

    # Recovery run with recover_partial=True must safely reconstruct full dataset
    res = seed_canonical_data(test_db_session, recover_partial=True)
    assert res["status"] == "SUCCESS_SEEDED"
    assert res["count"] == 175

    assert test_db_session.execute(select(func.count(Transaction.id))).scalar() == 175
    assert test_db_session.execute(select(func.count(AuditLog.id))).scalar() == 176


def test_scenario_4_runtime_heuristic_assessment_blocks_recovery(test_db_session: Session):
    """Scenario 4: Mandatory test - runtime HEURISTIC_RULES_V1 assessment attached to canonical tx aborts recovery."""
    _ensure_clean_seed(test_db_session)
    tx_1001 = test_db_session.execute(
        select(Transaction).where(Transaction.reference == "tx_app_1001")
    ).scalar_one()

    # Attach runtime heuristic assessment
    runtime_ra = RiskAssessment(
        transaction_id=tx_1001.id,
        base_score=10,
        raw_score=45,
        risk_score=45,
        is_score_clamped=False,
        risk_level="MEDIUM",
        recommended_action="REVIEW",
        scoring_method="HEURISTIC_RULES_V1",
        policy_version="1.0.0",
        risk_factors=["VELOCITY_WARN", "NEW_DEVICE"],
        feature_contributions=[{"rule": "VELOCITY", "points": 25}],
        created_at=datetime.now(timezone.utc),
    )
    test_db_session.add(runtime_ra)
    test_db_session.commit()

    # Confirm --recover-partial fails safely
    with pytest.raises(SeedIntegrityError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=True)
    assert "risk assessments" in str(exc_info.value) or "Runtime-generated risk assessment" in str(exc_info.value) or "Refusing to delete records" in str(exc_info.value)

    # Confirm the runtime assessment remains untouched
    test_db_session.rollback()
    persisted_runtime_ra = test_db_session.execute(
        select(RiskAssessment).where(
            RiskAssessment.transaction_id == tx_1001.id,
            RiskAssessment.scoring_method == "HEURISTIC_RULES_V1",
        )
    ).scalar_one_or_none()
    assert persisted_runtime_ra is not None
    assert persisted_runtime_ra.scoring_method == "HEURISTIC_RULES_V1"

    # Confirm all existing data remains unchanged
    assert test_db_session.execute(select(func.count(Transaction.id))).scalar() == 175


def test_scenario_5_runtime_audit_linkage_blocks_recovery(test_db_session: Session):
    """Scenario 5: Non-canonical runtime audit log referencing a canonical tx blocks recovery."""
    _ensure_clean_seed(test_db_session)
    tx_1001 = test_db_session.execute(
        select(Transaction).where(Transaction.reference == "tx_app_1001")
    ).scalar_one()

    runtime_log = AuditLog(
        actor_type="ANALYST",
        actor_id="analyst_lead_01",
        action="TRANSACTION_FLAGGED_FOR_AML",
        entity_type="transaction",
        entity_id=tx_1001.id,
        idempotency_key="runtime_audit:aml_flag_tx_1001",
        details={"reason": "Suspicious counterparty"},
    )
    test_db_session.add(runtime_log)
    test_db_session.commit()

    with pytest.raises(SeedIntegrityError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=True)
    assert "runtime audit logs reference canonical transactions" in str(exc_info.value)


def test_scenario_6_modified_analyst_case_blocks_recovery(test_db_session: Session):
    """Scenario 6: Analyst case with human workflow activity blocks recovery."""
    _ensure_clean_seed(test_db_session)
    case = test_db_session.execute(select(AnalystCase)).scalars().first()
    assert case is not None
    case.case_status = "IN_REVIEW"
    case.resolution_note = "Under active investigation by fraud specialist"
    test_db_session.commit()

    with pytest.raises(SeedIntegrityError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=True)
    assert "analyst cases have active human workflow state" in str(exc_info.value)


def test_scenario_7_modified_canonical_transaction_recovers_cleanly(test_db_session: Session):
    """Scenario 7: Modified canonical record triggers SeedIntegrityError on standard run and recovers cleanly."""
    _ensure_clean_seed(test_db_session)
    tx_1001 = test_db_session.execute(
        select(Transaction).where(Transaction.reference == "tx_app_1001")
    ).scalar_one()
    tx_1001.amount = Decimal("99999.00")
    test_db_session.commit()

    with pytest.raises(SeedIntegrityError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=False)
    assert "tx_app_1001" in str(exc_info.value)
    assert "amount drift" in str(exc_info.value)

    res = seed_canonical_data(test_db_session, recover_partial=True)
    assert res["status"] == "SUCCESS_SEEDED"
    assert res["count"] == 175

    test_db_session.expire_all()
    tx_1001_restored = test_db_session.execute(
        select(Transaction).where(Transaction.reference == "tx_app_1001")
    ).scalar_one()
    assert tx_1001_restored.amount == Decimal("1291.00")


def test_scenario_8_unexpected_merchant_audit_dependency_blocks_recovery(test_db_session: Session):
    """Scenario 8: Non-seed audit log attached to merchant blocks recovery."""
    _ensure_clean_seed(test_db_session)
    merchant = test_db_session.execute(select(Merchant)).scalar_one()

    runtime_merchant_log = AuditLog(
        actor_type="ADMIN",
        actor_id="admin_01",
        action="MERCHANT_SETTLEMENT_CONFIG_UPDATED",
        entity_type="merchant",
        entity_id=merchant.id,
        idempotency_key="runtime_audit:merchant_settlement_01",
        details={"settlement_cycle": "T+1"},
    )
    test_db_session.add(runtime_merchant_log)
    test_db_session.commit()

    with pytest.raises(SeedIntegrityError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=True)
    assert "runtime audit logs reference canonical merchant" in str(exc_info.value)


def test_scenario_9_failed_recovery_atomic_rollback(test_db_session: Session):
    """Scenario 9: When recovery safety boundary triggers, atomic transaction rollback occurs."""
    _ensure_clean_seed(test_db_session)
    case = test_db_session.execute(select(AnalystCase)).scalars().first()
    case.case_status = "IN_REVIEW"
    test_db_session.commit()

    initial_tx_count = test_db_session.execute(select(func.count(Transaction.id))).scalar()
    assert initial_tx_count == 175

    with pytest.raises(SeedIntegrityError):
        seed_canonical_data(test_db_session, recover_partial=True)

    test_db_session.expire_all()
    # Confirm 0 records were deleted due to atomic rollback
    post_tx_count = test_db_session.execute(select(func.count(Transaction.id))).scalar()
    assert post_tx_count == 175


def test_scenario_10_successful_recovery_exact_counts(test_db_session: Session):
    """Scenario 10: Successful recovery restores exactly 1 merchant, 175 tx, 175 ra, 14 cases, 176 audit logs."""
    _ensure_clean_seed(test_db_session)
    res = seed_canonical_data(test_db_session, recover_partial=True)
    assert res["status"] == "SUCCESS_SEEDED"

    assert test_db_session.execute(select(func.count(Merchant.id))).scalar() == 1
    assert test_db_session.execute(select(func.count(Transaction.id))).scalar() == 175
    assert test_db_session.execute(select(func.count(RiskAssessment.id))).scalar() == 175
    assert test_db_session.execute(select(func.count(AnalystCase.id))).scalar() == 14
    assert test_db_session.execute(select(func.count(AuditLog.id))).scalar() == 176
