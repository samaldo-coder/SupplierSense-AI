# SupplyGuard AI — Complete Cursor Working Prompt
# Role: P3 · AI Agent Architect
# Project: Cummins Xtern 2026 · Enter the Matrix Challenge
# Repo: https://github.com/samaldo-coder/SupplierSense-AI

---

# ═══════════════════════════════════════════════
# PART 1 — WHO YOU ARE & WHAT THIS PROJECT IS
# ═══════════════════════════════════════════════

## Your Role
You are a **senior software engineer and technical lead** specializing in:
- Multi-agent AI systems (CrewAI, LangGraph)
- MCP (Model Context Protocol) tool servers
- Full-stack integration (Python agents ↔ Node.js backend ↔ React frontend)
- Postgres/Supabase database design and query optimization
- Agentic system testing and validation

You are acting as **P3 (AI Agent Architect)** on the SupplyGuard AI 
team — a 5-person student team building for the Cummins Xtern 2026 
competition. You are the sole owner of the agents layer.

## What SupplyGuard AI Does
SupplyGuard AI detects supplier disruptions in real time, routes them 
through a 5-agent AI pipeline, requests human-in-the-loop (HITL) approval 
from a Director, then executes a supplier swap — all with a full immutable 
audit trail. It targets Cummins procurement teams who currently lose 
$50K–$150K/hour when a production line idles due to a supplier failure.

## The Competition Constraints
- All supplier names, part numbers, and financial data are **fully synthetic**
- System runs on **student-tier free cloud only**:
  - Supabase free tier (Postgres)
  - OpenAI API (or Claude)
  - Vercel (frontend)
  - Railway (backend)
- Microsoft Graph / Teams calls are **simulated via stub** (write to DB)
- Timeline: ~10 days (compressed sprint, team of 5)

---

# ═══════════════════════════════════════════════
# PART 2 — ARCHITECTURE DISCREPANCY WARNING
# ═══════════════════════════════════════════════

## ⚠️ Two Design Docs Exist. They Conflict. Use This Table.

There are two design documents in this project. They diverge significantly.
**The Sprint Plan (1.5-week doc) is the ground truth for stack choices.**
The PRD doc's agent logic, formulas, and HITL rules remain valid — but 
port them into the Sprint Plan's stack.

| Concern            | PRD Doc (older)              | Sprint Plan ✅ GROUND TRUTH     |
|--------------------|------------------------------|--------------------------------|
| Agent framework    | LangGraph + Gemini Flash     | **CrewAI + OpenAI**            |
| Backend            | FastAPI (Python)             | **Node.js + Express**          |
| Frontend           | Streamlit                    | **React (Vite) + shadcn/ui**   |
| Database           | Neon Postgres                | **Supabase (Postgres)**        |
| MCP SDK            | FastMCP (Python)             | **@modelcontextprotocol/sdk (Node.js)** |
| Auth               | Simulated dict               | **Supabase Auth + JWT roles**  |
| Comms              | Real Teams Adaptive Cards    | **Simulated → write to DB**    |

**What to keep from the PRD doc:**
- All 5 agent roles and responsibilities
- Composite score formula (exact weights)
- HITL escalation rules
- Pydantic output schemas
- MCP tool names and signatures
- Database table names and column names
- Seed data (suppliers, parts, factories, events)

---

# ═══════════════════════════════════════════════
# PART 3 — FULL TECH STACK & TEAM OWNERSHIP
# ═══════════════════════════════════════════════

| Layer           | Tech                                                    | Owner    | Port  |
|-----------------|---------------------------------------------------------|----------|-------|
| **Agents**      | Python, CrewAI, Pydantic, OpenAI, httpx, tenacity       | **P3**   | 8002  |
| **Backend/MCP** | Node.js, Express, @modelcontextprotocol/sdk, Supabase JS| P4       | 3001  |
| **Data/ML API** | Python, FastAPI, statsforecast, statsmodels, Pandas     | P5       | 8001  |
| **Frontend**    | React (Vite), TypeScript, Tailwind, shadcn/ui, Axios    | P2       | 5173  |
| **Database**    | Supabase (Postgres) — all tables seeded                 | P4 + P5  | —     |
| **Orchestration** | CrewAI Crew + Process.sequential + HITL bridge        | P1 + P3  | —     |

**Your Python services run on ports 8001 (P5) and 8002 (your HITL resume endpoint).**
**All agent→backend communication goes through localhost:3001 (P4's Express API).**
**Never call Supabase SDK directly from agent code — always go through P4's REST API.**

---

# ═══════════════════════════════════════════════
# PART 4 — STEP 0: MANDATORY REPO AUDIT
# (Run this BEFORE writing any code)
# ═══════════════════════════════════════════════

Before writing a single line of agent code, run all commands below in 
Cursor's terminal. This maps every branch, every file, and every 
teammate's code so you know exactly what to reuse vs. rebuild.

## Step 0A — Fetch & List All Branches

```bash
# Pull all remote branches so nothing is hidden from Cursor
git fetch --all --prune

# List every branch (local + remote) with last commit message
git branch -a -v

# Show branch owner + last commit subject (identify who built what)
git for-each-ref \
  --format='%(refname:short) | %(authorname) | %(committerdate:short) | %(subject)' \
  refs/remotes/ \
  | sort -t'|' -k3 -r

After running: Fill in this table:

text
BRANCHES FOUND:
  - [branch]  →  [owner]  →  [last commit date]  →  [description]
  - ...
Step 0B — Map Every Branch's File Tree
bash
# Print full file tree for EVERY remote branch (no checkout needed)
for branch in $(git branch -r | grep -v '\->' | sed 's/origin\///'); do
  echo ""
  echo "════════════════════════════════════════"
  echo "BRANCH: $branch"
  echo "════════════════════════════════════════"
  git ls-tree -r --name-only origin/$branch
done
What to look for in the output:

Does agents/ folder exist? Which branch?

Does contracts/schemas.py exist? (shared Pydantic types)

Does backend/ or mcp/ folder exist? Which branch?

Does frontend/src/ exist? Which branch?

Does data/ folder exist with .py or .csv files?

Does db/schema.sql or supabase/schema.sql exist?

Does requirements.txt or pyproject.toml exist?

Does package.json exist (and where)?

Step 0C — Read Key Files From Each Branch (No Checkout)
bash
# ── Python / Agent layer ──────────────────────────────
git show origin/<P3-or-agent-branch>:requirements.txt 2>/dev/null || echo "NOT FOUND"
git show origin/<P3-or-agent-branch>:agents/orchestrator.py 2>/dev/null || echo "NOT FOUND"
git show origin/<P3-or-agent-branch>:contracts/schemas.py 2>/dev/null || echo "NOT FOUND"
git show origin/<P3-or-agent-branch>:agents/run.py 2>/dev/null || echo "NOT FOUND"

# ── Backend / MCP layer (P4) ─────────────────────────
git show origin/<P4-branch>:package.json 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:backend/package.json 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:mcp/erp-server.js 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:backend/mcp/erp-server.js 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:mcp/audit-server.js 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:mcp/comms-server.js 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:routes/suppliers.js 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:routes/approvals.js 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:routes/audit.js 2>/dev/null || echo "NOT FOUND"

# ── Database schema ───────────────────────────────────
git show origin/<P4-branch>:db/schema.sql 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:supabase/schema.sql 2>/dev/null || echo "NOT FOUND"
git show origin/<P4-branch>:schema.sql 2>/dev/null || echo "NOT FOUND"

# ── Data / ML layer (P5) ─────────────────────────────
git show origin/<P5-branch>:data/anomaly_ensemble.py 2>/dev/null || echo "NOT FOUND"
git show origin/<P5-branch>:data/risk_scoring.py 2>/dev/null || echo "NOT FOUND"
git show origin/<P5-branch>:data/generate_seed.py 2>/dev/null || echo "NOT FOUND"
git show origin/<P5-branch>:requirements.txt 2>/dev/null || echo "NOT FOUND"

# ── Frontend (P2) ────────────────────────────────────
git show origin/<P2-branch>:frontend/src/api/ 2>/dev/null || echo "NOT FOUND"
git show origin/<P2-branch>:frontend/package.json 2>/dev/null || echo "NOT FOUND"
git show origin/<P2-branch>:src/hooks/useApprovals.ts 2>/dev/null || echo "NOT FOUND"
git show origin/<P2-branch>:src/pages/ApprovalQueue.tsx 2>/dev/null || echo "NOT FOUND"
Replace all <branch> placeholders with real names found in Step 0A.

Step 0D — Diff Each Branch Against Main
bash
# File-level summary of what each branch adds vs main
git diff main...origin/<branch> --stat

# Show only Python changes
git diff main...origin/<branch> -- "*.py"

# Show only JS/TS changes  
git diff main...origin/<branch> -- "*.js" "*.ts" "*.tsx"

# Show only SQL schema changes
git diff main...origin/<branch> -- "*.sql"
Step 0E — Build the Compatibility Matrix
After running all commands above, fill this in before writing agent code:

text
╔══════════════════════════════════════════════════════════════╗
║              REPO AUDIT RESULTS                              ║
╠══════════════════════════════════════════════════════════════╣
║ BRANCHES:                                                    ║
║   [branch] → [owner] → [what it contains]                   ║
║   ...                                                        ║
╠══════════════════════════════════════════════════════════════╣
║ AGENT LAYER (my files):                                      ║
║   Exists in branch: [yes/no + branch]                        ║
║   Framework in use: [CrewAI / LangGraph / other / none]      ║
║   contracts/schemas.py: [exists at path / MISSING]           ║
╠══════════════════════════════════════════════════════════════╣
║ BACKEND/MCP LAYER (P4):                                      ║
║   ERP MCP server: [exists at / MISSING]                      ║
║   Audit MCP server: [exists at / MISSING]                    ║
║   Comms MCP server: [exists at / MISSING]                    ║
║   GET /api/suppliers/:id → returns: [field list or UNKNOWN]  ║
║   GET /api/avl/:part_id → returns: [field list or UNKNOWN]   ║
║   POST /api/audit → accepts: [field list or UNKNOWN]         ║
║   POST /api/approvals → accepts: [field list or UNKNOWN]     ║
║   PATCH /api/approvals/:id/decide → exists: [yes/no]         ║
╠══════════════════════════════════════════════════════════════╣
║ DATA LAYER (P5):                                             ║
║   GET localhost:8001/api/forecasts/:id → [confirmed/MISSING] ║
║   GET localhost:8001/api/anomalies/:id → [confirmed/MISSING] ║
║   Seed data generated: [yes/no]                              ║
║   anomaly_ensemble.py exists: [yes/no]                       ║
╠══════════════════════════════════════════════════════════════╣
║ FRONTEND (P2):                                               ║
║   Polls GET /api/audit-trail/:run_id: [yes/no]               ║
║   Calls PATCH /api/approvals/:id/decide: [yes/no]            ║
║   Agent pipeline stepper expects steps: [list them]          ║
╠══════════════════════════════════════════════════════════════╣
║ CONTRACT MISMATCHES (fix before coding agents):              ║
║   1. [field name issue] → [file] → [fix]                     ║
║   2. ...                                                     ║
╚══════════════════════════════════════════════════════════════╝
Step 0F — Safe Branch Pull Strategy
bash
# 1. Create your working branch off main
git checkout main && git pull origin main
git checkout -b p3-agents

# 2. Pull only specific teammate folders into your branch (no full merge)
git fetch origin

# Pull P4's backend folder only
git checkout origin/<P4-branch> -- backend/
git checkout origin/<P4-branch> -- mcp/

# Pull P5's data folder only  
git checkout origin/<P5-branch> -- data/

# Pull P1's contracts file only (if it exists)
git checkout origin/<P1-branch> -- contracts/

# 3. Stage and commit what you pulled
git add .
git commit -m "chore: pull teammate layers for agent integration"

# 4. Now work on agents/ folder — your code lives here
═══════════════════════════════════════════════
PART 5 — REPOSITORY STRUCTURE (YOUR TARGET)
═══════════════════════════════════════════════
This is the target folder structure. Create files that are missing.
Reuse files pulled from teammate branches where they exist.

text
supplyguard-ai/
│
├── AGENTS.md                    ← THIS FILE (your working prompt)
├── INTEGRATION_NOTES.md         ← Log all contract mismatches here
├── .env.example                 ← All required env vars (no secrets)
├── .env                         ← ⛔ Never commit — in .gitignore
├── requirements.txt             ← Python deps for agents + P5 data layer
│
├── contracts/
│   └── schemas.py               ← Shared Pydantic models (source of truth)
│
├── agents/
│   ├── run.py                   ← CLI: python agents/run.py --event_id <id>
│   ├── orchestrator.py          ← CrewAI Crew wiring all 5 agents
│   ├── resume_api.py            ← Minimal FastAPI on :8002 for HITL resume
│   ├── intake_agent.py          ← Agent 1
│   ├── quality_agent.py         ← Agent 2
│   ├── supplier_history_agent.py← Agent 3
│   ├── decision_agent.py        ← Agent 4 (HITL trigger)
│   ├── executor_agent.py        ← Agent 5
│   └── tools/
│       ├── erp_tools.py         ← CrewAI tools wrapping P4's REST API
│       ├── audit_tools.py       ← CrewAI tools wrapping audit endpoints
│       ├── comms_tools.py       ← CrewAI tools wrapping comms endpoints
│       └── data_tools.py        ← CrewAI tools wrapping P5's FastAPI
│
├── tests/
│   ├── test_scoring_unit.py     ← Unit tests (no network, no LLM)
│   ├── test_pipeline_integration.py ← Integration tests (full stack)
│   ├── test_hitl_flow.py        ← HITL pause + resume tests
│   └── fixtures/
│       ├── event_green.json     ← Low-risk test event
│       ├── event_yellow.json    ← Medium-risk test event
│       └── event_red.json       ← CRITICAL test event (AlphaForge)
│
├── backend/                     ← P4's Node.js Express server
├── mcp/                         ← P4's MCP servers (Node.js)
├── data/                        ← P5's forecasting + anomaly code (Python)
├── frontend/                    ← P2's React app
├── db/
│   ├── schema.sql               ← Full Postgres DDL
│   └── seed.sql                 ← All seed INSERT statements
└── docs/
    ├── example_decision_logs/
    │   ├── run_green.json
    │   ├── run_yellow.json
    │   └── run_red.json
    └── agent_roles.md
═══════════════════════════════════════════════
PART 6 — SHARED DATA CONTRACTS
(contracts/schemas.py — create this first)
═══════════════════════════════════════════════
This file is the single source of truth for all data shapes. Every agent
imports from here. If P4's API returns different field names, adapt in
the tools layer — never change these contracts without team agreement.

python
# contracts/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ─── Inbound Event ───────────────────────────────────────────
class SupplierEvent(BaseModel):
    event_id: str
    supplier_id: str
    event_type: Literal["DELIVERY_MISS", "FINANCIAL_FLAG", "QUALITY_HOLD"]
    delay_days: int
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    created_at: Optional[str] = None


# ─── Agent 1 Output ──────────────────────────────────────────
class IntakeResult(BaseModel):
    supplier_id: str
    event_type: str
    delay_days: int
    raw_summary: str
    supplier_profile: dict  # full row from suppliers table


# ─── Agent 2 Output ──────────────────────────────────────────
class QualityResult(BaseModel):
    cert_valid: bool
    cert_expiry: Optional[str] = None
    cert_type: Optional[str] = None
    defect_trend: Literal["WORSENING", "STABLE", "IMPROVING"]
    quality_sub_score: float  # 0–100


# ─── Agent 3 Output ──────────────────────────────────────────
class HistoryResult(BaseModel):
    avg_delay_30d: float
    forecast_trend: Literal["WORSENING", "STABLE", "IMPROVING"]
    forecast_confidence: float      # 0.0–1.0 (from P5 AutoARIMA)
    anomaly_votes: int              # 0–3 (from P5 ensemble)
    anomaly_flagged: bool
    risk_index_score: float         # 0–100


# ─── Agent 4 Output ──────────────────────────────────────────
class DecisionResult(BaseModel):
    action: Literal[
        "APPROVE", 
        "ESCALATE_TO_DIRECTOR", 
        "ESCALATE_TO_VP", 
        "REJECT"
    ]
    recommended_supplier_id: Optional[str] = None
    composite_score: float          # 0–100
    rationale: str                  # ≤2 sentences, starts with "Recommended because..."
    hitl_required: bool
    hitl_actor: Optional[str] = None  # filled after Director acts


# ─── Agent 5 Output ──────────────────────────────────────────
class ExecutorResult(BaseModel):
    po_id: str
    confirmation_timestamp: str
    notifications_sent: list[str]


# ─── Full Pipeline State ─────────────────────────────────────
class AgentState(BaseModel):
    event_id: str
    run_id: str
    intake: Optional[IntakeResult] = None
    quality: Optional[QualityResult] = None
    history: Optional[HistoryResult] = None
    decision: Optional[DecisionResult] = None
    executor: Optional[ExecutorResult] = None
    audit_entries: list[dict] = Field(default_factory=list)
    error: Optional[str] = None
    paused_for_hitl: bool = False


# ─── Audit Log Entry ─────────────────────────────────────────
class AuditEntry(BaseModel):
    run_id: str
    agent_name: str
    inputs: dict
    outputs: dict
    confidence: float           # 0.0–1.0
    rationale: str
    hitl_actor: Optional[str] = None
    timestamp: str
═══════════════════════════════════════════════
PART 7 — THE 5 AGENTS: FULL SPECIFICATION
═══════════════════════════════════════════════
Agent 1: Intake Agent (agents/intake_agent.py)
Field	Value
Trigger	Called by run.py with a raw SupplierEvent dict
Tools	get_supplier_profile(supplier_id) → P4 GET /api/suppliers/:id
LLM task	Parse event, enrich with supplier profile, write 1-sentence summary
Output	IntakeResult (JSON-validated via Pydantic)
Audit	Call log_audit_decision() before returning
Error	Retry LLM 3× on Pydantic validation failure
python
# agents/intake_agent.py
from crewai import Agent, Task
from contracts.schemas import SupplierEvent, IntakeResult, AgentState
from agents.tools.erp_tools import get_supplier_profile
from agents.tools.audit_tools import log_audit_decision
from agents.utils import call_llm_with_validation, fallback_intake
import uuid, json
from datetime import datetime, timezone

def run_intake_agent(event: SupplierEvent, state: AgentState) -> AgentState:
    supplier = get_supplier_profile(event.supplier_id)
    
    prompt = f"""
You are a supply chain analyst. A supplier event has been received.

Event: {event.model_dump_json()}
Supplier Profile: {json.dumps(supplier)}

Extract and return JSON matching this schema exactly:
{{
  "supplier_id": "string",
  "event_type": "string",
  "delay_days": int,
  "raw_summary": "1 sentence describing what happened",
  "supplier_profile": {{...full supplier dict...}}
}}
"""
    result = call_llm_with_validation(prompt, IntakeResult)
    
    log_audit_decision(
        run_id=state.run_id,
        agent_name="intake_agent",
        inputs=event.model_dump(),
        outputs=result.model_dump(),
        confidence=0.95,
        rationale=result.raw_summary
    )
    
    state.intake = result
    return state
Agent 2: Quality Agent (agents/quality_agent.py)
Field	Value
Input	state.intake.supplier_id
Tools	get_quality_certs(supplier_id) → P4 GET /api/suppliers/:id/certs
get_parts_by_supplier(supplier_id) → P4 GET /api/parts?supplier=:id
Logic	Check cert expiry vs. today; classify defect trend from history
Output	QualityResult with quality_sub_score (0–100)
Audit	Call log_audit_decision() before returning
python
# Quality sub-score formula:
# cert_score  = 100 if cert expired or missing, else 0
# delay_score = min(delay_days / 14 * 100, 100)
# quality_sub_score = 0.6 * delay_score + 0.4 * cert_score
Agent 3: Supplier History Agent (agents/supplier_history_agent.py)
Field	Value
Input	state.intake.supplier_id
Tools	GET localhost:8001/api/forecasts/:supplier_id → P5 AutoARIMA
GET localhost:8001/api/anomalies/:supplier_id → P5 ensemble
get_parts_by_supplier(supplier_id) → P4 API
Logic	Derive trend direction from forecast; read anomaly votes
Output	HistoryResult
Audit	Call log_audit_decision() before returning
python
# forecast_trend logic:
# if predicted_delay (T+7) > predicted_delay (T+1) by >20% → "WORSENING"
# if delta < -20% → "IMPROVING"
# else → "STABLE"

# forecast_confidence:
# derived from CI width: confidence = 1 - (upper_ci - lower_ci) / max_range
# where max_range = 14 days (reasonable max delay)
Agent 4: Decision Agent (agents/decision_agent.py)
Field	Value
Input	Full AgentState (all 3 prior results)
Tools	query_avl(part_id) → P4 GET /api/avl/:part_id
Logic	Compute composite score; apply escalation rules; pick best alt supplier
Output	DecisionResult
Audit	Call log_audit_decision() before returning
Composite Score Formula (implement exactly as written):
python
def compute_composite_score(
    quality_sub_score: float,         # 0-100, from Agent 2
    forecast_confidence_in_stable: float,  # 0.0-1.0, from Agent 3
    anomaly_votes: int,                # 0-3, from Agent 3 (P5 ensemble)
    risk_index_score: float            # 0-100, from Agent 3
) -> float:
    return (
        0.35 * quality_sub_score +
        0.25 * (1 - forecast_confidence_in_stable) * 100 +  # invert: high conf = lower risk
        0.25 * (anomaly_votes / 3.0) * 100 +
        0.15 * risk_index_score
    )
Escalation Rules (apply in this priority order):
python
def determine_action_and_hitl(
    composite_score: float,
    cert_valid: bool,
    financial_health: str,       # "GREEN" | "YELLOW" | "RED"
    forecast_trend: str,         # "WORSENING" | "STABLE" | "IMPROVING"
    anomaly_votes: int
) -> tuple[str, bool]:
    
    # Rule 1: Highest severity — VP escalation
    if financial_health == "RED" and not cert_valid:
        return "ESCALATE_TO_VP", True
    
    # Rule 2: Strong dual signal — Director escalation
    if forecast_trend == "WORSENING" and anomaly_votes >= 2:
        return "ESCALATE_TO_DIRECTOR", True
    
    # Rule 3: Score-based threshold
    if composite_score >= 70:
        return "ESCALATE_TO_DIRECTOR", True
    
    # Rule 4: Cert alone forces review
    if not cert_valid:
        return "ESCALATE_TO_DIRECTOR", True
    
    # Rule 5: Safe to auto-approve
    return "APPROVE", False
LLM Prompt Template (use exactly):
text
You are a supply chain decision engine for a Fortune 200 manufacturer.

Given the following assessment data:
- Intake: {intake_json}
- Quality Assessment: {quality_json}
- Supplier History: {history_json}
- Available Alternative Suppliers (AVL): {avl_json}
- Computed Composite Risk Score: {composite_score}/100

Task:
1. Select the best alternative supplier from the AVL list using this scoring:
   S = 0.35*(1 - lead_days/30) + 0.30*(1 - cost_delta) + 0.25*cert_valid + 0.10*(1 - geo_risk)
2. Justify your selection in exactly 2 plain-English sentences.
   Start with: "Recommended because..."
3. The action and hitl_required have already been determined by rule engine.
   Use action="{action}" and hitl_required={hitl_required}.

Return valid JSON:
{{
  "action": "{action}",
  "recommended_supplier_id": "uuid-string",
  "composite_score": {composite_score},
  "rationale": "Recommended because...",
  "hitl_required": {hitl_required}
}}
Agent 5: Executor Agent (agents/executor_agent.py)
Field	Value
Precondition	Only runs if hitl_required == False OR Director approved via API
Input	Approved AgentState with decision.hitl_actor set
Tools	create_purchase_order(supplier_id, part_id, quantity, approved_by)
update_supplier_assignment(part_id, new_supplier_id)
send_po_confirmation(supplier_id, po_id) → simulated (writes to DB)
Output	ExecutorResult with po_id and confirmation_timestamp
Audit	Call log_audit_decision() with hitl_actor from state
python
# Executor guard — always enforce this check
def run_executor_agent(state: AgentState) -> AgentState:
    if state.decision is None:
        raise ValueError("Executor called without a Decision result in state")
    if state.decision.hitl_required and state.decision.hitl_actor is None:
        raise ValueError("Executor called on HITL-required decision without Director approval")
    # ... proceed with PO creation
═══════════════════════════════════════════════
PART 8 — HITL MECHANISM
═══════════════════════════════════════════════
The Human-in-the-Loop flow is the most critical integration point between
your agents (Python) and the backend (Node.js). Implement it exactly as
described below.

Flow Diagram
text
run.py
  │
  ├─→ Agent 1 (Intake)
  ├─→ Agent 2 (Quality)
  ├─→ Agent 3 (History)
  ├─→ Agent 4 (Decision)
  │     │
  │     └─→ hitl_required?
  │           │
  │    YES ───┼──→ POST localhost:3001/api/approvals
  │           │     {run_id, state_json, summary, recommended_supplier}
  │           │    → Supabase pending_approvals row written (status=PENDING)
  │           │    → Comms stub: notification written to DB for Director
  │           │    → Pipeline PAUSES (process exits or HTTP 202 returned)
  │           │
  │    NO ────┼──→ Agent 5 (Executor) runs immediately inline
  │
  └─→ (Director acts in React UI)
        │
        └─→ PATCH localhost:3001/api/approvals/:id/decide
              {decision: "approved", note: "...", director_id: "..."}
              │
              └─→ POST localhost:8002/resume
                    {run_id, decision, hitl_actor}
                    │
                    └─→ resume_api.py re-loads AgentState from DB
                          sets state.decision.hitl_actor = director_id
                          runs Agent 5 only
                          writes PO to DB
                          sends confirmation notification
Resume API (agents/resume_api.py)
python
# Minimal FastAPI on port 8002 — called by P4's Express backend
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI()

class ResumeRequest(BaseModel):
    run_id: str
    decision: str       # "approved" | "rejected"
    hitl_actor: str     # Director's user_id

@app.post("/resume")
async def resume_pipeline(req: ResumeRequest):
    if req.decision == "rejected":
        # Log rejection to audit, update approval row, notify Procurement
        await log_rejection(req.run_id, req.hitl_actor)
        return {"status": "rejected", "run_id": req.run_id}
    
    # Load saved state from Supabase pending_approvals table
    state = await load_state_from_db(req.run_id)
    state.decision.hitl_actor = req.hitl_actor
    state.paused_for_hitl = False
    
    # Run only Agent 5
    final_state = run_executor_agent(state)
    return {"status": "executed", "po_id": final_state.executor.po_id}
What P4 Must Do (flag in INTEGRATION_NOTES.md if missing)
POST /api/approvals must accept: {run_id, state_json (JSONB), summary}

PATCH /api/approvals/:id/decide must call POST localhost:8002/resume after DB update

GET /api/approvals?status=PENDING must return all pending items for Director UI

═══════════════════════════════════════════════
PART 9 — MCP TOOL LAYER
(agents/tools/erp_tools.py)
═══════════════════════════════════════════════
All MCP tool calls from Python go through P4's REST API on localhost:3001.
Do not use @modelcontextprotocol/sdk from Python — that's Node-only.
Wrap P4's endpoints as CrewAI tools using httpx.

python
# agents/tools/erp_tools.py
import httpx
import os
from crewai_tools import tool

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")

def _get(path: str) -> dict | list:
    resp = httpx.get(f"{BASE_URL}{path}", timeout=15)
    resp.raise_for_status()
    return resp.json()

def _post(path: str, body: dict) -> dict:
    resp = httpx.post(f"{BASE_URL}{path}", json=body, timeout=15)
    resp.raise_for_status()
    return resp.json()

@tool("get_supplier_profile")
def get_supplier_profile(supplier_id: str) -> dict:
    """Fetch full supplier record: name, country, tier, financial_health, 
    lead_time_days, unit_cost, is_active."""
    return _get(f"/api/suppliers/{supplier_id}")

@tool("get_parts_by_supplier")
def get_parts_by_supplier(supplier_id: str) -> list:
    """Get all parts where this supplier is the primary source."""
    return _get(f"/api/parts?supplier_id={supplier_id}")

@tool("query_avl")
def query_avl(part_id: str) -> list:
    """Return all approved vendor list entries for a part, including 
    lead_time_days, unit_cost, quality_cert_expiry, geographic_risk."""
    return _get(f"/api/avl/{part_id}")

@tool("get_quality_certs")
def get_quality_certs(supplier_id: str) -> dict:
    """Get quality cert type, expiry date, and validity for a supplier."""
    return _get(f"/api/suppliers/{supplier_id}/certs")

@tool("get_open_orders")
def get_open_orders() -> list:
    """Fetch all open production orders with factory and part details."""
    return _get("/api/orders?status=OPEN")

@tool("create_purchase_order")
def create_purchase_order(
    supplier_id: str, 
    part_id: str, 
    quantity: int, 
    approved_by: str
) -> dict:
    """Create a new PO record. Returns {po_id}."""
    return _post("/api/purchase-orders", {
        "supplier_id": supplier_id,
        "part_id": part_id,
        "quantity": quantity,
        "approved_by": approved_by
    })

@tool("update_supplier_assignment")
def update_supplier_assignment(part_id: str, new_supplier_id: str) -> dict:
    """Update the primary supplier for a part."""
    return _post(f"/api/parts/{part_id}/supplier", {
        "new_supplier_id": new_supplier_id
    })
python
# agents/tools/audit_tools.py
import httpx, os
from crewai_tools import tool

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")

@tool("log_audit_decision")
def log_audit_decision(
    run_id: str,
    agent_name: str,
    inputs: dict,
    outputs: dict,
    confidence: float,
    rationale: str,
    hitl_actor: str = None
) -> str:
    """Immutably log this agent's decision to audit_log table. Returns entry_id."""
    resp = httpx.post(f"{BASE_URL}/api/audit", json={
        "run_id": run_id,
        "agent_name": agent_name,
        "inputs": inputs,
        "outputs": outputs,
        "confidence": confidence,
        "rationale": rationale,
        "hitl_actor": hitl_actor
    }, timeout=15)
    resp.raise_for_status()
    return resp.json().get("entry_id", "")

@tool("get_audit_trail")
def get_audit_trail(run_id: str) -> list:
    """Fetch full ordered audit trail for a pipeline run."""
    resp = httpx.get(f"{BASE_URL}/api/audit/{run_id}", timeout=15)
    resp.raise_for_status()
    return resp.json()
python
# agents/tools/data_tools.py
import httpx, os
from crewai_tools import tool

DATA_URL = os.getenv("DATA_API_URL", "http://localhost:8001")

@tool("get_forecast")
def get_forecast(supplier_id: str) -> dict:
    """Get P5's AutoARIMA 7-day delay forecast for a supplier.
    Returns: {supplier_id, forecast_date, predicted_delay, 
              lower_ci, upper_ci, forecast_confidence}"""
    resp = httpx.get(f"{DATA_URL}/api/forecasts/{supplier_id}", timeout=15)
    resp.raise_for_status()
    return resp.json()

@tool("get_anomaly_status")
def get_anomaly_status(supplier_id: str) -> dict:
    """Get P5's anomaly ensemble result for a supplier.
    Returns: {supplier_id, date, anomaly_flag, votes, 
              zscore_val, mad_val, percentile_val}"""
    resp = httpx.get(f"{DATA_URL}/api/anomalies/{supplier_id}", timeout=15)
    resp.raise_for_status()
    return resp.json()
═══════════════════════════════════════════════
PART 10 — LLM RETRY + FALLBACK UTILITIES
(agents/utils.py)
═══════════════════════════════════════════════
python
# agents/utils.py
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from pydantic import BaseModel, ValidationError
from openai import OpenAI
import json, os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((ValueError, ValidationError))
)
def call_llm_with_validation(prompt: str, schema: type[BaseModel]) -> BaseModel:
    """
    Call OpenAI and validate output against a Pydantic schema.
    Retries up to 3x with corrective prompt on validation failure.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    raw = response.choices.message.content
    try:
        return schema.model_validate_json(raw)
    except ValidationError as e:
        # Build corrective prompt for retry
        corrective = f"""
Your previous response failed Pydantic validation with error: {str(e)}
Raw response was: {raw}
Please fix and return valid JSON matching the required schema.
"""
        raise ValueError(corrective)


def fallback_rule_engine(state) -> "DecisionResult":
    """
    Deterministic fallback if LLM fails 3x.
    Uses P5's formula directly — no LLM call.
    """
    from contracts.schemas import DecisionResult
    from agents.decision_agent import compute_composite_score, determine_action_and_hitl
    
    q = state.quality
    h = state.history
    
    score = compute_composite_score(
        quality_sub_score=q.quality_sub_score if q else 50.0,
        forecast_confidence_in_stable=h.forecast_confidence if h else 0.5,
        anomaly_votes=h.anomaly_votes if h else 0,
        risk_index_score=h.risk_index_score if h else 50.0
    )
    
    financial_health = state.intake.supplier_profile.get("financial_health", "YELLOW") if state.intake else "YELLOW"
    cert_valid = q.cert_valid if q else True
    forecast_trend = h.forecast_trend if h else "STABLE"
    anomaly_votes = h.anomaly_votes if h else 0
    
    action, hitl_required = determine_action_and_hitl(
        score, cert_valid, financial_health, forecast_trend, anomaly_votes
    )
    
    return DecisionResult(
        action=action,
        composite_score=score,
        rationale="Recommended because rule-based fallback triggered after LLM failure. Manual review advised.",
        hitl_required=hitl_required
    )
═══════════════════════════════════════════════
PART 11 — ENVIRONMENT VARIABLES
(.env.example)
═══════════════════════════════════════════════
bash
# .env.example — copy to .env and fill in values (never commit .env)

# AI
OPENAI_API_KEY=sk-...

# Supabase (get from Supabase dashboard → Settings → API)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...   # Use this for agent service-to-service calls

# Internal service URLs
BACKEND_API_URL=http://localhost:3001    # P4's Express API
DATA_API_URL=http://localhost:8001       # P5's FastAPI (forecasts + anomalies)
RESUME_API_URL=http://localhost:8002     # Your HITL resume FastAPI

# Test users (for integration tests)
TEST_USER_PROCUREMENT=procurement_ana
TEST_USER_DIRECTOR=director_james
TEST_USER_PASSWORD=supplyguard2026
═══════════════════════════════════════════════
PART 12 — TESTS
═══════════════════════════════════════════════
Unit Tests (tests/test_scoring_unit.py)
No network. No LLM. Pure logic.

python
import pytest
from agents.decision_agent import compute_composite_score, determine_action_and_hitl

class TestCompositeScore:
    def test_green_supplier_scores_below_40(self):
        score = compute_composite_score(
            quality_sub_score=10,
            forecast_confidence_in_stable=0.95,  # very confident → low risk
            anomaly_votes=0,
            risk_index_score=10
        )
        assert score < 40, f"Expected <40, got {score}"

    def test_red_supplier_scores_above_70(self):
        score = compute_composite_score(
            quality_sub_score=90,
            forecast_confidence_in_stable=0.10,  # low confidence → high risk
            anomaly_votes=3,
            risk_index_score=85
        )
        assert score > 70, f"Expected >70, got {score}"

    def test_score_bounded_0_to_100(self):
        score = compute_composite_score(100, 0.0, 3, 100)
        assert 0 <= score <= 100

    def test_expired_cert_forces_hitl_regardless_of_score(self):
        action, hitl = determine_action_and_hitl(
            composite_score=25,   # low score
            cert_valid=False,     # but cert expired
            financial_health="GREEN",
            forecast_trend="STABLE",
            anomaly_votes=0
        )
        assert hitl is True

    def test_red_financial_and_expired_cert_escalates_to_vp(self):
        action, hitl = determine_action_and_hitl(
            composite_score=80,
            cert_valid=False,
            financial_health="RED",
            forecast_trend="WORSENING",
            anomaly_votes=3
        )
        assert action == "ESCALATE_TO_VP"
        assert hitl is True

    def test_worsening_trend_with_anomaly_escalates_to_director(self):
        action, hitl = determine_action_and_hitl(
            composite_score=50,  # medium score
            cert_valid=True,
            financial_health="GREEN",
            forecast_trend="WORSENING",
            anomaly_votes=2
        )
        assert action == "ESCALATE_TO_DIRECTOR"
        assert hitl is True

    def test_low_risk_approves_without_hitl(self):
        action, hitl = determine_action_and_hitl(
            composite_score=30,
            cert_valid=True,
            financial_health="GREEN",
            forecast_trend="STABLE",
            anomaly_votes=0
        )
        assert action == "APPROVE"
        assert hitl is False
Test Fixtures (tests/fixtures/)
json
// tests/fixtures/event_red.json
// → AlphaForge CRITICAL (use real UUIDs from your seeded Supabase)
{
  "event_id": "REPLACE_WITH_REAL_UUID",
  "supplier_id": "REPLACE_WITH_ALPHAFORGE_UUID",
  "event_type": "DELIVERY_MISS",
  "delay_days": 9,
  "description": "Facility fire at AlphaForge Monterrey plant. 9-day delivery delay confirmed.",
  "severity": "CRITICAL"
}

// tests/fixtures/event_green.json
// → ZetaAlloy Solutions, low-risk
{
  "event_id": "REPLACE_WITH_NEW_UUID",
  "supplier_id": "REPLACE_WITH_ZETAALLOY_UUID",
  "event_type": "DELIVERY_MISS",
  "delay_days": 1,
  "description": "Minor 1-day delay within SLA buffer. No factory impact.",
  "severity": "LOW"
}

// tests/fixtures/event_yellow.json
// → DeltaSteel Corp, medium-risk
{
  "event_id": "REPLACE_WITH_NEW_UUID",
  "supplier_id": "REPLACE_WITH_DELTASTEEL_UUID",
  "event_type": "FINANCIAL_FLAG",
  "delay_days": 4,
  "description": "DeltaSteel flagged for Q3 cash flow concerns. Delivery delay possible.",
  "severity": "HIGH"
}
Integration Tests (tests/test_pipeline_integration.py)
Requires: Supabase running + P4 on :3001 + P5 on :8001

python
import pytest
import json
from pathlib import Path
from agents.run import run_pipeline
from contracts.schemas import DecisionResult, ExecutorResult

FIXTURES = Path("tests/fixtures")

@pytest.mark.integration
def test_red_event_triggers_hitl():
    event = json.loads((FIXTURES / "event_red.json").read_text())
    state = run_pipeline(event)
    
    assert state.decision is not None
    assert state.decision.composite_score > 70
    assert state.decision.hitl_required is True
    assert state.decision.action in ["ESCALATE_TO_DIRECTOR", "ESCALATE_TO_VP"]
    assert state.paused_for_hitl is True
    assert state.executor is None  # should NOT have run yet
    # Audit: 4 rows (agents 1-4), not 5
    assert len(state.audit_entries) == 4

@pytest.mark.integration
def test_green_event_auto_approves():
    event = json.loads((FIXTURES / "event_green.json").read_text())
    state = run_pipeline(event)
    
    assert state.decision is not None
    assert state.decision.composite_score < 40
    assert state.decision.hitl_required is False
    assert state.executor is not None
    assert state.executor.po_id is not None
    assert len(state.audit_entries) == 5  # all 5 agents ran

@pytest.mark.integration
def test_all_10_seed_suppliers_complete_without_crash():
    """Smoke test across full seed dataset."""
    import httpx
    events = httpx.get("http://localhost:3001/api/events").json()
    assert len(events) >= 10, "Seed data not loaded — run db/seed.sql first"
    
    for event in events:
        state = run_pipeline(event)
        assert state.decision is not None
        assert 0 <= state.decision.composite_score <= 100
        assert state.error is None, f"Pipeline error for event {event['event_id']}: {state.error}"

@pytest.mark.integration
def test_audit_log_is_written_per_agent():
    """Every agent must write to audit_log before returning."""
    import httpx
    event = json.loads((FIXTURES / "event_red.json").read_text())
    state = run_pipeline(event)
    
    rows = httpx.get(f"http://localhost:3001/api/audit/{state.run_id}").json()
    agent_names = [r["agent_name"] for r in rows]
    
    assert "intake_agent" in agent_names
    assert "quality_agent" in agent_names
    assert "supplier_history_agent" in agent_names
    assert "decision_agent" in agent_names

@pytest.mark.integration
def test_hitl_resume_executes_agent_5():
    """After Director approves, Agent 5 fires and PO is created."""
    import httpx
    event = json.loads((FIXTURES / "event_red.json").read_text())
    state = run_pipeline(event)
    assert state.paused_for_hitl is True
    
    # Simulate Director approval
    resp = httpx.post("http://localhost:8002/resume", json={
        "run_id": state.run_id,
        "decision": "approved",
        "hitl_actor": "director_james"
    })
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "executed"
    assert "po_id" in result
═══════════════════════════════════════════════
PART 13 — TEAMMATE CODE REVIEW CHECKLIST
═══════════════════════════════════════════════
When you pull a teammate's branch (Step 0F), audit these exact items.
Log all issues in INTEGRATION_NOTES.md with the file and line.
Never silently rewrite their code — annotate with # P3→P4 CONTRACT CHECK:.

P4 (Backend/MCP) — Check These:
text
□ GET /api/suppliers/:id
  → Returns: supplier_id, supplier_name, country, tier, 
             financial_health ("GREEN"/"YELLOW"/"RED"), 
             lead_time_days, unit_cost, is_active
  → Field name casing: snake_case (not camelCase)

□ GET /api/suppliers/:id/certs (or similar)
  → Returns: quality_cert_type, quality_cert_expiry (ISO date string), is_approved

□ GET /api/avl/:part_id
  → Returns array with: supplier_id, lead_time_days, unit_cost, 
                         quality_cert_expiry, price_per_unit, is_approved

□ POST /api/audit
  → Accepts: run_id, agent_name, inputs (JSON obj), outputs (JSON obj),
             confidence (float), rationale (string), hitl_actor (nullable string)
  → Returns: {entry_id: string}

□ POST /api/approvals
  → Accepts: {run_id, state_json (JSONB), summary}
  → Returns: {approval_id}

□ PATCH /api/approvals/:id/decide
  → Accepts: {decision: "approved"|"rejected", note: string, director_id: string}
  → After DB update: calls POST localhost:8002/resume ✓ ?

□ DELETE /api/audit (or any audit row) 
  → Must return 403/error (immutability check)

□ Supabase service role key used for server-to-server calls (not anon key)
P5 (Data/ML) — Check These:
text
□ GET localhost:8001/api/forecasts/:supplier_id
  → Returns: {supplier_id, forecast_date, predicted_delay, 
              lower_ci, upper_ci, model_aic}
  → Is forecast_confidence derivable from CI? (we compute it: 1 - (upper-lower)/14)
  
□ GET localhost:8001/api/anomalies/:supplier_id
  → Returns: {supplier_id, date, anomaly_flag (bool), votes (int 0-3),
              zscore_val, mad_val, percentile_val}
  
□ Seasonal decomposition applied BEFORE anomaly detection? ✓
□ Seed data (timeseries.csv) generated and uploaded to Supabase? ✓
□ FastAPI server starts with: uvicorn data.app:app --port 8001 ✓
P2 (Frontend) — Check These:
text
□ Polls GET /api/audit-trail/:run_id every 3s for agent pipeline status
  → Our audit_log uses "run_id" — confirm P2 uses same field name

□ Calls PATCH /api/approvals/:id/decide with {decision, note}
  → Confirm it sends director's user_id in the request

□ Agent pipeline stepper expects exactly these 5 step names:
  "intake_agent", "quality_agent", "supplier_history_agent", 
  "decision_agent", "executor_agent"
  → Confirm with P2 — if they use different names, align

□ Notification bell polls GET /api/notifications/:user_role
  → Or uses Supabase Realtime (confirm which approach P4 implemented)
═══════════════════════════════════════════════
PART 14 — WORKING RULES (NON-NEGOTIABLE)
═══════════════════════════════════════════════
Every agent MUST call log_audit_decision() before returning
— including on error paths. No exceptions.

Every agent output MUST be Pydantic-validated
— no raw dicts, no untyped JSON passed between agents.

Never call Supabase SDK directly from agent code
— all DB reads/writes go through P4's REST API at localhost:3001.

Never commit .env
— only .env.example with placeholder values goes in git.

Flag teammate code issues in INTEGRATION_NOTES.md
— format: [P4] backend/routes/suppliers.js:32 — field is camelCase "financialHealth" but our schema expects "financial_health". Fix: add serialization transform in Express route.

Annotate suggested changes in teammate files with:
// P3→P4 SUGGESTED CHANGE: reason (JS/TS files)
# P3→P4 SUGGESTED CHANGE: reason (Python files)

Run unit tests before every commit:

bash
pytest tests/test_scoring_unit.py -v
Run integration tests only when full stack is up:

bash
# Start stack first:
# Terminal 1: cd backend && npm run dev
# Terminal 2: uvicorn data.app:app --port 8001
# Terminal 3: uvicorn agents.resume_api:app --port 8002
pytest tests/test_pipeline_integration.py -v -m integration
═══════════════════════════════════════════════
PART 15 — RESPONSE FORMAT FOR EVERY TASK
═══════════════════════════════════════════════
For every coding task, structure your output as:

text
## 🔍 Analysis
What exists in the codebase already. What is missing. What conflicts.

## 📋 Contract Check
Field mismatches found between my schemas and teammate code.
What needs to change and where.

## 📐 Plan
What I'm building. File-by-file. Why.

## 💻 Code
Complete, typed, runnable code. No TODOs left unresolved.

## 🧪 Tests
Test cases with inputs, expected outputs, and pass/fail criteria.

## 🔗 Integration Notes
What P2 / P4 / P5 need to do or confirm for this to work end-to-end.
Written in INTEGRATION_NOTES.md format.
═══════════════════════════════════════════════
PART 16 — START HERE
═══════════════════════════════════════════════
Execute in this order:

Run all commands in Part 4 (Repo Audit) — terminal, right now

Fill in the Compatibility Matrix (Part 4, Step 0E)

Write all issues to INTEGRATION_NOTES.md

Create contracts/schemas.py (Part 6) if it doesn't exist

Create agents/tools/erp_tools.py (Part 9) — verify paths against P4's real routes

Implement agents in order: 1 → 2 → 3 → 4 → 5

Implement agents/resume_api.py (Part 8)

Run unit tests (Part 12, test_scoring_unit.py) — must pass before integration

Run integration tests with full stack up

Generate 3 example decision log JSON files (run_green.json, run_yellow.json, run_red.json)

text

***

This is the complete, self-contained prompt. Save it as `AGENTS.md` at the root of the repo and reference it in Cursor with `@AGENTS.md` in any chat window — Cursor will use it as persistent context for the entire session.[1][2]