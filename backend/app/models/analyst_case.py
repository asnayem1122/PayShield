"""Analyst review case entity model."""

from datetime import datetime, timezone
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class AnalystCase(Base):
    """Workflow tracking case for suspicious transactions under analyst review."""

    __tablename__ = "analyst_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    case_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="OPEN"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MEDIUM"
    )
    trigger_reason: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_analyst: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction", back_populates="analyst_case"
    )

    __table_args__ = (
        CheckConstraint(
            "case_status IN ('OPEN', 'IN_REVIEW', 'RESOLVED')",
            name="valid_case_status",
        ),
        CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH')", name="valid_case_priority"
        ),
        CheckConstraint(
            """
            trigger_reason IN (
                'UNUSUAL_HOUR', 'NEW_DEVICE', 'VELOCITY_WARN', 'HIGH_AMOUNT',
                'DISTANCE_DELTA', 'MULTIPLE_CARDS', 'DEVICE_MISMATCH', 'NEW_ACCOUNT',
                'OFF_HOURS', 'MANUAL_FLAG', 'SCORE_THRESHOLD_EXCEEDED'
            )
            """,
            name="valid_trigger_reason",
        ),
        CheckConstraint(
            """
            (case_status = 'RESOLVED' AND resolved_at IS NOT NULL) OR
            (case_status <> 'RESOLVED' AND resolved_at IS NULL)
            """,
            name="case_resolution_consistency",
        ),
        Index("ix_analyst_cases_status", "case_status"),
        Index("ix_analyst_cases_created_at", created_at.desc()),
    )
