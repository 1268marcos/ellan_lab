/**
 * Sprint 2 D11 — agregação por order_id para fila P0 (conciliação pedido → documento).
 * Aceita linhas no formato exportado por ops/fiscal/providers (`buildGapExportRows`).
 */

/**
 * @param {Array<Record<string, unknown>>} rows
 * @returns {{ scope: string; generated_at: string; source_rows: number; unique_orders_with_gaps: number; orders: Array<{ order_id: string; gap_count: number; by_severity: Record<string, number>; gap_types: string[] }> }}
 */
export function buildD11OrderIdRollupFromGapRows(rows) {
  const generatedAt = new Date().toISOString();
  const list = Array.isArray(rows) ? rows : [];
  /** @type {Map<string, { order_id: string; gap_count: number; by_severity: Record<string, number>; gap_types: Set<string> }>} */
  const byOrder = new Map();

  for (const row of list) {
    const oid = String(row?.order_id ?? "").trim();
    if (!oid) continue;
    let entry = byOrder.get(oid);
    if (!entry) {
      entry = { order_id: oid, gap_count: 0, by_severity: {}, gap_types: new Set() };
      byOrder.set(oid, entry);
    }
    entry.gap_count += 1;
    const sev = String(row?.severity ?? "UNKNOWN").toUpperCase();
    entry.by_severity[sev] = (entry.by_severity[sev] || 0) + 1;
    const gt = String(row?.gap_type ?? "").trim();
    if (gt) entry.gap_types.add(gt);
  }

  const orders = [...byOrder.values()]
    .map((e) => ({
      order_id: e.order_id,
      gap_count: e.gap_count,
      by_severity: { ...e.by_severity },
      gap_types: [...e.gap_types].sort(),
    }))
    .sort((a, b) => b.gap_count - a.gap_count || a.order_id.localeCompare(b.order_id));

  return {
    scope: "SPRINT2_D11_ORDER_ID_ROLLUP",
    generated_at: generatedAt,
    source_rows: list.length,
    unique_orders_with_gaps: orders.length,
    orders,
  };
}
