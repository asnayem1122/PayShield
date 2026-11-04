"""
PayShield Risk Scoring Heuristic Service (HEURISTIC_RULES_V1).

Calculates rule-based heuristic fraud-risk scores for financial transactions.
DISCLAIMER: The calculated score represents a heuristic policy risk index (0-100),
NOT a calibrated statistical fraud probability.
"""

from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


class FactorContribution(BaseModel):
    """Breakdown of an individual risk factor contribution."""

    code: str
    description: str
    weight: int
    applied: bool


class RiskScoringResult(BaseModel):
    """Output of the heuristic risk evaluation."""

    raw_score: int
    final_score: int
    risk_level: str  # LOW, MEDIUM, HIGH
    suggested_action: str  # APPROVE, REVIEW, BLOCK
    scoring_method: str = "HEURISTIC_RULES_V1"
    contributions: list[FactorContribution]
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskInput(BaseModel):
    """Input signals for transaction risk assessment."""

    amount: Decimal
    is_new_device: bool = False
    has_high_velocity: bool = False
    has_prior_chargebacks: bool = False
    is_suspicious_location: bool = False
    high_amount_threshold: Decimal = Decimal("10000.00")


class RiskScoringService:
    """Evaluates rule-based heuristic risk signals for transactions."""

    BASE_SCORE: int = 10
    WEIGHT_NEW_DEVICE: int = 25
    WEIGHT_VELOCITY: int = 25
    WEIGHT_CHARGEBACKS: int = 25
    WEIGHT_HIGH_AMOUNT: int = 15
    WEIGHT_LOCATION: int = 10

    @classmethod
    def evaluate(cls, inputs: RiskInput) -> RiskScoringResult:
        """
        Evaluate heuristic rules against input signals.

        Base score: 10
        +25: New / untrusted device
        +25: High velocity / burst activity
        +25: Prior chargebacks on counterparty or card
        +15: Transaction amount exceeding high_amount_threshold
        +10: Geographic anomaly / high-risk location

        Maximum raw score: 110.
        Clamping: final_score = min(100, max(0, raw_score)).
        """
        contributions: list[FactorContribution] = []
        raw_score = cls.BASE_SCORE

        # 1. Base Score
        contributions.append(
            FactorContribution(
                code="BASE_SCORE",
                description="Baseline transaction risk baseline",
                weight=cls.BASE_SCORE,
                applied=True,
            )
        )

        # 2. Device Signal
        if inputs.is_new_device:
            raw_score += cls.WEIGHT_NEW_DEVICE
            contributions.append(
                FactorContribution(
                    code="NEW_DEVICE",
                    description="Unrecognized device fingerprint or user agent",
                    weight=cls.WEIGHT_NEW_DEVICE,
                    applied=True,
                )
            )

        # 3. Velocity Signal
        if inputs.has_high_velocity:
            raw_score += cls.WEIGHT_VELOCITY
            contributions.append(
                FactorContribution(
                    code="HIGH_VELOCITY",
                    description="Rapid transaction frequency exceeding threshold",
                    weight=cls.WEIGHT_VELOCITY,
                    applied=True,
                )
            )

        # 4. Prior Chargebacks
        if inputs.has_prior_chargebacks:
            raw_score += cls.WEIGHT_CHARGEBACKS
            contributions.append(
                FactorContribution(
                    code="PRIOR_CHARGEBACKS",
                    description="Historical chargebacks or disputes on file",
                    weight=cls.WEIGHT_CHARGEBACKS,
                    applied=True,
                )
            )

        # 5. High Amount
        is_high_amount = inputs.amount >= inputs.high_amount_threshold
        if is_high_amount:
            raw_score += cls.WEIGHT_HIGH_AMOUNT
            contributions.append(
                FactorContribution(
                    code="HIGH_AMOUNT",
                    description=f"Transaction amount >= {inputs.high_amount_threshold} BDT",
                    weight=cls.WEIGHT_HIGH_AMOUNT,
                    applied=True,
                )
            )

        # 6. Location Anomaly
        if inputs.is_suspicious_location:
            raw_score += cls.WEIGHT_LOCATION
            contributions.append(
                FactorContribution(
                    code="LOCATION_ANOMALY",
                    description="Transaction from non-standard or flagged geographic location",
                    weight=cls.WEIGHT_LOCATION,
                    applied=True,
                )
            )

        # Clamping
        final_score = min(100, max(0, raw_score))

        # Risk level and action mapping strictly matching database check constraints
        if final_score <= 39:
            risk_level = "LOW"
            suggested_action = "APPROVE"
        elif final_score <= 74:
            risk_level = "MEDIUM"
            suggested_action = "REVIEW"
        else:
            risk_level = "HIGH"
            suggested_action = "BLOCK"

        metadata = {
            "raw_score": raw_score,
            "clamped": raw_score > 100,
            "clamping_differential": max(0, raw_score - 100),
            "amount_evaluated": str(inputs.amount),
            "signals": {
                "new_device": inputs.is_new_device,
                "high_velocity": inputs.has_high_velocity,
                "prior_chargebacks": inputs.has_prior_chargebacks,
                "high_amount": is_high_amount,
                "suspicious_location": inputs.is_suspicious_location,
            },
        }

        return RiskScoringResult(
            raw_score=raw_score,
            final_score=final_score,
            risk_level=risk_level,
            suggested_action=suggested_action,
            scoring_method="HEURISTIC_RULES_V1",
            contributions=contributions,
            metadata=metadata,
        )
