"""
SupplyGuard AI — Unified Backend API
FastAPI server providing ALL endpoints for:
  - Agent tools (ERP, audit, approvals, PO, comms)
  - Frontend dashboards (suppliers, events, approvals, audit trail)
  - Data/ML layer (forecasts, anomalies)

Runs on port 3001 (primary backend) with CORS enabled for frontend.
Uses in-memory seed data that mirrors db/seed.sql.
When Supabase is connected, swap _STORE dicts with real DB queries.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, date
from contextlib import asynccontextmanager
import asyncio
import uuid
import json
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root so OPENAI_API_KEY / SUPABASE_* are available
load_dotenv(Path(__file__).parent.parent.parent / ".env")

logger = logging.getLogger("supplyguard")

# ── Persistent storage layer (in-memory + Supabase write-through) ────────────
from api.db import (  # noqa: E402
    AUDIT_LOG,
    PENDING_APPROVALS,
    PURCHASE_ORDERS,
    NOTIFICATIONS,
    insert_audit_entry,
    get_audit_trail as db_get_audit_trail,
    insert_approval,
    update_approval,
    get_approval,
    get_approval_by_run_id,
    list_approvals,
    insert_purchase_order,
    list_purchase_orders,
    insert_notification,
    list_notifications,
    mark_notification_read,
    load_from_supabase,
)

# ── Import intelligence modules ──────────────────────────────
from intelligence.anomaly import anomaly_score, anomaly_score_for_supplier
from intelligence.forecast import run_forecast, run_forecast_for_supplier
from intelligence.risk_score import compute_risk

# ── Auto-scan interval (seconds). 0 = disabled. ─────────
AUTO_SCAN_INTERVAL = int(os.getenv("AUTO_SCAN_INTERVAL", "60"))  # default: every 60s


# ── Background auto-scan task ────────────────────────────
async def _background_auto_scan():
    """Periodic background task: scan all suppliers for anomalies,
    auto-create events, and auto-trigger the pipeline."""
    await asyncio.sleep(5)  # wait for server to be fully ready
    while True:
        try:
            logger.info("[AUTO-SCAN] Running scheduled supplier scan...")
            result = _run_auto_scan()
            if result["events_created"] > 0:
                logger.info(f"[AUTO-SCAN] Detected {result['events_created']} disruptions, triggered {result['pipelines_triggered']} pipelines")
            else:
                logger.info("[AUTO-SCAN] No new disruptions detected.")
        except Exception as e:
            logger.error(f"[AUTO-SCAN] Error: {e}")
        await asyncio.sleep(AUTO_SCAN_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: hydrate in-memory stores from Supabase, then launch auto-scan."""
    # Hydrate persisted data (audit trail, approvals, POs, notifications)
    try:
        load_from_supabase()
    except Exception as e:
        logger.warning(f"[Supabase] Hydration error (non-fatal): {e}")

    task = None
    if AUTO_SCAN_INTERVAL > 0:
        logger.info(f"[AUTO-SCAN] Background scan enabled (every {AUTO_SCAN_INTERVAL}s)")
        task = asyncio.create_task(_background_auto_scan())
    yield
    if task:
        task.cancel()


app = FastAPI(title="SupplyGuard AI Backend", version="1.0.0", lifespan=lifespan)

# ── CORS — allow frontend on any localhost port ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════
# IN-MEMORY SEED DATA (mirrors db/seed.sql)
# ═══════════════════════════════════════════════

SUPPLIERS = {
    "a1000000-0000-0000-0000-000000000001": {
        "supplier_id": "a1000000-0000-0000-0000-000000000001",
        "supplier_name": "AlphaForge Industries",
        "country": "Mexico",
        "tier": 1,
        "financial_health": "RED",
        "lead_time_days": 12,
        "unit_cost": 85.50,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2025-06-15",
    },
    "a1000000-0000-0000-0000-000000000002": {
        "supplier_id": "a1000000-0000-0000-0000-000000000002",
        "supplier_name": "BetaSteel Corporation",
        "country": "USA",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 5,
        "unit_cost": 92.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2027-12-31",
    },
    "a1000000-0000-0000-0000-000000000003": {
        "supplier_id": "a1000000-0000-0000-0000-000000000003",
        "supplier_name": "GammaCast Manufacturing",
        "country": "Germany",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 7,
        "unit_cost": 110.00,
        "is_active": True,
        "quality_cert_type": "IATF 16949",
        "quality_cert_expiry": "2027-08-20",
    },
    "a1000000-0000-0000-0000-000000000004": {
        "supplier_id": "a1000000-0000-0000-0000-000000000004",
        "supplier_name": "DeltaSteel Corp",
        "country": "Brazil",
        "tier": 2,
        "financial_health": "YELLOW",
        "lead_time_days": 9,
        "unit_cost": 78.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2026-03-01",
    },
    "a1000000-0000-0000-0000-000000000005": {
        "supplier_id": "a1000000-0000-0000-0000-000000000005",
        "supplier_name": "EpsilonCast Systems",
        "country": "India",
        "tier": 2,
        "financial_health": "GREEN",
        "lead_time_days": 8,
        "unit_cost": 65.00,
        "is_active": True,
        "quality_cert_type": "ISO 14001",
        "quality_cert_expiry": "2027-05-10",
    },
    "a1000000-0000-0000-0000-000000000006": {
        "supplier_id": "a1000000-0000-0000-0000-000000000006",
        "supplier_name": "ZetaAlloy Solutions",
        "country": "USA",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 4,
        "unit_cost": 98.00,
        "is_active": True,
        "quality_cert_type": "IATF 16949",
        "quality_cert_expiry": "2028-01-15",
    },
    "a1000000-0000-0000-0000-000000000007": {
        "supplier_id": "a1000000-0000-0000-0000-000000000007",
        "supplier_name": "EtaPrecision Parts",
        "country": "Japan",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 6,
        "unit_cost": 120.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2027-11-30",
    },
    "a1000000-0000-0000-0000-000000000008": {
        "supplier_id": "a1000000-0000-0000-0000-000000000008",
        "supplier_name": "ThetaForge Ltd",
        "country": "China",
        "tier": 2,
        "financial_health": "YELLOW",
        "lead_time_days": 10,
        "unit_cost": 55.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2025-12-01",
    },
    "a1000000-0000-0000-0000-000000000009": {
        "supplier_id": "a1000000-0000-0000-0000-000000000009",
        "supplier_name": "IotaMetals Inc",
        "country": "South Korea",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 5,
        "unit_cost": 105.00,
        "is_active": True,
        "quality_cert_type": "IATF 16949",
        "quality_cert_expiry": "2027-09-15",
    },
    "a1000000-0000-0000-0000-000000000010": {
        "supplier_id": "a1000000-0000-0000-0000-000000000010",
        "supplier_name": "KappaComponents Global",
        "country": "Turkey",
        "tier": 3,
        "financial_health": "RED",
        "lead_time_days": 14,
        "unit_cost": 48.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2024-08-01",
    },
}

PARTS = [
    {"part_id": "b2000000-0000-0000-0000-000000000001", "part_number": "PT-ENG-001", "part_name": "Engine Block Assembly", "category": "Engine", "primary_supplier_id": "a1000000-0000-0000-0000-000000000001", "factory": "Columbus Plant", "min_order_qty": 50},
    {"part_id": "b2000000-0000-0000-0000-000000000002", "part_number": "PT-ENG-002", "part_name": "Cylinder Head", "category": "Engine", "primary_supplier_id": "a1000000-0000-0000-0000-000000000002", "factory": "Columbus Plant", "min_order_qty": 100},
    {"part_id": "b2000000-0000-0000-0000-000000000003", "part_number": "PT-TURBO-001", "part_name": "Turbocharger Assembly", "category": "Turbo", "primary_supplier_id": "a1000000-0000-0000-0000-000000000003", "factory": "Jamestown Plant", "min_order_qty": 75},
    {"part_id": "b2000000-0000-0000-0000-000000000004", "part_number": "PT-TURBO-002", "part_name": "Turbo Wastegate Actuator", "category": "Turbo", "primary_supplier_id": "a1000000-0000-0000-0000-000000000004", "factory": "Jamestown Plant", "min_order_qty": 200},
    {"part_id": "b2000000-0000-0000-0000-000000000005", "part_number": "PT-EXH-001", "part_name": "Exhaust Manifold", "category": "Exhaust", "primary_supplier_id": "a1000000-0000-0000-0000-000000000005", "factory": "Rocky Mount Plant", "min_order_qty": 150},
    {"part_id": "b2000000-0000-0000-0000-000000000006", "part_number": "PT-EXH-002", "part_name": "DPF Assembly", "category": "Exhaust", "primary_supplier_id": "a1000000-0000-0000-0000-000000000006", "factory": "Rocky Mount Plant", "min_order_qty": 80},
    {"part_id": "b2000000-0000-0000-0000-000000000007", "part_number": "PT-FUEL-001", "part_name": "Fuel Injector Set", "category": "Fuel System", "primary_supplier_id": "a1000000-0000-0000-0000-000000000007", "factory": "Columbus Plant", "min_order_qty": 120},
    {"part_id": "b2000000-0000-0000-0000-000000000008", "part_number": "PT-FUEL-002", "part_name": "High Pressure Fuel Pump", "category": "Fuel System", "primary_supplier_id": "a1000000-0000-0000-0000-000000000008", "factory": "Jamestown Plant", "min_order_qty": 60},
    {"part_id": "b2000000-0000-0000-0000-000000000009", "part_number": "PT-COOL-001", "part_name": "Radiator Assembly", "category": "Cooling", "primary_supplier_id": "a1000000-0000-0000-0000-000000000009", "factory": "Columbus Plant", "min_order_qty": 90},
    {"part_id": "b2000000-0000-0000-0000-000000000010", "part_number": "PT-COOL-002", "part_name": "Water Pump", "category": "Cooling", "primary_supplier_id": "a1000000-0000-0000-0000-000000000010", "factory": "Rocky Mount Plant", "min_order_qty": 200},
    {"part_id": "b2000000-0000-0000-0000-000000000011", "part_number": "PT-ENG-003", "part_name": "Crankshaft", "category": "Engine", "primary_supplier_id": "a1000000-0000-0000-0000-000000000002", "factory": "Columbus Plant", "min_order_qty": 40},
    {"part_id": "b2000000-0000-0000-0000-000000000012", "part_number": "PT-TURBO-003", "part_name": "Intercooler", "category": "Turbo", "primary_supplier_id": "a1000000-0000-0000-0000-000000000005", "factory": "Jamestown Plant", "min_order_qty": 100},
    {"part_id": "b2000000-0000-0000-0000-000000000013", "part_number": "PT-EXH-003", "part_name": "SCR Catalyst", "category": "Exhaust", "primary_supplier_id": "a1000000-0000-0000-0000-000000000003", "factory": "Rocky Mount Plant", "min_order_qty": 70},
    {"part_id": "b2000000-0000-0000-0000-000000000014", "part_number": "PT-FUEL-003", "part_name": "Fuel Filter Module", "category": "Fuel System", "primary_supplier_id": "a1000000-0000-0000-0000-000000000009", "factory": "Columbus Plant", "min_order_qty": 250},
    {"part_id": "b2000000-0000-0000-0000-000000000015", "part_number": "PT-COOL-003", "part_name": "Thermostat Housing Assembly", "category": "Cooling", "primary_supplier_id": "a1000000-0000-0000-0000-000000000006", "factory": "Jamestown Plant", "min_order_qty": 180},
]

AVL = [
    {"part_id": "b2000000-0000-0000-0000-000000000001", "supplier_id": "a1000000-0000-0000-0000-000000000001", "lead_time_days": 12, "unit_cost": 85.50, "quality_cert_expiry": "2025-06-15", "geographic_risk": 0.40, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000001", "supplier_id": "a1000000-0000-0000-0000-000000000002", "lead_time_days": 5, "unit_cost": 95.00, "quality_cert_expiry": "2027-12-31", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000001", "supplier_id": "a1000000-0000-0000-0000-000000000003", "lead_time_days": 7, "unit_cost": 112.00, "quality_cert_expiry": "2027-08-20", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000002", "supplier_id": "a1000000-0000-0000-0000-000000000002", "lead_time_days": 5, "unit_cost": 92.00, "quality_cert_expiry": "2027-12-31", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000002", "supplier_id": "a1000000-0000-0000-0000-000000000007", "lead_time_days": 6, "unit_cost": 125.00, "quality_cert_expiry": "2027-11-30", "geographic_risk": 0.15, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000003", "supplier_id": "a1000000-0000-0000-0000-000000000003", "lead_time_days": 7, "unit_cost": 110.00, "quality_cert_expiry": "2027-08-20", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000003", "supplier_id": "a1000000-0000-0000-0000-000000000009", "lead_time_days": 5, "unit_cost": 115.00, "quality_cert_expiry": "2027-09-15", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000003", "supplier_id": "a1000000-0000-0000-0000-000000000005", "lead_time_days": 8, "unit_cost": 70.00, "quality_cert_expiry": "2027-05-10", "geographic_risk": 0.55, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000004", "supplier_id": "a1000000-0000-0000-0000-000000000004", "lead_time_days": 9, "unit_cost": 78.00, "quality_cert_expiry": "2026-03-01", "geographic_risk": 0.45, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000004", "supplier_id": "a1000000-0000-0000-0000-000000000008", "lead_time_days": 10, "unit_cost": 58.00, "quality_cert_expiry": "2025-12-01", "geographic_risk": 0.60, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000005", "supplier_id": "a1000000-0000-0000-0000-000000000005", "lead_time_days": 8, "unit_cost": 65.00, "quality_cert_expiry": "2027-05-10", "geographic_risk": 0.55, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000005", "supplier_id": "a1000000-0000-0000-0000-000000000006", "lead_time_days": 4, "unit_cost": 102.00, "quality_cert_expiry": "2028-01-15", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000006", "supplier_id": "a1000000-0000-0000-0000-000000000006", "lead_time_days": 4, "unit_cost": 98.00, "quality_cert_expiry": "2028-01-15", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000006", "supplier_id": "a1000000-0000-0000-0000-000000000007", "lead_time_days": 6, "unit_cost": 130.00, "quality_cert_expiry": "2027-11-30", "geographic_risk": 0.15, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000007", "supplier_id": "a1000000-0000-0000-0000-000000000007", "lead_time_days": 6, "unit_cost": 120.00, "quality_cert_expiry": "2027-11-30", "geographic_risk": 0.15, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000007", "supplier_id": "a1000000-0000-0000-0000-000000000009", "lead_time_days": 5, "unit_cost": 108.00, "quality_cert_expiry": "2027-09-15", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000008", "supplier_id": "a1000000-0000-0000-0000-000000000008", "lead_time_days": 10, "unit_cost": 55.00, "quality_cert_expiry": "2025-12-01", "geographic_risk": 0.60, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000008", "supplier_id": "a1000000-0000-0000-0000-000000000010", "lead_time_days": 14, "unit_cost": 50.00, "quality_cert_expiry": "2024-08-01", "geographic_risk": 0.70, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000009", "supplier_id": "a1000000-0000-0000-0000-000000000009", "lead_time_days": 5, "unit_cost": 105.00, "quality_cert_expiry": "2027-09-15", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000009", "supplier_id": "a1000000-0000-0000-0000-000000000002", "lead_time_days": 5, "unit_cost": 99.00, "quality_cert_expiry": "2027-12-31", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000010", "supplier_id": "a1000000-0000-0000-0000-000000000010", "lead_time_days": 14, "unit_cost": 48.00, "quality_cert_expiry": "2024-08-01", "geographic_risk": 0.70, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000010", "supplier_id": "a1000000-0000-0000-0000-000000000005", "lead_time_days": 8, "unit_cost": 68.00, "quality_cert_expiry": "2027-05-10", "geographic_risk": 0.55, "is_approved": True},
]

EVENTS = [
    {"event_id": "c3000000-0000-0000-0000-000000000001", "supplier_id": "a1000000-0000-0000-0000-000000000001", "event_type": "DELIVERY_MISS", "delay_days": 9, "description": "Facility fire at AlphaForge Monterrey plant. 9-day delivery delay confirmed.", "severity": "CRITICAL"},
    {"event_id": "c3000000-0000-0000-0000-000000000002", "supplier_id": "a1000000-0000-0000-0000-000000000006", "event_type": "DELIVERY_MISS", "delay_days": 1, "description": "Minor 1-day delay within SLA buffer. No factory impact.", "severity": "LOW"},
    {"event_id": "c3000000-0000-0000-0000-000000000003", "supplier_id": "a1000000-0000-0000-0000-000000000004", "event_type": "FINANCIAL_FLAG", "delay_days": 4, "description": "DeltaSteel flagged for Q3 cash flow concerns. Delivery delay possible.", "severity": "HIGH"},
    {"event_id": "c3000000-0000-0000-0000-000000000004", "supplier_id": "a1000000-0000-0000-0000-000000000010", "event_type": "QUALITY_HOLD", "delay_days": 6, "description": "KappaComponents quality cert expired. Multiple defect reports received.", "severity": "CRITICAL"},
    {"event_id": "c3000000-0000-0000-0000-000000000005", "supplier_id": "a1000000-0000-0000-0000-000000000008", "event_type": "DELIVERY_MISS", "delay_days": 5, "description": "ThetaForge production line down for 5 days. Partial shipment only.", "severity": "HIGH"},
    {"event_id": "c3000000-0000-0000-0000-000000000006", "supplier_id": "a1000000-0000-0000-0000-000000000002", "event_type": "DELIVERY_MISS", "delay_days": 1, "description": "Weather delay, 1-day impact. Full recovery expected.", "severity": "LOW"},
    {"event_id": "c3000000-0000-0000-0000-000000000007", "supplier_id": "a1000000-0000-0000-0000-000000000003", "event_type": "QUALITY_HOLD", "delay_days": 3, "description": "GammaCast batch #4421 held for dimensional tolerance review.", "severity": "MEDIUM"},
    {"event_id": "c3000000-0000-0000-0000-000000000008", "supplier_id": "a1000000-0000-0000-0000-000000000005", "event_type": "DELIVERY_MISS", "delay_days": 3, "description": "Port congestion in Mumbai causing 3-day delay on EpsilonCast shipment.", "severity": "MEDIUM"},
    {"event_id": "c3000000-0000-0000-0000-000000000009", "supplier_id": "a1000000-0000-0000-0000-000000000007", "event_type": "DELIVERY_MISS", "delay_days": 1, "description": "Customs clearance delay, 1-day impact. Documentation resolved.", "severity": "LOW"},
    {"event_id": "c3000000-0000-0000-0000-000000000010", "supplier_id": "a1000000-0000-0000-0000-000000000009", "event_type": "FINANCIAL_FLAG", "delay_days": 2, "description": "IotaMetals credit rating downgrade flagged by monitoring service.", "severity": "MEDIUM"},
]

# AUDIT_LOG, PENDING_APPROVALS, PURCHASE_ORDERS, NOTIFICATIONS
# are imported from api.db — do not re-declare them here.


# ═══════════════════════════════════════════════
# HEALTH & ROOT
# ═══════════════════════════════════════════════

@app.get("/")
def root():
    return {"message": "SupplyGuard AI Backend API running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "SupplyGuard AI Backend", "suppliers_loaded": len(SUPPLIERS), "events_loaded": len(EVENTS)}


# ═══════════════════════════════════════════════
# SUPPLIERS — used by agents/tools/erp_tools.py
# ═══════════════════════════════════════════════

@app.get("/api/suppliers")
def list_suppliers():
    """List all suppliers."""
    return list(SUPPLIERS.values())

@app.get("/api/suppliers/{supplier_id}")
def get_supplier(supplier_id: str):
    """GET /api/suppliers/:id — full supplier profile."""
    s = SUPPLIERS.get(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    return s

@app.get("/api/suppliers/{supplier_id}/certs")
def get_supplier_certs(supplier_id: str):
    """GET /api/suppliers/:id/certs — quality cert info."""
    s = SUPPLIERS.get(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    today = date.today().isoformat()
    expiry = s.get("quality_cert_expiry", "2025-01-01")
    return {
        "supplier_id": supplier_id,
        "quality_cert_type": s.get("quality_cert_type", "ISO 9001"),
        "quality_cert_expiry": expiry,
        "is_approved": expiry >= today,
    }


# ═══════════════════════════════════════════════
# PARTS — used by agents
# ═══════════════════════════════════════════════

@app.get("/api/parts")
def list_parts(supplier_id: Optional[str] = Query(None)):
    """GET /api/parts?supplier_id=:id — filter parts by primary supplier."""
    if supplier_id:
        return [p for p in PARTS if p["primary_supplier_id"] == supplier_id]
    return PARTS


# ═══════════════════════════════════════════════
# AVL (Approved Vendor List) — used by Decision Agent
# ═══════════════════════════════════════════════

@app.get("/api/avl/{part_id}")
def get_avl(part_id: str):
    """GET /api/avl/:part_id — all approved vendors for a part."""
    entries = [a for a in AVL if a["part_id"] == part_id]
    # Enrich with supplier name and cert_valid flag
    enriched = []
    for a in entries:
        s = SUPPLIERS.get(a["supplier_id"], {})
        today = date.today().isoformat()
        cert_valid = (a.get("quality_cert_expiry", "2025-01-01") >= today)
        enriched.append({
            **a,
            "supplier_name": s.get("supplier_name", "Unknown"),
            "cert_valid": cert_valid,
        })
    return enriched


# ═══════════════════════════════════════════════
# EVENTS — used by agents/run.py and frontend
# ═══════════════════════════════════════════════

@app.get("/api/events")
def list_events():
    """GET /api/events — all supplier events (for pipeline testing)."""
    return EVENTS

@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    """GET /api/events/:id — single event."""
    for e in EVENTS:
        if e["event_id"] == event_id:
            return e
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


# ═══════════════════════════════════════════════
# AUDIT LOG — used by all agents & frontend stepper
# ═══════════════════════════════════════════════

class AuditLogEntry(BaseModel):
    run_id: str
    agent_name: str
    inputs: dict = {}
    outputs: dict = {}
    confidence: float = 0.0
    rationale: str = ""
    hitl_actor: Optional[str] = None
    timestamp: Optional[str] = None

@app.post("/api/audit")
def create_audit_entry(entry: AuditLogEntry):
    """POST /api/audit — immutably log an agent decision (persists to Supabase)."""
    record = {
        "run_id": entry.run_id,
        "agent_name": entry.agent_name,
        "inputs": entry.inputs,
        "outputs": entry.outputs,
        "confidence": entry.confidence,
        "rationale": entry.rationale,
        "hitl_actor": entry.hitl_actor,
        "timestamp": entry.timestamp or datetime.now(timezone.utc).isoformat(),
    }
    saved = insert_audit_entry(record)
    return {"entry_id": saved["entry_id"]}

@app.get("/api/audit/{run_id}")
def get_audit_trail_endpoint(run_id: str):
    """GET /api/audit/:run_id — ordered audit trail for a pipeline run."""
    return db_get_audit_trail(run_id)

@app.delete("/api/audit/{entry_id}")
def delete_audit_entry(entry_id: str):
    """DELETE /api/audit/:id — FORBIDDEN (immutability)."""
    raise HTTPException(status_code=403, detail="audit_log is immutable — DELETE is forbidden")


# ═══════════════════════════════════════════════
# APPROVALS — HITL workflow
# ═══════════════════════════════════════════════

class ApprovalRequest(BaseModel):
    run_id: str
    state_json: dict = {}
    summary: str = ""
    recommended_supplier_id: Optional[str] = None

class ApprovalDecision(BaseModel):
    decision: str  # "approved" | "rejected"
    note: str = ""
    director_id: str = ""

@app.post("/api/approvals")
def create_approval(req: ApprovalRequest):
    """POST /api/approvals — create pending approval for Director (persists to Supabase)."""
    approval_id = str(uuid.uuid4())
    record = {
        "approval_id": approval_id,
        "run_id": req.run_id,
        "state_json": req.state_json,
        "summary": req.summary,
        "recommended_supplier_id": req.recommended_supplier_id,
        "status": "PENDING",
        "decided_by": None,
        "decision_note": None,
        "decided_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    insert_approval(record)

    insert_notification({
        "notification_id": str(uuid.uuid4()),
        "recipient_role": "director",
        "notification_type": "approval_required",
        "title": f"Approval Required: {req.summary[:80]}",
        "body": req.summary,
        "metadata": {"approval_id": approval_id, "run_id": req.run_id},
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"approval_id": approval_id}

@app.get("/api/approvals")
def list_approvals_endpoint(status: Optional[str] = Query(None)):
    """GET /api/approvals?status=PENDING — list approvals, optionally filtered."""
    return list_approvals(status)

@app.get("/api/approvals/state/{run_id}")
def get_approval_state(run_id: str):
    """GET /api/approvals/state/:run_id — load saved AgentState for HITL resume."""
    a = get_approval_by_run_id(run_id)
    if not a:
        raise HTTPException(status_code=404, detail=f"No approval found for run_id={run_id}")
    return {"run_id": run_id, "state_json": a.get("state_json", {})}

@app.get("/api/approvals/{approval_id}")
def get_approval_endpoint(approval_id: str):
    """GET /api/approvals/:id"""
    a = get_approval(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    return a

@app.patch("/api/approvals/{approval_id}/decide")
def decide_approval(approval_id: str, body: ApprovalDecision):
    """PATCH /api/approvals/:id/decide — Director approves/rejects.

    Flow:
      1. Validate the approval exists and is still PENDING.
      2. Persist the decision to Supabase via update_approval().
      3. POST to localhost:8002/resume — this loads the saved AgentState
         from the approval record and runs Agent 5 (Executor).
      4. Return the resume result.
    """
    a = get_approval(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    if a["status"] != "PENDING":
        raise HTTPException(status_code=400, detail=f"Approval already decided: {a['status']}")

    decided_at = datetime.now(timezone.utc).isoformat()
    decision_upper = body.decision.upper()

    # Persist decision to in-memory + Supabase
    update_approval(approval_id, {
        "status": decision_upper,
        "decided_by": body.director_id,
        "decision_note": body.note,
        "decided_at": decided_at,
    })

    # Notify the director's decision as a new notification
    action_label = "approved" if decision_upper == "APPROVED" else "rejected"
    insert_notification({
        "notification_id": str(uuid.uuid4()),
        "recipient_role": "procurement",
        "notification_type": "decision_made",
        "title": f"[DECISION] Pipeline {a['run_id']} {action_label} by {body.director_id or 'Director'}",
        "body": body.note or f"Director {action_label} the recommended action.",
        "metadata": {"approval_id": approval_id, "run_id": a["run_id"]},
        "is_read": False,
        "created_at": decided_at,
    })

    # Call the Agent Resume API — triggers Agent 5 on approval
    resume_url = os.getenv("RESUME_API_URL", "http://localhost:8002")
    try:
        import httpx
        resp = httpx.post(
            f"{resume_url}/resume",
            json={
                "run_id": a["run_id"],
                "decision": body.decision.lower(),
                "hitl_actor": body.director_id,
            },
            timeout=60,
        )
        resume_result = resp.json()
    except Exception as e:
        resume_result = {"status": "resume_call_failed", "error": str(e)}

    return {
        "approval_id": approval_id,
        "status": decision_upper,
        "resume_result": resume_result,
    }


# ═══════════════════════════════════════════════
# PURCHASE ORDERS — used by Executor Agent
# ═══════════════════════════════════════════════

class PORequest(BaseModel):
    supplier_id: str
    part_id: str
    quantity: int
    approved_by: str

@app.post("/api/purchase-orders")
def create_purchase_order(req: PORequest):
    """POST /api/purchase-orders — create a new PO (persists to Supabase)."""
    po_id = f"PO-{uuid.uuid4().hex[:8].upper()}"
    supplier = SUPPLIERS.get(req.supplier_id, {})
    record = {
        "po_id": po_id,
        "supplier_id": req.supplier_id,
        "supplier_name": supplier.get("supplier_name", ""),
        "part_id": req.part_id,
        "quantity": req.quantity,
        "approved_by": req.approved_by,
        "status": "CREATED",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    insert_purchase_order(record)
    return {"po_id": po_id}

@app.get("/api/purchase-orders")
def list_purchase_orders_endpoint():
    """GET /api/purchase-orders — list all POs."""
    return list_purchase_orders()


# ═══════════════════════════════════════════════
# PARTS SUPPLIER UPDATE — used by Executor Agent
# ═══════════════════════════════════════════════

class SupplierUpdateRequest(BaseModel):
    new_supplier_id: str

@app.post("/api/parts/{part_id}/supplier")
def update_part_supplier(part_id: str, body: SupplierUpdateRequest):
    """POST /api/parts/:part_id/supplier — update primary supplier assignment."""
    for p in PARTS:
        if p["part_id"] == part_id:
            old_supplier = p["primary_supplier_id"]
            p["primary_supplier_id"] = body.new_supplier_id
            return {"part_id": part_id, "old_supplier_id": old_supplier, "new_supplier_id": body.new_supplier_id}
    raise HTTPException(status_code=404, detail=f"Part {part_id} not found")


# ═══════════════════════════════════════════════
# ORDERS — used by agents
# ═══════════════════════════════════════════════

@app.get("/api/orders")
def list_orders(status: Optional[str] = Query(None)):
    """GET /api/orders?status=OPEN — (demo: returns empty or a few)."""
    # For demo purposes, generate some synthetic open orders
    demo_orders = [
        {"order_id": "ORD-001", "part_id": "b2000000-0000-0000-0000-000000000001", "factory": "Columbus Plant", "quantity": 50, "status": "OPEN", "due_date": "2026-03-10"},
        {"order_id": "ORD-002", "part_id": "b2000000-0000-0000-0000-000000000003", "factory": "Jamestown Plant", "quantity": 75, "status": "OPEN", "due_date": "2026-03-12"},
        {"order_id": "ORD-003", "part_id": "b2000000-0000-0000-0000-000000000005", "factory": "Rocky Mount Plant", "quantity": 150, "status": "OPEN", "due_date": "2026-03-08"},
    ]
    if status:
        return [o for o in demo_orders if o["status"] == status.upper()]
    return demo_orders


# ═══════════════════════════════════════════════
# COMMS — Notification system (simulated Teams)
# ═══════════════════════════════════════════════

class NotificationRequest(BaseModel):
    type: str = "general"
    supplier_id: Optional[str] = None
    po_id: Optional[str] = None
    run_id: Optional[str] = None
    recipient_role: str = "procurement"
    message: str = ""

@app.post("/api/comms/notify")
def send_notification(req: NotificationRequest):
    """POST /api/comms/notify — simulated Teams notification (persists to Supabase)."""
    notification_id = str(uuid.uuid4())
    record = {
        "notification_id": notification_id,
        "recipient_role": req.recipient_role,
        "notification_type": req.type,
        "title": f"[{req.type.upper()}] {req.message[:60] or 'Notification'}",
        "body": req.message or f"PO {req.po_id} for supplier {req.supplier_id}",
        "metadata": {"supplier_id": req.supplier_id, "po_id": req.po_id, "run_id": req.run_id},
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    insert_notification(record)
    return {"notification_id": notification_id, "status": "sent"}

@app.get("/api/notifications")
def list_notifications_endpoint(role: Optional[str] = Query(None), unread_only: bool = False):
    """GET /api/notifications?role=director&unread_only=true"""
    return list_notifications(role=role, unread_only=unread_only)

@app.patch("/api/notifications/{notification_id}/read")
def mark_notification_read_endpoint(notification_id: str):
    """PATCH /api/notifications/:id/read — mark as read."""
    found = mark_notification_read(notification_id)
    if not found:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok"}


# ═══════════════════════════════════════════════
# DATA/ML ENDPOINTS — Per-supplier forecasts & anomalies
# (Wraps intelligence/ modules with per-supplier support)
# ═══════════════════════════════════════════════

@app.get("/api/forecasts/{supplier_id}")
def get_forecast_for_supplier(supplier_id: str):
    """GET /api/forecasts/:supplier_id — P5-style per-supplier forecast."""
    try:
        result = run_forecast_for_supplier(supplier_id)
        return result
    except Exception as e:
        # Fallback with safe defaults
        return {
            "supplier_id": supplier_id,
            "forecast_date": date.today().isoformat(),
            "predicted_delay": 3.0,
            "lower_ci": 1.5,
            "upper_ci": 5.0,
            "model_aic": 0.0,
        }

@app.get("/api/anomalies/{supplier_id}")
def get_anomaly_for_supplier(supplier_id: str):
    """GET /api/anomalies/:supplier_id — P5-style per-supplier anomaly."""
    try:
        result = anomaly_score_for_supplier(supplier_id)
        return result
    except Exception as e:
        return {
            "supplier_id": supplier_id,
            "date": date.today().isoformat(),
            "anomaly_flag": False,
            "votes": 0,
            "zscore_val": 0.0,
            "mad_val": 0.0,
            "percentile_val": 0.5,
        }


# ═══════════════════════════════════════════════
# LEGACY ENDPOINTS (from original Backend branch)
# ═══════════════════════════════════════════════

@app.get("/risk/{supplier_id}")
def get_risk(supplier_id: str):
    """Legacy: overall risk score."""
    ratio = anomaly_score()
    s = SUPPLIERS.get(supplier_id, {})
    financial = s.get("financial_health", "YELLOW")
    risk, tier = compute_risk(financial_status=financial, anomaly_ratio=ratio, forecast_trend="UP")
    return {"supplier_id": supplier_id, "risk_score": risk, "tier": tier}

@app.get("/anomaly")
def get_anomaly():
    return {"anomaly_ratio": anomaly_score()}

@app.get("/forecast")
def get_forecast_all():
    forecast = run_forecast()
    return forecast.to_dict(orient="records")

@app.get("/supplier/{supplier_id}")
def analyze_supplier(supplier_id: str):
    """Legacy: full supplier analysis."""
    ratio = anomaly_score()
    forecast = run_forecast()
    s = SUPPLIERS.get(supplier_id, {})
    financial = s.get("financial_health", "YELLOW")
    risk, tier = compute_risk(financial_status=financial, anomaly_ratio=ratio, forecast_trend="UP")
    return {
        "supplier_id": supplier_id,
        "supplier_name": s.get("supplier_name", "Unknown"),
        "risk_score": risk,
        "tier": tier,
        "anomaly_ratio": ratio,
        "forecast_preview": forecast.head(5).to_dict(orient="records"),
    }


# ═══════════════════════════════════════════════
# DASHBOARD STATS — used by frontend
# ═══════════════════════════════════════════════

@app.get("/api/dashboard/stats")
def dashboard_stats():
    """Aggregate dashboard statistics for frontend."""
    total_events = len(EVENTS)
    critical_events = len([e for e in EVENTS if e["severity"] == "CRITICAL"])
    pending = len([a for a in PENDING_APPROVALS.values() if a["status"] == "PENDING"])
    approved = len([a for a in PENDING_APPROVALS.values() if a["status"] == "APPROVED"])
    total_pos = len(PURCHASE_ORDERS)
    active_suppliers = len([s for s in SUPPLIERS.values() if s["is_active"]])
    red_suppliers = len([s for s in SUPPLIERS.values() if s["financial_health"] == "RED"])

    return {
        "total_events": total_events,
        "critical_events": critical_events,
        "pending_approvals": pending,
        "approved_count": approved,
        "total_purchase_orders": total_pos,
        "active_suppliers": active_suppliers,
        "red_suppliers": red_suppliers,
        "total_audit_entries": len(AUDIT_LOG),
        "unread_notifications": len([n for n in NOTIFICATIONS if not n.get("is_read", False)]),
    }

# ═══════════════════════════════════════════════
# AUTO-SCAN — Automatic disruption detection
# ═══════════════════════════════════════════════

# Track which supplier+type combos we've already auto-flagged (avoid duplicates)
_AUTO_SCAN_SEEN: set[str] = set()


def _run_auto_scan() -> dict:
    """Scan all suppliers using anomaly detection + forecasting.
    Auto-creates events for flagged suppliers and triggers the pipeline.
    Returns a summary of findings."""
    findings = []
    events_created = 0
    pipelines_triggered = 0

    for sid, supplier in SUPPLIERS.items():
        if not supplier["is_active"]:
            continue

        # 1. Run anomaly detection
        anomaly = anomaly_score_for_supplier(sid)
        anomaly_flagged = anomaly.get("anomaly_flag", False)
        anomaly_votes = anomaly.get("votes", 0)

        # 2. Run forecast
        forecast = run_forecast_for_supplier(sid)
        predicted_delay = forecast.get("predicted_delay", 0)
        lower_ci = forecast.get("lower_ci", 0)
        upper_ci = forecast.get("upper_ci", 0)

        # Derive trend: compare predicted to historical mean
        # If predicted > upper CI of a "normal" range, it's worsening
        forecast_trend = "STABLE"
        if predicted_delay > 5:
            forecast_trend = "WORSENING"
        elif predicted_delay < 2:
            forecast_trend = "IMPROVING"

        # 3. Check cert expiry
        cert_expiry = supplier.get("quality_cert_expiry", "2099-12-31")
        cert_expired = cert_expiry < date.today().isoformat()

        # 4. Check financial health
        financial_red = supplier.get("financial_health") == "RED"

        # ── Decision: should we flag this supplier? ──────────
        should_flag = False
        event_type = "DELIVERY_MISS"
        severity = "MEDIUM"
        reason = ""

        if anomaly_flagged and anomaly_votes >= 2:
            should_flag = True
            event_type = "DELIVERY_MISS"
            severity = "HIGH" if anomaly_votes >= 3 else "MEDIUM"
            reason = f"Anomaly ensemble flagged ({anomaly_votes}/3 votes). Predicted delay: {predicted_delay:.1f} days."

        if forecast_trend == "WORSENING" and predicted_delay > 5:
            should_flag = True
            event_type = "DELIVERY_MISS"
            severity = "HIGH" if predicted_delay > 7 else "MEDIUM"
            reason = f"Forecast trend WORSENING — predicted {predicted_delay:.1f}-day delay (CI: {lower_ci:.1f}–{upper_ci:.1f})."

        if cert_expired:
            should_flag = True
            event_type = "QUALITY_HOLD"
            severity = "CRITICAL" if financial_red else "HIGH"
            reason = f"Quality cert expired ({cert_expiry}). {'Financial health RED.' if financial_red else ''}"

        if financial_red and not cert_expired:
            should_flag = True
            event_type = "FINANCIAL_FLAG"
            severity = "HIGH"
            reason = f"Financial health RED flagged by monitoring."

        if not should_flag:
            findings.append({
                "supplier_id": sid,
                "supplier_name": supplier["supplier_name"],
                "status": "OK",
                "anomaly_votes": anomaly_votes,
                "predicted_delay": round(predicted_delay, 2),
                "event_created": False,
            })
            continue

        # Deduplicate: don't create same event type for same supplier twice
        dedup_key = f"{sid}:{event_type}"
        if dedup_key in _AUTO_SCAN_SEEN:
            findings.append({
                "supplier_id": sid,
                "supplier_name": supplier["supplier_name"],
                "status": "ALREADY_FLAGGED",
                "anomaly_votes": anomaly_votes,
                "predicted_delay": round(predicted_delay, 2),
                "event_created": False,
            })
            continue

        _AUTO_SCAN_SEEN.add(dedup_key)

        # ── Auto-create event ────────────────────────────────
        event_id = str(uuid.uuid4())
        new_event = {
            "event_id": event_id,
            "supplier_id": sid,
            "event_type": event_type,
            "delay_days": max(1, int(round(predicted_delay))),
            "description": f"[AUTO-DETECTED] {reason}",
            "severity": severity,
            "auto_detected": True,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
        EVENTS.append(new_event)
        events_created += 1

        # ── Auto-trigger pipeline ────────────────────────────
        pipeline_result = None
        try:
            import sys
            from pathlib import Path
            project_root = str(Path(__file__).resolve().parent.parent.parent)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from agents.orchestrator import run_pipeline
            state = run_pipeline(new_event)
            pipeline_result = {
                "run_id": state.run_id,
                "action": state.decision.action if state.decision else None,
                "composite_score": state.decision.composite_score if state.decision else None,
                "hitl_required": state.decision.hitl_required if state.decision else None,
                "paused_for_hitl": state.paused_for_hitl,
                "po_id": state.executor.po_id if state.executor else None,
            }
            pipelines_triggered += 1
        except Exception as e:
            pipeline_result = {"error": str(e)}

        findings.append({
            "supplier_id": sid,
            "supplier_name": supplier["supplier_name"],
            "status": "FLAGGED",
            "reason": reason,
            "anomaly_votes": anomaly_votes,
            "predicted_delay": round(predicted_delay, 2),
            "severity": severity,
            "event_type": event_type,
            "event_id": event_id,
            "event_created": True,
            "pipeline_result": pipeline_result,
        })

    return {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "suppliers_scanned": len([s for s in SUPPLIERS.values() if s["is_active"]]),
        "events_created": events_created,
        "pipelines_triggered": pipelines_triggered,
        "findings": findings,
    }


@app.post("/api/auto-scan")
def trigger_auto_scan():
    """POST /api/auto-scan — Manually trigger the AI disruption scanner.
    Scans all active suppliers using anomaly detection + forecasting,
    auto-creates events for flagged suppliers, and triggers the pipeline."""
    return _run_auto_scan()


@app.post("/api/auto-scan/reset")
def reset_auto_scan():
    """Reset the dedup cache so the scanner can re-flag suppliers."""
    _AUTO_SCAN_SEEN.clear()
    return {"status": "ok", "message": "Auto-scan dedup cache cleared"}


class PipelineRunRequest(BaseModel):
    event_id: str

@app.post("/api/pipeline/run")
def trigger_pipeline(req: PipelineRunRequest):
    """POST /api/pipeline/run — trigger the agent pipeline for an event.
    Calls the agent layer and returns the pipeline result."""
    # Find the event
    event = None
    for e in EVENTS:
        if e["event_id"] == req.event_id:
            event = e
            break
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {req.event_id} not found")

    try:
        import sys
        from pathlib import Path
        # Add project root to path so we can import agents
        project_root = str(Path(__file__).resolve().parent.parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from agents.orchestrator import run_pipeline
        state = run_pipeline(event)
        return {
            "status": "completed",
            "run_id": state.run_id,
            "composite_score": state.decision.composite_score if state.decision else None,
            "action": state.decision.action if state.decision else None,
            "hitl_required": state.decision.hitl_required if state.decision else None,
            "paused_for_hitl": state.paused_for_hitl,
            "po_id": state.executor.po_id if state.executor else None,
            "audit_entries": len(state.audit_entries),
            "error": state.error,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/api/events")
def create_event(event: dict):
    """POST /api/events — create a new supplier event (for UI demo)."""
    event_id = event.get("event_id") or str(uuid.uuid4())
    event["event_id"] = event_id
    # Ensure required fields
    if "supplier_id" not in event or "event_type" not in event:
        raise HTTPException(status_code=400, detail="Missing supplier_id or event_type")
    if "severity" not in event:
        event["severity"] = "MEDIUM"
    if "delay_days" not in event:
        event["delay_days"] = 0
    if "description" not in event:
        event["description"] = f"{event['event_type']} event for supplier {event['supplier_id']}"
    EVENTS.append(event)
    return event

@app.get("/api/pipeline/runs")
def list_pipeline_runs():
    """Get all distinct pipeline runs from audit log (memory + Supabase-hydrated)."""
    runs: dict = {}
    for entry in AUDIT_LOG:
        rid = entry.get("run_id", "")
        if not rid:
            continue
        ts = entry.get("timestamp", "")
        if rid not in runs:
            runs[rid] = {
                "run_id": rid,
                "agents_completed": [],
                "started_at": ts,
                "last_update": ts,
                "supplier_id": None,
                "supplier_name": None,
            }
        agent_name = entry.get("agent_name", "")
        # Dedup: only add each agent name once per run
        if agent_name and agent_name not in runs[rid]["agents_completed"]:
            runs[rid]["agents_completed"].append(agent_name)
        if ts and ts > runs[rid]["last_update"]:
            runs[rid]["last_update"] = ts
        # Extract supplier info from intake_agent outputs
        if entry.get("agent_name") == "intake_agent" and not runs[rid]["supplier_name"]:
            outputs = entry.get("outputs", {}) or {}
            profile = outputs.get("supplier_profile", {}) or {}
            runs[rid]["supplier_id"] = (
                profile.get("supplier_id")
                or outputs.get("supplier_id")
                or entry.get("inputs", {}).get("supplier_id")
            )
            runs[rid]["supplier_name"] = (
                profile.get("supplier_name")
                or entry.get("inputs", {}).get("supplier_id")
            )
    result = list(runs.values())
    result.sort(key=lambda x: x.get("last_update", ""), reverse=True)
    return result


@app.post("/api/reset")
def reset_in_memory_stores():
    """Wipe all in-memory stores and reload from Supabase (or start clean).

    Useful in development to clear duplicate/stale data without restarting the server.
    WARNING: This clears all in-memory approvals, audit entries, POs, and notifications.
    """
    AUDIT_LOG.clear()
    PENDING_APPROVALS.clear()
    PURCHASE_ORDERS.clear()
    NOTIFICATIONS.clear()

    # Re-hydrate from Supabase if connected
    load_from_supabase()

    return {
        "status": "ok",
        "message": "In-memory stores cleared and reloaded from Supabase.",
        "counts": {
            "audit_log": len(AUDIT_LOG),
            "approvals": len(PENDING_APPROVALS),
            "purchase_orders": len(PURCHASE_ORDERS),
            "notifications": len(NOTIFICATIONS),
        },
    }


@app.get("/api/debug/supabase")
def debug_supabase():
    """Check Supabase connectivity and row counts in every key table.

    Open http://localhost:3001/api/debug/supabase in your browser to diagnose
    whether the backend is actually writing to the database.
    """
    from api.supabase_client import get_supabase  # type: ignore
    sb = get_supabase()

    if sb is None:
        return {
            "connected": False,
            "reason": "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set / supabase package missing",
            "in_memory": {
                "audit_log": len(AUDIT_LOG),
                "approvals": len(PENDING_APPROVALS),
                "purchase_orders": len(PURCHASE_ORDERS),
                "notifications": len(NOTIFICATIONS),
            },
        }

    counts = {}
    errors = {}
    for table in ["pending_approvals", "audit_log", "purchase_orders", "notifications",
                  "pipeline_runs", "suppliers", "supplier_events"]:
        try:
            result = sb.table(table).select("*", count="exact", head=True).execute()
            counts[table] = result.count
        except Exception as e:
            errors[table] = str(e)

    # Also fetch the 3 most recent pending_approvals so you can verify content
    recent_approvals = []
    try:
        rows = (
            sb.table("pending_approvals")
            .select("approval_id, run_id, status, decided_at, created_at")
            .order("created_at", desc=True)
            .limit(3)
            .execute()
            .data or []
        )
        recent_approvals = rows
    except Exception as e:
        errors["recent_approvals_fetch"] = str(e)

    return {
        "connected": True,
        "supabase_row_counts": counts,
        "in_memory": {
            "audit_log": len(AUDIT_LOG),
            "approvals": len(PENDING_APPROVALS),
            "purchase_orders": len(PURCHASE_ORDERS),
            "notifications": len(NOTIFICATIONS),
        },
        "recent_pending_approvals": recent_approvals,
        "errors": errors,
    }
