// Artefactos Sprint 2 — D12 (handoff contábil ligado ao D11) e D13 (aceite) com nomes `SPRINT2_*`
// alinhados ao padrão de evidência do D11 (`SPRINT2_D11_ORDER_ID_ROLLUP*`).

import { buildD11OrderIdRollupFromGapRows } from "./fiscalD11OrderIdRollup";

/**
 * @param {object} opts
 * @param {string} opts.generatedAt ISO
 * @param {string} opts.source rota ou página geradora
 * @param {object|null} opts.stubReadiness payload FG-1 stub-wave-readiness
 * @param {object|null} [opts.catalog] opcional — contagens de catálogo global
 * @param {object|null} [opts.matrix] opcional — matriz de cenários
 * @param {object|null} [opts.d11Handoff] lote publicado em ops/fiscal/providers (localStorage)
 */
export function buildSprint2D12AccountingHandoffEvidence({
  generatedAt,
  source,
  stubReadiness,
  catalog = null,
  matrix = null,
  d11Handoff = null,
}) {
  const decision = String(stubReadiness?.decision || "NO_GO").toUpperCase();
  const readinessChecks = Array.isArray(stubReadiness?.checks) ? stubReadiness.checks : [];
  const passedChecks = readinessChecks.filter((c) => String(c?.status || "").toUpperCase() === "PASS").length;
  const failedChecks = Math.max(readinessChecks.length - passedChecks, 0);
  const countriesNotReady = Number(stubReadiness?.countries_not_ready || 0);
  const riskLevel = decision === "GO" ? "LOW" : countriesNotReady >= 2 ? "HIGH" : "MEDIUM";

  let d11_fiscal_gap_handoff = null;
  if (d11Handoff && typeof d11Handoff === "object") {
    const embedded = d11Handoff.order_id_rollup;
    const items = Array.isArray(d11Handoff.items) ? d11Handoff.items : [];
    const d11OrderIdRollup =
      embedded && typeof embedded === "object" && Array.isArray(embedded.orders)
        ? embedded
        : buildD11OrderIdRollupFromGapRows(items);

    d11_fiscal_gap_handoff = {
      generated_at: String(d11Handoff?.generated_at || "-"),
      total_items: Number(d11Handoff?.summary?.total_items || 0),
      severity: d11Handoff?.summary?.severity || {},
      unique_partners: Number(d11Handoff?.summary?.unique_partners || 0),
      unique_batches: Number(d11Handoff?.summary?.unique_batches || 0),
      unique_orders_with_gaps: Number(
        d11Handoff?.summary?.unique_orders_with_gaps ?? d11OrderIdRollup?.unique_orders_with_gaps ?? 0,
      ),
      filters: d11Handoff?.filters || {},
      order_id_rollup_summary: d11OrderIdRollup
        ? {
            scope: d11OrderIdRollup.scope,
            generated_at: d11OrderIdRollup.generated_at,
            unique_orders_with_gaps: d11OrderIdRollup.unique_orders_with_gaps,
            top_orders: d11OrderIdRollup.orders.slice(0, 15),
          }
        : null,
    };
  }

  return {
    scope: "SPRINT2_D12_ACCOUNTING_HANDOFF",
    generated_at: generatedAt,
    source: String(source || "fiscal/management-daily"),
    fiscal_context: {
      scope: "FISCAL_MANAGEMENT_DAILY_SNAPSHOT",
      decision_consolidated: decision,
      risk_level: riskLevel,
      checks_pass: `${passedChecks}/${readinessChecks.length}`,
      checks_failed: failedChecks,
      reference: {
        readiness_version: String(stubReadiness?.readiness_version || "-"),
        catalog_count: Number(catalog?.count || 0),
        scenario_matrix_count: Number(matrix?.count || 0),
        countries_not_ready: countriesNotReady,
      },
    },
    d11_fiscal_gap_handoff,
  };
}

/**
 * Envelope Sprint 2 para export/ZIP sem alterar o corpo enviado ao POST `/accounting-approvals`.
 * @param {object} innerPayload resultado de `buildAccountingApprovalPayload` (management-daily)
 */
export function wrapSprint2D13AccountingAcceptance(innerPayload, generatedAt, source) {
  if (!innerPayload || typeof innerPayload !== "object") {
    throw new Error("wrapSprint2D13AccountingAcceptance: innerPayload inválido");
  }
  return {
    scope: "SPRINT2_D13_ACCOUNTING_ACCEPTANCE",
    generated_at: generatedAt,
    source: String(source || "fiscal/management-daily"),
    fiscal_accounting_daily_approval: innerPayload,
  };
}

/**
 * Corpo `FISCAL_ACCOUNTING_DAILY_APPROVAL` para o ZIP executivo em `fiscal/accounting-close`
 * (rascunho local + stub FG-1 + opcional lote D11), alinhado ao envio do management-daily.
 */
export function buildExecutiveAccountingApprovalInnerForClose({
  nowIso,
  gateDecision,
  stubReadiness,
  passedChecks,
  readinessChecksLength,
  failedChecks,
  approvalDraft,
  d11Snapshot,
}) {
  const decision = String(gateDecision || "NO_GO").toUpperCase();
  const countriesNotReady = Number(stubReadiness?.countries_not_ready || 0);
  const riskLevel = decision === "GO" ? "LOW" : countriesNotReady >= 2 ? "HIGH" : "MEDIUM";

  let d11_total = 0;
  let d11_gen = "-";
  let d11_unique_orders = 0;
  if (d11Snapshot && typeof d11Snapshot === "object") {
    d11_total = Number(d11Snapshot?.summary?.total_items || 0);
    d11_gen = String(d11Snapshot?.generated_at || "-");
    const embedded = d11Snapshot.order_id_rollup;
    const items = Array.isArray(d11Snapshot.items) ? d11Snapshot.items : [];
    const rollup =
      embedded && typeof embedded === "object" && Array.isArray(embedded.orders)
        ? embedded
        : buildD11OrderIdRollupFromGapRows(items);
    d11_unique_orders = Number(d11Snapshot?.summary?.unique_orders_with_gaps ?? rollup?.unique_orders_with_gaps ?? 0);
  }

  return {
    scope: "FISCAL_ACCOUNTING_DAILY_APPROVAL",
    generated_at: nowIso,
    approval: {
      owner: String(approvalDraft?.owner || "-").trim() || "-",
      status: String(approvalDraft?.status || "PENDING_REVIEW"),
      eta: String(approvalDraft?.eta || "").trim() || "-",
      notes: String(approvalDraft?.notes || "-").trim() || "-",
      timestamp: String(approvalDraft?.timestamp || nowIso),
    },
    context: {
      decision_consolidated: decision,
      risk_level: riskLevel,
      checks_pass: `${passedChecks}/${readinessChecksLength}`,
      checks_failed: failedChecks,
      readiness_version: String(stubReadiness?.readiness_version || "-"),
      d11_total_items: d11_total,
      d11_generated_at: d11_gen,
      d11_unique_orders_with_gaps: d11_unique_orders,
    },
    d13_critical_checklist: {
      owner: String(approvalDraft?.owner || "-").trim() || "-",
      eta: String(approvalDraft?.eta || "").trim() || "-",
      total_items: 0,
      done_items: 0,
      items: [],
    },
  };
}
