"""Analyst case repository."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.analyst_case import AnalystCase


class AnalystCaseRepository:
    """Repository managing analyst cases."""

    @staticmethod
    def list_cases(
        session: Session,
        status: str | None = None,
        priority: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AnalystCase], int]:
        stmt = select(AnalystCase).options(selectinload(AnalystCase.transaction))

        if status:
            stmt = stmt.where(AnalystCase.case_status == status.upper())
        if priority:
            stmt = stmt.where(AnalystCase.priority == priority.upper())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(AnalystCase.created_at.desc()).limit(limit).offset(offset)
        items = list(session.execute(stmt).scalars().all())

        return items, total

    @staticmethod
    def get_by_id(session: Session, case_id: uuid.UUID) -> AnalystCase | None:
        stmt = (
            select(AnalystCase)
            .options(selectinload(AnalystCase.transaction))
            .where(AnalystCase.id == case_id)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_transaction_id(session: Session, transaction_id: uuid.UUID) -> AnalystCase | None:
        stmt = (
            select(AnalystCase)
            .options(selectinload(AnalystCase.transaction))
            .where(AnalystCase.transaction_id == transaction_id)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(session: Session, case: AnalystCase) -> AnalystCase:
        session.add(case)
        session.flush()
        return case

    @staticmethod
    def update(
        session: Session,
        case: AnalystCase,
        status: str | None = None,
        resolution_note: str | None = None,
    ) -> AnalystCase:
        now = datetime.now(timezone.utc)
        if status is not None:
            case.case_status = status
            if status == "RESOLVED":
                case.resolved_at = now
            elif status in ("OPEN", "IN_REVIEW"):
                case.resolved_at = None
        if resolution_note is not None:
            case.resolution_note = resolution_note
        case.updated_at = now

        session.flush()
        return case
