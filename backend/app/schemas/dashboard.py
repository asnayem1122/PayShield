"""Dashboard summary and distribution schemas."""

from pydantic import BaseModel
from app.schemas.transaction import TransactionResponse


class DashboardSummaryResponse(BaseModel):
    """Aggregate financial and fraud risk performance metrics."""

    total_volume: str
    approved_volume: str
    review_volume: str
    flagged_volume: str
    blocked_volume: str
    total_transactions: int
    approved_count: int
    review_count: int
    flagged_count: int
    blocked_count: int
    open_cases_count: int
    average_risk_score: float
    high_risk_ratio: float


class RiskDistributionResponse(BaseModel):
    """Counts of transactions across risk levels."""

    low_count: int
    medium_count: int
    high_count: int
    total_count: int
