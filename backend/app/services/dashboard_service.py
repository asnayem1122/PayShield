"""Dashboard service for live metrics."""

from sqlalchemy.orm import Session
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    RiskDistributionResponse,
)
from app.schemas.transaction import TransactionResponse


class DashboardService:
    """Provides dashboard and reporting aggregates."""

    @staticmethod
    def get_summary(session: Session) -> DashboardSummaryResponse:
        stats = DashboardRepository.get_summary(session)
        return DashboardSummaryResponse(**stats)

    @staticmethod
    def get_risk_distribution(session: Session) -> RiskDistributionResponse:
        dist = DashboardRepository.get_risk_distribution(session)
        return RiskDistributionResponse(**dist)

    @staticmethod
    def get_recent_transactions(session: Session, limit: int = 10) -> list[TransactionResponse]:
        txs = DashboardRepository.get_recent_transactions(session, limit)
        return [TransactionResponse.from_orm_model(tx) for tx in txs]
