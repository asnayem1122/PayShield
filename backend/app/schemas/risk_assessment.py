"""Risk assessment schemas."""

from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict
from app.schemas.common import DecimalString


class RiskIndicator(BaseModel):
    code: str
    name: str
    category: str
    weight: int
    description: str


class RiskIndicatorsResponse(BaseModel):
    scoring_method: str
    base_score: int
    max_raw_score: int
    clamped_score_cap: int
    indicators: list[RiskIndicator]
    thresholds: dict[str, Any]


class RiskAssessRequest(BaseModel):
    amount: DecimalString
    is_new_device: bool = False
    has_high_velocity: bool = False
    has_prior_chargebacks: bool = False
    is_suspicious_location: bool = False


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_id: uuid.UUID
    scoring_method: str
    raw_score: int
    clamped_score: int
    risk_factors: list[dict[str, Any]]
    scoring_metadata: dict[str, Any]
    created_at: datetime
