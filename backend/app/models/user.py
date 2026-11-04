"""User entity model for authentication and role-based access control."""

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.auth_session import AuthSession
    from app.models.merchant import Merchant


class User(Base, TimestampMixin):
    """User account entity with credentials, role, and lockout controls."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    merchant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="RESTRICT"),
        nullable=True,
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    merchant: Mapped["Merchant | None"] = relationship("Merchant")
    sessions: Mapped[list["AuthSession"]] = relationship(
        "AuthSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('MERCHANT', 'ANALYST', 'ADMIN')",
            name="valid_role",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED')",
            name="valid_status",
        ),
        CheckConstraint("length(trim(email)) > 0", name="nonblank_email"),
        CheckConstraint("length(trim(full_name)) > 0", name="nonblank_name"),
        CheckConstraint("failed_login_attempts >= 0", name="nonnegative_failed_attempts"),
        CheckConstraint(
            "(role = 'MERCHANT' AND merchant_id IS NOT NULL) OR (role IN ('ANALYST', 'ADMIN') AND merchant_id IS NULL)",
            name="role_merchant_match",
        ),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
        Index("ix_users_merchant_id", "merchant_id"),
    )
