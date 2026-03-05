# tests/test_scoring_unit.py
# Unit tests for the composite score formula and escalation rule engine.
# No network. No LLM. Pure deterministic logic.
# Run with: pytest tests/test_scoring_unit.py -v

import sys
from pathlib import Path

# Ensure repo root is on path for local imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from agents.utils import compute_composite_score, determine_action_and_hitl


class TestCompositeScore:
    def test_green_scores_below_40(self):
        """A healthy supplier with low delay and low anomaly activity scores < 40."""
        score = compute_composite_score(
            quality_sub_score=10,
            forecast_confidence_in_stable=0.95,  # very confident → low risk
            anomaly_votes=0,
            risk_index_score=10,
        )
        assert score < 40, f"Expected < 40, got {score}"

    def test_red_scores_above_70(self):
        """A deeply troubled supplier scores > 70."""
        score = compute_composite_score(
            quality_sub_score=90,
            forecast_confidence_in_stable=0.10,  # low confidence → high risk
            anomaly_votes=3,
            risk_index_score=85,
        )
        assert score > 70, f"Expected > 70, got {score}"

    def test_score_bounded_0_to_100(self):
        """Score must never exceed 0–100 range regardless of inputs."""
        score = compute_composite_score(100, 0.0, 3, 100)
        assert 0 <= score <= 100, f"Score {score} out of [0, 100]"

    def test_score_minimum_is_zero(self):
        """Perfect supplier scores ≥ 0."""
        score = compute_composite_score(0.0, 1.0, 0, 0.0)
        assert score >= 0, f"Score {score} should be >= 0"

    def test_formula_weights_add_to_100(self):
        """Verify formula: max inputs should yield 100."""
        score = compute_composite_score(
            quality_sub_score=100,
            forecast_confidence_in_stable=0.0,  # (1-0)*100 = 100
            anomaly_votes=3,                     # (3/3)*100 = 100
            risk_index_score=100,
        )
        # 0.35*100 + 0.25*100 + 0.25*100 + 0.15*100 = 100
        assert abs(score - 100.0) < 0.01, f"Expected ~100, got {score}"


class TestEscalationRules:
    def test_expired_cert_forces_hitl_regardless_of_score(self):
        """Low composite score but expired cert must still require HITL."""
        action, hitl = determine_action_and_hitl(
            composite_score=25,
            cert_valid=False,
            financial_health="GREEN",
            forecast_trend="STABLE",
            anomaly_votes=0,
        )
        assert hitl is True, "Expired cert must force HITL"
        assert action == "ESCALATE_TO_DIRECTOR"

    def test_red_financial_and_expired_cert_escalates_to_vp(self):
        """RED financial health + expired cert = highest severity = VP escalation."""
        action, hitl = determine_action_and_hitl(
            composite_score=80,
            cert_valid=False,
            financial_health="RED",
            forecast_trend="WORSENING",
            anomaly_votes=3,
        )
        assert action == "ESCALATE_TO_VP", f"Expected ESCALATE_TO_VP, got {action}"
        assert hitl is True

    def test_worsening_trend_with_anomaly_escalates_to_director(self):
        """WORSENING trend + ≥2 anomaly votes triggers Director escalation."""
        action, hitl = determine_action_and_hitl(
            composite_score=50,
            cert_valid=True,
            financial_health="GREEN",
            forecast_trend="WORSENING",
            anomaly_votes=2,
        )
        assert action == "ESCALATE_TO_DIRECTOR", f"Expected ESCALATE_TO_DIRECTOR, got {action}"
        assert hitl is True

    def test_low_risk_approves_without_hitl(self):
        """A fully green supplier should auto-approve with no HITL."""
        action, hitl = determine_action_and_hitl(
            composite_score=30,
            cert_valid=True,
            financial_health="GREEN",
            forecast_trend="STABLE",
            anomaly_votes=0,
        )
        assert action == "APPROVE", f"Expected APPROVE, got {action}"
        assert hitl is False

    def test_score_above_70_triggers_hitl(self):
        """Composite score ≥ 70 alone triggers Director escalation."""
        action, hitl = determine_action_and_hitl(
            composite_score=72,
            cert_valid=True,
            financial_health="GREEN",
            forecast_trend="STABLE",
            anomaly_votes=0,
        )
        assert action == "ESCALATE_TO_DIRECTOR"
        assert hitl is True

    def test_red_financial_green_cert_not_vp(self):
        """RED financial but valid cert does NOT escalate to VP (Rule 1 requires both)."""
        action, hitl = determine_action_and_hitl(
            composite_score=50,
            cert_valid=True,        # cert is fine
            financial_health="RED",
            forecast_trend="STABLE",
            anomaly_votes=0,
        )
        # Should NOT hit Rule 1 (needs both RED + cert_invalid)
        assert action != "ESCALATE_TO_VP", "Should not VP-escalate when cert is valid"

    def test_worsening_but_only_1_vote_no_director_escalation(self):
        """WORSENING + only 1 anomaly vote does NOT trigger Rule 2 (needs ≥2)."""
        action, hitl = determine_action_and_hitl(
            composite_score=40,
            cert_valid=True,
            financial_health="GREEN",
            forecast_trend="WORSENING",
            anomaly_votes=1,    # only 1 vote — Rule 2 needs ≥2
        )
        # Rule 2 not triggered, score < 70, cert valid → should APPROVE
        assert action == "APPROVE"
        assert hitl is False
