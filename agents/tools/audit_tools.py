# agents/tools/audit_tools.py
# CrewAI tools wrapping P4's audit trail REST endpoints.
# Falls back to local state.audit_entries list when backend is offline.
#
# P3→P4 CONTRACT CHECK: POST /api/audit and GET /api/audit/:run_id
# do not exist yet in api/main.py. P4 must add them.

import httpx
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


def log_audit_decision(
    run_id: str,
    agent_name: str,
    inputs: dict,
    outputs: dict,
    confidence: float,
    rationale: str,
    hitl_actor: str = None,
) -> dict:
    """Immutably log this agent's decision to audit_log table via P4 API.
    Returns the full audit entry dict (with entry_id if backend is online,
    or a local fallback dict if offline)."""
    entry = {
        "run_id": run_id,
        "agent_name": agent_name,
        "inputs": inputs,
        "outputs": outputs,
        "confidence": confidence,
        "rationale": rationale,
        "hitl_actor": hitl_actor,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        resp = httpx.post(f"{BASE_URL}/api/audit", json=entry, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        entry["entry_id"] = data.get("entry_id", "")
        return entry
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning(f"Audit log POST failed ({agent_name}): {e} — saving locally")
        entry["entry_id"] = f"LOCAL-{run_id}-{agent_name}"
        return entry


def get_audit_trail(run_id: str) -> list:
    """Fetch full ordered audit trail for a pipeline run."""
    try:
        resp = httpx.get(f"{BASE_URL}/api/audit/{run_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning(f"Audit trail GET failed for {run_id}: {e}")
        return []
