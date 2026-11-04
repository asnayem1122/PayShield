"""Audit log entity model."""

from datetime import datetime, timezone
import uuid
from typing import Any
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Role-restricted application-level append-only audit trail."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(150), unique=True, nullable=True
    )
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "actor_type IN ('SYSTEM', 'ANALYST', 'MERCHANT', 'ADMIN')",
            name="valid_actor_type",
        ),
        CheckConstraint("length(trim(action)) > 0", name="nonblank_action"),
        CheckConstraint("length(trim(entity_type)) > 0", name="nonblank_entity_type"),
        UniqueConstraint("idempotency_key", name="uq_audit_logs_idempotency_key"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", created_at.desc()),
    )
