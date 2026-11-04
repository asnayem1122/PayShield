"""Risk assessment and indicator API endpoints."""

from decimal import Decimal
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.risk_assessment import (
    RiskAssessRequest,
    RiskIndicator,
    RiskIndicatorsResponse,
)
from app.services.risk_scoring_service import (
    RiskInput,
    RiskScoringResult,
    RiskScoringService,
)

router = APIRouter(prefix="/risk", tags=["Risk Management"])


@router.get("/indicators", response_model=RiskIndicatorsResponse)
def get_risk_indicators(current_user: User = Depends(get_current_user)):
    """Retrieve rule metadata, weights, and scoring policy configuration."""
    indicators = [
        RiskIndicator(
            code="BASE_SCORE",
            name="Baseline Policy Floor",
            category="System",
            weight=RiskScoringService.BASE_SCORE,
            description="Minimum starting policy risk assigned to all evaluated transactions",
        ),
        RiskIndicator(
            code="NEW_DEVICE",
            name="Unrecognized Device",
            category="Device",
            weight=RiskScoringService.WEIGHT_NEW_DEVICE,
            description="Device fingerprint has not been previously seen for this account",
        ),
        RiskIndicator(
            code="HIGH_VELOCITY",
            name="High Transaction Velocity",
            category="Behavioral",
            weight=RiskScoringService.WEIGHT_VELOCITY,
            description="Unusual spike in transaction frequency within a rolling time window",
        ),
        RiskIndicator(
            code="PRIOR_CHARGEBACKS",
            name="Prior Dispute History",
            category="Reputation",
            weight=RiskScoringService.WEIGHT_CHARGEBACKS,
            description="Counterparty or card credential associated with past chargebacks",
        ),
        RiskIndicator(
            code="HIGH_AMOUNT",
            name="High Transaction Volume",
            category="Financial",
            weight=RiskScoringService.WEIGHT_HIGH_AMOUNT,
            description="Transaction amount meets or exceeds 10,000.00 BDT threshold",
        ),
        RiskIndicator(
            code="LOCATION_ANOMALY",
            name="Geographic Location Anomaly",
            category="Geographic",
            weight=RiskScoringService.WEIGHT_LOCATION,
            description="Transaction originates from flagged or unexpected geographic region",
        ),
    ]

    return RiskIndicatorsResponse(
        scoring_method="HEURISTIC_RULES_V1",
        base_score=RiskScoringService.BASE_SCORE,
        max_raw_score=110,
        clamped_score_cap=100,
        indicators=indicators,
        thresholds={
            "low_risk_max": 39,
            "medium_risk_max": 74,
            "high_risk_min": 75,
            "high_amount_threshold_bdt": "10000.00",
        },
    )


@router.post("/assess", response_model=RiskScoringResult)
def evaluate_risk(
    payload: RiskAssessRequest,
    current_user: User = Depends(get_current_user),
):
    """Run ad-hoc dry-run heuristic risk evaluation without persisting transaction."""
    inp = RiskInput(
        amount=Decimal(payload.amount),
        is_new_device=payload.is_new_device,
        has_high_velocity=payload.has_high_velocity,
        has_prior_chargebacks=payload.has_prior_chargebacks,
        is_suspicious_location=payload.is_suspicious_location,
    )
    return RiskScoringService.evaluate(inp)
