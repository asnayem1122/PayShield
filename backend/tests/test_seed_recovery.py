"""
PayShield Phase 2 - Canonical Seed Verification and Safe Recovery Test Suite.

Verifies all five required recovery scenarios against PostgreSQL (payshield_test):
1. Empty state: Clean database seeds exactly 1 merchant, 175 tx, 175 assessments, 14 cases, 176 audit logs.
2. Fully seeded state: Idempotent run with recover_partial=False detects 175 records, verifies all 5 entity sets, and returns VERIFIED_EXISTING without mutation.
3. Partial state: Incomplete dataset (e.g. 50 transactions) aborts with PartialSeedAbortedError; recovers cleanly with recover_partial=True.
4. Drifted state: Modified canonical record aborts with SeedIntegrityError; recovers cleanly with recover_partial=True.
5. Runtime-linked state: Non-seed audit log or modified analyst case blocks recovery and triggers rollback.
"""

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
    verify_existing_canonical_seed,
    get_canonical_transaction_specs,
)


@pytest.fixture(scope="module")
def test_db_session():
    """Admin/migrator session connected to payshield_test."""
    url = settings.get_migration_sqlalchemy_url().set(database="payshield_test")
    engine = create_engine(url)
    with Session(engine) as session:
        # Pre-clean any test remnants
        _clean_test_db(session)
        yield session
        # Post-clean
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
    # Artificially delete 50 transactions to simulate interrupted seed
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

    # Assert exactly 175 transactions and 176 audit logs restored
    assert test_db_session.execute(select(func.count(Transaction.id))).scalar() == 175
    assert test_db_session.execute(select(func.count(AuditLog.id))).scalar() == 176


def test_scenario_4_drifted_state_recovery(test_db_session: Session):
    """Scenario 4: Drifted record triggers SeedIntegrityError and recovers cleanly with recover_partial."""
    test_db_session.rollback()
    # Tamper with tx_app_1001 amount
    tx_1001 = test_db_session.execute(
        select(Transaction).where(Transaction.reference == "tx_app_1001")
    ).scalar_one()
    tx_1001.amount = Decimal("99999.00")
    test_db_session.commit()

    # Standard run must detect the drift and fail
    with pytest.raises(SeedIntegrityError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=False)
    assert "tx_app_1001" in str(exc_info.value)
    assert "amount drift" in str(exc_info.value)

    # Recovery run must restore canonical amount
    res = seed_canonical_data(test_db_session, recover_partial=True)
    assert res["status"] == "SUCCESS_SEEDED"
    assert res["count"] == 175

    test_db_session.expire_all()
    tx_1001_restored = test_db_session.execute(
        select(Transaction).where(Transaction.reference == "tx_app_1001")
    ).scalar_one()
    assert tx_1001_restored.amount == Decimal("1291.00")


def test_scenario_5a_runtime_audit_linkage_blocks_recovery(test_db_session: Session):
    """Scenario 5a: A non-canonical runtime audit log referencing a canonical tx blocks recovery."""
    test_db_session.rollback()
    tx_1001 = test_db_session.execute(
        select(Transaction).where(Transaction.reference == "tx_app_1001")
    ).scalar_one()

    # Add a runtime audit log (e.g. from an analyst or compliance job)
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

    # Recovery must refuse to delete records with external runtime dependencies
    with pytest.raises(SeedIntegrityError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=True)
    assert "runtime audit logs reference canonical transactions" in str(exc_info.value)

    # Clean up the runtime log for subsequent tests
    test_db_session.rollback()
    test_db_session.execute(delete(AuditLog).where(AuditLog.idempotency_key == "runtime_audit:aml_flag_tx_1001"))
    test_db_session.commit()


def test_scenario_5b_modified_analyst_case_blocks_recovery(test_db_session: Session):
    """Scenario 5b: An analyst case with human workflow activity blocks recovery."""
    test_db_session.rollback()
    case = test_db_session.execute(select(AnalystCase)).scalars().first()
    assert case is not None
    case.case_status = "IN_REVIEW"
    case.resolution_note = "Under active investigation by fraud specialist"
    test_db_session.commit()

    # Recovery must refuse to destroy active human workflow state
    with pytest.raises(SeedIntegrityError) as exc_info:
        seed_canonical_data(test_db_session, recover_partial=True)
    assert "analyst cases have active human workflow state" in str(exc_info.value)

    # Reset case back to OPEN/pristine for test teardown
    test_db_session.rollback()
    case.case_status = "OPEN"
    case.resolution_note = None
    test_db_session.commit()
