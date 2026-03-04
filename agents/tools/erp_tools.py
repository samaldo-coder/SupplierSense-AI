# agents/tools/erp_tools.py
# CrewAI tools wrapping P4's REST API for ERP operations.
# All calls go through the backend at localhost:3001.
#
# P3→P4 CONTRACT CHECK: Backend is currently Python FastAPI, not Node.js Express.
# P3→P4 CONTRACT CHECK: None of these endpoints exist yet in api/main.py.
# P4 must add: /api/suppliers/:id, /api/parts, /api/avl/:part_id,
#              /api/purchase-orders, /api/orders, /api/comms/notify
# See INTEGRATION_NOTES.md for full list.

import httpx
import os
import logging

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")

# ─── Safe default responses when backend is offline ──────────
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


def _get(path: str) -> dict | list:
    """HTTP GET with timeout and error handling."""
    try:
        resp = httpx.get(f"{BASE_URL}{path}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning(f"ERP GET {path} failed: {e}")
        raise


def _post(path: str, body: dict) -> dict:
    """HTTP POST with timeout and error handling."""
    try:
        resp = httpx.post(f"{BASE_URL}{path}", json=body, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning(f"ERP POST {path} failed: {e}")
        raise


def get_supplier_profile(supplier_id: str) -> dict:
    """Fetch full supplier record: name, country, tier, financial_health,
    lead_time_days, unit_cost, is_active."""
    try:
        return _get(f"/api/suppliers/{supplier_id}")
    except Exception:
        logger.warning(f"Falling back to default supplier profile for {supplier_id}")
        return {**_DEFAULT_SUPPLIER, "supplier_id": supplier_id}


def get_parts_by_supplier(supplier_id: str) -> list:
    """Get all parts where this supplier is the primary source."""
    try:
        return _get(f"/api/parts?supplier_id={supplier_id}")
    except Exception:
        logger.warning(f"Falling back to empty parts list for {supplier_id}")
        return []


def query_avl(part_id: str) -> list:
    """Return all approved vendor list entries for a part, including
    lead_time_days, unit_cost, quality_cert_expiry, geographic_risk."""
    try:
        return _get(f"/api/avl/{part_id}")
    except Exception:
        logger.warning(f"Falling back to empty AVL for part {part_id}")
        return []


def get_quality_certs(supplier_id: str) -> dict:
    """Get quality cert type, expiry date, and validity for a supplier."""
    try:
        return _get(f"/api/suppliers/{supplier_id}/certs")
    except Exception:
        logger.warning(f"Falling back to default certs for {supplier_id}")
        return {**_DEFAULT_CERTS}


def get_open_orders() -> list:
    """Fetch all open production orders with factory and part details."""
    try:
        return _get("/api/orders?status=OPEN")
    except Exception:
        logger.warning("Falling back to empty open orders list")
        return []


def create_purchase_order(
    supplier_id: str,
    part_id: str,
    quantity: int,
    approved_by: str
) -> dict:
    """Create a new PO record. Returns {po_id}."""
    try:
        return _post("/api/purchase-orders", {
            "supplier_id": supplier_id,
            "part_id": part_id,
            "quantity": quantity,
            "approved_by": approved_by,
        })
    except Exception:
        import uuid
        fallback_po_id = f"PO-OFFLINE-{uuid.uuid4().hex[:8].upper()}"
        logger.warning(f"PO creation offline, generated fallback: {fallback_po_id}")
        return {"po_id": fallback_po_id}


def update_supplier_assignment(part_id: str, new_supplier_id: str) -> dict:
    """Update the primary supplier for a part."""
    try:
        return _post(f"/api/parts/{part_id}/supplier", {
            "new_supplier_id": new_supplier_id,
        })
    except Exception:
        logger.warning(f"Supplier assignment update offline for part {part_id}")
        return {"status": "offline", "part_id": part_id, "new_supplier_id": new_supplier_id}


def send_po_confirmation(supplier_id: str, po_id: str) -> dict:
    """Send PO confirmation notification (simulated — writes to DB)."""
    try:
        return _post("/api/comms/notify", {
            "type": "po_confirmation",
            "supplier_id": supplier_id,
            "po_id": po_id,
        })
    except Exception:
        logger.warning(f"Notification send offline for PO {po_id}")
        return {"status": "offline", "notification": f"PO {po_id} confirmation pending"}
