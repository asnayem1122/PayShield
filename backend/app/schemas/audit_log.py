"""Audit log schemas."""

from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    actor_type: str
    actor_id: str
    details: dict[str, Any]
    ip_address: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
