"""Transaction entity model."""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.analyst_case import AnalystCase
    from app.models.merchant import Merchant
    from app.models.risk_assessment import RiskAssessment


class Transaction(Base):
    """Monitored payment transaction ledger record."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    reference: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    counterparty_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BDT")
    transaction_status: Mapped[str] = mapped_column(String(20), nullable=False)
    device_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_location_anomaly: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(20), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="MOBILE_APP")
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

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant", back_populates="transactions"
    )
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        "RiskAssessment",
        back_populates="transaction",
        cascade="none",
        passive_deletes="all",
    )
    analyst_case: Mapped["AnalystCase | None"] = relationship(
        "AnalystCase",
        back_populates="transaction",
        uselist=False,
        cascade="none",
        passive_deletes="all",
    )

    __table_args__ = (
        CheckConstraint("length(trim(reference)) > 0", name="nonblank_reference"),
        CheckConstraint(
            "length(trim(counterparty_name)) > 0", name="nonblank_counterparty"
        ),
        CheckConstraint("amount > 0.00", name="positive_amount"),
        CheckConstraint("currency = 'BDT'", name="bdt_currency_only"),
        CheckConstraint(
            "transaction_status IN ('APPROVED', 'REVIEW', 'BLOCKED')",
            name="valid_transaction_status",
        ),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100", name="valid_risk_score"
        ),
        CheckConstraint(
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH')", name="valid_risk_level"
        ),
        CheckConstraint(
            "recommended_action IN ('APPROVE', 'REVIEW', 'BLOCK')",
            name="valid_recommended_action",
        ),
        CheckConstraint(
            """
            (risk_score >= 0 AND risk_score <= 39 AND risk_level = 'LOW') OR
            (risk_score >= 40 AND risk_score <= 74 AND risk_level = 'MEDIUM') OR
            (risk_score >= 75 AND risk_score <= 100 AND risk_level = 'HIGH')
            """,
            name="score_level_consistency",
        ),
        CheckConstraint(
            """
            (risk_level = 'LOW' AND recommended_action = 'APPROVE') OR
            (risk_level = 'MEDIUM' AND recommended_action = 'REVIEW') OR
            (risk_level = 'HIGH' AND recommended_action = 'BLOCK')
            """,
            name="level_action_consistency",
        ),
        Index("ix_transactions_merchant_id", "merchant_id"),
        Index("ix_transactions_status", "transaction_status"),
        Index("ix_transactions_risk_level", "risk_level"),
        Index("ix_transactions_created_at", created_at.desc()),
    )
