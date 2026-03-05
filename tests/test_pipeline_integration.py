# tests/test_pipeline_integration.py
# Integration tests — requires backend running on :3001.
# Run with: pytest tests/test_pipeline_integration.py -v -m integration

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import json
import httpx

from agents.orchestrator import run_pipeline

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BACKEND_URL = "http://localhost:3001"


def backend_available():
    try:
        resp = httpx.get(f"{BACKEND_URL}/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not backend_available(),
    reason="Backend not running on localhost:3001",
)


class TestPipelineIntegration:
    def test_green_event_auto_approves(self):
        """Green event: low-risk supplier should auto-approve with all 5 agents."""
        event = json.loads((FIXTURES_DIR / "event_green.json").read_text())
        state = run_pipeline(event)

        assert state.error is None, f"Pipeline error: {state.error}"
        assert state.decision is not None
        assert state.decision.composite_score < 40
        assert state.decision.hitl_required is False
        assert state.decision.action == "APPROVE"
        assert state.executor is not None
        assert state.executor.po_id is not None
        assert state.paused_for_hitl is False
        assert len(state.audit_entries) == 5  # all 5 agents ran

    def test_red_event_triggers_hitl(self):
        """Red event: AlphaForge CRITICAL should trigger HITL and pause."""
        event = json.loads((FIXTURES_DIR / "event_red.json").read_text())
        state = run_pipeline(event)

        assert state.error is None, f"Pipeline error: {state.error}"
        assert state.decision is not None
        assert state.decision.hitl_required is True
        assert state.decision.action in ["ESCALATE_TO_DIRECTOR", "ESCALATE_TO_VP"]
        assert state.paused_for_hitl is True
        assert state.executor is None  # Agent 5 should NOT run
        assert len(state.audit_entries) == 4  # only agents 1-4

    def test_yellow_event_escalates(self):
        """Yellow event: DeltaSteel should require director review."""
        event = json.loads((FIXTURES_DIR / "event_yellow.json").read_text())
        state = run_pipeline(event)

        assert state.error is None, f"Pipeline error: {state.error}"
        assert state.decision is not None
        assert state.decision.hitl_required is True
        assert state.paused_for_hitl is True
        assert state.executor is None

    def test_audit_log_written_per_agent(self):
        """Every agent must write to the audit_log."""
        event = json.loads((FIXTURES_DIR / "event_green.json").read_text())
        state = run_pipeline(event)

        # Check audit trail via API
        resp = httpx.get(f"{BACKEND_URL}/api/audit/{state.run_id}", timeout=10)
        assert resp.status_code == 200
        rows = resp.json()
        agent_names = [r["agent_name"] for r in rows]

        assert "intake_agent" in agent_names
        assert "quality_agent" in agent_names
        assert "supplier_history_agent" in agent_names
        assert "decision_agent" in agent_names
        assert "executor_agent" in agent_names  # green event auto-approves

    def test_approval_created_for_hitl_event(self):
        """HITL event should create a pending approval in the backend."""
        event = json.loads((FIXTURES_DIR / "event_red.json").read_text())
        state = run_pipeline(event)

        # Check approvals API
        resp = httpx.get(f"{BACKEND_URL}/api/approvals?status=PENDING", timeout=10)
        assert resp.status_code == 200
        approvals = resp.json()

        run_ids = [a["run_id"] for a in approvals]
        assert state.run_id in run_ids, f"Approval for {state.run_id} not found in pending list"

    def test_all_seed_events_complete_without_crash(self):
        """Smoke test: every seed event should complete without errors."""
        resp = httpx.get(f"{BACKEND_URL}/api/events", timeout=10)
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) >= 10, f"Expected >= 10 events, got {len(events)}"

        for event in events:
            state = run_pipeline(event)
            assert state.decision is not None, f"No decision for event {event['event_id']}"
            assert 0 <= state.decision.composite_score <= 100
            assert state.error is None, f"Error for event {event['event_id']}: {state.error}"

    def test_dashboard_stats_update_after_pipeline(self):
        """Dashboard stats should reflect pipeline runs."""
        resp = httpx.get(f"{BACKEND_URL}/api/dashboard/stats", timeout=10)
        assert resp.status_code == 200
        stats = resp.json()
        assert stats["total_audit_entries"] > 0, "Audit entries should exist after runs"
