"""Dashboard aggregation API endpoints."""

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    RiskDistributionResponse,
)
from app.schemas.transaction import TransactionResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _resolve_scoped_merchant_id(
    current_user: User,
    requested_merchant_id: uuid.UUID | None = None,
) -> uuid.UUID | None:
    if current_user.role == "MERCHANT":
        return current_user.merchant_id
    return requested_merchant_id


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    merchant_id: uuid.UUID | None = Query(
        None, description="Scope summary to merchant (Analyst/Admin only)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve live database aggregates for financial volume, transaction counts, and risk metrics."""
    scoped_id = _resolve_scoped_merchant_id(current_user, merchant_id)
    return DashboardService.get_summary(db, merchant_id=scoped_id)


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
def get_risk_distribution(
    merchant_id: uuid.UUID | None = Query(
        None, description="Scope distribution to merchant (Analyst/Admin only)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve risk score level distribution (LOW, MEDIUM, HIGH counts)."""
    scoped_id = _resolve_scoped_merchant_id(current_user, merchant_id)
    return DashboardService.get_risk_distribution(db, merchant_id=scoped_id)


@router.get("/recent-transactions", response_model=list[TransactionResponse])
def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50),
    merchant_id: uuid.UUID | None = Query(
        None, description="Scope recent transactions to merchant (Analyst/Admin only)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve most recent transactions."""
    scoped_id = _resolve_scoped_merchant_id(current_user, merchant_id)
    return DashboardService.get_recent_transactions(
        db, limit=limit, merchant_id=scoped_id
    )
