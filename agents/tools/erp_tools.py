# agents/tools/erp_tools.py
# Tools wrapping ERP data (suppliers, parts, AVL, POs).
#
# When the pipeline runs IN-PROCESS (triggered by the backend itself),
# we access the in-memory data stores DIRECTLY to avoid HTTP self-deadlock.
# When agents run as a separate process, we fall back to HTTP calls.

import os
import uuid
import logging
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


# ── Direct-access helpers ────────────────────────────────────
def _get_backend_data():
    """Try to import the in-memory data stores from the backend.
    Returns (SUPPLIERS, PARTS, AVL, PURCHASE_ORDERS, NOTIFICATIONS) or None."""
    try:
        from api.main import SUPPLIERS, PARTS, AVL, PURCHASE_ORDERS, NOTIFICATIONS
        return SUPPLIERS, PARTS, AVL, PURCHASE_ORDERS, NOTIFICATIONS
    except ImportError:
        return None


def _http_get(path: str) -> dict | list:
    """HTTP GET with timeout and error handling (fallback path)."""
    import httpx
    resp = httpx.get(f"{BASE_URL}{path}", timeout=15)
    resp.raise_for_status()
    return resp.json()


def _http_post(path: str, body: dict) -> dict:
    """HTTP POST with timeout and error handling (fallback path)."""
    import httpx
    resp = httpx.post(f"{BASE_URL}{path}", json=body, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ── Safe default responses ───────────────────────────────────
_DEFAULT_SUPPLIER = {
    "supplier_id": "unknown",
    "supplier_name": "Unknown Supplier",
    "country": "Unknown",
    "tier": 2,
    "financial_health": "YELLOW",
    "lead_time_days": 7,
    "unit_cost": 100.0,
    "is_active": True,
}

_DEFAULT_CERTS = {
    "quality_cert_type": "ISO 9001",
    "quality_cert_expiry": "2025-01-01",
    "is_approved": False,
}


# ═══════════════════════════════════════════════
# PUBLIC TOOL FUNCTIONS
# ═══════════════════════════════════════════════

def get_supplier_profile(supplier_id: str) -> dict:
    """Fetch full supplier record."""
    try:
        data = _get_backend_data()
        if data:
            SUPPLIERS = data[0]
            s = SUPPLIERS.get(supplier_id)
            if s:
                return s
            logger.warning(f"Supplier {supplier_id} not found in memory")
            return {**_DEFAULT_SUPPLIER, "supplier_id": supplier_id}
        return _http_get(f"/api/suppliers/{supplier_id}")
    except Exception as e:
        logger.warning(f"get_supplier_profile({supplier_id}) failed: {e} — using default")
        return {**_DEFAULT_SUPPLIER, "supplier_id": supplier_id}


def get_parts_by_supplier(supplier_id: str) -> list:
    """Get all parts where this supplier is the primary source."""
    try:
        data = _get_backend_data()
        if data:
            PARTS = data[1]
            return [p for p in PARTS if p["primary_supplier_id"] == supplier_id]
        return _http_get(f"/api/parts?supplier_id={supplier_id}")
    except Exception as e:
        logger.warning(f"get_parts_by_supplier({supplier_id}) failed: {e}")
        return []


def query_avl(part_id: str) -> list:
    """Return all approved vendor list entries for a part."""
    try:
        data = _get_backend_data()
        if data:
            SUPPLIERS, _, AVL, _, _ = data
            entries = [a for a in AVL if a["part_id"] == part_id]
            enriched = []
            today = date.today().isoformat()
            for a in entries:
                s = SUPPLIERS.get(a["supplier_id"], {})
                cert_valid = (a.get("quality_cert_expiry", "2025-01-01") >= today)
                enriched.append({
                    **a,
                    "supplier_name": s.get("supplier_name", "Unknown"),
                    "cert_valid": cert_valid,
                })
            return enriched
        return _http_get(f"/api/avl/{part_id}")
    except Exception as e:
        logger.warning(f"query_avl({part_id}) failed: {e}")
        return []


def get_quality_certs(supplier_id: str) -> dict:
    """Get quality cert type, expiry date, and validity for a supplier."""
    try:
        data = _get_backend_data()
        if data:
            SUPPLIERS = data[0]
            s = SUPPLIERS.get(supplier_id)
            if s:
                today = date.today().isoformat()
                expiry = s.get("quality_cert_expiry", "2025-01-01")
                return {
                    "supplier_id": supplier_id,
                    "quality_cert_type": s.get("quality_cert_type", "ISO 9001"),
                    "quality_cert_expiry": expiry,
                    "is_approved": expiry >= today,
                }
        return _http_get(f"/api/suppliers/{supplier_id}/certs")
    except Exception as e:
        logger.warning(f"get_quality_certs({supplier_id}) failed: {e}")
        return {**_DEFAULT_CERTS, "supplier_id": supplier_id}


def get_open_orders() -> list:
    """Fetch all open production orders."""
    try:
        data = _get_backend_data()
        if data:
            # Return demo orders (same as the backend endpoint)
            return [
                {"order_id": "ORD-001", "part_id": "b2000000-0000-0000-0000-000000000001", "factory": "Columbus Plant", "quantity": 50, "status": "OPEN", "due_date": "2026-03-10"},
                {"order_id": "ORD-002", "part_id": "b2000000-0000-0000-0000-000000000003", "factory": "Jamestown Plant", "quantity": 75, "status": "OPEN", "due_date": "2026-03-12"},
                {"order_id": "ORD-003", "part_id": "b2000000-0000-0000-0000-000000000005", "factory": "Rocky Mount Plant", "quantity": 150, "status": "OPEN", "due_date": "2026-03-08"},
            ]
        return _http_get("/api/orders?status=OPEN")
    except Exception as e:
        logger.warning(f"get_open_orders() failed: {e}")
        return []


def create_purchase_order(
    supplier_id: str,
    part_id: str,
    quantity: int,
    approved_by: str,
) -> dict:
    """Create a new PO record. Returns {po_id}."""
    try:
        data = _get_backend_data()
        if data:
            PURCHASE_ORDERS = data[3]
            po_id = f"PO-{uuid.uuid4().hex[:8].upper()}"
            record = {
                "po_id": po_id,
                "supplier_id": supplier_id,
                "part_id": part_id,
                "quantity": quantity,
                "approved_by": approved_by,
                "status": "CREATED",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            PURCHASE_ORDERS.append(record)
            return {"po_id": po_id}
        return _http_post("/api/purchase-orders", {
            "supplier_id": supplier_id,
            "part_id": part_id,
            "quantity": quantity,
            "approved_by": approved_by,
        })
    except Exception as e:
        fallback_po_id = f"PO-OFFLINE-{uuid.uuid4().hex[:8].upper()}"
        logger.warning(f"PO creation failed: {e} — generated fallback: {fallback_po_id}")
        return {"po_id": fallback_po_id}


def update_supplier_assignment(part_id: str, new_supplier_id: str) -> dict:
    """Update the primary supplier for a part."""
    try:
        data = _get_backend_data()
        if data:
            PARTS = data[1]
            for p in PARTS:
                if p["part_id"] == part_id:
                    old_supplier = p["primary_supplier_id"]
                    p["primary_supplier_id"] = new_supplier_id
                    return {"part_id": part_id, "old_supplier_id": old_supplier, "new_supplier_id": new_supplier_id}
            return {"part_id": part_id, "error": "Part not found"}
        return _http_post(f"/api/parts/{part_id}/supplier", {"new_supplier_id": new_supplier_id})
    except Exception as e:
        logger.warning(f"Supplier assignment update failed for part {part_id}: {e}")
        return {"status": "error", "part_id": part_id, "new_supplier_id": new_supplier_id}


def send_po_confirmation(supplier_id: str, po_id: str) -> dict:
    """Send PO confirmation notification (simulated — writes to DB)."""
    try:
        data = _get_backend_data()
        if data:
            NOTIFICATIONS = data[4]
            notification_id = str(uuid.uuid4())
            record = {
                "notification_id": notification_id,
                "recipient_role": "procurement",
                "notification_type": "po_confirmation",
                "title": f"[PO_CONFIRMATION] PO {po_id} created for supplier {supplier_id}",
                "body": f"Purchase order {po_id} has been created for supplier {supplier_id}.",
                "metadata": {"supplier_id": supplier_id, "po_id": po_id},
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            NOTIFICATIONS.append(record)
            return {"notification_id": notification_id, "status": "sent"}
        return _http_post("/api/comms/notify", {
            "type": "po_confirmation",
            "supplier_id": supplier_id,
            "po_id": po_id,
        })
    except Exception as e:
        logger.warning(f"Notification send failed for PO {po_id}: {e}")
        return {"status": "offline", "notification": f"PO {po_id} confirmation pending"}
