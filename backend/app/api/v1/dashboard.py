"""Dashboard aggregation API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    RiskDistributionResponse,
)
from app.schemas.transaction import TransactionResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Retrieve live database aggregates for financial volume, transaction counts, and risk metrics."""
    return DashboardService.get_summary(db)


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
def get_risk_distribution(db: Session = Depends(get_db)):
    """Retrieve risk score level distribution (LOW, MEDIUM, HIGH counts)."""
    return DashboardService.get_risk_distribution(db)


@router.get("/recent-transactions", response_model=list[TransactionResponse])
def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Retrieve most recent transactions."""
    return DashboardService.get_recent_transactions(db, limit)
