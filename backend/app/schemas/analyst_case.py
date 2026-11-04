"""Analyst review case schemas."""

from datetime import datetime
from typing import Literal
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.transaction import TransactionResponse


class AnalystCaseUpdate(BaseModel):
    """Payload to update an analyst case."""

    case_status: Literal["OPEN", "IN_REVIEW", "RESOLVED"] | None = None
    assigned_analyst: str | None = Field(default=None, max_length=100)
    resolution_note: str | None = Field(default=None, max_length=2000)
    actor_id: str = Field(default="analyst_user", max_length=100)


class AnalystCaseResponse(BaseModel):
    """Analyst case details response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_id: uuid.UUID
    case_status: str
    priority: str
    trigger_reason: str
    assigned_analyst: str | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    transaction: TransactionResponse | None = None


class AnalystCaseListResponse(BaseModel):
    items: list[AnalystCaseResponse]
    total: int
