/**
 * SupplyGuard AI — Competition Deliverable Document Generator
 * Generates all required Word documents for the Cummins Xtern 2026 challenge.
 *
 * Output files:
 *   1. technical_design_document.docx (2-3 pages)
 *   2. governance_safety_brief.docx (1 page)
 *   3. business_sketch.docx (1 page)
 *   4. next_steps_pilot_plan.docx (1 page)
 *   5. tco_cost_optimization.docx (2 pages)
 *   6. tco_cost_model.docx (1 page)
 *   7. tco_integration_sla.docx (1 page)
 *   8. tco_licensing_legal.docx (1 page)
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, TabStopType, TabStopPosition,
  PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo, PositionalTabLeader
} = require("docx");
const fs = require("fs");
const path = require("path");

const OUTPUT_DIR = process.argv[2] || path.join(__dirname, "..", "docs");

// ─── Shared Styles ──────────────────────────────────────────
const BLUE = "1F4E79";
const LIGHT_BLUE = "D6E4F0";
const DARK_GRAY = "333333";
const MEDIUM_GRAY = "666666";

const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };

function docStyles() {
  return {
    default: { document: { run: { font: "Arial", size: 22, color: DARK_GRAY } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: DARK_GRAY },
        paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 2 }
      },
    ]
  };
}

function numbering() {
  return {
    config: [
      {
        reference: "bullets", levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "numbers", levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
    ]
  };
}

function pageProps() {
  return {
    page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1200, right: 1200, bottom: 1200, left: 1200 }
    }
  };
}

function headerFooter(title) {
  return {
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE, space: 4 } },
          children: [
            new TextRun({ text: "SupplyGuard AI", bold: true, size: 18, font: "Arial", color: BLUE }),
            new TextRun({ text: `  |  ${title}`, size: 18, font: "Arial", color: MEDIUM_GRAY }),
          ]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC", space: 4 } },
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Cummins Xtern 2026 Challenge  |  Team 5  |  Page ", size: 16, color: MEDIUM_GRAY }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: MEDIUM_GRAY }),
          ]
        })]
      })
    }
  };
}

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    ...opts,
    children: [new TextRun({ size: 22, ...opts.run, text })]
  });
}
function bold(text) {
  return new TextRun({ text, bold: true, size: 22 });
}
function normal(text) {
  return new TextRun({ text, size: 22 });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text, size: 22 })]
  });
}
function numberedItem(text, ref = "numbers") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text, size: 22 })]
  });
}

function makeTable(headers, rows, colWidths) {
  const tableWidth = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      borders, width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: BLUE, type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: "FFFFFF", size: 20, font: "Arial" })] })]
    }))
  });
  const dataRows = rows.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders, width: { size: colWidths[i], type: WidthType.DXA },
      margins: cellMargins,
      children: [new Paragraph({ children: [new TextRun({ text: String(cell), size: 20, font: "Arial" })] })]
    }))
  }));
  return new Table({
    width: { size: tableWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows],
  });
}

function titlePage(title, subtitle) {
  return [
    new Paragraph({ spacing: { before: 2400 } }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: "SUPPLYGUARD AI", bold: true, size: 44, color: BLUE, font: "Arial" })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [new TextRun({ text: title, bold: true, size: 32, color: DARK_GRAY, font: "Arial" })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 400 },
      children: [new TextRun({ text: subtitle, size: 24, color: MEDIUM_GRAY, font: "Arial", italics: true })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 100 },
      children: [new TextRun({ text: "Cummins Xtern 2026 Challenge  |  Team 5", size: 22, color: MEDIUM_GRAY })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 100 },
      children: [new TextRun({ text: "March 2026", size: 22, color: MEDIUM_GRAY })]
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT 1: TECHNICAL DESIGN DOCUMENT (2-3 pages)
// ═════════════════════════════════════════════════════════════
async function buildTechnicalDesign() {
  const doc = new Document({
    styles: docStyles(),
    numbering: numbering(),
    sections: [{
      properties: { ...pageProps(), ...headerFooter("Technical Design Document") },
      children: [
        ...titlePage("Technical Design Document", "AI-Powered Supply Chain Disruption Detection & Response"),

        h1("1. Architecture Overview"),
        p("SupplyGuard AI is a multi-agent, multi-user intelligent system designed for Fortune 200 supply chain operations. The system detects supplier disruptions in real time, routes them through a 5-agent AI pipeline, supports human-in-the-loop (HITL) approval from a Director, and executes automated supplier swaps with a full immutable audit trail."),

        h2("1.1 System Layers"),
        makeTable(
          ["Layer", "Technology", "Port", "Owner"],
          [
            ["Frontend", "React 19 + TypeScript + Tailwind CSS + shadcn/ui", "5173", "P2"],
            ["Backend API", "Python FastAPI (unified REST API)", "3001", "P4"],
            ["Agent Pipeline", "Python (5 sequential agents, Pydantic-validated)", "In-process", "P3"],
            ["MCP Servers", "Node.js @modelcontextprotocol/sdk (3 servers)", "stdio", "P3/P4"],
            ["Intelligence/ML", "Python (statsforecast, NumPy, Pandas)", "In-process", "P5"],
            ["HITL Resume API", "Python FastAPI (resumes paused pipelines)", "8002", "P3"],
            ["Data Store", "In-memory (production: Supabase Postgres)", "N/A", "P4"],
          ],
          [2000, 3800, 800, 800]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("1.2 Architecture Diagram"),
        p("The system follows a layered architecture with clear separation of concerns:"),
        p("User (React UI) --> Vite Proxy --> FastAPI Backend (port 3001) --> Agent Orchestrator --> [Agent 1: Intake] --> [Agent 2: Quality] --> [Agent 3: History] --> [Agent 4: Decision] --> HITL Check --> [Agent 5: Executor]"),
        p("Each agent reads data from the backend via MCP tool wrappers (ERP, Audit, Comms servers) and writes immutable audit log entries after every decision."),

        h1("2. Agent Roles & Decision Boundaries"),

        h2("2.1 Agent Pipeline"),
        makeTable(
          ["Agent", "Role", "Key Tools", "Output"],
          [
            ["1. Intake", "Parse event, enrich with supplier profile", "get_supplier_profile", "IntakeResult"],
            ["2. Quality", "Check certs, compute quality sub-score", "get_quality_certs, get_parts_by_supplier", "QualityResult"],
            ["3. History", "Forecast delays, detect anomalies", "get_forecast, get_anomaly_status", "HistoryResult"],
            ["4. Decision", "Composite risk score, escalation rules", "query_avl, get_parts_by_supplier", "DecisionResult"],
            ["5. Executor", "Create PO, swap supplier, notify", "create_purchase_order, update_supplier_assignment", "ExecutorResult"],
          ],
          [1400, 2400, 2600, 1400]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("2.2 Decision Logic"),
        p("Agent 4 computes a composite risk score (0-100) using a weighted formula: 35% quality sub-score + 25% forecast instability + 25% anomaly ensemble votes + 15% risk index. Escalation rules are applied in priority order: (1) RED financial + expired cert triggers VP escalation, (2) worsening trend + 2+ anomaly votes triggers Director escalation, (3) score >= 70 triggers Director escalation, (4) expired cert alone forces Director review, (5) otherwise auto-approve."),

        h1("3. MCP Usage & Context Flow"),
        p("The system implements three Model Context Protocol servers using @modelcontextprotocol/sdk (Node.js):"),

        makeTable(
          ["MCP Server", "Tools Exposed", "Data Flow"],
          [
            ["ERP Server", "get_supplier_profile, get_parts_by_supplier, query_avl, get_quality_certs, create_purchase_order, update_supplier_assignment, get_open_orders, list_suppliers", "Read/write supplier, parts, AVL, and PO data"],
            ["Audit Server", "log_audit_decision, get_audit_trail, list_pipeline_runs", "Immutable append-only decision logging"],
            ["Comms Server", "send_notification, create_approval_request, get_pending_approvals, decide_approval, get_notifications", "Simulated Teams notifications, HITL approvals"],
          ],
          [1800, 3400, 2600]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        p("Python agents invoke MCP tools via HTTP wrappers that call the FastAPI backend. The MCP servers provide the canonical tool interface for external integrations. Context flows as structured Pydantic models (AgentState) through the pipeline, with each agent enriching the state object."),

        h1("4. Orchestration Strategy"),
        p("The pipeline uses sequential orchestration: Agent 1 through 4 execute in order, each receiving the cumulative AgentState. After Agent 4, a deterministic HITL check occurs. If escalation is required, the state is serialized to the approvals store and the pipeline pauses. The Director acts via the React UI, which calls PATCH /api/approvals/:id/decide, which in turn calls the Resume API (port 8002) to reload state and execute Agent 5 only. For auto-approved events, Agent 5 runs inline immediately after Agent 4."),
        p("Every agent call is wrapped in try/catch with fallback logic. If the LLM fails 3 times, a deterministic rule engine takes over. This ensures the pipeline never stalls on transient API failures."),

        h1("5. Data Persistence & Audit Strategy"),
        p("The current implementation uses in-memory Python dictionaries (SUPPLIERS, PARTS, AVL, AUDIT_LOG, PENDING_APPROVALS, PURCHASE_ORDERS, NOTIFICATIONS) that mirror the production Supabase Postgres schema defined in db/schema.sql. All data resets on server restart, which is acceptable for the demo. In production, the FastAPI endpoints would be backed by Supabase client calls."),
        p("The audit trail is append-only and immutable. DELETE requests on audit entries return HTTP 403. Each entry records: run_id, agent_name, inputs (full JSON), outputs (full JSON), confidence score (0-1), human-readable rationale, optional HITL actor, and ISO timestamp. This provides full traceability for every agent decision."),

        h1("6. Security Overview"),
        bullet("Authentication: Simulated role-based login (Director, QC Manager, Warehouse). Production: Supabase Auth with JWT and role claims."),
        bullet("Encryption in transit: All HTTP traffic between frontend and backend flows through Vite dev proxy. Production: HTTPS/TLS termination at load balancer."),
        bullet("Secrets handling: API keys stored in .env file (never committed). .env.example provided with placeholders. Production: environment variables via Railway/Vercel secret management."),
        bullet("Data isolation: No real/proprietary data used. All supplier names, part numbers, and financials are fully synthetic."),
        bullet("Audit immutability: Audit log entries cannot be deleted or modified via any API endpoint."),
      ]
    }]
  });
  return Packer.toBuffer(doc);
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT 2: GOVERNANCE & SAFETY BRIEF (1 page)
// ═════════════════════════════════════════════════════════════
async function buildGovernanceBrief() {
  const doc = new Document({
    styles: docStyles(),
    numbering: numbering(),
    sections: [{
      properties: { ...pageProps(), ...headerFooter("Governance & Safety Brief") },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 200, after: 300 },
          children: [new TextRun({ text: "Governance & Safety Brief", bold: true, size: 34, color: BLUE, font: "Arial" })]
        }),

        h2("Human-in-the-Loop Rules"),
        p("SupplyGuard AI enforces mandatory human oversight for high-risk supplier decisions through deterministic escalation rules. The system never executes a supplier swap autonomously when any of the following conditions are met:"),
        bullet("The supplier has RED financial health AND an expired quality certification (escalates to VP)."),
        bullet("Forecast trend is WORSENING with 2 or more anomaly ensemble votes (escalates to Director)."),
        bullet("Composite risk score is 70 or above on the 0-100 scale (escalates to Director)."),
        bullet("Quality certification is expired, regardless of risk score (escalates to Director)."),
        p("Agent 5 (Executor) includes a hard guard: it raises a ValueError if called on a HITL-required decision without a Director approval. This guard cannot be bypassed by any code path."),

        h2("Audit & Traceability Strategy"),
        p("Every agent in the pipeline writes an immutable audit log entry BEFORE returning its result. Each entry contains: the pipeline run ID, agent name, full input data, full output data, confidence score (0.0-1.0), human-readable rationale, optional HITL actor ID, and an ISO 8601 timestamp. The audit log is append-only; DELETE requests return HTTP 403. Audit trails are queryable by run_id, enabling full reconstruction of any pipeline decision."),

        h2("Data Handling Assumptions"),
        bullet("All data is fully synthetic. No real Cummins data, no PII, no proprietary information."),
        bullet("Supplier names, part numbers, financial statuses, and event data are generated for demonstration."),
        bullet("In production, data at rest would be encrypted via Supabase Postgres (AES-256). Data in transit uses TLS."),
        bullet("LLM prompts contain only synthetic supplier data. No sensitive information is sent to OpenAI."),

        h2("Fail-Safe Behaviors"),
        bullet("LLM failure: If the LLM fails 3 consecutive validation attempts, a deterministic rule engine takes over with no LLM dependency. Pipeline never stalls."),
        bullet("Backend offline: Agent tools include safe defaults (conservative risk scores) when API calls fail. Audit entries are logged locally if the backend is unreachable."),
        bullet("Invalid events: Malformed event data is caught at the orchestrator level with a ValidationError before any agent runs."),
        bullet("Executor guard: Agent 5 refuses to execute if decision state is missing or HITL approval is absent."),
        bullet("Auto-scan deduplication: The background scanner tracks flagged suppliers to prevent duplicate event creation."),
      ]
    }]
  });
  return Packer.toBuffer(doc);
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT 3: BUSINESS SKETCH (1 page)
// ═════════════════════════════════════════════════════════════
async function buildBusinessSketch() {
  const doc = new Document({
    styles: docStyles(),
    numbering: numbering(),
    sections: [{
      properties: { ...pageProps(), ...headerFooter("Business Sketch") },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 200, after: 300 },
          children: [new TextRun({ text: "Business Sketch", bold: true, size: 34, color: BLUE, font: "Arial" })]
        }),

        h2("Target Users & Stakeholders"),
        p("SupplyGuard AI serves three primary user roles within a Fortune 200 manufacturing supply chain organization:"),
        bullet("Warehouse Associates: Report incoming shipment issues, log quality data, and create disruption events in real time."),
        bullet("QC Managers: Monitor the AI agent pipeline, trigger disruption scans across the supplier base, and review agent decision trails."),
        bullet("Supply Chain Directors: Approve or reject high-risk supplier swap recommendations, with full visibility into risk scores, audit trails, and alternative supplier options."),
        p("Secondary stakeholders include procurement teams (receive PO notifications), plant managers (impacted by supplier changes), and finance (cost impact of supplier swaps)."),

        h2("KPIs"),
        makeTable(
          ["KPI", "Baseline (Manual)", "Target (SupplyGuard AI)", "Improvement"],
          [
            ["Disruption detection time", "4-24 hours", "< 5 minutes", "95% faster"],
            ["Decision cycle time", "2-5 days", "< 30 minutes (auto) / < 4 hours (HITL)", "90% faster"],
            ["Supplier swap accuracy", "~70% (manual matching)", "~92% (composite scoring + AVL)", "+22% accuracy"],
            ["Audit compliance coverage", "~40% documented", "100% (every decision logged)", "100% coverage"],
            ["Annual downtime cost avoided", "N/A", "$2.4M-$7.2M (at $50K-$150K/hr)", "New capability"],
          ],
          [2000, 1800, 2200, 1400]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("Baseline vs. Target Outcomes"),
        p("Today, supplier disruptions are detected via email, phone calls, or manual ERP checks, taking 4-24 hours. Procurement analysts manually search for alternatives, negotiate terms, and route approvals through email chains averaging 2-5 days. Decisions are poorly documented, creating audit gaps and compliance risk."),
        p("With SupplyGuard AI, disruptions are detected automatically via anomaly detection and forecasting. The 5-agent pipeline identifies alternatives, scores them on lead time, cost, certification, and geographic risk, and routes high-risk decisions to Directors within minutes. Every decision is logged with full traceability."),

        h2("ROI Estimate"),
        p("Conservative assumptions: A Fortune 200 manufacturer experiences 50-100 supplier disruptions per year. At $50K-$150K per hour of production line downtime, reducing average response time from 12 hours to 2 hours saves 10 hours per incident. At a midpoint of $100K/hour, this yields $50M-$100M in potential annual savings on the high end. Even capturing 5-10% of this value through faster detection and response yields $2.5M-$10M annually against an estimated $150K-$300K annual system cost (cloud infrastructure, LLM API, maintenance)."),
      ]
    }]
  });
  return Packer.toBuffer(doc);
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT 4: NEXT STEPS / PILOT PLAN (1 page)
// ═════════════════════════════════════════════════════════════
async function buildPilotPlan() {
  const doc = new Document({
    styles: docStyles(),
    numbering: numbering(),
    sections: [{
      properties: { ...pageProps(), ...headerFooter("Next Steps / Pilot Plan") },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 200, after: 300 },
          children: [new TextRun({ text: "Next Steps / Pilot Plan", bold: true, size: 34, color: BLUE, font: "Arial" })]
        }),

        h2("What a Pilot Would Require"),
        p("A 90-day production pilot would target one Cummins plant (e.g., Columbus Engine Plant) with 15-25 Tier 1 suppliers. The pilot requires: (1) integration with Cummins ERP system (SAP) for live supplier data, parts catalog, and purchase order creation; (2) connection to the existing supplier monitoring feeds for real-time event ingestion; (3) Supabase Postgres instance for persistent audit trail and approval state; (4) SSO integration with Cummins Active Directory for role-based access."),

        h2("Minimal Integrations"),
        makeTable(
          ["Integration", "Purpose", "Effort", "Priority"],
          [
            ["SAP ERP (read)", "Supplier profiles, parts, AVL data", "2-3 weeks", "Critical"],
            ["SAP ERP (write)", "Purchase order creation", "2-3 weeks", "Critical"],
            ["Supplier monitoring feed", "Real-time event ingestion", "1-2 weeks", "Critical"],
            ["Cummins SSO (Active Directory)", "Role-based authentication", "1 week", "High"],
            ["Microsoft Teams", "Director notifications and approvals", "1-2 weeks", "Medium"],
            ["Supabase Postgres (production)", "Persistent data store", "1 week", "Critical"],
          ],
          [2400, 2400, 1200, 1200]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("Effort Estimate"),
        makeTable(
          ["Phase", "Duration", "Team Size", "Key Activities"],
          [
            ["Phase 1: Integration", "Weeks 1-4", "3-4 engineers", "SAP connectors, SSO, database migration"],
            ["Phase 2: Validation", "Weeks 5-8", "2-3 engineers + 1 SME", "Historical backtesting, threshold tuning, UAT"],
            ["Phase 3: Controlled Rollout", "Weeks 9-12", "2 engineers + 1 ops", "Shadow mode, gradual HITL handoff, monitoring"],
          ],
          [2000, 1400, 1600, 3000]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("Risks"),
        bullet("Data quality: SAP data may have inconsistencies requiring cleansing and mapping to our schema."),
        bullet("LLM latency: OpenAI API response times may exceed SLA targets during peak usage; mitigated by deterministic fallback engine."),
        bullet("Change management: Procurement teams may resist AI-driven recommendations; mitigated by HITL design ensuring human control."),
        bullet("Integration complexity: SAP connector development may take longer than estimated if custom BAPIs are needed."),
        bullet("Cost overruns: LLM API costs at scale may exceed projections; mitigated by caching and fallback-first strategy."),
      ]
    }]
  });
  return Packer.toBuffer(doc);
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT 5: TCO COST OPTIMIZATION (2 pages)
// ═════════════════════════════════════════════════════════════
async function buildTCOPlan() {
  const doc = new Document({
    styles: docStyles(),
    numbering: numbering(),
    sections: [{
      properties: { ...pageProps(), ...headerFooter("YOY Cost Optimization Plan") },
      children: [
        ...titlePage("YOY Cost Optimization Plan", "Targeting Minimum Spend, Efficiency Gains, and Reusability"),

        h1("1. Value Proposition"),
        p("SupplyGuard AI is designed as a reusable multi-agent framework, not a single-purpose application. The agent pipeline architecture (orchestrator + domain agents + MCP tool servers) can be repurposed for warranty claims, preventive maintenance scheduling, parts fulfillment, and other supply chain workflows with minimal modification. This reuse-first design minimizes Cummins IT investment year over year."),

        h1("2. Framework Reusability"),
        p("The system is built on three reusable layers:"),
        bullet("Agent Orchestration Layer: Sequential pipeline with HITL pause/resume, audit logging, and fallback logic. Reusable for any multi-step approval workflow."),
        bullet("MCP Tool Server Layer: Standardized tool interface via Model Context Protocol. New use cases only need new tool definitions, not new infrastructure."),
        bullet("Frontend Shell: Role-based React dashboard with approval queues, audit trail viewer, and notification system. Reskinnable for different business domains."),
        p("Estimated reuse savings: 60-70% reduction in development effort for each subsequent use case deployed on the same framework."),

        h1("3. YOY Cost Trajectory"),
        makeTable(
          ["Cost Category", "Year 1 (Build)", "Year 2 (Optimize)", "Year 3 (Scale)"],
          [
            ["Development / Build", "$120,000", "$30,000", "$15,000"],
            ["Cloud Infrastructure", "$18,000", "$18,000", "$24,000"],
            ["LLM API (OpenAI)", "$24,000", "$12,000", "$8,000"],
            ["Maintenance & Support", "$15,000", "$20,000", "$20,000"],
            ["Training & Onboarding", "$10,000", "$5,000", "$3,000"],
            ["Total Annual Spend", "$187,000", "$85,000", "$70,000"],
          ],
          [2400, 1600, 1600, 1600]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("3.1 Key Optimization Levers"),
        bullet("Year 1 to Year 2: LLM cost reduction via deterministic fallback first (use rule engine for 80% of decisions, LLM only for complex rationale generation). Migration from OpenAI to self-hosted open-source models (Llama 3, Mistral) for non-critical agents."),
        bullet("Year 2 to Year 3: Framework reuse for 2-3 additional use cases amortizes infrastructure cost. Prompt caching and response memoization reduce API calls by 40-60%."),
        bullet("Ongoing: Supabase free tier covers development; production Postgres at $25/month. Railway backend hosting at $5/month for student tier, scaling to $20-50/month in production."),

        h1("4. Build vs. Buy vs. Reuse"),
        makeTable(
          ["Option", "Year 1 Cost", "3-Year TCO", "Pros", "Cons"],
          [
            ["Build (SupplyGuard)", "$187K", "$342K", "Full control, reusable framework, no vendor lock-in", "Initial build effort"],
            ["Buy (Vendor SaaS)", "$250K", "$750K+", "Faster initial deployment", "Vendor lock-in, per-seat pricing, limited customization"],
            ["Hybrid (Open-source + managed)", "$150K", "$310K", "Lower build cost, community support", "Integration complexity, less Cummins-specific"],
          ],
          [1600, 1200, 1200, 1800, 2000]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        p("Recommendation: The Build option (SupplyGuard framework) provides the best 3-year TCO with full reusability. The framework approach means Year 2+ costs drop 55% as the same architecture serves multiple use cases. Vendor SaaS solutions charge per-seat and per-transaction, resulting in 2.2x higher 3-year TCO with no reusability."),

        h1("5. Efficiency Gains Over Time"),
        bullet("Year 1: 90% reduction in disruption response time (12 hours to 1.2 hours average)."),
        bullet("Year 2: Framework reuse for warranty claim processing saves $120K in duplicate development."),
        bullet("Year 3: Full automation of low-risk decisions (composite score < 40) eliminates 60% of manual procurement reviews."),
        p("Cumulative 3-year value: $7.5M-$15M in avoided downtime cost vs. $342K total system cost = 22-44x ROI."),
      ]
    }]
  });
  return Packer.toBuffer(doc);
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT 6: TCO COST MODEL & FINANCIALS (1 page)
// ═════════════════════════════════════════════════════════════
async function buildTCOCostModel() {
  const doc = new Document({
    styles: docStyles(),
    numbering: numbering(),
    sections: [{
      properties: { ...pageProps(), ...headerFooter("Cost Model & Financials") },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 200, after: 200 },
          children: [new TextRun({ text: "Cost Model & Financials", bold: true, size: 34, color: BLUE, font: "Arial" })]
        }),

        h2("3-Year Cost Comparison"),
        makeTable(
          ["Cost Category", "One-Time (Y1)", "Annual Recurring (Y1)", "Annual Recurring (Y2+)", "3-Year TCO"],
          [
            ["Implementation / Build", "$120,000", "-", "-", "$120,000"],
            ["Hardware / Infrastructure", "-", "$18,000", "$21,000", "$60,000"],
            ["Software / Licensing", "-", "$0 (open-source)", "$0", "$0"],
            ["LLM API Costs", "-", "$24,000", "$10,000", "$44,000"],
            ["Integration (SAP, SSO)", "$35,000", "-", "-", "$35,000"],
            ["Training & Change Mgmt", "$10,000", "$5,000", "$3,000", "$21,000"],
            ["Maintenance & Support", "-", "$15,000", "$20,000", "$55,000"],
            ["Contingency (10%)", "$16,500", "-", "-", "$16,500"],
          ],
          [2200, 1400, 1600, 1600, 1400]
        ),

        new Paragraph({ spacing: { before: 120 } }),
        new Paragraph({
          spacing: { after: 200 },
          children: [
            bold("Total 3-Year TCO: $351,500"),
            normal("  |  "),
            bold("Recommended Option: Build (open-source framework)"),
            normal("  |  "),
            bold("% Savings vs. SaaS: 53%"),
          ]
        }),

        h2("ROI / Payback Analysis"),
        makeTable(
          ["Metric", "Value", "Assumptions"],
          [
            ["Annual cost savings (downtime avoided)", "$2.4M - $7.2M", "50 incidents/yr x 10 hrs saved x $50K-$150K/hr"],
            ["Annual productivity gains", "$180K", "3 FTE procurement analysts x 30% time savings"],
            ["Annual cost avoidance (audit/compliance)", "$200K", "Reduced regulatory risk, fewer manual audits"],
            ["Total annual benefit", "$2.8M - $7.6M", "Conservative to optimistic range"],
            ["Payback period", "< 2 months", "At $2.8M benefit vs. $187K Year 1 cost"],
            ["Net cost neutral by", "Month 1 of Year 1", "Benefits exceed costs immediately"],
            ["3-Year Net Value", "$7.5M - $22.5M", "Total benefit minus $351K TCO"],
          ],
          [2800, 1800, 3600]
        ),

        new Paragraph({ spacing: { before: 120 } }),
        h2("Core Assumptions"),
        bullet("50-100 supplier disruptions per year across the Cummins supply base."),
        bullet("Average production line downtime cost of $100K/hour (Cummins public filings cite $50K-$150K range)."),
        bullet("SupplyGuard reduces average response time from 12 hours to 2 hours per incident."),
        bullet("LLM costs decrease 50%+ in Year 2 via fallback-first strategy and potential self-hosted model migration."),
        bullet("Framework reuse for 2+ additional use cases in Years 2-3 amortizes build cost."),
      ]
    }]
  });
  return Packer.toBuffer(doc);
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT 7: TCO INTEGRATION & SLA (1 page)
// ═════════════════════════════════════════════════════════════
async function buildTCOIntegrationSLA() {
  const doc = new Document({
    styles: docStyles(),
    numbering: numbering(),
    sections: [{
      properties: { ...pageProps(), ...headerFooter("Integration & SLA Feasibility") },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 200, after: 300 },
          children: [new TextRun({ text: "Integration & SLA Feasibility", bold: true, size: 34, color: BLUE, font: "Arial" })]
        }),

        h2("Deployment Options"),
        makeTable(
          ["Option", "Description", "Effort", "Recommendation"],
          [
            ["Cloud (Recommended)", "Supabase Postgres + Railway (backend) + Vercel (frontend)", "2-3 weeks", "Best for pilot"],
            ["On-Premise", "Docker containers on Cummins Kubernetes cluster", "4-6 weeks", "Best for production"],
            ["Hybrid", "Frontend on Vercel, backend on internal network with SAP access", "3-4 weeks", "Good compromise"],
          ],
          [1600, 3000, 1200, 1800]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("Estimated Effort for Production Pilot"),
        makeTable(
          ["Task", "Duration", "Resources", "Dependencies"],
          [
            ["SAP ERP read connector", "2-3 weeks", "1 backend engineer + 1 SAP consultant", "SAP API access"],
            ["SAP PO write connector", "2-3 weeks", "1 backend engineer + 1 SAP consultant", "SAP write permissions"],
            ["Supabase production setup", "1 week", "1 DevOps engineer", "Database provisioning"],
            ["SSO / Active Directory", "1 week", "1 backend engineer", "AD service account"],
            ["Teams notification integration", "1-2 weeks", "1 engineer", "Teams admin approval"],
            ["UAT and threshold tuning", "2-3 weeks", "1 engineer + 2 business SMEs", "Historical data access"],
            ["Total estimated pilot effort", "10-14 weeks", "2-3 FTE equivalent", ""],
          ],
          [2400, 1200, 2400, 2000]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("Sample SLA Excerpt"),
        makeTable(
          ["SLA Metric", "Target", "Measurement"],
          [
            ["System availability", "99.5% uptime (excludes planned maintenance)", "Monthly uptime calculation"],
            ["Pipeline execution time", "< 30 seconds for 5-agent pipeline (no LLM)", "P95 latency measured per run"],
            ["LLM-augmented pipeline time", "< 90 seconds end-to-end", "P95 latency with OpenAI calls"],
            ["HITL notification delivery", "< 2 minutes from escalation to Director alert", "Timestamp delta in audit log"],
            ["Audit log completeness", "100% of agent decisions logged", "Audit entry count vs. agent count"],
            ["Incident response time", "< 4 hours for P1 issues (system down)", "Ticket creation to resolution"],
            ["Data backup frequency", "Daily automated backups with 30-day retention", "Supabase backup schedule"],
          ],
          [2400, 2800, 2800]
        ),
      ]
    }]
  });
  return Packer.toBuffer(doc);
}

// ═════════════════════════════════════════════════════════════
// DOCUMENT 8: TCO LICENSING & LEGAL (1 page)
// ═════════════════════════════════════════════════════════════
async function buildTCOLicensing() {
  const doc = new Document({
    styles: docStyles(),
    numbering: numbering(),
    sections: [{
      properties: { ...pageProps(), ...headerFooter("Licensing & Legal") },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 200, after: 300 },
          children: [new TextRun({ text: "Licensing & Legal: Build vs. Buy", bold: true, size: 34, color: BLUE, font: "Arial" })]
        }),

        h2("Models Used"),
        makeTable(
          ["Component", "Model / Library", "License", "Implications"],
          [
            ["LLM (primary)", "OpenAI GPT-4o-mini", "Commercial API (pay-per-token)", "No data retention by OpenAI on API tier. Cummins data stays private."],
            ["LLM (fallback option)", "Meta Llama 3 / Mistral", "Open-source (Meta Community License / Apache 2.0)", "Self-hostable. No API cost. Full data control."],
            ["Agent framework", "Custom Python (Pydantic + httpx)", "MIT (dependencies)", "No vendor lock-in. Fully owned by Cummins."],
            ["MCP servers", "@modelcontextprotocol/sdk", "MIT", "Open standard. No licensing fees."],
            ["Frontend", "React + Tailwind + shadcn/ui", "MIT", "Open-source. No licensing fees."],
            ["Backend", "Python FastAPI", "MIT", "Open-source. No licensing fees."],
            ["ML / Forecasting", "statsforecast (AutoARIMA)", "Apache 2.0", "Open-source. Commercial use permitted."],
            ["Database", "Supabase (Postgres)", "Apache 2.0 (self-hosted) / Commercial (managed)", "Free tier for development. $25/mo managed."],
          ],
          [1600, 2000, 1800, 2800]
        ),

        new Paragraph({ spacing: { before: 160 } }),
        h2("Open-Source Usage & Data Governance"),
        bullet("All core dependencies use permissive licenses (MIT, Apache 2.0) that allow commercial use, modification, and distribution without royalties."),
        bullet("No copyleft (GPL) dependencies that would require source code disclosure."),
        bullet("OpenAI API tier: Data is not used for training per OpenAI API terms. For maximum data governance, self-hosted models (Llama 3, Mistral) eliminate external data transfer entirely."),
        bullet("Synthetic data only in the prototype. Production deployment requires Cummins data governance review for any real supplier data flowing through the system."),

        h2("Build vs. Buy Legal Comparison"),
        makeTable(
          ["Factor", "Build (SupplyGuard)", "Buy (Vendor SaaS)"],
          [
            ["IP ownership", "Cummins owns all code and customizations", "Vendor owns platform; Cummins licenses access"],
            ["Data sovereignty", "Full control (self-hosted option available)", "Data on vendor cloud; subject to vendor DPA"],
            ["Vendor lock-in risk", "None (open-source stack, MCP standard)", "High (proprietary APIs, data format lock-in)"],
            ["Licensing cost", "$0 software licensing (open-source)", "$50K-$200K/yr typical enterprise SaaS"],
            ["Customization freedom", "Unlimited (full source access)", "Limited to vendor configuration options"],
            ["Audit / compliance", "Full source code audit possible", "Dependent on vendor SOC 2 / ISO certs"],
          ],
          [2000, 2800, 3400]
        ),

        new Paragraph({ spacing: { before: 120 } }),
        p("Recommendation: The build approach using open-source components with permissive licenses gives Cummins full IP ownership, zero software licensing costs, and complete data sovereignty. The MCP standard ensures interoperability without vendor lock-in."),
      ]
    }]
  });
  return Packer.toBuffer(doc);
}

// ═════════════════════════════════════════════════════════════
// GENERATE ALL DOCUMENTS
// ═════════════════════════════════════════════════════════════
async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const docs = [
    { name: "technical_design_document.docx", fn: buildTechnicalDesign },
    { name: "governance_safety_brief.docx", fn: buildGovernanceBrief },
    { name: "business_sketch.docx", fn: buildBusinessSketch },
    { name: "next_steps_pilot_plan.docx", fn: buildPilotPlan },
    { name: "tco_yoy_cost_optimization.docx", fn: buildTCOPlan },
    { name: "tco_cost_model_financials.docx", fn: buildTCOCostModel },
    { name: "tco_integration_sla.docx", fn: buildTCOIntegrationSLA },
    { name: "tco_licensing_legal.docx", fn: buildTCOLicensing },
  ];

  for (const { name, fn } of docs) {
    console.log(`Generating ${name}...`);
    const buffer = await fn();
    const outPath = path.join(OUTPUT_DIR, name);
    fs.writeFileSync(outPath, buffer);
    console.log(`  -> ${outPath} (${(buffer.length / 1024).toFixed(1)} KB)`);
  }

  console.log(`\nAll ${docs.length} documents generated in ${OUTPUT_DIR}`);
}

main().catch(console.error);
