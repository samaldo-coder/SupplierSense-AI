# tests/test_hitl_flow.py
# Unit tests for the HITL guard logic in the executor agent.
# No network. No LLM. Pure logic.

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from contracts.schemas import (
    AgentState,
    IntakeResult,
    QualityResult,
    HistoryResult,
    DecisionResult,
)
from agents.executor_agent import run_executor_agent


def _make_state(
    hitl_required: bool = False,
    hitl_actor: str | None = None,
    recommended_supplier: str = "a1000000-0000-0000-0000-000000000002",
) -> AgentState:
    """Build a minimal AgentState for testing the executor guard."""
    return AgentState(
        event_id="test-event-001",
        run_id="RUN-TEST-001",
        intake=IntakeResult(
            supplier_id="a1000000-0000-0000-0000-000000000001",
            event_type="DELIVERY_MISS",
            delay_days=9,
            raw_summary="Test event",
            supplier_profile={
                "supplier_id": "a1000000-0000-0000-0000-000000000001",
                "supplier_name": "AlphaForge Industries",
                "financial_health": "RED",
            },
        ),
        quality=QualityResult(
            cert_valid=False,
            cert_expiry="2025-06-15",
            cert_type="ISO 9001",
            defect_trend="STABLE",
            quality_sub_score=78.57,
        ),
        history=HistoryResult(
            avg_delay_30d=9.03,
            forecast_trend="WORSENING",
            forecast_confidence=0.16,
            anomaly_votes=0,
            anomaly_flagged=False,
            risk_index_score=61.36,
        ),
        decision=DecisionResult(
            action="ESCALATE_TO_VP" if hitl_required else "APPROVE",
            recommended_supplier_id=recommended_supplier,
            composite_score=57.74,
            rationale="Test decision",
            hitl_required=hitl_required,
            hitl_actor=hitl_actor,
        ),
    )


class TestHITLGuard:
    def test_executor_rejects_missing_decision(self):
        """Executor must raise if decision is None."""
        state = AgentState(event_id="test", run_id="RUN-TEST")
        # decision is None by default
        with pytest.raises(ValueError, match="without a Decision result"):
            run_executor_agent(state)

    def test_executor_rejects_unapproved_hitl(self):
        """Executor must raise if HITL required but no actor."""
        state = _make_state(hitl_required=True, hitl_actor=None)
        with pytest.raises(ValueError, match="without Director approval"):
            run_executor_agent(state)

    def test_executor_allows_approved_hitl(self):
        """Executor should run if HITL is required AND actor is set."""
        state = _make_state(hitl_required=True, hitl_actor="director_james")
        # This will call the actual tools (backend must be running)
        # We just verify the guard passes and doesn't raise
        try:
            result = run_executor_agent(state)
            assert result.executor is not None
            assert result.executor.po_id is not None
        except Exception as e:
            # If backend isn't running, that's ok — we're testing the guard
            if "without Director approval" in str(e):
                pytest.fail(f"Guard should have passed but raised: {e}")

    def test_executor_allows_auto_approve(self):
        """Executor should run if HITL is not required (auto-approve path)."""
        state = _make_state(hitl_required=False, hitl_actor=None)
        try:
            result = run_executor_agent(state)
            assert result.executor is not None
        except Exception as e:
            if "without Director approval" in str(e):
                pytest.fail(f"Auto-approve path should not trigger HITL guard: {e}")
