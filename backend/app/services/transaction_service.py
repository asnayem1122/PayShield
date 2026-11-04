"""Transaction domain service."""

from decimal import Decimal
import uuid
from sqlalchemy.orm import Session
from app.models.analyst_case import AnalystCase
from app.models.audit_log import AuditLog
from app.models.risk_assessment import RiskAssessment
from app.models.transaction import Transaction
from app.repositories.analyst_case_repository import AnalystCaseRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdateStatus
from app.services.risk_scoring_service import RiskInput, RiskScoringService


class TransactionService:
    """Orchestrates transaction ingestion, risk assessment, case creation, and auditing."""

    @staticmethod
    def create_transaction(
        session: Session,
        payload: TransactionCreate,
    ) -> tuple[Transaction, RiskAssessment, AnalystCase | None]:
        # 1. Resolve merchant
        merchant_id = payload.merchant_id
        if not merchant_id:
            default_merchant = MerchantRepository.get_default_merchant(session)
            if not default_merchant:
                raise ValueError("No active merchant configured in system")
            merchant_id = default_merchant.id

        # 2. Evaluate risk
        amount_decimal = Decimal(payload.amount)
        risk_input = RiskInput(
            amount=amount_decimal,
            is_new_device=payload.is_new_device,
            has_high_velocity=payload.has_high_velocity,
            has_prior_chargebacks=payload.has_prior_chargebacks,
            is_suspicious_location=payload.is_location_anomaly,
        )
        scoring_res = RiskScoringService.evaluate(risk_input)

        # 3. Determine transaction status from suggested action
        # APPROVE -> APPROVED, REVIEW -> REVIEW, BLOCK -> BLOCKED
        if scoring_res.suggested_action == "APPROVE":
            status = "APPROVED"
        elif scoring_res.suggested_action == "REVIEW":
            status = "REVIEW"
        else:
            status = "BLOCKED"

        # 4. Generate reference
        reference = f"tx_live_{uuid.uuid4().hex[:10]}"

        # 5. Create Transaction record
        tx = Transaction(
            reference=reference,
            merchant_id=merchant_id,
            counterparty_name=payload.counterparty_name,
            amount=amount_decimal,
            currency=payload.currency,
            transaction_status=status,
            device_model=payload.device_model,
            location_city=payload.location_city,
            is_location_anomaly=payload.is_location_anomaly,
            risk_score=scoring_res.final_score,
            risk_level=scoring_res.risk_level,
            recommended_action=scoring_res.suggested_action,
            channel=payload.channel,
        )
        TransactionRepository.create(session, tx)

        # 6. Create RiskAssessment record
        factor_codes = [
            c.code for c in scoring_res.contributions if c.applied and c.code != "BASE_SCORE"
        ]
        contributions_data = [c.model_dump() for c in scoring_res.contributions]
        assessment = RiskAssessment(
            transaction_id=tx.id,
            base_score=RiskScoringService.BASE_SCORE,
            raw_score=scoring_res.raw_score,
            risk_score=scoring_res.final_score,
            is_score_clamped=scoring_res.raw_score > 100,
            risk_level=scoring_res.risk_level,
            recommended_action=scoring_res.suggested_action,
            scoring_method="HEURISTIC_RULES_V1",
            policy_version="1.0.0",
            risk_factors=factor_codes,
            feature_contributions=contributions_data,
        )
        RiskAssessmentRepository.create(session, assessment)

        # 7. Create AnalystCase if REVIEW or BLOCKED
        analyst_case: AnalystCase | None = None
        if status in ("REVIEW", "BLOCKED"):
            # Select appropriate controlled trigger_reason:
            # 'UNUSUAL_HOUR', 'NEW_DEVICE', 'VELOCITY_WARN', 'HIGH_AMOUNT',
            # 'DISTANCE_DELTA', 'MULTIPLE_CARDS', 'DEVICE_MISMATCH', 'NEW_ACCOUNT',
            # 'OFF_HOURS', 'MANUAL_FLAG', 'SCORE_THRESHOLD_EXCEEDED'
            if payload.has_high_velocity:
                reason = "VELOCITY_WARN"
            elif payload.is_new_device:
                reason = "NEW_DEVICE"
            elif payload.is_location_anomaly:
                reason = "DISTANCE_DELTA"
            elif amount_decimal >= Decimal("10000.00"):
                reason = "HIGH_AMOUNT"
            else:
                reason = "SCORE_THRESHOLD_EXCEEDED"

            priority = "HIGH" if status == "BLOCKED" else "MEDIUM"
            analyst_case = AnalystCase(
                transaction_id=tx.id,
                case_status="OPEN",
                priority=priority,
                trigger_reason=reason,
            )
            AnalystCaseRepository.create(session, analyst_case)

        # 8. Record AuditLog
        audit = AuditLog(
            entity_type="transaction",
            entity_id=tx.id,
            action="TRANSACTION_EVALUATED_AND_CREATED",
            actor_type="SYSTEM",
            actor_id="risk_engine",
            details={
                "reference": tx.reference,
                "amount": str(tx.amount),
                "risk_score": tx.risk_score,
                "risk_level": tx.risk_level,
                "status": tx.transaction_status,
                "case_created": analyst_case is not None,
            },
            ip_address=None,
        )
        AuditLogRepository.create(session, audit)

        session.commit()
        return tx, assessment, analyst_case

    @staticmethod
    def update_transaction_status(
        session: Session,
        reference: str,
        payload: TransactionUpdateStatus,
    ) -> Transaction:
        tx = TransactionRepository.get_by_reference(session, reference)
        if not tx:
            raise ValueError(f"Transaction with reference '{reference}' not found")

        old_status = tx.transaction_status
        new_status = payload.status
        if old_status == new_status:
            return tx

        TransactionRepository.update_status(session, tx, new_status)

        # If an analyst case exists and new_status is terminal (APPROVED or BLOCKED), resolve case
        case = AnalystCaseRepository.get_by_transaction_id(session, tx.id)
        if case and case.case_status != "RESOLVED" and new_status in ("APPROVED", "BLOCKED"):
            note = f"Transaction marked {new_status} by {payload.actor_id}."
            if payload.notes:
                note += f" Notes: {payload.notes}"
            AnalystCaseRepository.update(
                session,
                case,
                status="RESOLVED",
                resolution_note=note,
            )

        # Record AuditLog
        audit = AuditLog(
            entity_type="transaction",
            entity_id=tx.id,
            action="TRANSACTION_STATUS_UPDATED",
            actor_type="ANALYST",
            actor_id=payload.actor_id,
            details={
                "reference": tx.reference,
                "old_status": old_status,
                "new_status": new_status,
                "notes": payload.notes,
            },
        )
        AuditLogRepository.create(session, audit)

        session.commit()
        return tx
