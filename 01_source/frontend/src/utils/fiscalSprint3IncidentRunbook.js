/**
 * Sprint 3 P0-3 — runbook + checklist de resposta a incidente (Fiscal/OPS).
 * Conteúdo versionado para export auditável (referência estática).
 */

export const SPRINT3_INCIDENT_RUNBOOK_VERSION = "sprint3-incident-runbook-v1";

export const SPRINT3_INCIDENT_CHECKLIST = [
  {
    id: "triage_scope",
    label: "Triagem — confirmar escopo e impacto",
    hint: "Pedido/emissor/país afetados; janela de tempo; volume estimado.",
  },
  {
    id: "correlation_keys",
    label: "Correlação — coletar chaves mínimas",
    hint: "order_id, invoice_id, partner_id, batch_id (usar fiscal/slo-alerts evidência P0-1 quando aplicável).",
  },
  {
    id: "evidence_capture",
    label: "Evidência — consolidar artefatos",
    hint: "Logs, JSON exportado, screenshots, IDs de ticket; colar no bloco de anexos desta página.",
  },
  {
    id: "mitigation",
    label: "Mitigação — ação imediata segura",
    hint: "Rollback controlado (flags provider), reprocesso, ou contenção; documentar decisão.",
  },
  {
    id: "comms",
    label: "Comunicação — handoff padronizado",
    hint: "Slack/Teams + stakeholders; incluir severidade, owner e ETA.",
  },
  {
    id: "post_incident",
    label: "Pós-incidente — slot de revisão",
    hint: "Registrar causa provável e item de backlog para hardening.",
  },
];

export const SPRINT3_INCIDENT_RUNBOOK_LINKS = [
  { id: "ops_health", label: "OPS — Saúde operacional", path: "/ops/health", note: "Visão geral + pacote diário." },
  {
    id: "ops_quick_enablement",
    label: "OPS — Treinamento rápido (Sprint 3)",
    path: "/ops/quick-enablement",
    note: "Checklist OPS/Suporte + export auditável de sessão.",
  },
  { id: "ops_fiscal_providers", label: "OPS — Providers fiscais", path: "/ops/fiscal/providers", note: "BR/PT + gaps D11." },
  { id: "fiscal_slo", label: "FISCAL — SLO + auditoria E2E", path: "/fiscal/slo-alerts", note: "Scorecard + evidência P0-1." },
  {
    id: "fiscal_sprint4_regression_matrix",
    label: "FISCAL — Matriz Sprint 4 (regressão por persona)",
    path: "/fiscal/sprint4-regression-matrix",
    note: "Checklist mínimo + export JSON assinado para Go/No-Go.",
  },
  { id: "fiscal_management", label: "FISCAL — Gestão diária", path: "/fiscal/management-daily", note: "Aprovação e pacotes diários." },
  { id: "ops_dev_errors", label: "OPS — Erros UI", path: "/ops/dev/errors", note: "Telemetria de front + macros." },
];

/** Mesma chave que `FiscalIncidentResponsePage` — pacotes diários leem daqui. */
export const SPRINT3_INCIDENT_RESPONSE_STORAGE_KEY = "fiscal_incident_response:sprint3_p03_v1";

export const SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO = "Simulação assistida Sprint 3 (tabletop 15–20 min)";

export function loadSprint3IncidentResponseDraft() {
  try {
    const raw = window.localStorage.getItem(SPRINT3_INCIDENT_RESPONSE_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Payload fonte (sem envelope SHA-256). `draft` opcional: objeto persistido ou snapshot em memória.
 */
export function buildSprint3AssistedSimulationStampPayload(nowIso, sourceAttach, draft) {
  const d = draft ?? loadSprint3IncidentResponseDraft() ?? {};
  const stamps = Array.isArray(d.simulation_stamps) ? d.simulation_stamps.slice(-15) : [];
  return {
    scope: "SPRINT3_P0_3_ASSISTED_SIMULATION_STAMP",
    runbook_version: SPRINT3_INCIDENT_RUNBOOK_VERSION,
    generated_at: nowIso,
    source_attach: String(sourceAttach || "unknown"),
    incident: {
      incident_id: String(d.incident_id || "").trim() || "-",
      owner: String(d.owner || "").trim() || "-",
      severity: String(d.severity || "MEDIUM"),
    },
    scenario_default: SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO,
    scenario_draft: String(d.simulation_scenario || SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO),
    stamps_count: stamps.length,
    stamps,
  };
}

/**
 * Anexa carimbo P0-3 ao ZIP diário se houver pelo menos um registro em localStorage.
 * @returns {Promise<{ attached: string[] }>}
 */
export async function appendSprint3P03OptionalSignedZipEntries({
  buildSignedPayload,
  strToU8,
  fileBasePrefix,
  ts,
  nowIso,
  zipEntries,
  source,
}) {
  const draft = loadSprint3IncidentResponseDraft();
  const stamps = Array.isArray(draft?.simulation_stamps) ? draft.simulation_stamps : [];
  if (stamps.length === 0) {
    return { attached: [] };
  }
  const payload = buildSprint3AssistedSimulationStampPayload(nowIso, source, draft);
  const signed = await buildSignedPayload(payload);
  const name = `${fileBasePrefix}_SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH_${ts}.json`;
  zipEntries[name] = strToU8(JSON.stringify(signed, null, 2));
  return { attached: ["sprint3_p03_simulation_stamp"] };
}
