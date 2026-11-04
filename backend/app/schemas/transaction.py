"""Transaction schemas matching PayShield domain model."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import DecimalString


class TransactionBase(BaseModel):
    counterparty_name: str = Field(min_length=1, max_length=255)
    amount: DecimalString
    currency: str = Field(default="BDT", min_length=3, max_length=3)
    channel: str = Field(default="MOBILE_APP", max_length=50)
    device_model: str | None = Field(default=None, max_length=100)
    location_city: str | None = Field(default=None, max_length=100)
    is_location_anomaly: bool = False


class TransactionCreate(TransactionBase):
    """Payload for submitting a new payment transaction."""

    merchant_id: uuid.UUID | None = None
    # Evaluation signals
    is_new_device: bool = False
    has_high_velocity: bool = False
    has_prior_chargebacks: bool = False


class TransactionUpdateStatus(BaseModel):
    """Payload for updating a transaction's review/resolution status."""

    status: Literal["APPROVED", "REVIEW", "BLOCKED"]
    notes: str | None = Field(default=None, max_length=1000)
    actor_id: str = Field(default="analyst_system", max_length=100)


class TransactionResponse(BaseModel):
    """Canonical transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    merchant_id: uuid.UUID
    counterparty_name: str
    amount: str
    currency: str
    transaction_status: str
    risk_score: int
    risk_level: str
    recommended_action: str
    channel: str
    device_model: str | None = None
    location_city: str | None = None
    is_location_anomaly: bool = False
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, obj) -> "TransactionResponse":
        return cls(
            id=obj.id,
            reference=obj.reference,
            merchant_id=obj.merchant_id,
            counterparty_name=obj.counterparty_name,
            amount=f"{obj.amount:.2f}",
            currency=obj.currency,
            transaction_status=obj.transaction_status,
            risk_score=obj.risk_score,
            risk_level=obj.risk_level,
            recommended_action=obj.recommended_action,
            channel=obj.channel,
            device_model=obj.device_model,
            location_city=obj.location_city,
            is_location_anomaly=obj.is_location_anomaly,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
