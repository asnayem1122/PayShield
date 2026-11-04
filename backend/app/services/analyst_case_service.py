"""Analyst case management service."""

import uuid
from sqlalchemy.orm import Session
from app.models.analyst_case import AnalystCase
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.analyst_case_repository import AnalystCaseRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.analyst_case import (
    AnalystCaseListResponse,
    AnalystCaseResponse,
    AnalystCaseUpdate,
)
from app.schemas.transaction import TransactionResponse


class AnalystCaseService:
    """Service managing fraud analyst review workflows."""

    @staticmethod
    def list_cases(
        session: Session,
        status: str | None = None,
        priority: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AnalystCaseListResponse:
        cases, total = AnalystCaseRepository.list_cases(session, status, priority, limit, offset)
        items = []
        for c in cases:
            tx_resp = TransactionResponse.from_orm_model(c.transaction) if c.transaction else None
            items.append(
                AnalystCaseResponse(
                    id=c.id,
                    transaction_id=c.transaction_id,
                    case_status=c.case_status,
                    priority=c.priority,
                    trigger_reason=c.trigger_reason,
                    assigned_analyst=c.assigned_analyst,
                    resolution_note=c.resolution_note,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    resolved_at=c.resolved_at,
                    transaction=tx_resp,
                )
            )
        return AnalystCaseListResponse(items=items, total=total)

    @staticmethod
    def get_case(session: Session, case_id: uuid.UUID) -> AnalystCaseResponse | None:
        c = AnalystCaseRepository.get_by_id(session, case_id)
        if not c:
            return None
        tx_resp = TransactionResponse.from_orm_model(c.transaction) if c.transaction else None
        return AnalystCaseResponse(
            id=c.id,
            transaction_id=c.transaction_id,
            case_status=c.case_status,
            priority=c.priority,
            trigger_reason=c.trigger_reason,
            assigned_analyst=c.assigned_analyst,
            resolution_note=c.resolution_note,
            created_at=c.created_at,
            updated_at=c.updated_at,
            resolved_at=c.resolved_at,
            transaction=tx_resp,
        )

    @staticmethod
    def update_case(
        session: Session,
        case_id: uuid.UUID,
        payload: AnalystCaseUpdate,
        current_user: User | None = None,
    ) -> AnalystCaseResponse:
        case = AnalystCaseRepository.get_by_id(session, case_id)
        if not case:
            raise ValueError(f"Analyst case {case_id} not found")

        AnalystCaseRepository.update(
            session,
            case,
            status=payload.case_status,
            resolution_note=payload.resolution_note,
        )

        actor_type = current_user.role if current_user else "ANALYST"
        actor_id = str(current_user.id) if current_user else payload.actor_id
        audit = AuditLog(
            entity_type="analyst_case",
            entity_id=str(case.id),
            action="CASE_WORKFLOW_UPDATED",
            actor_type=actor_type,
            actor_id=actor_id,
            details={
                "case_id": str(case.id),
                "case_status": case.case_status,
                "assigned_analyst": case.assigned_analyst,
                "resolution_note": case.resolution_note,
            },
        )
        AuditLogRepository.create(session, audit)
        session.commit()

        return AnalystCaseService.get_case(session, case.id)  # type: ignore
