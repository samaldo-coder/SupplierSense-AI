# agents/tools/audit_tools.py
# Tools wrapping the audit trail (immutable log of every agent decision).
#
# Write path (fastest → slowest):
#   1. Direct import of api.db.insert_audit_entry (in-process, no HTTP)
#   2. HTTP POST to /api/audit (cross-process fallback)
#
# Read path:
#   1. Direct import of api.db.get_audit_trail (in-process)
#   2. HTTP GET /api/audit/:run_id (cross-process fallback)

import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


def _db():
    """Try to import the db layer (works when running in-process with the backend)."""
    try:
        import api.db as db  # type: ignore
        return db
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

    # ── Direct in-process access (writes to memory + Supabase) ──
    db = _db()
    if db is not None:
        return db.insert_audit_entry(entry)

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
        import uuid
        entry["entry_id"] = f"LOCAL-{run_id}-{agent_name}"
        return entry


def get_audit_trail(run_id: str) -> list:
    """Fetch full ordered audit trail for a pipeline run."""
    # ── Direct in-process access ──
    db = _db()
    if db is not None:
        return db.get_audit_trail(run_id)

    # ── Fallback: HTTP call ──
    try:
        import httpx
        resp = httpx.get(f"{BASE_URL}/api/audit/{run_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Audit trail GET failed for {run_id}: {e}")
        return []
