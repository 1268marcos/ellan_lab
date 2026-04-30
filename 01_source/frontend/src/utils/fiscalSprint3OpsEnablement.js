/**
 * Sprint 3 — treinamento rápido operacional (OPS / Suporte).
 * Checklist curto + evidência exportável (mesmo padrão SHA-256 / prefixo diário).
 */

export const OPS_ENABLEMENT_STORAGE_KEY = "ellan_ops_sprint3_quick_training_v1";
export const OPS_ENABLEMENT_VERSION = "sprint3-ops-enablement-v1";
export const OPS_ENABLEMENT_PAGE_VERSION = "ops/quick-enablement v1.0.0";

/** @typedef {{ id: string, label: string, description: string, path: string }} EnablementItem */

/** @type {EnablementItem[]} */
export const OPS_ENABLEMENT_CHECKLIST = [
  {
    id: "ops_health",
    label: "OPS / health",
    description: "Revisar decisão FG-1, handoff e pacote diário quando no turno.",
    path: "/ops/health",
  },
  {
    id: "fiscal_slo",
    label: "Fiscal / SLO scorecard",
    description: "Ler severidade, perfil de calibragem BR/PT e playbook endurecer vs investigar.",
    path: "/fiscal/slo-alerts",
  },
  {
    id: "fiscal_incident",
    label: "Fiscal / incident response",
    description: "Runbook + checklist de incidente; export ZIP/JSON quando houver simulação.",
    path: "/fiscal/incident-response",
  },
  {
    id: "fiscal_management_daily",
    label: "Fiscal / management daily",
    description: "Pacote diário com D16, P0-1b e Sprint 4 opcional a partir do localStorage.",
    path: "/fiscal/management-daily",
  },
  {
    id: "ops_fiscal_providers",
    label: "OPS / fiscal providers",
    description: "Gaps D11, batch_id e severidade; publicar lote para handoff quando necessário.",
    path: "/ops/fiscal/providers",
  },
  {
    id: "fiscal_sprint4_matrix",
    label: "Fiscal / Sprint 4 matriz",
    description: "Em pré-produção: registrar rodada piloto e exportar evidência.",
    path: "/fiscal/sprint4-regression-matrix",
  },
  {
    id: "ops_reconciliation_audit",
    label: "OPS / reconciliação ou auditoria",
    description: "Lookup por order_id conforme caso (reconciliação ou audit trail).",
    path: "/ops/reconciliation",
  },
];

export function loadOpsEnablementStateRaw() {
  try {
    const raw = window.localStorage.getItem(OPS_ENABLEMENT_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/**
 * @param {Record<string, { done?: boolean }> | null | undefined} savedById
 */
export function mergeOpsEnablementChecklist(savedById) {
  const map = savedById && typeof savedById === "object" ? savedById : {};
  return OPS_ENABLEMENT_CHECKLIST.map((item) => {
    const prev = map[item.id] || {};
    return {
      ...item,
      done: Boolean(prev.done),
      marked_at: prev.marked_at || null,
    };
  });
}

export function computeOpsEnablementProgress(rows) {
  const total = rows.length;
  const done = rows.filter((r) => r.done).length;
  const pct = total > 0 ? Math.round((done / total) * 1000) / 10 : 0;
  return { total, done, pct };
}

/**
 * @param {string} nowIso
 * @param {{ trainee: string, role: string, notes: string, rows: ReturnType<typeof mergeOpsEnablementChecklist> }} body
 */
export function buildOpsEnablementTrainingPayload(nowIso, { trainee, role, notes, rows }) {
  const progress = computeOpsEnablementProgress(rows);
  return {
    scope: "SPRINT3_OPS_SUPPORT_QUICK_TRAINING",
    generated_at: nowIso,
    version: OPS_ENABLEMENT_VERSION,
    page_version: OPS_ENABLEMENT_PAGE_VERSION,
    storage: { key: OPS_ENABLEMENT_STORAGE_KEY },
    trainee: String(trainee || "").trim() || "-",
    role: String(role || "").trim() || "-",
    session_notes: String(notes || "").trim() || "-",
    progress,
    checklist: rows.map((r) => ({
      id: r.id,
      label: r.label,
      path: r.path,
      done: r.done,
      marked_at: r.marked_at,
    })),
  };
}
