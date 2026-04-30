/**
 * Sprint 3 P0-1b: anexos auditáveis ao pacote diário único — trilha E2E (4 chaves)
 * + consolidação por partner_id para reconciliação/handoff.
 */

/**
 * @param {object} params
 * @param {object} params.e2ePayload Resposta JSON de GET /admin/fiscal/global/sprint3/e2e-audit-trail
 * @param {object | null} params.d11Handoff Snapshot localStorage D11 (opcional)
 * @param {string} params.generatedAt ISO
 * @param {string} params.source ex.: fiscal/management-daily | ops/health
 */
export function buildP01bPartnerReconciliationSlice({ e2ePayload, d11Handoff, generatedAt, source }) {
  const items = Array.isArray(e2ePayload?.items) ? e2ePayload.items : [];
  /** @type {Map<string, { partner_id: string, gap_rows: number, batches: Set<string>, materialized_complete: number, raw_complete: number, severities: Record<string, number> }>} */
  const byPartner = new Map();

  for (const it of items) {
    const pid = String(it?.trace?.partner_id || "UNKNOWN_PARTNER");
    const batch = String(it?.trace?.batch_id || "").trim();
    let cur = byPartner.get(pid);
    if (!cur) {
      cur = {
        partner_id: pid,
        gap_rows: 0,
        batches: new Set(),
        materialized_complete: 0,
        raw_complete: 0,
        severities: {},
      };
      byPartner.set(pid, cur);
    }
    cur.gap_rows += 1;
    if (batch) cur.batches.add(batch);
    if (it?.trace_quality?.materialized_complete) cur.materialized_complete += 1;
    if (it?.trace_quality?.raw_complete) cur.raw_complete += 1;
    const sev = String(it?.severity || "UNK").toUpperCase();
    cur.severities[sev] = (cur.severities[sev] || 0) + 1;
  }

  const MAX_BATCHES_PER_PARTNER = 80;
  const partners = Array.from(byPartner.values())
    .map((p) => ({
      partner_id: p.partner_id,
      gap_rows: p.gap_rows,
      batches: Array.from(p.batches).slice(0, MAX_BATCHES_PER_PARTNER),
      batches_truncated: p.batches.size > MAX_BATCHES_PER_PARTNER,
      materialized_complete: p.materialized_complete,
      raw_complete: p.raw_complete,
      severities: p.severities,
    }))
    .sort((a, b) => b.gap_rows - a.gap_rows);

  const d11Cross =
    d11Handoff && typeof d11Handoff === "object"
      ? {
          storage_unique_partners: Number(d11Handoff?.summary?.unique_partners || 0),
          storage_unique_batches: Number(d11Handoff?.summary?.unique_batches || 0),
          storage_total_items: Number(d11Handoff?.summary?.total_items || 0),
          e2e_distinct_partners: byPartner.size,
          note:
            "D11 é snapshot em localStorage (gerado em ops/fiscal/providers). E2E vem de fiscal_reconciliation_gaps no billing — cruzar para handoff único.",
        }
      : null;

  return {
    scope: "SPRINT3_P0_1B_PARTNER_RECONCILIATION_SLICE",
    slice_version: "p0-1b-v1",
    generated_at: generatedAt,
    source,
    mandatory_trace_keys: ["order_id", "invoice_id", "partner_id", "batch_id"],
    e2e_coverage_ref: {
      decision: e2ePayload?.decision ?? null,
      materialized_rate: e2ePayload?.coverage?.materialized_rate ?? null,
      raw_rate: e2ePayload?.coverage?.raw_rate ?? null,
      total: e2ePayload?.coverage?.total ?? null,
      handoff_evidence_id: e2ePayload?.handoff_evidence?.evidence_id ?? null,
    },
    partners,
    d11_cross_check: d11Cross,
  };
}

/**
 * Anexa ao mapa do ZIP (mutação) JSONs assinados: trilha E2E completa + fatia por parceiro.
 * @param {object} opts
 * @param {string} opts.billingBase
 * @param {() => Record<string, string>} opts.getHeaders
 * @param {(p: object) => Promise<object>} opts.buildSignedPayload mesma função SHA-256 das páginas FISCAL/OPS
 * @param {(s: string) => Uint8Array} opts.strToU8
 * @param {string} opts.fileBasePrefix ex.: ELLAN_FISCAL_DAILY_20260430
 * @param {string} opts.ts timestamp file-safe
 * @param {string} opts.nowIso
 * @param {object | null} opts.d11Handoff
 * @param {string} opts.source
 * @param {Record<string, Uint8Array>} opts.zipEntries
 * @param {number} [opts.e2eLimit]
 */
export async function appendP01bSignedZipEntries({
  billingBase,
  getHeaders,
  buildSignedPayload,
  strToU8,
  fileBasePrefix,
  ts,
  nowIso,
  d11Handoff,
  source,
  zipEntries,
  e2eLimit = 500,
}) {
  const url = `${billingBase.replace(/\/$/, "")}/admin/fiscal/global/sprint3/e2e-audit-trail?status=OPEN&limit=${encodeURIComponent(String(e2eLimit))}`;
  let res;
  try {
    res = await fetch(url, { method: "GET", headers: getHeaders() });
  } catch (err) {
    const signedErr = await buildSignedPayload({
      scope: "SPRINT3_P0_1B_E2E_ATTACH_ERROR",
      generated_at: nowIso,
      source,
      error: `network: ${String(err?.message || err)}`,
    });
    zipEntries[`${fileBasePrefix}_P0_1B_E2E_AUDIT_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
    return;
  }

  const e2e = await res.json().catch(() => ({}));
  if (!res.ok) {
    const signedErr = await buildSignedPayload({
      scope: "SPRINT3_P0_1B_E2E_ATTACH_ERROR",
      generated_at: nowIso,
      source,
      http_status: res.status,
      error: String(e2e?.detail || e2e?.message || "e2e-audit-trail failed"),
    });
    zipEntries[`${fileBasePrefix}_P0_1B_E2E_AUDIT_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
    return;
  }

  const signedE2e = await buildSignedPayload(e2e);
  zipEntries[`${fileBasePrefix}_SPRINT3_E2E_AUDIT_TRAIL_${ts}.json`] = strToU8(JSON.stringify(signedE2e, null, 2));

  const slice = buildP01bPartnerReconciliationSlice({
    e2ePayload: e2e,
    d11Handoff,
    generatedAt: nowIso,
    source,
  });
  const signedSlice = await buildSignedPayload(slice);
  zipEntries[`${fileBasePrefix}_P0_1B_PARTNER_RECONCILIATION_${ts}.json`] = strToU8(JSON.stringify(signedSlice, null, 2));
}
