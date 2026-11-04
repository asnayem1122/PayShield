"""Risk assessment entity model."""

from datetime import datetime, timezone
import uuid
from typing import TYPE_CHECKING, Any
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class RiskAssessment(Base):
    """Authoritative risk assessment calculation record."""

    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    base_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    is_score_clamped: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(20), nullable=False)
    scoring_method: Mapped[str] = mapped_column(String(50), nullable=False)
    policy_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="1.0.0"
    )
    risk_factors: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    feature_contributions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction", back_populates="risk_assessments"
    )

    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            "scoring_method",
            "policy_version",
            name="uq_risk_assessment_tx_method_version",
        ),
        CheckConstraint(
            "raw_score IS NULL OR (raw_score >= 0 AND raw_score <= 110)",
            name="valid_raw_score",
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
            "scoring_method IN ('CANONICAL_SEED', 'HEURISTIC_RULES_V1')",
            name="valid_scoring_method",
        ),
        CheckConstraint(
            """
            (risk_score >= 0 AND risk_score <= 39 AND risk_level = 'LOW') OR
            (risk_score >= 40 AND risk_score <= 74 AND risk_level = 'MEDIUM') OR
            (risk_score >= 75 AND risk_score <= 100 AND risk_level = 'HIGH')
            """,
            name="assessment_score_level_consistency",
        ),
        CheckConstraint(
            """
            (risk_level = 'LOW' AND recommended_action = 'APPROVE') OR
            (risk_level = 'MEDIUM' AND recommended_action = 'REVIEW') OR
            (risk_level = 'HIGH' AND recommended_action = 'BLOCK')
            """,
            name="assessment_level_action_consistency",
        ),
        CheckConstraint(
            """
            (scoring_method = 'CANONICAL_SEED' AND 
             base_score IS NULL AND 
             raw_score IS NULL AND 
             is_score_clamped IS NULL)
            OR
            (scoring_method = 'HEURISTIC_RULES_V1' AND 
             base_score = 10 AND 
             raw_score >= 0 AND raw_score <= 110 AND 
             is_score_clamped IS NOT NULL AND
             ((raw_score > 100 AND risk_score = 100 AND is_score_clamped = TRUE) OR
              (raw_score <= 100 AND risk_score = raw_score AND is_score_clamped = FALSE)))
            """,
            name="scoring_metadata_consistency",
        ),
        Index("ix_risk_assessments_tx_id", "transaction_id"),
        Index("ix_risk_assessments_scoring_method", "scoring_method"),
    )
