# agents/orchestrator.py
# Pipeline orchestrator: runs Agents 1→2→3→4 in sequence,
# then either runs Agent 5 inline (auto-approve) or pauses for HITL.

import uuid
import json
import logging
import os
from datetime import datetime, timezone
from contracts.schemas import SupplierEvent, AgentState
from agents.intake_agent import run_intake_agent
from agents.quality_agent import run_quality_agent
from agents.supplier_history_agent import run_history_agent
from agents.decision_agent import run_decision_agent
from agents.executor_agent import run_executor_agent

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


def _post_approval_direct(run_id: str, state: AgentState) -> bool:
    """Write the approval via api.db (in-process write-through to Supabase).
    Returns True if successful, False if db layer is not importable."""
    try:
        import api.db as db  # type: ignore

        approval_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        db.insert_approval({
            "approval_id": approval_id,
            "run_id": run_id,
            "state_json": state.model_dump(),
            "summary": state.decision.rationale if state.decision else "",
            "recommended_supplier_id": (
                state.decision.recommended_supplier_id if state.decision else None
            ),
            "status": "PENDING",
            "created_at": created_at,
            "decided_at": None,
            "decided_by": None,
            "decision_note": None,
        })

        db.insert_notification({
            "notification_id": str(uuid.uuid4()),
            "recipient_role": "director",
            "notification_type": "approval_required",
            "title": f"[APPROVAL REQUIRED] Pipeline {run_id}",
            "body": state.decision.rationale if state.decision else "Approval needed",
            "metadata": {"run_id": run_id, "approval_id": approval_id},
            "is_read": False,
            "created_at": created_at,
        })

        logger.info(f"[{run_id}] Approval + notification written via db layer (approval_id={approval_id})")
        return True
    except ImportError:
        return False


def _db_track(run_id: str, **kwargs) -> None:
    """Non-blocking pipeline_runs upsert — swallows all errors."""
    try:
        import api.db as db  # type: ignore
        db.upsert_pipeline_run(run_id=run_id, **kwargs)
    except Exception:
        pass


def run_pipeline(event_dict: dict) -> AgentState:
    """
    Run the full SupplyGuard AI 5-agent pipeline.

    Args:
        event_dict: Raw event dict (must match SupplierEvent schema)

    Returns:
        AgentState with all agent outputs populated.
        If HITL is required, state.paused_for_hitl=True and executor is None.
        Never raises — sets state.error on failure.
    """
    run_id = f"RUN-{uuid.uuid4().hex[:12].upper()}"

    # Validate inbound event
    try:
        event = SupplierEvent(**event_dict)
    except Exception as e:
        logger.error(f"Invalid event: {e}")
        return AgentState(
            event_id=event_dict.get("event_id", "UNKNOWN"),
            run_id=run_id,
            error=f"Invalid event: {e}",
        )

    state = AgentState(event_id=event.event_id, run_id=run_id)
    _db_track(run_id, event_id=event.event_id, status="running", current_step="intake")

    # ─── Agent 1: Intake ─────────────────────────────────────
    try:
        logger.info(f"[{run_id}] Running Agent 1: Intake")
        state = run_intake_agent(event, state)
    except Exception as e:
        logger.error(f"[{run_id}] Agent 1 failed: {e}")
        state.error = f"Intake agent failed: {e}"
        return state

    # ─── Agent 2: Quality ────────────────────────────────────
    try:
        logger.info(f"[{run_id}] Running Agent 2: Quality")
        state = run_quality_agent(state)
    except Exception as e:
        logger.error(f"[{run_id}] Agent 2 failed: {e}")
        state.error = f"Quality agent failed: {e}"
        return state

    # ─── Agent 3: Supplier History ───────────────────────────
    try:
        logger.info(f"[{run_id}] Running Agent 3: History")
        state = run_history_agent(state)
    except Exception as e:
        logger.error(f"[{run_id}] Agent 3 failed: {e}")
        state.error = f"History agent failed: {e}"
        return state

    # ─── Agent 4: Decision ───────────────────────────────────
    try:
        logger.info(f"[{run_id}] Running Agent 4: Decision")
        _db_track(run_id, status="running", current_step="decision")
        state = run_decision_agent(state)
    except Exception as e:
        logger.error(f"[{run_id}] Agent 4 failed: {e}")
        state.error = f"Decision agent failed: {e}"
        _db_track(run_id, status="failed", current_step="decision")
        return state

    # ─── HITL Check ──────────────────────────────────────────
    if state.decision and state.decision.hitl_required:
        logger.info(
            f"[{run_id}] HITL required — action={state.decision.action}. "
            f"Pausing pipeline."
        )
        _db_track(
            run_id,
            status="awaiting_approval",
            current_step="hitl",
            risk_score=float(state.decision.composite_score or 0),
            recommendation_summary=state.decision.rationale or "",
            final_decision=state.decision.action or "",
        )

        # Try direct in-memory write first (avoids HTTP self-deadlock)
        if not _post_approval_direct(run_id, state):
            # Fallback: HTTP call (only works when backend is a separate process)
            try:
                import httpx
                resp = httpx.post(
                    f"{BACKEND_URL}/api/approvals",
                    json={
                        "run_id": run_id,
                        "state_json": state.model_dump(),
                        "summary": state.decision.rationale,
                        "recommended_supplier_id": state.decision.recommended_supplier_id,
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                logger.info(f"[{run_id}] Approval request posted to backend via HTTP")
            except Exception as e:
                logger.warning(
                    f"[{run_id}] Could not post approval to backend: {e} — "
                    f"state preserved in memory only"
                )

        state.paused_for_hitl = True
        return state  # Do NOT run Agent 5

    # ─── Agent 5: Executor (auto-approve path) ──────────────
    try:
        logger.info(f"[{run_id}] Auto-approved — running Agent 5: Executor")
        _db_track(run_id, status="running", current_step="executor")
        state = run_executor_agent(state)
        _db_track(
            run_id,
            status="completed",
            current_step="done",
            risk_score=float(state.decision.composite_score if state.decision else 0),
            recommendation_summary=state.decision.rationale if state.decision else "",
            final_decision=state.executor.po_id if state.executor else "auto_approved",
        )
    except Exception as e:
        logger.error(f"[{run_id}] Agent 5 failed: {e}")
        state.error = f"Executor agent failed: {e}"
        _db_track(run_id, status="failed", current_step="executor")

    return state
