"""Merchant entity model."""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class Merchant(Base, TimestampMixin):
    """Registered commercial merchant profile."""

    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")

    # One-to-many relationship with transactions
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="merchant",
        cascade="none",
        passive_deletes="all",
    )

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="nonblank_name"),
        CheckConstraint("length(trim(category)) > 0", name="nonblank_category"),
        CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')", name="valid_status"
        ),
        Index("ix_merchants_status", "status"),
    )
