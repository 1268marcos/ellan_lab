
/**
 * Sprint 3 P0-3 — runbook + checklist de resposta a incidente (Fiscal/OPS).
 * Conteúdo versionado para export auditável (referência estática).
 */

export const SPRINT3_INCIDENT_RUNBOOK_VERSION = "sprint3-incident-runbook-v3-1-p03-presencial-evidence";

/** Duração alvo da tabletop assistida (P0-3). */
export const SPRINT3_ASSISTED_SIMULATION_DURATION_MIN = 15;

/**
 * Roteiro minuto-a-minuto (15 min) — referência para facilitador; espelhado no stamp JSON.
 * @type {{ minute_start: number, minute_end: number, phase: string, title: string, facilitator_actions: string[] }[]}
 */
export const SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M = [
  {
    minute_start: 0,
    minute_end: 3,
    phase: "OPEN",
    title: "Abertura — contexto e papéis",
    facilitator_actions: [
      "Ler incident_id / severidade; confirmar owner e canal Slack/Teams.",
      "Abrir fiscal/slo-alerts em paralelo se houver suspeita de emissor.",
    ],
  },
  {
    minute_start: 3,
    minute_end: 7,
    phase: "TRIAGE",
    title: "Triagem — escopo e impacto",
    facilitator_actions: [
      "Marcar checklist triage_scope; estimar volume e países.",
      "Copiar correlation_keys alvo (order_id, partner_id) para o quadro.",
    ],
  },
  {
    minute_start: 7,
    minute_end: 11,
    phase: "TABLETOP",
    title: "Tabletop — mitigação + comunicação",
    facilitator_actions: [
      "Percorrer mitigation + comms com decisão explícita (rollback vs contenção).",
      "Simular postagem de handoff (texto curto) com severidade e ETA.",
    ],
  },
  {
    minute_start: 11,
    minute_end: 14,
    phase: "EVIDENCE",
    title: "Evidência — anexos mínimos",
    facilitator_actions: [
      "Preencher evidence_capture; colar 1 link ou ID de ticket no bloco de anexos.",
      "Validar que checklist atinge ≥4/6 antes do carimbo final (recomendado).",
    ],
  },
  {
    minute_start: 14,
    minute_end: 15,
    phase: "CLOSE",
    title: "Encerramento — carimbo + daily",
    facilitator_actions: [
      "Gravar carimbo assistido na página; exportar ZIP local ou gerar pacote diário com token.",
      "Registrar item pós-incidente (uma linha) para backlog hardening.",
    ],
  },
];

/** Comandos de laboratório para correr a simulação (15 min) + teste do runbook. */
export const SPRINT3_ASSISTED_SIMULATION_15MIN_COMMANDS = [
  "cd 01_source/frontend && npm run dev",
  "# Navegador: abrir /fiscal/incident-response (ex.: http://127.0.0.1:5173/fiscal/incident-response)",
  "cd 01_source/frontend && npm run sprint3:p03-sim",
  "cd 01_source/frontend && npm run sprint3:p03-sim -- --presencial",
];

/**
 * Evidência mínima drill presencial (agenda + participantes + alinhamento ao carimbo `simulation_stamps`).
 * Preencher no `localStorage` via cockpit `fiscal/incident-response` (campos opcionais) antes do ZIP diário.
 */
export const SPRINT3_PRESENCIAL_DRILL_EVIDENCE_TEMPLATE = {
  agenda_session_id: "p03-drill-{YYYYMMDD}-turno-{A|B|C}",
  agenda_started_at: "ISO8601",
  agenda_ended_at: "ISO8601",
  turn_label: "ex.: triagem / tabletop / encerramento",
  participants: [{ name: "", role: "OPS|Fiscal|Parceiro|Suporte|..." }],
  facilitator_signoff: { name: "", signed_at: "ISO8601" },
  linked_simulation_stamp_ids: ["sprint3_sim_<timestamp>"],
};

/**
 * @param {{ agenda_session_id?: string, turn_label?: string, participants_lines?: string, signoff_name?: string }} raw
 * @param {string} signedAtIso
 */
export function buildPresencialDrillEvidenceFromForm(raw, signedAtIso) {
  const agenda = String(raw?.agenda_session_id || "").trim();
  const turn = String(raw?.turn_label || "").trim();
  const agendaStarted = String(raw?.agenda_started_at || "").trim();
  const agendaEnded = String(raw?.agenda_ended_at || "").trim();
  const lines = String(raw?.participants_lines || "")
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map((line) => {
      const [name, role] = line.split("|").map((x) => x.trim());
      return { name: name || line, role: role || "-" };
    });
  const signoffName = String(raw?.signoff_name || "").trim();
  if (!agenda && lines.length === 0 && !turn && !signoffName && !agendaStarted && !agendaEnded) return null;
  const out = {
    agenda_session_id: agenda || "-",
    turn_label: turn || "-",
    participants: lines.length ? lines : [{ name: "-", role: "-" }],
    facilitator_signoff: {
      name: signoffName || "-",
      signed_at: signedAtIso || new Date().toISOString(),
    },
  };
  if (agendaStarted) out.agenda_started_at = agendaStarted;
  if (agendaEnded) out.agenda_ended_at = agendaEnded;
  return out;
}

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

export const SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO = `Simulação assistida Sprint 3 (tabletop ${SPRINT3_ASSISTED_SIMULATION_DURATION_MIN} min — ver SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M)`;

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
  const presencial =
    d.presencial_drill && typeof d.presencial_drill === "object" && Object.keys(d.presencial_drill).length
      ? d.presencial_drill
      : null;
  const out = {
    scope: "SPRINT3_P0_3_ASSISTED_SIMULATION_STAMP",
    runbook_version: SPRINT3_INCIDENT_RUNBOOK_VERSION,
    generated_at: nowIso,
    source_attach: String(sourceAttach || "unknown"),
    stamp_attach_scope: "SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH",
    daily_zip_filename_pattern: "ELLAN_FISCAL_DAILY_{YYYYMMDD}_SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH_{ts}.json",
    simulation_duration_min: SPRINT3_ASSISTED_SIMULATION_DURATION_MIN,
    simulation_timeline: SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M,
    cli_commands_reference: SPRINT3_ASSISTED_SIMULATION_15MIN_COMMANDS,
    presencial_drill_template_ref: "SPRINT3_PRESENCIAL_DRILL_EVIDENCE_TEMPLATE",
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
  if (presencial) out.presencial_drill = presencial;
  return out;
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

