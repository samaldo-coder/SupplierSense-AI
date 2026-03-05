/**
 * SupplyGuard AI — Comms MCP Server
 * Model Context Protocol server for notifications and approvals.
 * Simulates Microsoft Teams (writes to DB via FastAPI backend).
 *
 * Start: node mcp/comms-server.js
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
  name: "supplyguard-comms",
  version: "1.0.0",
  description:
    "Notifications, approvals, and simulated Teams comms for SupplyGuard AI",
});

// ─── Tool: send_notification ────────────────────────────────
server.tool(
  "send_notification",
  "Send a notification to a user role (simulated Teams message, persisted to DB)",
  {
    recipient_role: z
      .enum(["procurement", "director", "qc_manager", "warehouse"])
      .describe("Target user role"),
    message: z.string().describe("Notification message body"),
    notification_type: z
      .enum([
        "info",
        "approval_required",
        "po_created",
        "execution_complete",
        "po_confirmation",
        "disruption_alert",
      ])
      .describe("Type of notification"),
    run_id: z.string().optional().describe("Associated pipeline run ID"),
    supplier_id: z.string().optional().describe("Related supplier UUID"),
    po_id: z.string().optional().describe("Related purchase order ID"),
  },
  async ({
    recipient_role,
    message,
    notification_type,
    run_id,
    supplier_id,
    po_id,
  }) => {
    const data = await fetchJSON("/api/comms/notify", {
      method: "POST",
      body: JSON.stringify({
        recipient_role,
        message,
        type: notification_type,
        run_id: run_id || null,
        supplier_id: supplier_id || null,
        po_id: po_id || null,
      }),
    });
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: create_approval_request ──────────────────────────
server.tool(
  "create_approval_request",
  "Create a pending HITL approval request for the Director. Pauses the pipeline until decided.",
  {
    run_id: z.string().describe("Pipeline run ID"),
    state_json: z
      .record(z.unknown())
      .describe("Full AgentState serialized as JSON"),
    summary: z.string().describe("Human-readable summary for the Director"),
    recommended_supplier_id: z
      .string()
      .optional()
      .describe("Recommended alternative supplier UUID"),
  },
  async ({ run_id, state_json, summary, recommended_supplier_id }) => {
    const data = await fetchJSON("/api/approvals", {
      method: "POST",
      body: JSON.stringify({
        run_id,
        state_json,
        summary,
        recommended_supplier_id: recommended_supplier_id || null,
      }),
    });
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: get_pending_approvals ────────────────────────────
server.tool(
  "get_pending_approvals",
  "List all pending HITL approval requests awaiting Director decision",
  {},
  async () => {
    const data = await fetchJSON("/api/approvals?status=PENDING");
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: decide_approval ──────────────────────────────────
server.tool(
  "decide_approval",
  "Director approves or rejects a pending approval. Triggers Agent 5 (executor) on approval.",
  {
    approval_id: z.string().describe("UUID of the pending approval"),
    decision: z.enum(["approved", "rejected"]).describe("Director decision"),
    note: z.string().describe("Director note explaining the decision"),
    director_id: z.string().describe("Director user ID"),
  },
  async ({ approval_id, decision, note, director_id }) => {
    const data = await fetchJSON(`/api/approvals/${approval_id}/decide`, {
      method: "PATCH",
      body: JSON.stringify({ decision, note, director_id }),
    });
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: get_notifications ────────────────────────────────
server.tool(
  "get_notifications",
  "List notifications for a role, optionally only unread ones",
  {
    role: z
      .enum(["procurement", "director", "qc_manager", "warehouse"])
      .optional()
      .describe("Filter by role"),
    unread_only: z.boolean().optional().describe("Only unread notifications"),
  },
  async ({ role, unread_only }) => {
    const params = new URLSearchParams();
    if (role) params.set("role", role);
    if (unread_only) params.set("unread_only", "true");
    const data = await fetchJSON(`/api/notifications?${params}`);
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("SupplyGuard Comms MCP Server running on stdio");
