# agents/orchestrator.py
# Pipeline orchestrator: runs Agents 1→2→3→4 in sequence,
# then either runs Agent 5 inline (auto-approve) or pauses for HITL.

import uuid
import json
import logging
import httpx
import os
from contracts.schemas import SupplierEvent, AgentState
from agents.intake_agent import run_intake_agent
from agents.quality_agent import run_quality_agent
from agents.supplier_history_agent import run_history_agent
from agents.decision_agent import run_decision_agent
from agents.executor_agent import run_executor_agent

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


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
        state = run_decision_agent(state)
    except Exception as e:
        logger.error(f"[{run_id}] Agent 4 failed: {e}")
        state.error = f"Decision agent failed: {e}"
        return state

    # ─── HITL Check ──────────────────────────────────────────
    if state.decision and state.decision.hitl_required:
        logger.info(
            f"[{run_id}] HITL required — action={state.decision.action}. "
            f"Pausing pipeline."
        )
        # Try to persist to approval queue via P4 API
        try:
            resp = httpx.post(
                f"{BACKEND_URL}/api/approvals",
                json={
                    "run_id": run_id,
                    "state_json": state.model_dump(),
                    "summary": state.decision.rationale,
                    "recommended_supplier": state.decision.recommended_supplier_id,
                },
                timeout=15,
            )
            resp.raise_for_status()
            logger.info(f"[{run_id}] Approval request posted to backend")
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
        state = run_executor_agent(state)
    except Exception as e:
        logger.error(f"[{run_id}] Agent 5 failed: {e}")
        state.error = f"Executor agent failed: {e}"

    return state
