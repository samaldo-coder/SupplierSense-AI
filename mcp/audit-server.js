/**
 * SupplyGuard AI — Audit Trail MCP Server
 * Model Context Protocol server for immutable agent decision logging.
 * All writes go through the FastAPI backend at localhost:3001.
 *
 * Start: node mcp/audit-server.js
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const BACKEND_URL = process.env.BACKEND_API_URL || "http://localhost:3001";

async function fetchJSON(path, options = {}) {
  const url = `${BACKEND_URL}${path}`;
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
  return resp.json();
}

const server = new McpServer({
  name: "supplyguard-audit",
  version: "1.0.0",
  description:
    "Immutable audit trail for SupplyGuard AI agent decisions. Supports logging and querying.",
});

// ─── Tool: log_audit_decision ───────────────────────────────
server.tool(
  "log_audit_decision",
  "Immutably log an agent decision to the audit trail. Returns { entry_id }. Cannot be deleted.",
  {
    run_id: z.string().describe("Pipeline run ID"),
    agent_name: z
      .string()
      .describe(
        "Name of the agent: intake_agent, quality_agent, supplier_history_agent, decision_agent, executor_agent"
      ),
    inputs: z
      .record(z.unknown())
      .describe("Input data the agent received (JSON object)"),
    outputs: z
      .record(z.unknown())
      .describe("Output data the agent produced (JSON object)"),
    confidence: z
      .number()
      .min(0)
      .max(1)
      .describe("Agent confidence score 0.0-1.0"),
    rationale: z
      .string()
      .describe("Human-readable explanation of the decision"),
    hitl_actor: z
      .string()
      .optional()
      .describe("Director user ID if HITL approval was involved"),
  },
  async ({ run_id, agent_name, inputs, outputs, confidence, rationale, hitl_actor }) => {
    const data = await fetchJSON("/api/audit", {
      method: "POST",
      body: JSON.stringify({
        run_id,
        agent_name,
        inputs,
        outputs,
        confidence,
        rationale,
        hitl_actor: hitl_actor || null,
      }),
    });
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: get_audit_trail ──────────────────────────────────
server.tool(
  "get_audit_trail",
  "Fetch the full ordered audit trail for a pipeline run. Returns array of audit entries.",
  { run_id: z.string().describe("Pipeline run ID to query") },
  async ({ run_id }) => {
    const data = await fetchJSON(`/api/audit/${run_id}`);
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: list_pipeline_runs ───────────────────────────────
server.tool(
  "list_pipeline_runs",
  "List all distinct pipeline runs with their completed agents and timestamps",
  {},
  async () => {
    const data = await fetchJSON("/api/pipeline/runs");
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Resource: recent audit entries ─────────────────────────
server.resource(
  "recent-audits",
  "supplyguard://audit/recent",
  async (uri) => {
    const runs = await fetchJSON("/api/pipeline/runs");
    return {
      contents: [
        {
          uri: uri.href,
          mimeType: "application/json",
          text: JSON.stringify(runs, null, 2),
        },
      ],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("SupplyGuard Audit MCP Server running on stdio");
