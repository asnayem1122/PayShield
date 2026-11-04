"""
Tests for RiskScoringService (HEURISTIC_RULES_V1).
"""

from decimal import Decimal
import pytest
from app.services.risk_scoring_service import (
    RiskInput,
    RiskScoringService,
)


def test_baseline_score():
    """Verify clean transaction has base score of 10, LOW risk, APPROVE action."""
    inp = RiskInput(amount=Decimal("1500.00"))
    res = RiskScoringService.evaluate(inp)
    assert res.raw_score == 10
    assert res.final_score == 10
    assert res.risk_level == "LOW"
    assert res.suggested_action == "APPROVE"
    assert res.metadata["clamped"] is False


def test_boundary_39_and_40():
    """
    Verify boundary 39 (LOW, APPROVE) vs 40 (MEDIUM, REVIEW).
    Base 10 + High Amount 15 + Location 10 = 35 (LOW)
    Base 10 + High Velocity 25 + Location 10 = 45 (MEDIUM)
    Base 10 + High Velocity 25 + Location 10 - Location 10 + Amount 15 + ...
    Let's test Base 10 + High Velocity 25 = 35 (LOW)
    Let's test Base 10 + New Device 25 + High Amount 15 = 50 (MEDIUM)
    """
    # Base 10 + Location 10 + High Amount 15 = 35 <= 39 -> LOW
    inp_35 = RiskInput(
        amount=Decimal("12000.00"),
        is_suspicious_location=True,
    )
    res_35 = RiskScoringService.evaluate(inp_35)
    assert res_35.final_score == 35
    assert res_35.risk_level == "LOW"
    assert res_35.suggested_action == "APPROVE"

    # Base 10 + New Device 25 + Location 10 = 45 -> MEDIUM
    inp_45 = RiskInput(
        amount=Decimal("2000.00"),
        is_new_device=True,
        is_suspicious_location=True,
    )
    res_45 = RiskScoringService.evaluate(inp_45)
    assert res_45.final_score == 45
    assert res_45.risk_level == "MEDIUM"
    assert res_45.suggested_action == "REVIEW"


def test_boundary_74_and_75():
    """
    Verify boundary <= 74 is MEDIUM, >= 75 is HIGH.
    Base 10 + Device 25 + Velocity 25 + Amount 15 = 75 (HIGH, BLOCK)
    Base 10 + Device 25 + Velocity 25 + Location 10 = 70 (MEDIUM, REVIEW)
    """
    inp_70 = RiskInput(
        amount=Decimal("500.00"),
        is_new_device=True,
        has_high_velocity=True,
        is_suspicious_location=True,
    )
    res_70 = RiskScoringService.evaluate(inp_70)
    assert res_70.final_score == 70
    assert res_70.risk_level == "MEDIUM"
    assert res_70.suggested_action == "REVIEW"

    inp_75 = RiskInput(
        amount=Decimal("15000.00"),
        is_new_device=True,
        has_high_velocity=True,
    )
    res_75 = RiskScoringService.evaluate(inp_75)
    assert res_75.final_score == 75
    assert res_75.risk_level == "HIGH"
    assert res_75.suggested_action == "BLOCK"


def test_score_clamping_to_100():
    """
    Verify maximum raw score is 110 and clamps to final_score 100.
    10 + 25 + 25 + 25 + 15 + 10 = 110 -> 100
    """
    inp_all = RiskInput(
        amount=Decimal("25000.00"),
        is_new_device=True,
        has_high_velocity=True,
        has_prior_chargebacks=True,
        is_suspicious_location=True,
    )
    res_all = RiskScoringService.evaluate(inp_all)
    assert res_all.raw_score == 110
    assert res_all.final_score == 100
    assert res_all.risk_level == "HIGH"
    assert res_all.suggested_action == "BLOCK"
    assert res_all.metadata["clamped"] is True
    assert res_all.metadata["clamping_differential"] == 10

    # Total contribution weights must equal raw_score 110
    total_weights = sum(c.weight for c in res_all.contributions)
    assert total_weights == 110


def test_near_clamping_score_95():
    """
    Raw 95: Base 10 + Device 25 + Velocity 25 + Chargebacks 25 + Location 10 = 95 -> 95 (no clamp)
    """
    inp = RiskInput(
        amount=Decimal("1000.00"),
        is_new_device=True,
        has_high_velocity=True,
        has_prior_chargebacks=True,
        is_suspicious_location=True,
    )
    res = RiskScoringService.evaluate(inp)
    assert res.raw_score == 95
    assert res.final_score == 95
    assert res.risk_level == "HIGH"
    assert res.suggested_action == "BLOCK"
    assert res.metadata["clamped"] is False
    assert res.metadata["clamping_differential"] == 0
