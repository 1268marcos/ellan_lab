
/**
 * D15 / D16 / D17 helpers: accounting approval snapshots, compare, retention, divergence health.
 */

export async function fetchConsolidatedAccountingApprovals({
  billingBase,
  getHeaders,
  filters = {},
  pageSize = 200,
}) {
  const owner = String(filters.owner || "").trim();
  const status = String(filters.status || "").trim();
  const dateFrom = String(filters.date_from || "").trim();
  const dateTo = String(filters.date_to || "").trim();

  const items = [];
  let offset = 0;
  let total = 0;

  for (;;) {
    const params = new URLSearchParams({
      limit: String(Math.min(Math.max(pageSize, 1), 500)),
      offset: String(offset),
    });
    if (owner) params.set("owner", owner);
    if (status) params.set("status", status);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);

    const r = await fetch(`${billingBase}/admin/fiscal/accounting-approvals?${params.toString()}`, {
      method: "GET",
      headers: getHeaders(),
    });
    const payload = await r.json().catch(() => ({}));
    if (!r.ok) {
      throw new Error(String(payload?.detail || "Falha ao carregar histórico de aceites."));
    }
    const batch = Array.isArray(payload?.items) ? payload.items : [];
    total = Number(payload?.total ?? batch.length);
    items.push(...batch);
    offset += batch.length;
    if (batch.length === 0 || offset >= total) break;
  }

  return {
    items,
    total,
    filters: { owner: owner || null, status: status || null, date_from: dateFrom || null, date_to: dateTo || null },
  };
}

export async function fetchAccountingApprovalsDivergenceHealth({
  billingBase,
  getHeaders,
  window = 8,
  prolongedEdges = 3,
}) {
  const params = new URLSearchParams();
  params.set("window", String(Math.min(Math.max(Number(window) || 8, 3), 30)));
  params.set("prolonged_edges", String(Math.min(Math.max(Number(prolongedEdges) || 3, 2), 15)));
  const r = await fetch(`${billingBase}/admin/fiscal/accounting-approvals/divergence-health?${params.toString()}`, {
    method: "GET",
    headers: getHeaders(),
  });
  const payload = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(String(payload?.detail || "Falha ao carregar divergence-health D17."));
  }
  return payload;
}

export async function postAccountingApprovalsRetention({ billingBase, getHeaders, body }) {
  const r = await fetch(`${billingBase}/admin/fiscal/accounting-approvals/retention`, {
    method: "POST",
    headers: { ...getHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body && typeof body === "object" ? body : {}),
  });
  const payload = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(String(payload?.detail || "Falha na política de retenção D17."));
  }
  return payload;
}

export async function fetchAccountingApprovalsCompare({ billingBase, getHeaders, currentId = "", previousId = "" }) {
  const params = new URLSearchParams();
  if (String(currentId || "").trim()) params.set("current_id", String(currentId).trim());
  if (String(previousId || "").trim()) params.set("previous_id", String(previousId).trim());
  const qs = params.toString();
  const url = `${billingBase}/admin/fiscal/accounting-approvals/compare${qs ? `?${qs}` : ""}`;
  const r = await fetch(url, { method: "GET", headers: getHeaders() });
  const payload = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(String(payload?.detail || "Falha ao comparar snapshots de aceite."));
  }
  return payload;
}

export function accountingApprovalsToCsvRows(items) {
  const headers = ["id", "owner", "status", "eta", "created_at", "approval_notes_preview"];
  const rows = (Array.isArray(items) ? items : []).map((row) => {
    const payload = row?.payload_json && typeof row.payload_json === "object" ? row.payload_json : {};
    const approval = payload?.approval && typeof payload.approval === "object" ? payload.approval : {};
    const notes = String(approval?.notes || "").replaceAll("\n", " ").slice(0, 200);
    return [
      String(row?.id || ""),
      String(row?.owner || ""),
      String(row?.status || ""),
      String(row?.eta || ""),
      String(row?.created_at || ""),
      notes,
    ];
  });
  return { headers, rows };
}

export function buildAccountingApprovalsCsv({ headers, rows }) {
  const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  return [headers.join(","), ...rows.map((cells) => cells.map(esc).join(","))].join("\n");
}

