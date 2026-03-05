/**
 * SupplyGuard AI — ERP MCP Server
 * Model Context Protocol server exposing supplier, parts, AVL, and PO tools.
 * Reads/writes to the FastAPI backend at localhost:3001.
 *
 * Start: node mcp/erp-server.js
 * Transport: stdio (for agent integration) or SSE (for web clients)
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
  name: "supplyguard-erp",
  version: "1.0.0",
  description:
    "ERP data tools for SupplyGuard AI: suppliers, parts, AVL, purchase orders",
});

// ─── Tool: get_supplier_profile ─────────────────────────────
server.tool(
  "get_supplier_profile",
  "Fetch full supplier record: name, country, tier, financial_health, lead_time_days, unit_cost, is_active, certs",
  { supplier_id: z.string().describe("UUID of the supplier") },
  async ({ supplier_id }) => {
    const data = await fetchJSON(`/api/suppliers/${supplier_id}`);
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: get_parts_by_supplier ────────────────────────────
server.tool(
  "get_parts_by_supplier",
  "Get all parts where this supplier is the primary source",
  { supplier_id: z.string().describe("UUID of the supplier") },
  async ({ supplier_id }) => {
    const data = await fetchJSON(`/api/parts?supplier_id=${supplier_id}`);
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: query_avl ────────────────────────────────────────
server.tool(
  "query_avl",
  "Return all approved vendor list entries for a part, including lead_time, cost, cert, geo_risk",
  { part_id: z.string().describe("UUID of the part") },
  async ({ part_id }) => {
    const data = await fetchJSON(`/api/avl/${part_id}`);
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: get_quality_certs ────────────────────────────────
server.tool(
  "get_quality_certs",
  "Get quality cert type, expiry date, and validity for a supplier",
  { supplier_id: z.string().describe("UUID of the supplier") },
  async ({ supplier_id }) => {
    const data = await fetchJSON(`/api/suppliers/${supplier_id}/certs`);
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: create_purchase_order ────────────────────────────
server.tool(
  "create_purchase_order",
  "Create a new purchase order record. Returns { po_id }",
  {
    supplier_id: z.string().describe("UUID of the supplier"),
    part_id: z.string().describe("UUID of the part"),
    quantity: z.number().int().positive().describe("Order quantity"),
    approved_by: z.string().describe("User ID of approver"),
  },
  async ({ supplier_id, part_id, quantity, approved_by }) => {
    const data = await fetchJSON("/api/purchase-orders", {
      method: "POST",
      body: JSON.stringify({ supplier_id, part_id, quantity, approved_by }),
    });
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: update_supplier_assignment ───────────────────────
server.tool(
  "update_supplier_assignment",
  "Update the primary supplier for a part (supplier swap)",
  {
    part_id: z.string().describe("UUID of the part"),
    new_supplier_id: z.string().describe("UUID of the new primary supplier"),
  },
  async ({ part_id, new_supplier_id }) => {
    const data = await fetchJSON(`/api/parts/${part_id}/supplier`, {
      method: "POST",
      body: JSON.stringify({ new_supplier_id }),
    });
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: get_open_orders ──────────────────────────────────
server.tool(
  "get_open_orders",
  "Fetch all open production orders with factory and part details",
  {},
  async () => {
    const data = await fetchJSON("/api/orders?status=OPEN");
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Tool: list_suppliers ───────────────────────────────────
server.tool(
  "list_suppliers",
  "List all suppliers with full profiles",
  {},
  async () => {
    const data = await fetchJSON("/api/suppliers");
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// ─── Resource: supplier list ────────────────────────────────
server.resource("suppliers", "supplyguard://suppliers", async (uri) => {
  const data = await fetchJSON("/api/suppliers");
  return {
    contents: [
      {
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify(data, null, 2),
      },
    ],
  };
});

// ─── Start server ───────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("SupplyGuard ERP MCP Server running on stdio");
