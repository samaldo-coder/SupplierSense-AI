"""
SupplyGuard AI — Persistent storage layer.

Write-through design:
  1. Every write hits the in-memory store immediately (so the current
     process always sees a consistent view and agent direct-imports work).
  2. Every write is also pushed to Supabase (when configured).

On startup, call load_from_supabase() to hydrate the in-memory stores
from the real database so data survives server restarts.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def _run_id_to_uuid(run_id: str) -> str:
    """Convert any string (e.g. 'RUN-ABC123') to a deterministic UUID5.

    Supabase stores several FK columns as UUID. Our internal run_ids use a
    human-readable 'RUN-XXX' format, so we derive a stable UUID from them.
    Real UUIDs pass through unchanged.
    """
    import uuid as _uuid
    try:
        # If it's already a valid UUID, return as-is
        str(_uuid.UUID(run_id))
        return run_id
    except (ValueError, AttributeError):
        return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, run_id))


# ─────────────────────────────────────────────────────────────
# In-memory stores  (single source of truth inside this process)
# ─────────────────────────────────────────────────────────────
AUDIT_LOG: list[dict] = []
PENDING_APPROVALS: dict[str, dict] = {}
PURCHASE_ORDERS: list[dict] = []
NOTIFICATIONS: list[dict] = []

# Maps our RUN-XXX string → Supabase pipeline_runs.id (UUID)
# Needed because notifications/purchase_orders have FK → pipeline_runs.id
_PIPELINE_RUN_MAP: dict[str, str] = {}


# ─────────────────────────────────────────────────────────────
# Supabase helper
# ─────────────────────────────────────────────────────────────

def _sb():
    """Return the Supabase client, or None if not configured."""
    try:
        from api.supabase_client import get_supabase  # type: ignore
        return get_supabase()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Startup hydration
# ─────────────────────────────────────────────────────────────

def load_from_supabase() -> None:
    """Populate in-memory stores from Supabase on server startup."""
    sb = _sb()
    if sb is None:
        logger.info("[DB] Supabase not configured — skipping hydration.")
        return

    # audit_log
    try:
        rows = sb.table("audit_log").select("*").order("timestamp").execute().data or []
        AUDIT_LOG.clear()
        AUDIT_LOG.extend(_normalise_rows(rows))
        logger.info(f"[DB] Loaded {len(rows)} audit entries from Supabase.")
    except Exception as e:
        logger.warning(f"[DB] Could not load audit_log: {e}")

    # pending_approvals
    try:
        rows = sb.table("pending_approvals").select("*").order("created_at", desc=True).execute().data or []
        PENDING_APPROVALS.clear()
        for r in _normalise_rows(rows):
            PENDING_APPROVALS[r["approval_id"]] = r
        logger.info(f"[DB] Loaded {len(rows)} approvals from Supabase.")
    except Exception as e:
        logger.warning(f"[DB] Could not load pending_approvals: {e}")

    # purchase_orders
    try:
        rows = sb.table("purchase_orders").select("*").order("created_at", desc=True).execute().data or []
        PURCHASE_ORDERS.clear()
        PURCHASE_ORDERS.extend(_normalise_rows(rows))
        logger.info(f"[DB] Loaded {len(rows)} purchase orders from Supabase.")
    except Exception as e:
        logger.warning(f"[DB] Could not load purchase_orders: {e}")

    # notifications — Supabase uses 'status' field; our code expects 'is_read' bool
    try:
        rows = sb.table("notifications").select("*").order("created_at", desc=True).execute().data or []
        NOTIFICATIONS.clear()
        for r in _normalise_rows(rows):
            # Translate Supabase 'status' → our internal 'is_read' bool
            if "is_read" not in r:
                r["is_read"] = r.get("status") == "read"
            NOTIFICATIONS.append(r)
        logger.info(f"[DB] Loaded {len(rows)} notifications from Supabase.")
    except Exception as e:
        logger.warning(f"[DB] Could not load notifications: {e}")


def _normalise_rows(rows: list) -> list:
    """Convert Supabase JSONB/datetime fields to plain Python types."""
    result = []
    for r in rows:
        row = dict(r)
        # Supabase returns datetime objects for TIMESTAMPTZ — convert to ISO string
        for k, v in row.items():
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat()
        result.append(row)
    return result


# ─────────────────────────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────────────────────────

def insert_audit_entry(entry: dict) -> dict:
    """Append to in-memory AUDIT_LOG and persist to Supabase.

    Also mirrors to agent_steps table (same data, Supabase's own schema).
    Idempotent: skips insert if entry_id already exists in memory.
    """
    if "entry_id" not in entry or not entry.get("entry_id"):
        entry["entry_id"] = str(uuid.uuid4())
    if "timestamp" not in entry or not entry.get("timestamp"):
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Dedup: skip if we already have this entry_id in memory
    existing_ids = {e.get("entry_id") for e in AUDIT_LOG}
    if entry["entry_id"] in existing_ids:
        logger.debug(f"[DB] Skipping duplicate audit entry {entry['entry_id']}")
        return entry

    AUDIT_LOG.append(entry)

    sb = _sb()
    if sb:
        # Write to audit_log (our schema — matches perfectly)
        try:
            sb.table("audit_log").insert({
                "entry_id": entry["entry_id"],
                "run_id": entry["run_id"],
                "agent_name": entry["agent_name"],
                "inputs": entry.get("inputs", {}),
                "outputs": entry.get("outputs", {}),
                "confidence": float(entry.get("confidence", 0.0)),
                "rationale": str(entry.get("rationale", "")),
                "hitl_actor": entry.get("hitl_actor"),
            }).execute()
        except Exception as e:
            logger.warning(f"[DB] Supabase audit_log insert failed: {e}")

        # Also mirror to agent_steps (agent_steps.run_id is FK → pipeline_runs.id)
        try:
            pl_id = _get_or_create_pipeline_run_id(entry["run_id"], sb)
            if pl_id:
                sb.table("agent_steps").insert({
                    "run_id": pl_id,
                    "agent_name": entry["agent_name"],
                    "step_status": "completed",
                    "input": entry.get("inputs", {}),
                    "output": entry.get("outputs", {}),
                    "notes": str(entry.get("rationale", ""))[:500],
                }).execute()
        except Exception:
            pass  # agent_steps is optional — never block the main flow

    return entry


def get_audit_trail(run_id: str) -> list:
    """Return ordered audit entries for a pipeline run."""
    # Try Supabase for the freshest persisted data
    sb = _sb()
    if sb:
        try:
            rows = (
                sb.table("audit_log")
                .select("*")
                .eq("run_id", run_id)
                .order("timestamp")
                .execute()
                .data
                or []
            )
            if rows:
                return _normalise_rows(rows)
        except Exception as e:
            logger.warning(f"[DB] Supabase audit_log read failed: {e}")

    # Fallback to in-memory
    trail = [a for a in AUDIT_LOG if a.get("run_id") == run_id]
    trail.sort(key=lambda x: x.get("timestamp", ""))
    return trail


# ─────────────────────────────────────────────────────────────
# Pending Approvals (HITL queue)
# ─────────────────────────────────────────────────────────────

def insert_approval(record: dict) -> dict:
    """Insert approval into in-memory store and Supabase.

    Uses upsert (on_conflict=approval_id) so re-runs of the same pipeline
    don't blow up the run_id UNIQUE constraint with a duplicate insert.
    """
    PENDING_APPROVALS[record["approval_id"]] = record

    sb = _sb()
    if sb:
        try:
            sb.table("pending_approvals").upsert({
                "approval_id": record["approval_id"],
                "run_id": record["run_id"],
                "state_json": record.get("state_json", {}),
                "summary": record.get("summary", ""),
                "recommended_supplier_id": record.get("recommended_supplier_id") or None,
                "status": record.get("status", "PENDING"),
            }, on_conflict="approval_id").execute()
            logger.info(f"[DB] Approval {record['approval_id']} upserted to Supabase (run={record['run_id']})")
        except Exception as e:
            logger.error(f"[DB] Supabase pending_approvals upsert FAILED: {e}")

    return record


def update_approval(approval_id: str, updates: dict) -> dict | None:
    """Update approval fields in in-memory store and Supabase."""
    record = PENDING_APPROVALS.get(approval_id)
    if record is None:
        return None

    record.update(updates)

    sb = _sb()
    if sb:
        # Only push fields that exist in the DB schema
        db_updates = {
            k: updates[k]
            for k in ("status", "decided_by", "decision_note", "decided_at")
            if k in updates
        }
        if db_updates:
            try:
                result = sb.table("pending_approvals").update(db_updates).eq("approval_id", approval_id).execute()
                logger.info(f"[DB] Approval {approval_id} updated in Supabase → status={updates.get('status')}")
            except Exception as e:
                logger.error(f"[DB] Supabase pending_approvals update FAILED for {approval_id}: {e}")

    return record


def get_approval(approval_id: str) -> dict | None:
    return PENDING_APPROVALS.get(approval_id)


def get_approval_by_run_id(run_id: str) -> dict | None:
    for a in PENDING_APPROVALS.values():
        if a.get("run_id") == run_id:
            return a
    return None


def list_approvals(status: Optional[str] = None) -> list:
    items = list(PENDING_APPROVALS.values())
    if status:
        items = [a for a in items if a.get("status") == status.upper()]
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


# ─────────────────────────────────────────────────────────────
# Purchase Orders
# ─────────────────────────────────────────────────────────────

def insert_purchase_order(record: dict) -> dict:
    """Append PO to in-memory store and persist to Supabase.

    Supabase purchase_orders schema (actual):
      id, created_at, run_id, supplier_id, supplier_name, item, quantity, eta_date, status
    Idempotent: skips insert if po_id already exists in memory.
    """
    po_id = record.get("po_id")
    if po_id and any(p.get("po_id") == po_id for p in PURCHASE_ORDERS):
        logger.debug(f"[DB] Skipping duplicate purchase order {po_id}")
        return record

    PURCHASE_ORDERS.append(record)

    sb = _sb()
    if sb:
        try:
            from datetime import date, timedelta
            eta = (date.today() + timedelta(days=record.get("lead_time_days", 7))).isoformat()
            raw_run_id = record.get("run_id") or ""
            # purchase_orders.run_id is FK → pipeline_runs.id in Supabase
            pl_id = _get_or_create_pipeline_run_id(raw_run_id, sb) if raw_run_id else None
            supplier_name = record.get("supplier_name", "")
            sb.table("purchase_orders").insert({
                "run_id": pl_id,
                "supplier_id": record["supplier_id"],
                "supplier_name": supplier_name,
                "item": record.get("part_id", ""),
                "quantity": int(record["quantity"]),
                "eta_date": eta,
                "status": record.get("status", "CREATED"),
            }).execute()
        except Exception as e:
            logger.warning(f"[DB] Supabase purchase_orders insert failed: {e}")

    return record


def list_purchase_orders() -> list:
    return list(PURCHASE_ORDERS)


# ─────────────────────────────────────────────────────────────
# Pipeline Runs  (Supabase-native table for frontend tracking)
# ─────────────────────────────────────────────────────────────

def _get_or_create_pipeline_run_id(run_id: str, sb) -> Optional[str]:
    """Get (or create) the Supabase pipeline_runs.id for a given run_id.

    Returns the auto-generated UUID from pipeline_runs.id, or None on error.
    This UUID is required as FK for agent_steps, notifications, purchase_orders.
    """
    if run_id in _PIPELINE_RUN_MAP:
        return _PIPELINE_RUN_MAP[run_id]
    try:
        result = sb.table("pipeline_runs").insert({
            "status": "running",
            "current_step": "",
            "risk_score": 0.0,
            "recommendation_summary": "",
            "final_decision": "",
        }).execute()
        if result.data:
            pl_id = result.data[0]["id"]
            _PIPELINE_RUN_MAP[run_id] = pl_id
            return pl_id
    except Exception as e:
        logger.warning(f"[DB] Could not create pipeline_runs row for {run_id}: {e}")
    return None


def upsert_pipeline_run(
    run_id: str,
    event_id: str = "",
    status: str = "running",
    current_step: str = "",
    risk_score: float = 0.0,
    recommendation_summary: str = "",
    final_decision: str = "",
) -> None:
    """Write/update a pipeline_runs row in Supabase."""
    sb = _sb()
    if not sb:
        return
    try:
        pl_id = _get_or_create_pipeline_run_id(run_id, sb)
        if not pl_id:
            return
        sb.table("pipeline_runs").update({
            "status": status,
            "current_step": current_step,
            "risk_score": risk_score,
            "recommendation_summary": recommendation_summary[:500] if recommendation_summary else "",
            "final_decision": final_decision,
        }).eq("id", pl_id).execute()
    except Exception:
        pass  # pipeline_runs is optional — never block the agent pipeline


# ─────────────────────────────────────────────────────────────
# Notifications  (simulated Teams / comms)
# ─────────────────────────────────────────────────────────────

def insert_notification(record: dict) -> dict:
    """Append notification to in-memory store and persist to Supabase.

    Supabase notifications schema (actual):
      id, created_at, run_id, channel, recipient, message, status
    Idempotent: skips insert if notification_id already exists in memory.
    """
    nid = record.get("notification_id")
    if nid and any(n.get("notification_id") == nid for n in NOTIFICATIONS):
        logger.debug(f"[DB] Skipping duplicate notification {nid}")
        return record

    NOTIFICATIONS.append(record)

    sb = _sb()
    if sb:
        try:
            meta = record.get("metadata", {}) or {}
            raw_run_id = meta.get("run_id") or ""
            # notifications.run_id is FK → pipeline_runs.id (UUID) in Supabase
            pl_id = _get_or_create_pipeline_run_id(raw_run_id, sb) if raw_run_id else None
            sb.table("notifications").insert({
                "run_id": pl_id,
                "channel": record.get("notification_type", "general"),
                "recipient": record.get("recipient_role", "system"),
                "message": f"{record.get('title', '')} — {record.get('body', '')}".strip(" —"),
                "status": "unread",
            }).execute()
        except Exception as e:
            logger.warning(f"[DB] Supabase notifications insert failed: {e}")

    return record


def list_notifications(role: Optional[str] = None, unread_only: bool = False) -> list:
    items = list(NOTIFICATIONS)
    if role:
        items = [n for n in items if n.get("recipient_role") == role]
    if unread_only:
        items = [n for n in items if not n.get("is_read", False)]
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def mark_notification_read(notification_id: str) -> bool:
    """Mark notification as read in memory and Supabase."""
    for n in NOTIFICATIONS:
        if n.get("notification_id") == notification_id:
            n["is_read"] = True
            sb = _sb()
            if sb:
                try:
                    meta = n.get("metadata", {}) or {}
                    raw_run_id = meta.get("run_id", "")
                    pl_id = _PIPELINE_RUN_MAP.get(raw_run_id)
                    if pl_id:
                        sb.table("notifications").update({"status": "read"}).eq(
                            "run_id", pl_id
                        ).execute()
                except Exception as e:
                    logger.warning(f"[DB] Supabase notification mark-read failed: {e}")
            return True
    return False
