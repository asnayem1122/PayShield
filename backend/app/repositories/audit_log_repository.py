"""Audit log repository."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Append-only audit log repository."""

    @staticmethod
    def create(session: Session, log: AuditLog) -> AuditLog:
        session.add(log)
        session.flush()
        return log

    @staticmethod
    def list_logs(
        session: Session,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLog)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        items = list(session.execute(stmt).scalars().all())

        return items, total
