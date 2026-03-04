# agents/resume_api.py
# Minimal FastAPI on port 8002 — called by P4's backend after Director approves.
#
# Start with: uvicorn agents.resume_api:app --port 8002
#
# P3→P4 CONTRACT CHECK: P4 backend must call POST localhost:8002/resume
# after PATCH /api/approvals/:id/decide updates the DB.

import json
import logging
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from contracts.schemas import AgentState
from agents.executor_agent import run_executor_agent
from agents.tools.audit_tools import log_audit_decision

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SupplyGuard AI — HITL Resume API",
    description="Resumes the agent pipeline after Director approval/rejection",
    version="1.0.0",
)

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


class ResumeRequest(BaseModel):
    run_id: str
    decision: str       # "approved" | "rejected"
    hitl_actor: str     # Director's user_id


@app.get("/health")
async def health():
    return {"status": "ok", "service": "supplyguard-resume-api", "port": 8002}


@app.post("/resume")
async def resume_pipeline(req: ResumeRequest):
    """
    Resume a paused pipeline after Director decision.
    - If approved: loads state, sets hitl_actor, runs Agent 5, returns PO.
    - If rejected: logs rejection to audit, returns status.
    """
    logger.info(f"Resume request: run_id={req.run_id}, decision={req.decision}, actor={req.hitl_actor}")

    if req.decision == "rejected":
        # Log rejection to audit trail
        log_audit_decision(
            run_id=req.run_id,
            agent_name="hitl_rejection",
            inputs={"decision": "rejected", "hitl_actor": req.hitl_actor},
            outputs={"status": "rejected"},
            confidence=1.0,
            rationale=f"Director {req.hitl_actor} rejected the recommended action.",
            hitl_actor=req.hitl_actor,
        )
        return {"status": "rejected", "run_id": req.run_id}

    if req.decision != "approved":
        raise HTTPException(status_code=400, detail=f"Invalid decision: {req.decision}. Must be 'approved' or 'rejected'.")

    # Load saved state from backend
    state = await _load_state_from_db(req.run_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"No saved state found for run_id={req.run_id}")

    # Set HITL actor and unpause
    if state.decision:
        state.decision.hitl_actor = req.hitl_actor
    state.paused_for_hitl = False

    # Run Agent 5 only
    try:
        final_state = run_executor_agent(state)
        logger.info(f"Pipeline resumed and executed. PO: {final_state.executor.po_id if final_state.executor else 'N/A'}")
        return {
            "status": "executed",
            "run_id": req.run_id,
            "po_id": final_state.executor.po_id if final_state.executor else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Resume execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {e}")


async def _load_state_from_db(run_id: str) -> AgentState | None:
    """Load saved AgentState from P4's API (pending_approvals table)."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/approvals/state/{run_id}",
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            state_json = data.get("state_json")
            if state_json:
                if isinstance(state_json, str):
                    state_json = json.loads(state_json)
                return AgentState(**state_json)
    except httpx.ConnectError:
        logger.warning(f"Backend offline — cannot load state for {run_id}")
    except Exception as e:
        logger.error(f"Failed to load state for {run_id}: {e}")
    return None
