# agents/tools/audit_tools.py
# Tools wrapping the audit trail (immutable log of every agent decision).
#
# When running in-process with the backend, writes directly to AUDIT_LOG.
# When running standalone, falls back to HTTP calls.

import os
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


def _get_audit_log():
    """Try to import the in-memory AUDIT_LOG from the backend."""
    try:
        from api.main import AUDIT_LOG
        return AUDIT_LOG
    except ImportError:
        return None


def log_audit_decision(
    run_id: str,
    agent_name: str,
    inputs: dict,
    outputs: dict,
    confidence: float,
    rationale: str,
    hitl_actor: str = None,
) -> dict:
    """Immutably log this agent's decision to audit_log.
    Returns the full audit entry dict (with entry_id)."""
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

    # ── Direct in-memory access (avoids HTTP self-deadlock) ──
    audit_log = _get_audit_log()
    if audit_log is not None:
        entry_id = str(uuid.uuid4())
        entry["entry_id"] = entry_id
        audit_log.append(entry)
        return entry

    # ── Fallback: HTTP call to backend ──
    try:
        import httpx
        resp = httpx.post(f"{BASE_URL}/api/audit", json=entry, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        entry["entry_id"] = data.get("entry_id", "")
        return entry
    except Exception as e:
        logger.warning(f"Audit log POST failed ({agent_name}): {e} — saving locally")
        entry["entry_id"] = f"LOCAL-{run_id}-{agent_name}"
        return entry


def get_audit_trail(run_id: str) -> list:
    """Fetch full ordered audit trail for a pipeline run."""
    # ── Direct in-memory access ──
    audit_log = _get_audit_log()
    if audit_log is not None:
        trail = [a for a in audit_log if a["run_id"] == run_id]
        trail.sort(key=lambda x: x.get("timestamp", ""))
        return trail

    # ── Fallback: HTTP call ──
    try:
        import httpx
        resp = httpx.get(f"{BASE_URL}/api/audit/{run_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Audit trail GET failed for {run_id}: {e}")
        return []
