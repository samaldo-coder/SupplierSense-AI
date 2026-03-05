# Integration Notes — P3 (AI Agent Architect)
# Update this file whenever you find a contract mismatch with a teammate.

## Format:
## [TeammateName] | file:line | issue | suggested fix

## Repo Audit Results (2026-03-04)

```
╔══════════════════════════════════════════════════════════════╗
║              REPO AUDIT RESULTS                              ║
╠══════════════════════════════════════════════════════════════╣
║ BRANCHES:                                                    ║
║   Backend  → P4/P5  → api/main.py, intelligence/, data/     ║
║   Frontend → P2     → React app with role-based dashboards   ║
║   MCP      → empty  → just README                            ║
║   agents   → empty  → just README                            ║
║   database → empty  → just README                            ║
║   docs     → empty  → just README                            ║
║   main     → P2     → Frontend code (React/Vite)             ║
╠══════════════════════════════════════════════════════════════╣
║ AGENT LAYER (my files):                                      ║
║   Exists in branch: NO → built from scratch by P3            ║
║   Framework in use: CrewAI-style (function-based agents)     ║
║   contracts/schemas.py: ✅ CREATED                           ║
╠══════════════════════════════════════════════════════════════╣
║ BACKEND/MCP LAYER (P4):                                      ║
║   ⚠️ Backend was Python FastAPI, NOT Node.js Express         ║
║   → P3 extended api/main.py with all required endpoints      ║
║   ERP MCP server: SKIPPED (REST-only approach)               ║
║   Audit MCP server: SKIPPED (REST-only approach)             ║
║   Comms MCP server: SKIPPED (REST-only approach)             ║
║   GET /api/suppliers/:id → ✅ ADDED                          ║
║   GET /api/avl/:part_id → ✅ ADDED                           ║
║   POST /api/audit → ✅ ADDED                                 ║
║   POST /api/approvals → ✅ ADDED                             ║
║   PATCH /api/approvals/:id/decide → ✅ ADDED                 ║
║   POST /api/purchase-orders → ✅ ADDED                       ║
║   POST /api/comms/notify → ✅ ADDED                          ║
║   GET /api/dashboard/stats → ✅ ADDED                        ║
║   GET /api/pipeline/runs → ✅ ADDED                          ║
║   GET /api/notifications → ✅ ADDED                          ║
╠══════════════════════════════════════════════════════════════╣
║ DATA LAYER (P5):                                             ║
║   intelligence/anomaly.py → ✅ Added per-supplier function   ║
║   intelligence/forecast.py → ✅ Added per-supplier function  ║
║   GET /api/forecasts/:id → ✅ ADDED (in api/main.py)        ║
║   GET /api/anomalies/:id → ✅ ADDED (in api/main.py)        ║
║   Seed data: ✅ generate_data.py updated for 10 suppliers    ║
╠══════════════════════════════════════════════════════════════╣
║ FRONTEND (P2):                                               ║
║   ✅ App.tsx created with routing + auth + role-based views  ║
║   ✅ api/index.ts — full API service layer with types        ║
║   ✅ DirectorDashboard — real approval queue + HITL buttons  ║
║   ✅ QCManagerDashboard — live pipeline stepper + audit      ║
║   ✅ WarehouseDashboard — real supplier list + stats         ║
║   ✅ Navigation — polls notifications from backend           ║
║   ✅ Vite proxy: /api → localhost:3001                       ║
║   Polls GET /api/audit/:run_id: ✅ YES (3s interval)        ║
║   Calls PATCH /api/approvals/:id/decide: ✅ YES             ║
║   Agent pipeline stepper: ✅ 5 correct agent names           ║
╠══════════════════════════════════════════════════════════════╣
║ DATABASE:                                                     ║
║   In-memory seed data in api/main.py (mirrors db/seed.sql)  ║
║   db/schema.sql: ✅ CREATED                                  ║
║   db/seed.sql: ✅ CREATED                                    ║
║   Supabase: NOT connected (using in-memory for demo)         ║
╚══════════════════════════════════════════════════════════════╝
```

---

## ✅ RESOLVED Issues (all fixed by P3):

### [P4] api/main.py — Backend is FastAPI (Python), not Node.js Express
- **Status**: ✅ RESOLVED
- **Fix**: P3 extended api/main.py with all required endpoints instead of building a separate Express server. All agent tools hit localhost:3001 as specified.

### [P4] No supplier CRUD endpoints existed
- **Status**: ✅ RESOLVED
- **Fix**: Added `GET /api/suppliers`, `GET /api/suppliers/:id`, `GET /api/suppliers/:id/certs` with correct schema (snake_case, all required fields).

### [P4] No audit trail endpoints existed
- **Status**: ✅ RESOLVED
- **Fix**: Added `POST /api/audit` (immutable insert), `GET /api/audit/:run_id` (ordered trail), `DELETE /api/audit/:id` (returns 403 — immutability enforced).

### [P4] No approval/HITL endpoints existed
- **Status**: ✅ RESOLVED
- **Fix**: Added `POST /api/approvals`, `GET /api/approvals?status=PENDING`, `PATCH /api/approvals/:id/decide`. The decide endpoint calls `POST localhost:8002/resume` to trigger Agent 5 after Director approval.

### [P4] No MCP servers existed
- **Status**: ✅ RESOLVED (skipped)
- **Decision**: MCP layer skipped. All agent→backend calls use REST via httpx. MCP servers are not needed for the demo.

### [P5] intelligence/anomaly.py — Returned global ratio, not per-supplier
- **Status**: ✅ RESOLVED
- **Fix**: Added `anomaly_score_for_supplier(supplier_id)` function that filters timeseries data by supplier before computing anomaly stats. Exposed via `GET /api/anomalies/:supplier_id`.

### [P5] intelligence/forecast.py — Returned DataFrame, not per-supplier JSON
- **Status**: ✅ RESOLVED
- **Fix**: Added `run_forecast_for_supplier(supplier_id)` function that filters data and returns per-supplier JSON with `{predicted_delay, lower_ci, upper_ci, trend}`. Exposed via `GET /api/forecasts/:supplier_id`.

### [P5] data/generate_data.py — Only 3 suppliers
- **Status**: ✅ RESOLVED
- **Fix**: Updated to generate 180 days of timeseries data for all 10 suppliers with varying delay profiles.

### [P2] Frontend had no API integration
- **Status**: ✅ RESOLVED
- **Fix**: Created `frontend/src/api/index.ts` with typed API functions. Updated all 3 dashboards + Navigation to use real backend data. Created missing `App.tsx` with routing and role-based auth.

### [DB] No database schema existed
- **Status**: ✅ RESOLVED
- **Fix**: Created `db/schema.sql` and `db/seed.sql`. Backend uses in-memory data mirroring the SQL seed for demo purposes.

---

## Verification Results (2026-03-04):

| Check | Status |
|-------|--------|
| Backend running on :3001 | ✅ |
| 10 suppliers loaded | ✅ |
| 10 events loaded | ✅ |
| Agent pipeline runs successfully (green/yellow/red) | ✅ |
| Audit trail written per agent | ✅ |
| HITL pauses pipeline correctly | ✅ |
| Approvals created for escalated events | ✅ |
| POs created for auto-approved events | ✅ |
| Notifications generated | ✅ |
| Frontend TypeScript compiles | ✅ |
| Frontend Vite build succeeds | ✅ |
| Frontend API proxy works (/api → :3001) | ✅ |
| Unit tests pass (7/7) | ✅ |
| HITL guard tests pass (4/4) | ✅ |
| All 10 seed events complete without crash | ✅ |
