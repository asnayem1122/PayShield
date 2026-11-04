"""Dashboard service for live metrics."""

import uuid
from sqlalchemy.orm import Session
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    RiskDistributionResponse,
)
from app.schemas.transaction import TransactionResponse


class DashboardService:
    """Provides dashboard and reporting aggregates with optional merchant scoping."""

    @staticmethod
    def get_summary(
        session: Session,
        merchant_id: uuid.UUID | None = None,
    ) -> DashboardSummaryResponse:
        stats = DashboardRepository.get_summary(session, merchant_id=merchant_id)
        return DashboardSummaryResponse(**stats)

    @staticmethod
    def get_risk_distribution(
        session: Session,
        merchant_id: uuid.UUID | None = None,
    ) -> RiskDistributionResponse:
        dist = DashboardRepository.get_risk_distribution(session, merchant_id=merchant_id)
        return RiskDistributionResponse(**dist)

    @staticmethod
    def get_recent_transactions(
        session: Session,
        limit: int = 10,
        merchant_id: uuid.UUID | None = None,
    ) -> list[TransactionResponse]:
        txs = DashboardRepository.get_recent_transactions(
            session, limit=limit, merchant_id=merchant_id
        )
        return [TransactionResponse.from_orm_model(tx) for tx in txs]
